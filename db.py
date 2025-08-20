import pymysql
import pandas as pd
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4"
    )

# DB 초기화
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # 상품 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id VARCHAR(50) PRIMARY KEY,
        brandName VARCHAR(100),
        goodsName VARCHAR(255),
        price INT,
        reviewCount INT,
        reviewScore FLOAT,
        thumbnail TEXT,
        goodsLinkUrl TEXT
    )
    """)

    # 리뷰 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        review_no VARCHAR(50) PRIMARY KEY,
        product_id VARCHAR(50),
        createDate DATE,
        userNickName VARCHAR(100),
        content TEXT,
        grade INT,
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )
    """)

    conn.commit()
    conn.close()

# 상품 저장
def save_products(product_df: pd.DataFrame):
    conn = get_connection()
    cur = conn.cursor()

    sql = """
    REPLACE INTO products
    (product_id, brandName, goodsName, price, reviewCount, reviewScore, thumbnail, goodsLinkUrl)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """

    for _, row in product_df.iterrows():
        cur.execute(sql, tuple(row))

    conn.commit()
    conn.close()

# 리뷰 저장
def save_reviews(review_df: pd.DataFrame):
    conn = get_connection()
    cur = conn.cursor()

    sql = """
    REPLACE INTO reviews
    (review_no, product_id, createDate, userNickName, content, grade)
    VALUES (%s,%s,%s,%s,%s,%s)
    """

    for _, row in review_df.iterrows():
        cur.execute(sql, tuple(row))

    conn.commit()
    conn.close()

# 데이터 로드
def load_products():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM products", conn)
    conn.close()
    return df

def load_reviews(product_id: str):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM reviews WHERE product_id = %s", conn, params=[product_id])
    conn.close()
    return df
