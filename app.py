import streamlit as st
import matplotlib.pyplot as plt
from crawler import get_categories, get_products, get_reviews
from analyzer import analyze_reviews
from PIL import Image
import webbrowser

plt.rcParams['font.family'] = 'Malgun Gothic'  # 한글 폰트 설정
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="Review AI Dashboard", layout="wide")
st.title("🛍️ MUSINSA 상품 리뷰 AI분석")

# --- Sidebar ---
image = Image.open("assets/musinsa.png")
st.sidebar.image(image)
st.sidebar.header("카테고리 및 상품 선택")

categories = get_categories()
category_name = st.sidebar.selectbox("카테고리 선택", list(categories.keys()))
category_id = categories[category_name]

products = get_products(category_id)
product_names = products["goodsName"].tolist()
selected_product = st.sidebar.selectbox("상품 선택", product_names)

product_id = None
product_img = None

if selected_product:
    selected_row = products[products["goodsName"] == selected_product].iloc[0]
    product_id = selected_row["product_id"]   # 실제 product_id 컬럼명 확인 필요
    product_img = selected_row["thumbnail"] if "thumbnail" in products.columns else None

# --- Main Content ---
if selected_product:
    brand_name = selected_row["brandName"] if "brandName" in products.columns else ""

    with st.container():
        st.markdown("### 🛒 상품 정보")

        col1, col2 = st.columns([1, 2])  # 왼쪽: 이미지 / 오른쪽: 정보

        with col1:
            if product_img:
                st.image(product_img, width=200)

        with col2:
            st.subheader(f"[{brand_name}] {selected_product}")

            # 가격
            if "price" in selected_row:
                price = selected_row["price"]
                st.markdown(f"**💰 가격:** {price:,} 원")

            # 상품 링크 버튼
            if "goodsLinkUrl" in selected_row and selected_row["goodsLinkUrl"]:
                if st.button("🛒 구매하기"):
                    webbrowser.open(selected_row["goodsLinkUrl"])

            # ⭐ 리뷰 평점 표시 (별 아이콘)
            if "reviewScore" in selected_row:
                review_score = float(selected_row["reviewScore"]) / 20  # 0~100 → 0~5 변환
                full_stars = int(review_score)
                half_star = review_score - full_stars >= 0.5
                stars = "⭐" * full_stars + ("✩" if half_star else "")
                st.write(f"사용자 평점: {stars} ({review_score:.1f}/5.0)")

            # 리뷰 개수 표시
            if "reviewCount" in selected_row:
                review_count = int(selected_row["reviewCount"])
                st.markdown(f"**📝 리뷰 개수:** {review_count:,}개")

    # 리뷰 불러오기
    reviews = get_reviews(product_id)

    if hasattr(reviews, "columns"):  # DataFrame일 경우
        review_texts = reviews["content"].dropna().tolist()
    elif isinstance(reviews, list) and len(reviews) > 0 and isinstance(reviews[0], dict):
        review_texts = [r["content"] for r in reviews if "content" in r]
    else:
        review_texts = reviews

    if review_texts:
        st.info(f"총 {len(review_texts)}개의 리뷰 AI 분석 결과입니다.")
        analysis_result = analyze_reviews(review_texts)

        with st.container():
            st.markdown("### 📊 리뷰 분석 결과")

            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(analysis_result.get("summary", "분석 요약 없음"))
                st.markdown("**키워드:** " + ", ".join(analysis_result.get("keywords", [])))

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

        # 긍정 / 부정 TOP3 리뷰
        st.markdown("### 📝 상세 리뷰 요약")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 👍 긍정적인 리뷰 Top3")
            for idx, review in enumerate(analysis_result.get("top_positive", []), 1):
                st.markdown(f"{idx}. {review}")

        with col2:
            st.markdown("#### 👎 부정적인 리뷰 Top3")
            for idx, review in enumerate(analysis_result.get("top_negative", []), 1):
                st.markdown(f"{idx}. {review}")

        # 구매자 한마디
        if "common_opinion" in analysis_result:
            st.markdown("### 이런 구매자들이 사면 좋아요!")
            st.info(analysis_result["common_opinion"])

    else:
        st.warning("해당 상품에 대한 리뷰가 아직 없습니다.")
