import pymysql
import pandas as pd
from datetime import datetime
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

#  DB 연결
def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# DB 초기화 (테이블 생성)
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
    ) CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
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
        FOREIGN KEY(product_id) REFERENCES products(product_id),
        INDEX product_idx (product_id)
    ) CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 마지막 리뷰 수집일 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS product_last_date (
        product_id VARCHAR(50) PRIMARY KEY,
        last_collected_date DATE
    ) CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    conn.commit()
    conn.close()

#  상품 저장 (전체 덮어쓰기)
def save_products(product_df: pd.DataFrame):
    if product_df.empty:
        return
    conn = get_connection()
    cur = conn.cursor()

    # 기존 상품 전체 삭제 후 새로 삽입
    cur.execute("DELETE FROM products;")

    sql = """
    INSERT INTO products
    (product_id, brandName, goodsName, price, reviewCount, reviewScore, thumbnail, goodsLinkUrl)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """
    cur.executemany(sql, [tuple(row) for _, row in product_df.iterrows()])
    conn.commit()
    conn.close()


#  리뷰 저장 (batch insert 적용)
def save_reviews(review_df: pd.DataFrame, batch_size=1000):
    if review_df.empty:
        return
    conn = get_connection()
    cur = conn.cursor()

    sql = """
    INSERT INTO reviews
    (review_no, product_id, createDate, userNickName, content, grade)
    VALUES (%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE 
        createDate=VALUES(createDate),
        content=VALUES(content),
        grade=VALUES(grade)
    """
    values = review_df[["review_no", "product_id", "createDate", "userNickName", "content", "grade"]].values.tolist()

    # batch insert
    for i in range(0, len(values), batch_size):
        cur.executemany(sql, values[i:i+batch_size])

    conn.commit()
    conn.close()


# 상품 불러오기
def load_products():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM products", conn)
    conn.close()
    return df


# 특정 상품 리뷰 불러오기
def load_reviews(product_id: str = None):
    conn = get_connection()
    if product_id:
        query = "SELECT * FROM reviews WHERE product_id = %s ORDER BY createDate DESC"
        df = pd.read_sql(query, conn, params=[product_id])
    else:
        query = "SELECT * FROM reviews ORDER BY createDate DESC LIMIT 100"
        df = pd.read_sql(query, conn)
    conn.close()
    return df


# 마지막 리뷰 수집일 불러오기
def get_last_collected_date(product_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT last_collected_date FROM product_last_date WHERE product_id=%s", (product_id,))
    result = cur.fetchone()
    conn.close()
    if result and result["last_collected_date"]:
        return result["last_collected_date"]
    else:
        return datetime(2000, 1, 1).date()


# 마지막 리뷰 수집일 갱신
def update_last_collected_date(product_id: str, latest_date):
    conn = get_connection()
    cur = conn.cursor()
    sql = """
    INSERT INTO product_last_date (product_id, last_collected_date)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE last_collected_date = VALUES(last_collected_date)
    """
    cur.execute(sql, (product_id, latest_date))
    conn.commit()
    conn.close()
