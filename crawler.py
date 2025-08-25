import time
import requests
import pandas as pd
from datetime import datetime
from db import init_db, save_products, save_reviews, get_last_collected_date, update_last_collected_date

def get_products(category="103004", top_n=50):
    url = f"https://api.musinsa.com/api2/dp/v1/plp/goods?gf=A&category={category}&size={top_n}&caller=CATEGORY&page=1"
    res = requests.get(url, headers={"user-agent": "Mozilla/5.0"})
    res.raise_for_status()
    items = res.json().get("data", {}).get("list", [])

    return pd.DataFrame([{
        "product_id": item.get("goodsNo"),
        "brandName": item.get("brandName"),
        "goodsName": item.get("goodsName"),
        "price": item.get("price"),
        "reviewCount": item.get("reviewCount"),
        "reviewScore": item.get("reviewScore"),
        "thumbnail": item.get("thumbnail"),
        "goodsLinkUrl": item.get("goodsLinkUrl"),
    } for item in items])


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

            # 마지막 수집일 이후 리뷰만
            if dt.date() <= last_collected_date:
                continue

            reviews.append({
                "product_id": goods_no,
                "createDate": dt.strftime("%Y-%m-%d"),
                "review_no": r.get("no") or r.get("reviewNo") or r.get("reviewId"),
                "userNickName": r.get("userProfileInfo", {}).get("userNickName"),
                "content": r.get("content"),
                "grade": r.get("grade"),
            })
            collected += 1
        time.sleep(0.2)  

    # (product_id + userNickName) 기준으로 중복 제거 → 최신 리뷰만 유지
    df = pd.DataFrame(reviews)
    if not df.empty:
        df["createDate"] = pd.to_datetime(df["createDate"])
        df = (
            df.sort_values(by="createDate", ascending=False)
              .drop_duplicates(subset=["product_id", "userNickName"], keep="first")
        )
    return df

def run_crawler(category="103004", num_products=60, max_reviews=300):
    init_db()

    products_df = get_products(category=category, top_n=num_products)
    all_reviews = []

    for _, row in products_df.iterrows():
        goods_no = row["product_id"]
        # DB에서 마지막 수집일 가져오기
        last_date = get_last_collected_date(goods_no)
        # 리뷰 크롤링
        product_reviews_df = get_reviews(goods_no, last_collected_date=last_date, max_reviews=max_reviews)

        if not product_reviews_df.empty:
            all_reviews.append(product_reviews_df)
            # 최신 리뷰일 추출해서 DB 업데이트
            latest_date = product_reviews_df["createDate"].max().date()
            update_last_collected_date(goods_no, latest_date)

        print(f"상품 {goods_no}의 리뷰 {len(product_reviews_df)}개 수집")

    # 모든 리뷰 합치기
    reviews_df = pd.concat(all_reviews, ignore_index=True) if all_reviews else pd.DataFrame()

    # DB 저장
    save_products(products_df)
    save_reviews(reviews_df)

    return products_df, reviews_df

if __name__ == "__main__":
    products, reviews = run_crawler(category="103004", num_products=60, max_reviews=300)

    print(f"\n총 상품 개수: {len(products)}개")
    print(f"총 리뷰 개수(중복 제거 후): {len(reviews)}개")
    print("DB 저장 완료")
