import os
import streamlit as st
from PIL import Image

def setup_page(title: str):
    st.set_page_config(page_title="알고사(ALGOSA) AI 리뷰분석서비스", layout="wide")

    st.markdown( # CSS 설정
        """
        <style>
          .stMainBlockContainer {
              max-width: 1000px !important;
              padding-left: 2rem !important;
              padding-right: 4rem !important;
              margin: auto !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    st.title(title)

def render_sidebar(category_map: dict[str, str]) -> tuple[str, bool]:
    st.sidebar.image(Image.open("/app/assets/logo/title.png"), use_container_width=True)
    st.sidebar.header("무신사 추천순 🔽")
    
    name = st.sidebar.selectbox("카테고리를 선택하세요", list(category_map.keys()))
    code = category_map[name]
    do_crawl = st.sidebar.button("데이터 새로 수집")
    return code, do_crawl

def render_product_info(row):
    st.subheader("상품 정보")
    c1, c2 = st.columns([1, 2], vertical_alignment="center")
    with c1:
        thumb = row.get("thumbnail")
        if thumb and str(thumb).startswith("http"):
            st.image(thumb, width=200)
        else:
            st.image("https://via.placeholder.com/200x200.png?text=No+Image", width=200)
    with c2:
        st.write(f"**브랜드:** {row['brandName']}")
        st.write(f"**상품명:** {row['goodsName']}")
        st.write(f"**가격:** {row['price']:,}원" if row["price"] else "가격 정보 없음")
        st.write(f"**리뷰:** {row['reviewCount']:,}개")
        st.write(f"**평점:** {int(row['reviewScore'])}/100점")
        if row.get("goodsLinkUrl"):
            st.link_button("🛒 구매하기", row["goodsLinkUrl"])
