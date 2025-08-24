# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from db import load_products, load_reviews
from analyzer import analyze_reviews

# 페이지 설정
st.set_page_config(page_title="Musinsa Review AI Dashboard", layout="wide")
st.title("🛍️ MUSINSA 상품 리뷰 AI Dashboard")

try:
    # ✅ DB에서 products 테이블 불러오기
    products = load_products()

    if not products.empty:
        st.success(f"총 {len(products)}개의 상품을 불러왔습니다.")
        products["display_name"] = products["brandName"] + " | " + products["goodsName"]

        # 사이드바에서 상품 선택
        selected_display = st.sidebar.selectbox("상품 선택", products["display_name"].tolist())
        selected_row = products[products["display_name"] == selected_display].iloc[0]
        selected_product_id = str(selected_row['product_id'])

        # -------------------------------
        # 📦 선택된 상품 정보 출력
        # -------------------------------
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
            st.write(f"**가격:** {selected_row['price']:,} 원" if selected_row['price'] else "가격 정보 없음")
            st.write(f"**리뷰 개수:** {selected_row['reviewCount']}")
            st.write(f"**평점:** {selected_row['reviewScore']}")

            if selected_row.get("goodsLinkUrl"):
                st.markdown(f"[🛒 구매하러 가기]({selected_row['goodsLinkUrl']})")

        # -------------------------------
        # 📝 선택된 상품 리뷰
        # -------------------------------
        st.subheader("📝 선택된 상품 리뷰")
        reviews_df = load_reviews(selected_product_id)

        if not reviews_df.empty:
            st.dataframe(reviews_df)

            # -------------------------------
            # 🤖 LLM 리뷰 분석
            # -------------------------------
            st.subheader("🤖 리뷰 분석 결과")
            reviews_texts = reviews_df["content"].dropna().astype(str).tolist()
            analysis_result = analyze_reviews(reviews_texts)

            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("**📌 전반적인 요약:**")
                st.write(analysis_result.get("summary", "요약 없음"))

                st.markdown("**✨ 키워드:**")
                st.write(", ".join(analysis_result.get("keywords", [])))

                st.markdown("**👍 TOP 긍정 리뷰:**")
                for pos in analysis_result.get("TOP_POSITIVE", []):
                    st.success(pos)

                st.markdown("**👎 TOP 부정 리뷰:**")
                for neg in analysis_result.get("TOP_NEGATIVE", []):
                    st.error(neg)

                st.markdown("**🛒 구매자 공통 의견:**")
                st.info(analysis_result.get("common_opinion", ""))

            with col2:
                labels = ["긍정", "중립", "부정"]
                values = [
                    int(analysis_result.get("positive", "0%").replace("%", "")),
                    int(analysis_result.get("neutral", "0%").replace("%", "")),
                    int(analysis_result.get("negative", "0%").replace("%", "")),
                ]
                fig, ax = plt.subplots()
                ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
                ax.axis("equal")
                st.pyplot(fig)

        else:
            st.warning("⚠️ 해당 상품에 리뷰가 없습니다.")

        # -------------------------------
        # 📊 전체 상품 테이블
        # -------------------------------
        st.subheader("📊 전체 상품 테이블")
        st.dataframe(products)

    else:
        st.warning("⚠️ products 테이블이 비어 있습니다.")

except Exception as e:
    st.error(f"DB에서 데이터를 불러오는 중 오류 발생: {e}")
