import streamlit as st
from crawler import get_categories, get_products, get_reviews
from analyzer import analyze_reviews

st.set_page_config(page_title="Review AI Dashboard", layout="wide")
st.title("🛍️ MUSINSA 상품 리뷰 AI분석")

# --- Sidebar ---
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
    st.subheader(f"[{brand_name}] {selected_product}")
    if product_img:
        st.image(product_img, width=200)

    reviews = get_reviews(product_id)

    # 리뷰를 analyzer에 맞게 문자열 리스트로 변환
    if hasattr(reviews, "columns"):  # DataFrame일 경우
        review_texts = reviews["content"].dropna().tolist()
    elif isinstance(reviews, list) and len(reviews) > 0 and isinstance(reviews[0], dict):  # dict 리스트
        review_texts = [r["content"] for r in reviews if "content" in r]
    else:  # 이미 문자열 리스트라면 그대로
        review_texts = reviews

    if review_texts:
        st.info(f"총 {len(review_texts)}개의 리뷰 AI 분석 결과입니다.")
        analysis_result = analyze_reviews(review_texts)

        # --- LLM 분석 결과 출력 ---
        st.subheader("종합 평가")
        st.write(analysis_result.get("summary", "분석 요약 없음"))
        st.markdown("**키워드:** " + ", ".join(analysis_result.get("keywords", [])))
        st.markdown("---")
        st.markdown("**긍정 비율:** " + str(analysis_result.get("positive", "0%")))
        st.markdown("**중립 비율:** " + str(analysis_result.get("neutral", "0%")))
        st.markdown("**부정 비율:** " + str(analysis_result.get("negative", "0%")))
    else:
        st.warning("해당 상품에 대한 리뷰가 아직 없습니다.")
