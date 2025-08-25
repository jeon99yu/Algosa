# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import webbrowser
from db import load_products, load_reviews
from analyzer import summarize_reviews
from config import engine

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="ALGOSA", layout="wide")
st.title("🛍️ MUSINSA 상품리뷰")

def load_reviews(product_id=None):
    if product_id:
        query = f"SELECT * FROM reviews WHERE product_id = '{product_id}' LIMIT 300"
    else:
        query = "SELECT * FROM reviews LIMIT 300"
    return pd.read_sql(query, engine)

try:
    products = pd.read_sql(
        "SELECT product_id, brandName, goodsName, price, reviewCount, reviewScore, thumbnail, goodsLinkUrl FROM products",
        engine
    )

    if not products.empty:
        st.success(f"총 {len(products)}개의 상품을 불러왔습니다.")
        products["display_name"] = products["brandName"] + " | " + products["goodsName"]

        selected_display = st.sidebar.selectbox("상품 선택", products["display_name"].tolist())
        selected_row = products[products["display_name"] == selected_display].iloc[0]
        selected_product_id = selected_row['product_id']

        # 상품 정보
        st.subheader("📦 선택된 상품 정보")
        col1, col2 = st.columns([1, 2])
        with col1:
            if pd.notna(selected_row.get("thumbnail")) and str(selected_row["thumbnail"]).startswith("http"):
                st.image(selected_row["thumbnail"], width=200)
            else:
                st.image("https://via.placeholder.com/200x200.png?text=No+Image", width=200)
        with col2:
            st.write(f"**브랜드:** {selected_row['brandName']}")
            st.write(f"**상품명:** {selected_row['goodsName']}")
            st.write(f"**가격:** {selected_row['price']:,}원" if selected_row['price'] else "가격 정보 없음")
            st.write(f"**리뷰:** {selected_row['reviewCount']:,}개")
            st.write(f"**평점:** {int(selected_row['reviewScore'])}/100점")
            if "goodsLinkUrl" in selected_row and selected_row["goodsLinkUrl"]:
                if st.button("🛒 구매하기"):
                    webbrowser.open(selected_row["goodsLinkUrl"])

        # 리뷰
        st.subheader("📝 선택된 상품 리뷰")
        reviews_df = load_reviews(selected_product_id)

        if not reviews_df.empty:
            st.dataframe(reviews_df)

            # 감정 분류
            st.markdown("### 📊 리뷰 분석 결과")
            reviews_df["sentiment"] = reviews_df["grade"].apply(
                lambda g: "긍정" if g >= 4 else ("부정" if g <= 2 else "중립")
            )
            sentiment_counts = reviews_df["sentiment"].value_counts(normalize=True) * 100
            labels = sentiment_counts.index.tolist()
            values = sentiment_counts.values.tolist()

            col1, col2 = st.columns([1, 1])
            col3, col4 = st.columns([1, 1])

            with col1:
                st.write("총 리뷰 개수:", len(reviews_df))
                fig, ax = plt.subplots()
                ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90,
                       colors=["#4CAF50", "#FFC107", "#F44336"])
                ax.axis("equal")
                st.pyplot(fig)

            reviews_texts = reviews_df["content"].dropna().astype(str).tolist()
            summary_result = summarize_reviews(reviews_texts, sample_size=50)

            with col2:
                st.subheader("[전반적인 평가]")
                st.write(summary_result.get("positive_negative", "요약 없음"))
            with col3:
                st.subheader("[자주 언급된 특징]")
                for f in summary_result.get("features", []):
                    st.success(f)
            with col4:
                st.subheader("[소비자가 주의해야 할 점]")
                for c in summary_result.get("cautions", []):
                    st.error(c)
        else:
            st.warning("⚠️ 해당 상품에 리뷰가 없습니다.")

        with st.expander("📊 전체 상품 테이블 보기"):
            st.dataframe(products)
    else:
        st.warning("⚠️ products 테이블이 비어 있습니다.")
except Exception as e:
    st.error(f"DB에서 데이터를 불러오는 중 오류 발생: {e}")

