import requests
import pandas as pd
from datetime import datetime

# 카테고리 목록
def get_categories():
    return {
        "상의": "001",
        "바지": "003",
        "스니커즈": "103004",
        "향수": "104005"
    }

# 상품 목록 가져오기
def get_products(category="001", max_pages=1, page_size=60):
    data_list = []

    for page in range(1, max_pages + 1):
        url = f"https://api.musinsa.com/api2/dp/v1/plp/goods?gf=A&category={category}&size={page_size}&caller=CATEGORY&page={page}"
        res = requests.get(url, headers={"user-agent": "Mozilla/5.0"})
        
        if res.status_code != 200:
            continue

        items = res.json().get("data", {}).get("list", [])
        for item in items:
            data_list.append({
                "product_id": item.get("goodsNo"),
                "brandName": item.get("brandName"),
                "goodsName": item.get("goodsName"),
                "price": item.get("price"),
                "reviewCount": item.get("reviewCount"),
                "reviewScore": item.get("reviewScore"),
                "thumbnail": item.get("thumbnail"),
                "goodsLinkUrl": item.get("goodsLinkUrl"),
            })
    return pd.DataFrame(data_list)

# 리뷰 가져오기
def get_reviews(goods_no, max_pages=10, page_size=10):
    reviews = []
    base_url = "https://goods.musinsa.com/api2/review/v1/view/list"
    headers = {"user-agent": "Mozilla/5.0"}
    
    for page in range(1, max_pages+1):
        url = f"{base_url}?page={page}&pageSize={page_size}&goodsNo={goods_no}"
        res = requests.get(url, headers=headers)
        
        if res.status_code != 200:
            break
        items = res.json().get("data", {}).get("list", [])
        if not items:
            break
        for r in items:
            raw_date = r.get("createDate")
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00")) if raw_date else None
            reviews.append({
                "review_no": r.get("no"),
                "product_id": goods_no,
                "createDate": dt.strftime("%Y-%m-%d") if dt else None,
                "userNickName": r.get("userProfileInfo", {}).get("userNickName"),
                "content": r.get("content"),
                "grade": r.get("grade")
            })
    return reviews
