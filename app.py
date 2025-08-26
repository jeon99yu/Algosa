import streamlit as st
import pandas as pd
from sqlalchemy import text

from modules.layout import setup_page, render_sidebar, render_product_info
from modules.data import load_products_by_category, load_reviews_by_product
from modules.tabs import render_tabs
from crawler import run_all_crawlers

setup_page(title="📦 ALGOSA")
st.markdown("####  MUSINSA 상품리뷰 AI분석 서비스")

# 사이드바
CATEGORY_MAP = {"스니커즈": "103004", 
                "스포츠화": "103005", 
                "구두": "103001"}

selected_category_code, do_crawl = render_sidebar(CATEGORY_MAP)

if do_crawl:
    with st.spinner("전체 카테고리 크롤링 중..."):
        run_all_crawlers(num_products=60, max_reviews=300)
    st.success("데이터 수집 및 DB 저장 완료")

products = load_products_by_category(selected_category_code)
if products.empty:
    st.warning("⚠️ 선택한 카테고리에 상품이 없습니다.")
    st.stop()

products["display_name"] = products["brandName"] + " | " + products["goodsName"]
selected_display = st.selectbox("상품을 선택하세요", products["display_name"].tolist())
selected_row = products.loc[products["display_name"] == selected_display].iloc[0]
selected_product_id = selected_row["product_id"]
render_product_info(selected_row)

reviews_df = load_reviews_by_product(selected_product_id)
if reviews_df.empty:
    st.warning("⚠️ 해당 상품에 리뷰가 없습니다.")
    st.stop()

render_tabs(reviews_df, products)
