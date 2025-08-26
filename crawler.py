import time
import requests
import pandas as pd
from datetime import datetime
from db import (
    init_db, save_products, save_reviews,
    get_last_collected_date, update_last_collected_date
)
# -------------------------
# 카테고리 매핑
# -------------------------
CATEGORY_MAP = {
    "스니커즈": "103004",
    "스포츠화": "103005",
    "구두": "103001"
}
# -------------------------
# 상품 목록 크롤링
# -------------------------
def get_products(category="103004", top_n=50):
    url = f"https://api.musinsa.com/api2/dp/v1/plp/goods?gf=A&category={category}&size={top_n}&caller=CATEGORY&page=1"
    res = requests.get(url, headers={"user-agent": "Mozilla/5.0"})
    res.raise_for_status()
    items = res.json().get("data", {}).get("list", [])

    return pd.DataFrame([{
        "product_id": str(item.get("goodsNo")),
        "brandName": item.get("brandName"),
        "goodsName": item.get("goodsName"),
        "price": item.get("price"),
        "reviewCount": item.get("reviewCount"),
        "reviewScore": item.get("reviewScore"),
        "thumbnail": item.get("thumbnail"),
        "goodsLinkUrl": item.get("goodsLinkUrl"),
        "category": category 
    } for item in items])

# -------------------------
# 리뷰 크롤링
# -------------------------
def get_reviews(goods_no, last_collected_date, max_reviews=200, page_size=20):
    reviews, collected = [], 0
    base_url = "https://goods.musinsa.com/api2/review/v1/view/list"

    for page in range(1, 21):  # 최대 20페이지
        if collected >= max_reviews:
            break

        url = f"{base_url}?page={page}&pageSize={page_size}&goodsNo={goods_no}"
        res = requests.get(url, headers={"user-agent": "Mozilla/5.0"})
        if res.status_code != 200:
            break

        items = res.json().get("data", {}).get("list", [])
        if not items:
            break

        for r in items:
            if collected >= max_reviews:
                break

            raw_date = r.get("createDate")
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00")) if raw_date else None
            if dt is None:
                continue

            if dt.date() <= last_collected_date: # 마지막 수집일 이후 데이터만 저장
                continue

            reviews.append({
                "review_no": str(r.get("no") or r.get("reviewNo") or r.get("reviewId")),
                "product_id": str(goods_no),
                "createDate": dt.strftime("%Y-%m-%d"),
                "userNickName": r.get("userProfileInfo", {}).get("userNickName"),
                "content": r.get("content"),
                "grade": r.get("grade"),
            })
            collected += 1
        time.sleep(0.2)

    df = pd.DataFrame(reviews)
    if not df.empty:
        df["createDate"] = pd.to_datetime(df["createDate"])
        df = (
            df.sort_values(by="createDate", ascending=False)
              .drop_duplicates(subset=["product_id", "userNickName"], keep="first")
        )
        df["grade"] = pd.to_numeric(df["grade"], errors="coerce").fillna(0).astype(int)

    return df

# -------------------------
# 크롤러 실행 (전체 카테고리)
# -------------------------
def run_all_crawlers(num_products=60, max_reviews=300):
    init_db()
    all_products, all_reviews = [], []

    for cat_name, cat_code in CATEGORY_MAP.items():
        print(f"\n===== [{cat_name}] 카테고리 크롤링 시작 =====")
        products_df = get_products(category=cat_code, top_n=num_products)

        cat_reviews = []
        for _, row in products_df.iterrows():
            goods_no = row["product_id"]

            last_date = get_last_collected_date(goods_no)
            product_reviews_df = get_reviews(goods_no, last_collected_date=last_date, max_reviews=max_reviews)

            if not product_reviews_df.empty:
                cat_reviews.append(product_reviews_df)
                latest_date = product_reviews_df["createDate"].max().date()
                update_last_collected_date(goods_no, latest_date)

            print(f"상품 {goods_no} 리뷰 {len(product_reviews_df)}개 수집")

        reviews_df = pd.concat(cat_reviews, ignore_index=True) if cat_reviews else pd.DataFrame()
        save_products(products_df)
        save_reviews(reviews_df)

        all_products.append(products_df)
        all_reviews.append(reviews_df)

    all_products_df = pd.concat(all_products, ignore_index=True)
    all_reviews_df = pd.concat(all_reviews, ignore_index=True)

    return all_products_df, all_reviews_df

# -------------------------
# 실행
# -------------------------
if __name__ == "__main__":
    products, reviews = run_all_crawlers(num_products=60, max_reviews=300)

    print(f"\n총 상품 개수: {len(products)}개")
    print(f"총 리뷰 개수(중복 제거 후): {len(reviews)}개")
    print("DB 저장 완료")
