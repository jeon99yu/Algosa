import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from typing import Optional, Tuple, Dict

from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer

# 폰트 한글깨짐 방지
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# konlpy 설치 여부 확인
try:
    from konlpy.tag import Okt
    _HAS_KONLPY = True
except Exception:
    Okt = None
    _HAS_KONLPY = False


# KPI
def compute_kpis(reviews_df: pd.DataFrame) -> dict:
    total = len(reviews_df)
    pos = int((reviews_df["grade"] >= 4).sum())
    neg = int((reviews_df["grade"] <= 2).sum())
    neu = int(total - pos - neg)
    unique_users = int(reviews_df["userNickName"].nunique())
    date_min = pd.to_datetime(reviews_df["createDate"], errors="coerce").min()
    date_max = pd.to_datetime(reviews_df["createDate"], errors="coerce").max()
    return {
        "total": total,
        "pos": pos,
        "neu": neu,
        "neg": neg,
        "unique_users": unique_users,
        "date_min": date_min,
        "date_max": date_max,
    }


def sentiment_percentages(kpis: dict) -> list[float]:
    t = max(kpis["total"], 1)
    return [kpis["pos"] / t * 100, kpis["neu"] / t * 100, kpis["neg"] / t * 100]


def donut_figure(values: list[float], total_reviews: int):
    labels = ["긍정", "중립", "부정"]
    colors = ["#4CAF50", "#FFC107", "#F44336"]

    fig, ax = plt.subplots(figsize=(4.6, 4.6), dpi=140)
    if sum(values) > 0:
        def _autopct(pct):
            return f"{pct:.0f}%" if pct >= 5 else ""

        wedges, *_ = ax.pie(
            values,
            startangle=90,
            labels=None,
            autopct=_autopct,
            pctdistance=0.8,
            wedgeprops=dict(width=0.55, edgecolor="white"),
            colors=colors,
        )
        ax.text(
            0, 0, f"총 {total_reviews}\n리뷰",
            ha="center", va="center", fontsize=13, fontweight="bold", linespacing=1.2
        )
        legend_labels = [f"{l} {v:.0f}%" for l, v in zip(labels, values)]
        ax.legend(
            wedges, legend_labels, loc="center left", bbox_to_anchor=(1.02, 0.5),
            frameon=False, borderaxespad=0.0
        )
    else:
        ax.text(0.5, 0.5, "데이터 없음", ha="center", va="center")

    ax.set(aspect="equal")
    plt.tight_layout()
    return fig


# ========================== 키워드 분석 ==========================

def default_stopwords() -> list[str]: # 불용어 사전
    return [
        "정도","조금","그리고","그러나","하지만","사용","제품","구매","리뷰","역시",
        "신발","평가","사용자","부분","좀","것","거","이번","처음","생각보다"
        "솔직히","진짜","너무","정말","약간","그냥","좀더","조금더","그리고요","근데","그래도",
        "여기","저기","거의","매우","굉장히","대박","완전","요즘","최근","때문","때문에",
    ]


# 용언 (접미사)
_VERB_SUFFIXES = (
    "하다","합니다","해요","했다","했어요","하네요","하니까","하였","하였습","하긴",
    "같아요","같았","같네요","같았어요","이네요","이었","입니다","어요","에요","였어요",
    "됩니다","되네요","되는","되는지","되요","돼요","됐어요","했네","했구","했더","했습",
    "좋아요","좋네요","좋습니다","좋았","예요","네요","이라","이라고","신는데","신고",
    "같아요","같습니다"
)


def keyword_freq(
    reviews_texts: list[str],
    stopwords: Optional[list[str]] = None,
    use_morph: bool = False,
    max_features: int = 2000,
) -> Dict[str, int]:
    """
    - use_morph=True & konlpy 설치됨: Okt 명사 기반 집계
    - 그 외: CountVectorizer(2자 이상 한글) 기반 집계
    """
    stop = set(stopwords or default_stopwords())

    if use_morph and _HAS_KONLPY:
        okt = Okt() 
        bag: list[str] = []
        for t in reviews_texts:
            nouns = [w for w in okt.nouns(t) if len(w) >= 2 and w not in stop]
            # 용언 접미사 제거
            cleaned = []
            for w in nouns:
                if any(w.endswith(suf) for suf in _VERB_SUFFIXES):
                    continue
                cleaned.append(w)
            bag.extend(cleaned)
        return dict(Counter(bag))

    # 형태소 분석 우회: CountVectorizer
    vectorizer = CountVectorizer(
        token_pattern=r"(?u)[가-힣]{2,}",
        stop_words=list(stop),
        max_features=max_features,
    )
    X = vectorizer.fit_transform(reviews_texts)
    counts = np.asarray(X.sum(axis=0)).ravel()
    words = vectorizer.get_feature_names_out()
    return dict(zip(words, counts))


def _font_path() -> Optional[str]:
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


def wordcloud_figure(freq: dict) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
    font_path = _font_path()
    if not font_path:
        return None, None

    wc = WordCloud(
        font_path=font_path,
        width=900,
        height=500,
        background_color="white",
        prefer_horizontal=0.9,
        max_words=200,
    ).generate_from_frequencies(freq)

    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=140)
    ax.imshow(wc)
    ax.axis("off")
    plt.tight_layout()
    return fig, ax


def topn_bar_figure(kw_df: pd.DataFrame, topn: int):
    kw_df_sorted = kw_df.sort_values(by="count", ascending=False)
    
    fig, ax = plt.subplots(figsize=(6.2, 5.0), dpi=140)
    ax.barh(kw_df_sorted["keyword"], kw_df_sorted["count"], color="#FF5252")
    
    ax.set_xlabel("count")
    ax.set_ylabel("")
    ax.set_title(f"키워드 TOP {topn}")
    for i, v in enumerate(kw_df_sorted["count"].tolist()):
        ax.text(v + max(kw_df_sorted["count"]) * 0.01, i, str(int(v)), va="center")
        
    plt.tight_layout()
    return fig