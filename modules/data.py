import pandas as pd
from sqlalchemy import text
from config import engine
import streamlit as st

@st.cache_data(ttl=300) # 캐시방지
def load_products_by_category(cat_code: str) -> pd.DataFrame:
    query = """
        SELECT product_id, brandName, goodsName, price, reviewCount, reviewScore,
               thumbnail, goodsLinkUrl, category
        FROM products
        WHERE category = ?
    """
    return pd.read_sql(query, engine, params=(cat_code,))

def load_reviews_by_product(product_id: str) -> pd.DataFrame:
    sql = text(
        """
        SELECT review_no, product_id, createDate, userNickName, content, grade
        FROM reviews
        WHERE product_id = :pid
        ORDER BY createDate DESC
        """
    )
    df = pd.read_sql(sql, engine, params={"pid": product_id})
    if not df.empty:
        df["grade"] = pd.to_numeric(df["grade"], errors="coerce")
        df = df.dropna(subset=["grade"]).assign(grade=lambda d: d["grade"].astype(int))
    return df
