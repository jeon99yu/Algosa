import streamlit as st
import pandas as pd

from analyzer import summarize_reviews, summarize_size_and_fit, summarize_coordination
from modules.analytics import (
    compute_kpis, sentiment_percentages, donut_figure,
    default_stopwords, keyword_freq, wordcloud_figure, topn_bar_figure
)

def render_tabs(reviews_df: pd.DataFrame, products: pd.DataFrame):
    reviews_texts = reviews_df["content"].dropna().astype(str).tolist()
    kpis = compute_kpis(reviews_df)

    # KPI 요약
    st.markdown("### 📌 요약 지표")
    m1, m2, m3 = st.columns([0.8, 1.2, 2.0]) 
    m1.metric("분석대상 리뷰 수", f"{kpis['total']:,}개")
    m2.metric("긍정 / 중립 / 부정", f"{kpis['pos']:,} / {kpis['neu']:,} / {kpis['neg']:,}")

    start, end = kpis["date_min"], kpis["date_max"]
    period = f"{start:%y/%m/%d} ~ {end:%y/%m/%d}" if pd.notna(start) and pd.notna(end) else "기간 정보 없음"
    m3.metric("수집 리뷰 기간", period)

    tab1, tab2, tab3 = st.tabs([f"📊 리뷰 분석 ({kpis['total']:,})", "👟 사이즈·코디", "🔤 키워드"])

    # Tab1: 리뷰 분석
    with tab1:
        st.markdown("### 📊 리뷰 분석 결과")

        vals = sentiment_percentages(kpis)
        c1, c2 = st.columns([1, 1])

        with c1:
            fig = donut_figure(vals, kpis["total"])
            st.pyplot(fig, use_container_width=False)

        summary_result = summarize_reviews(reviews_texts, sample_size=50)

        with c2:
            st.markdown("#### ✅ 전반적인 평가")
            st.write(summary_result.get("positive_negative", "요약 없음"))

        c3, c4 = st.columns([1, 1])
        with c3:
            st.markdown("#### ⚠️ 주의해야 할 점")
            for c in summary_result.get("cautions", []):
                st.error(c)
        with c4:
            st.markdown("#### 💬 자주 언급된 특징")
            for f in summary_result.get("features", []):
                st.success(f)

    # Tab2: 사이즈/코디
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

    # Tab3: 키워드 워드클라우드
    with tab3:
        st.markdown("### 🔤 리뷰 키워드 분석")
        if len(reviews_texts) == 0:
            st.info("키워드 분석할 리뷰가 없습니다.")
        else:
            freq = keyword_freq(
                reviews_texts,
                stopwords=default_stopwords(),
                use_morph=True,          # konlpy 설치 시 명사 기준, 미설치면 자동 우회
                max_features=2000,
            )


            if not freq:
                st.info("표시할 키워드가 없습니다.")
            else:
                topn = st.slider("표시 개수", 3, 10, 5, 1, key="kw_topn_tab3")
                items = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:topn]
                kw_df = pd.DataFrame(items, columns=["keyword", "count"])

                k1, k2 = st.columns([1, 1])
                with k1:
                    fig_wc, _ = wordcloud_figure(freq)
                    if fig_wc is None:
                        st.info("한글 폰트를 찾지 못해 워드클라우드를 표시할 수 없습니다.")
                    else:
                        st.pyplot(fig_wc, use_container_width=True)
                with k2:
                    fig_bar = topn_bar_figure(kw_df, topn)
                    st.pyplot(fig_bar, use_container_width=True)

    # 리뷰 원본/상품 테이블
    st.divider()
    st.markdown("### 전체목록 보기")

    with st.expander("📊 선택된 상품 리뷰 보기", expanded=False):
        show_cols = ["userNickName", "content", "grade", "createDate"]
        r_df = reviews_df.loc[:, show_cols].copy()
        r_df["grade"] = pd.to_numeric(r_df["grade"], errors="coerce").astype("Int64")
        r_df["createDate"] = pd.to_datetime(r_df["createDate"], errors="coerce").dt.strftime("%Y-%m-%d")
        r_df = r_df.sort_values("createDate", ascending=False, na_position="last")
        r_df = r_df.rename(columns={"userNickName": "닉네임", "content": "내용", "grade": "평점", "createDate": "작성일"})
        st.dataframe(r_df, use_container_width=True, hide_index=True)

    with st.expander("🛒 다른 무신사 추천상품 보기", expanded=False): 
        show_cols = ["brandName","goodsName","price","reviewScore","reviewCount"] 
        p_df = products.loc[:, show_cols].copy() 
        p_df = p_df.rename(columns={"brandName":"브랜드","goodsName":"상품명","price":"가격","reviewScore":"평점","reviewCount":"리뷰 수"}) 
        st.dataframe(p_df, use_container_width=True, hide_index=True)

