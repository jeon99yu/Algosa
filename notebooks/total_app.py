import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import webbrowser
from PIL import Image
from sqlalchemy import text
from sklearn.feature_extraction.text import CountVectorizer
from wordcloud import WordCloud

from analyzer import summarize_reviews, summarize_size_and_fit, summarize_coordination
from crawler import run_all_crawlers
from config import engine

# -------------------------
# 기본 설정
# -------------------------
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="ALGOSA", layout="wide")

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
st.title("🛍️ MUSINSA 상품리뷰")

# -------------------------
# 사이드바
# -------------------------
CATEGORY_MAP = {
    "스니커즈": "103004",
    "스포츠화": "103005",
    "구두": "103001",
}
if os.path.exists("assets/musinsa.png"):
    st.sidebar.image(Image.open("assets/logo.png"), use_container_width=True)

st.sidebar.header("카테고리 선택")
selected_category_name = st.sidebar.selectbox("카테고리를 선택하세요", list(CATEGORY_MAP.keys()))
selected_category_code = CATEGORY_MAP[selected_category_name]

if st.sidebar.button("데이터 새로 수집"):
    with st.spinner("전체 카테고리 크롤링 중..."):
        run_all_crawlers(num_products=60, max_reviews=300)
    st.success("데이터 수집 및 DB 저장 완료")

# -------------------------
# 데이터 로드
# -------------------------
@st.cache_data(ttl=300)
def load_products_by_category(cat_code: str) -> pd.DataFrame:
    query = """
        SELECT product_id, brandName, goodsName, price, reviewCount, reviewScore,
               thumbnail, goodsLinkUrl, category
        FROM products
        WHERE category = %s
    """
    return pd.read_sql(query, engine, params=(cat_code,))

