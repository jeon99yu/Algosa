import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import webbrowser
from sqlalchemy import text
from analyzer import summarize_reviews
from crawler import run_all_crawlers
from config import engine

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="ALGOSA", layout="wide")
st.title("🛍️ MUSINSA 상품리뷰")

# -------------------------
# 카테고리 매핑
# -------------------------
CATEGORY_MAP = {
    "운동화": "103004",
    "스포츠화": "103005",
    "구두": "103001"
}

# -------------------------
# 사이드바 - 카테고리 선택
# -------------------------
st.sidebar.header("카테고리 선택")
selected_category_name = st.sidebar.selectbox("카테고리를 선택하세요", list(CATEGORY_MAP.keys()))
selected_category_code = CATEGORY_MAP[selected_category_name]

if st.sidebar.button("데이터 새로 수집"):
    st.info("👉 전체 카테고리 크롤링 시작")
    run_all_crawlers(num_products=60, max_reviews=300)
    st.success("데이터 수집 및 DB 저장 완료 ✅")

# -------------------------
# 상품 목록 불러오기
# -------------------------
try:
    query = """
        SELECT product_id, brandName, goodsName, price, reviewCount, reviewScore, 
               thumbnail, goodsLinkUrl, category
        FROM products
        WHERE category = %s
    """
    products = pd.read_sql(query, engine, params=(selected_category_code,))

    if not products.empty:
        st.success(f"총 {len(products)}개의 상품을 불러왔습니다.")

        # 상품 선택
        products["display_name"] = products["brandName"] + " | " + products["goodsName"]
        selected_display = st.selectbox("상품을 선택하세요", products["display_name"].tolist())
        selected_row = products[products["display_name"] == selected_display].iloc[0]
        selected_product_id = selected_row['product_id']

        # -------------------------
        # 선택된 상품 정보
        # -------------------------
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

        # -------------------------
        # 리뷰 테이블
        # -------------------------
        st.subheader("📝 선택된 상품 리뷰")

        sql = text("""
            SELECT review_no, product_id, createDate, userNickName, content, grade
            FROM reviews
            WHERE product_id = :pid
            ORDER BY createDate DESC
        """)
        reviews_df = pd.read_sql(sql, engine, params={"pid": selected_product_id})

        if not reviews_df.empty:
            reviews_df["grade"] = pd.to_numeric(reviews_df["grade"], errors="coerce")
            reviews_df = reviews_df.dropna(subset=["grade"]).assign(grade=lambda d: d["grade"].astype(int))

            with st.expander("🗂️ 선택된 상품 리뷰 테이블 보기", expanded=False):
                show_cols = ["userNickName", "content", "grade", "createDate"]
                _df = reviews_df.loc[:, show_cols].copy()
                _df["grade"] = pd.to_numeric(_df["grade"], errors="coerce").astype("Int64")
                _df["createDate"] = pd.to_datetime(_df["createDate"], errors="coerce").dt.strftime("%Y-%m-%d")
                _df = _df.sort_values("createDate", ascending=False, na_position="last")
                _df = _df.rename(columns={"userNickName": "닉네임","content": "내용","grade": "평점","createDate": "작성일"})

                st.dataframe(_df, use_container_width=True, hide_index=True)
            
            st.markdown("### 📊 리뷰 분석 결과")

            # 감정 분류
            reviews_df["sentiment"] = reviews_df["grade"].apply(
                lambda g: "긍정" if g >= 4 else ("부정" if g <= 2 else "중립")
            )
            sentiment_counts = reviews_df["sentiment"].value_counts(normalize=True) * 100

            labels = ["긍정", "중립", "부정"]
            values = [
                sentiment_counts.get("긍정", 0),
                sentiment_counts.get("중립", 0),
                sentiment_counts.get("부정", 0),
            ]

            col1, col2 = st.columns([1, 1])
            col3, col4 = st.columns([1, 1])

            with col1:
                fig, ax = plt.subplots(figsize=(4.6, 4.6), dpi=140)

                if sum(values) > 0:
                    colors=["#4CAF50", "#FFC107", "#F44336"]  

                    def _autopct(pct):
                        return f"{pct:.0f}%" if pct >= 5 else ""

                    wedges, _texts, autotexts = ax.pie(
                        values,
                        startangle=90,
                        labels=None,                   
                        autopct=_autopct,
                        pctdistance=0.8,                
                        wedgeprops=dict(width=0.55, edgecolor="white"),
                        colors=colors
                    )

                    # 가운데 총 리뷰 수(도넛 중앙)
                    ax.text(0, 0, f"총 {len(reviews_df)}\n리뷰", ha="center", va="center", fontsize=13, fontweight="bold", linespacing=1.2)

                    # 우측 범례(퍼센트 포함)
                    legend_labels = [f"{l} {v:.0f}%" for l, v in zip(labels, values)]
                    ax.legend(
                        wedges, legend_labels,
                        loc="center left", bbox_to_anchor=(1.02, 0.5),
                        frameon=False, borderaxespad=0.0
                    )

                    ax.set(aspect="equal")
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=False)

                else:
                    ax.text(0.5, 0.5, "데이터 없음", ha="center", va="center")
                    ax.set(aspect="equal")
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=False)


            reviews_texts = reviews_df["content"].dropna().astype(str).tolist()
            summary_result = summarize_reviews(reviews_texts, sample_size=50)

            with col2:
                st.subheader("[전반적인 평가]")
                st.write(summary_result.get("positive_negative", "요약 없음"))

            with col3:
                st.subheader("[소비자가 주의해야 할 점]")
                for c in summary_result.get("cautions", []):
                    st.error(c)

            with col4:
                st.subheader("[자주 언급된 특징]")
                for f in summary_result.get("features", []):
                    st.success(f)

        else:
            st.warning("⚠️ 해당 상품에 리뷰가 없습니다.")

        # -------------------------
        # 전체 상품 보기
        # -------------------------
        with st.expander("📊 전체 상품 테이블 보기"):
            st.dataframe(products)

    else:
        st.warning("⚠️ 선택한 카테고리에 상품이 없습니다.")

except Exception as e:
    st.error(f"DB에서 데이터를 불러오는 중 오류 발생: {e}")
