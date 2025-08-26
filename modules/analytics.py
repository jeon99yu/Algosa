import os, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple, Dict, List
from collections import Counter

from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# konlpy가 있으면 명사 기반, 없으면 자동 우회
try:
    from konlpy.tag import Okt
    _HAS_KONLPY = True
except Exception:
    Okt = None  # type: ignore
    _HAS_KONLPY = False

# ============================== KPI/차트 ==============================

def compute_kpis(reviews_df: pd.DataFrame) -> dict:
    total = len(reviews_df)
    pos = int((reviews_df["grade"] >= 4).sum())
    neg = int((reviews_df["grade"] <= 2).sum())
    neu = int(total - pos - neg)
    unique_users = int(reviews_df["userNickName"].nunique())
    date_min = pd.to_datetime(reviews_df["createDate"], errors="coerce").min()
    date_max = pd.to_datetime(reviews_df["createDate"], errors="coerce").max()
    return {
        "total": total, "pos": pos, "neu": neu, "neg": neg,
        "unique_users": unique_users, "date_min": date_min, "date_max": date_max,
    }

def sentiment_percentages(kpis: dict) -> List[float]:
    t = max(kpis["total"], 1)
    return [kpis["pos"]/t*100, kpis["neu"]/t*100, kpis["neg"]/t*100]

def donut_figure(values: List[float], total_reviews: int):
    labels = ["긍정", "중립", "부정"]
    colors = ["#4CAF50", "#FFC107", "#F44336"]
    fig, ax = plt.subplots(figsize=(4.6, 4.6), dpi=140)

    if sum(values) > 0:
        wedges, *_ = ax.pie(
            values, startangle=90, labels=None, autopct=None, pctdistance=0.8,
            wedgeprops=dict(width=0.55, edgecolor="none"), colors=colors
        )
        ax.text(0, 0, f"총 {total_reviews}\n리뷰", ha="center", va="center",
                fontsize=13, fontweight="bold", linespacing=1.2)
        legend_labels = [f"{l} {v:.0f}%" for l, v in zip(labels, values)]
        ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1.02, 0.5),
                  frameon=False, borderaxespad=0.0)
    else:
        ax.text(0.5, 0.5, "데이터 없음", ha="center", va="center")
    ax.set(aspect="equal")
    plt.tight_layout()
    
    return fig

# ======================= 불용어/접미사 + 키워드 전처리 =======================

# ▶ 확장 불용어
_STOPWORDS: List[str] = [
    "정도","조금","그리고","그러나","하지만","사용","제품","구매","리뷰","가격","배송",
    "신발","운동화","브랜드","디자인","평가","사용자","부분","좀","것","거","이번","처음",
    "솔직히","진짜","너무","정말","약간","그냥","좀더","조금더","그리고요","근데","그래도",
    "여기","저기","거의","매우","굉장히","대박","완전","요즘","최근","때문","때문에",
    "역시","살짝","생각보다","신발은","평소","많이","착화감이","착화감도","발볼이"
]

# ▶ 용언/어미 접미사 
_VERB_SUFFIXES: Tuple[str, ...] = (
    "하다","합니다","해요","했다","했어요","하네요","하니까","하였","하였습","하긴",
    "같아요","같았","같네요","같았어요","같습니다","이네요","이었","입니다","어요","에요","였어요",
    "됩니다","되네요","되는","되는지","되요","돼요","됐어요","했네","했구","했더","했습",
    "좋아요","좋네요","좋습니다","좋았","예요","네요","이라","이라고","신는데","신고","신을"

)

def default_stopwords() -> List[str]:
    return list(_STOPWORDS)

def verb_suffixes() -> Tuple[str, ...]:
    return _VERB_SUFFIXES

_hangul = re.compile(r"^[가-힣]+$")

def _post_filter(freq: Dict[str, int], stop: set[str], remove_suffixes: bool = True) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for w, c in freq.items():
        if w in stop:         # 불용어 제거
            continue
        if len(w) < 2:        # 2자 미만 제거
            continue
        if not _hangul.match(w):  # 한글만
            continue
        if remove_suffixes and any(w.endswith(suf) for suf in _VERB_SUFFIXES):
            continue
        out[w] = c
    # 자주 나온 순서로 정렬하여 반환
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))

def keyword_freq(
    reviews_texts: List[str],
    stopwords: Optional[List[str]] = None,
    use_morph: bool = False,         # konlpy(Okt) 사용 여부
    max_features: int = 2000,
    remove_suffixes: bool = True,
) -> Dict[str, int]:
    stop = set(stopwords or default_stopwords())

    # konlpy(Okt) 있으면 명사 기반
    if use_morph and _HAS_KONLPY:
        okt = Okt()  # type: ignore
        bag: List[str] = []
        for t in reviews_texts:
            # 명사만 사용 + 2자 이상 + 불용어 제거
            nouns = [w for w in okt.nouns(t) if len(w) >= 2 and w not in stop]
            bag.extend(nouns)
        base = dict(Counter(bag))
        return _post_filter(base, stop, remove_suffixes)

    # 우회: 2글자 이상 한글 토큰화 + 불용어 제거
    vectorizer = CountVectorizer(
        token_pattern=r"(?u)[가-힣]{2,}",
        stop_words=list(stop),
        max_features=max_features,
    )
    X = vectorizer.fit_transform(reviews_texts)
    counts = np.asarray(X.sum(axis=0)).ravel()
    words = vectorizer.get_feature_names_out()
    base = dict(zip(words, counts))
    return _post_filter(base, stop, remove_suffixes)

# ============================== 시각화 ==============================

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
        font_path=font_path, width=900, height=500, background_color="white",
        prefer_horizontal=0.9, max_words=200
    ).generate_from_frequencies(freq)
    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=140)
    ax.imshow(wc); ax.axis("off")
    plt.tight_layout()
    return fig, ax

def topn_bar_figure(kw_df: pd.DataFrame, topn: int):
    fig, ax = plt.subplots(figsize=(6.2, 5.0), dpi=140)
    ax.barh(kw_df["keyword"][::-1], kw_df["count"][::-1], color="#FF5252")
    ax.set_xlabel("count"); ax.set_ylabel("")
    ax.set_title(f"키워드 TOP {topn}")
    ax.invert_yaxis()
    for i, v in enumerate(kw_df["count"][::-1].tolist()):
        ax.text(v + max(kw_df["count"]) * 0.01, i, str(int(v)), va="center")
    plt.tight_layout()
    return fig
