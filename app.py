import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from config import engine, OPENAI_API_KEY
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="Review AI Dashboard", layout="wide")
st.title("🛍️ MUSINSA 상품 리뷰 AI Dashboard")

# 리뷰 테이블 불러오기 함수
def load_reviews(product_id=None):
    if product_id:
        query = f"SELECT * FROM reviews WHERE product_id = '{product_id}' LIMIT 300"
    else:
        query = "SELECT * FROM reviews LIMIT 300"
    return pd.read_sql(query, engine)

# ✅ DB에서 products 테이블 불러오기
try:
    products = pd.read_sql(
        "SELECT product_id, brandName, goodsName, price, reviewCount, reviewScore, thumbnail, goodsLinkUrl FROM products",
        engine
    )

    if not products.empty:
        st.success(f"총 {len(products)}개의 상품을 불러왔습니다.")
        products["display_name"] = products["brandName"] + " | " + products["goodsName"]

        # 사이드바에서 선택
        selected_display = st.sidebar.selectbox("상품 선택", products["display_name"].tolist())
        selected_row = products[products["display_name"] == selected_display].iloc[0]
        selected_product_id = selected_row['product_id']

        # 선택된 상품 정보 출력
        st.subheader("📦 선택된 상품 정보")
        st.write(f"브랜드: {selected_row['brandName']}")
        st.write(f"상품명: {selected_row['goodsName']}")
        st.write(f"가격: {selected_row['price']:,}원" if selected_row['price'] else "가격 정보 없음")

        # 📌 선택된 상품 리뷰
        reviews_df = load_reviews(selected_product_id)
        st.subheader("📝 선택된 상품 리뷰")
        st.dataframe(reviews_df)

        # ✅ --- 리뷰 분석 (간단 감정 비율 계산) ---
        if not reviews_df.empty:
            st.markdown("### 📊 리뷰 감정 분석")
            
            # grade 기준으로 단순 긍/중/부 분류 예시
            reviews_df["sentiment"] = reviews_df["grade"].apply(
                lambda g: "긍정" if g >= 4 else ("부정" if g <= 2 else "중립")
            )
            sentiment_counts = reviews_df["sentiment"].value_counts(normalize=True) * 100

            labels = sentiment_counts.index.tolist()
            values = sentiment_counts.values.tolist()

            col1, col2 = st.columns([1, 1])
            with col1:
                st.write("총 리뷰 개수:", len(reviews_df))
                fig, ax = plt.subplots()
                ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=["#4CAF50", "#FFC107", "#F44336"])
                ax.axis("equal")
                st.pyplot(fig)

            with col2:
                st.write("📌 감정 분포 (%)")
                for lbl, val in zip(labels, values):
                    st.write(f"- {lbl}: {val:.1f}%")

            # ✅ --- LLM을 이용한 요약 ---
            st.markdown("### 🧠 전반적인 평가 요약 (AI)")
            sample_reviews = "\n".join(reviews_df["content"].dropna().astype(str).head(50).tolist())  # 앞 50개만 샘플링
            prompt = f"""
            다음은 어떤 상품에 대한 리뷰 모음입니다.
            리뷰를 읽고 전체적인 평가를 요약해 주세요.
            - 긍정/부정 의견 핵심
            - 자주 언급되는 특징
            - 소비자들이 주의해야 할 점

            리뷰:
            {sample_reviews}

            출력은 한국어 요약문으로 작성해 주세요.
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "You are a helpful review analysis assistant."},
                              {"role": "user", "content": prompt}],
                    max_tokens=500
                )
                summary = response.choices[0].message["content"]
                st.info(summary)
            except Exception as e:
                st.error(f"LLM 분석 중 오류 발생: {e}")

        # 전체 상품 테이블
        with st.expander("📊 전체 상품 테이블 보기"):
            st.dataframe(products)

    else:
        st.warning("⚠️ products 테이블이 비어 있습니다.")

except Exception as e:
    st.error(f"DB에서 데이터를 불러오는 중 오류 발생: {e}")
