import pymysql
from datetime import datetime
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# -------------------------
# DB 연결
# -------------------------
def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# -------------------------
# DB 초기화 (테이블 생성)
# -------------------------
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
        goodsLinkUrl TEXT,
        category VARCHAR(50)
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

# -------------------------
# 저장 함수
# -------------------------
def save_products(product_df):
    if product_df.empty:
        return
    conn = get_connection()
    cur = conn.cursor()
    sql = """
    INSERT INTO products
    (product_id, brandName, goodsName, price, reviewCount, reviewScore, thumbnail, goodsLinkUrl, category)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        brandName=VALUES(brandName),
        goodsName=VALUES(goodsName),
        price=VALUES(price),
        reviewCount=VALUES(reviewCount),
        reviewScore=VALUES(reviewScore),
        thumbnail=VALUES(thumbnail),
        goodsLinkUrl=VALUES(goodsLinkUrl),
        category=VALUES(category)
    """
    values = product_df[[
        "product_id", "brandName", "goodsName", "price",
        "reviewCount", "reviewScore", "thumbnail", "goodsLinkUrl", "category"
    ]].fillna("").values.tolist()
    cur.executemany(sql, values)
    conn.commit()
    conn.close()

def save_reviews(df):
    if df is None or df.empty:
        return
    conn = get_connection()
    cur = conn.cursor()
    values = df[["review_no", "product_id", "createDate", "userNickName", "content", "grade"]].values.tolist()
    cur.executemany("""
        REPLACE INTO reviews (review_no, product_id, createDate, userNickName, content, grade)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, values)
    conn.commit()
    conn.close()

# -------------------------
# 마지막 리뷰 수집일 관리
# -------------------------
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