try:
    products = load_products_by_category(selected_category_code)

    if products.empty:
        st.warning("⚠️ 선택한 카테고리에 상품이 없습니다.")
        st.stop()

    # st.success(f"총 {len(products)}개의 상품을 불러왔습니다.")

    # 상품 선택
    products["display_name"] = products["brandName"] + " | " + products["goodsName"]
    selected_display = st.selectbox("상품을 선택하세요", products["display_name"].tolist())
    selected_row = products.loc[products["display_name"] == selected_display].iloc[0]
    selected_product_id = selected_row["product_id"]

    # -------------------------
    # 선택된 상품 정보
    # -------------------------
    st.subheader("상품 정보")
    c1, c2 = st.columns([1, 2], vertical_alignment="center")
    with c1:
        if pd.notna(selected_row.get("thumbnail")) and str(selected_row["thumbnail"]).startswith("http"):
            st.image(selected_row["thumbnail"], width=200)
        else:
            st.image("https://via.placeholder.com/200x200.png?text=No+Image", width=200)
    with c2:
        st.write(f"**브랜드:** {selected_row['brandName']}")
        st.write(f"**상품명:** {selected_row['goodsName']}")
        st.write(f"**가격:** {selected_row['price']:,}원" if selected_row["price"] else "가격 정보 없음")
        st.write(f"**리뷰:** {selected_row['reviewCount']:,}개")
        st.write(f"**평점:** {int(selected_row['reviewScore'])}/100점")
        if selected_row.get("goodsLinkUrl"):
            st.link_button("🛒 구매하기", selected_row["goodsLinkUrl"])

    # -------------------------
    # 리뷰 조회 (먼저 정제 후 공통 활용)
    # -------------------------
    st.divider()
    
    sql = text(
        """
        SELECT review_no, product_id, createDate, userNickName, content, grade
        FROM reviews
        WHERE product_id = :pid
        ORDER BY createDate DESC
        """
    )
    reviews_df = pd.read_sql(sql, engine, params={"pid": selected_product_id})

    if reviews_df.empty:
        st.warning("⚠️ 해당 상품에 리뷰가 없습니다.")
        st.stop()

    # grade 정수화 → 이후 모든 분석에서 재사용
    reviews_df["grade"] = pd.to_numeric(reviews_df["grade"], errors="coerce")
    reviews_df = reviews_df.dropna(subset=["grade"]).assign(grade=lambda d: d["grade"].astype(int))
    reviews_texts = reviews_df["content"].dropna().astype(str).tolist()

    # -------------------------
    # KPI 요약
    # -------------------------
    total_reviews = len(reviews_df)
    pos = int((reviews_df["grade"] >= 4).sum())
    neg = int((reviews_df["grade"] <= 2).sum())
    neu = int(total_reviews - pos - neg)
    unique_users = int(reviews_df["userNickName"].nunique())
    date_min = pd.to_datetime(reviews_df["createDate"], errors="coerce").min()
    date_max = pd.to_datetime(reviews_df["createDate"], errors="coerce").max()

    st.markdown("#### 📌 요약 지표")
    m1, m2, m3 = st.columns(3)
    m1.metric("분석대상 리뷰 수", f"{total_reviews:,}")
    m2.metric("긍정 / 중립 / 부정", f"{pos:,} / {neu:,} / {neg:,}")
    m3.metric(
        "수집 리뷰 기간",
        f"{date_min:%Y-%m-%d} ~ {date_max:%Y-%m-%d}" if pd.notna(date_min) else "기간 정보 없음",
    )

    # -------------------------
    # 탭 구성
    # -------------------------
    tab1_label = f"📊 리뷰 분석 ({total_reviews:,})"
    tab2_label = "👟 사이즈·코디"
    tab3_label = "🔤 키워드"

    tab1, tab2, tab3 = st.tabs([tab1_label, tab2_label, tab3_label])

    # =======================
    # Tab 1: 리뷰 분석
    # =======================
    with tab1:
        st.markdown("### 📊 리뷰 분석 결과")

        labels = ["긍정", "중립", "부정"]
        if total_reviews:
            values = [
                pos / total_reviews * 100,
                neu / total_reviews * 100,
                neg / total_reviews * 100,
            ]
        else:
            values = [0, 0, 0]

        t1c1, t1c2 = st.columns([1, 1])
        t1c3, t1c4 = st.columns([1, 1])

        with t1c1:
            fig, ax = plt.subplots(figsize=(4.6, 4.6), dpi=140)
            if sum(values) > 0:
                colors = ["#4CAF50", "#FFC107", "#F44336"]

                def _autopct(pct):
                    return f"{pct:.0f}%" if pct >= 5 else ""

                wedges, _texts, _autotexts = ax.pie(
                    values,
                    startangle=90,
                    labels=None,
                    autopct=_autopct,
                    pctdistance=0.8,
                    wedgeprops=dict(width=0.55, edgecolor="white"),
                    colors=colors,
                )
                ax.text(
                    0,
                    0,
                    f"총 {total_reviews}\n리뷰",
                    ha="center",
                    va="center",
                    fontsize=13,
                    fontweight="bold",
                    linespacing=1.2,
                )
                legend_labels = [f"{l} {v:.0f}%" for l, v in zip(labels, values)]
                ax.legend(
                    wedges,
                    legend_labels,
                    loc="center left",
                    bbox_to_anchor=(1.02, 0.5),
                    frameon=False,
                    borderaxespad=0.0,
                )
                ax.set(aspect="equal")
                plt.tight_layout()
                st.pyplot(fig, use_container_width=False)
            else:
                ax.text(0.5, 0.5, "데이터 없음", ha="center", va="center")
                ax.set(aspect="equal")
                plt.tight_layout()
                st.pyplot(fig, use_container_width=False)

        # 전반 요약
        summary_result = summarize_reviews(reviews_texts, sample_size=50)

        with t1c2:
            st.markdown("#### ✅ 전반적인 평가")
            st.write(summary_result.get("positive_negative", "요약 없음"))

        with t1c3:
            st.markdown("#### ⚠️ 주의해야 할 점")
            for c in summary_result.get("cautions", []):
                st.error(c)

        with t1c4:
            st.markdown("#### 💬 자주 언급된 특징")
            for f in summary_result.get("features", []):
                st.success(f)

    # =======================
    # Tab 2: 사이즈/코디
    # =======================
    with tab2:
        st.markdown("### 👟 구매자들이 느낀 사이즈 체감입니다.")
        size_res = summarize_size_and_fit(reviews_texts, sample_size=80)
        st.info(size_res.get("size_summary", "요약 없음"))
        for r in size_res.get("recommendations", []):
            st.warning(r)

        st.divider()

        st.markdown("### 💁‍♂️ 이런 분이라면 만족하실 거예요.")
        coord_res = summarize_coordination(reviews_texts, sample_size=80)
        st.info(coord_res.get("coord_summary", "요약 없음"))
        for t in coord_res.get("outfit_tips", []):
            st.success(t)

    # =======================
    # Tab 3: 키워드(워드클라우드 + 리더보드)
    # =======================
    with tab3:
        st.markdown("### 🔤 리뷰 키워드 분석")

        stopwords = [
            "정도",
            "조금",
            "그리고",
            "그러나",
            "하지만",
            "사용",
            "제품",
            "구매",
            "리뷰",
            "가격",
            "배송",
            "신발",
            "운동화",
            "브랜드",
            "디자인",
            "평가",
            "사용자",
            "부분",
            "좀",
            "것",
            "거",
            "이번",
            "처음",
        ]

        if len(reviews_texts) == 0:
            st.info("키워드 분석할 리뷰가 없습니다.")
        else:
            vectorizer = CountVectorizer(
                token_pattern=r"(?u)[가-힣]{2,}",
                stop_words=stopwords,
                max_features=2000,
            )
            X = vectorizer.fit_transform(reviews_texts)
            counts = np.asarray(X.sum(axis=0)).ravel()
            words = vectorizer.get_feature_names_out()
            freq = dict(zip(words, counts))

            if not freq:
                st.info("표시할 키워드가 없습니다.")
            else:
                topn = st.slider("표시 개수", 5, 30, 15, 1, key="kw_topn_tab3")
                items = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:topn]
                kw_df = pd.DataFrame(items, columns=["keyword", "count"])

                k1, k2 = st.columns([1, 1])

                with k1:
                    def _font_path():
                        cands = [
                            "C:/Windows/Fonts/malgun.ttf",
                            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                        ]
                        for p in cands:
                            if os.path.exists(p):
                                return p
                        return None

                    font_path = _font_path()
                    if font_path:
                        wc = WordCloud(
                            font_path=font_path,
                            width=900,
                            height=500,
                            background_color="white",
                            prefer_horizontal=0.9,
                            max_words=200,
                        ).generate_from_frequencies(freq)
                        fig_wc, ax_wc = plt.subplots(figsize=(6.4, 3.8), dpi=140)
                        ax_wc.imshow(wc)
                        ax_wc.axis("off")
                        plt.tight_layout()
                        st.pyplot(fig_wc, use_container_width=True)
                    else:
                        st.info("한글 폰트를 찾지 못해 워드클라우드를 표시할 수 없습니다.")

                with k2:
                    fig_bar, ax_bar = plt.subplots(figsize=(6.2, 5.0), dpi=140)
                    ax_bar.barh(kw_df["keyword"][::-1], kw_df["count"][::-1], color="#FF5252")
                    ax_bar.set_xlabel("count")
                    ax_bar.set_ylabel("")
                    ax_bar.set_title(f"키워드 TOP {topn}")
                    ax_bar.invert_yaxis()
                    for i, v in enumerate(kw_df["count"][::-1].tolist()):
                        ax_bar.text(v + max(kw_df["count"]) * 0.01, i, str(int(v)), va="center")
                    plt.tight_layout()
                    st.pyplot(fig_bar, use_container_width=True)

    # -------------------------
    # 리뷰 원본 테이블(접기/펼치기)
    # -------------------------

    st.divider()
    st.subheader("선택된 상품 리뷰")

    with st.expander("📊 선택된 상품 리뷰 목록 보기", expanded=False):
        show_cols = ["userNickName", "content", "grade", "createDate"]
        _df = reviews_df.loc[:, show_cols].copy()
        _df["grade"] = pd.to_numeric(_df["grade"], errors="coerce").astype("Int64")
        _df["createDate"] = pd.to_datetime(_df["createDate"], errors="coerce").dt.strftime("%Y-%m-%d")
        _df = _df.sort_values("createDate", ascending=False, na_position="last")
        _df = _df.rename(columns={"userNickName": "닉네임", "content": "내용", "grade": "평점", "createDate": "작성일"})
        st.dataframe(_df, use_container_width=True, hide_index=True)

    with st.expander("🛒 무신사 추천상품 목록 보기", expanded=False):
        st.dataframe(products, use_container_width=True)

except Exception as e:
    st.error(f"DB에서 데이터를 불러오는 중 오류 발생: {e}")
