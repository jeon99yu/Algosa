import pandas as pd
import config
from datetime import datetime
from config import engine  # ← 앱이 실제로 사용하는 SQLAlchemy engine

def get_connection():
    """config.USE_MYSQL에 따라 DBAPI 커넥션을 반환 (대량 insert 등에 활용)"""
    if config.USE_MYSQL:
        import pymysql  # 필요할 때만 import
        return pymysql.connect(
            host=getattr(config, "DB_HOST", "localhost"),
            user=getattr(config, "DB_USER", ""),
            password=getattr(config, "DB_PASSWORD", ""),
            database=getattr(config, "DB_NAME", ""),
            port=getattr(config, "DB_PORT", 3306),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    else:
        import sqlite3
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


# -------------------------
# DB 초기화 (테이블 생성)
# → 반드시 SQLAlchemy engine으로 실행하여
#   쿼리에서 사용하는 연결과 일치시키기
# -------------------------
def init_db():
    if config.USE_MYSQL:
        CREATE_PRODUCTS = """
        CREATE TABLE IF NOT EXISTS products (
            product_id   VARCHAR(50) PRIMARY KEY,
            brandName    VARCHAR(100),
            goodsName    VARCHAR(255),
            price        INT,
            reviewCount  INT,
            reviewScore  FLOAT,
            thumbnail    TEXT,
            goodsLinkUrl TEXT,
            category     VARCHAR(50)
        ) CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """

        CREATE_REVIEWS = """
        CREATE TABLE IF NOT EXISTS reviews (
            review_no     VARCHAR(50) PRIMARY KEY,
            product_id    VARCHAR(50),
            createDate    DATE,
            userNickName  VARCHAR(100),
            content       TEXT,
            grade         INT,
            FOREIGN KEY(product_id) REFERENCES products(product_id),
            INDEX product_idx (product_id)
        ) CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """

        CREATE_LASTDATE = """
        CREATE TABLE IF NOT EXISTS product_last_date (
            product_id          VARCHAR(50) PRIMARY KEY,
            last_collected_date DATE
        ) CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        with engine.begin() as conn:
            conn.exec_driver_sql(CREATE_PRODUCTS)
            conn.exec_driver_sql(CREATE_REVIEWS)
            conn.exec_driver_sql(CREATE_LASTDATE)

    else:
        # SQLite 스키마
        CREATE_PRODUCTS = """
        CREATE TABLE IF NOT EXISTS products (
            product_id    TEXT PRIMARY KEY,
            brandName     TEXT,
            goodsName     TEXT,
            price         INTEGER,
            reviewCount   INTEGER,
            reviewScore   REAL,
            thumbnail     TEXT,
            goodsLinkUrl  TEXT,
            category      TEXT
        );
        """

        CREATE_REVIEWS = """
        CREATE TABLE IF NOT EXISTS reviews (
            review_no     TEXT PRIMARY KEY,
            product_id    TEXT,
            createDate    TEXT,
            userNickName  TEXT,
            content       TEXT,
            grade         INTEGER,
            FOREIGN KEY(product_id) REFERENCES products(product_id)
        );
        """

        CREATE_LASTDATE = """
        CREATE TABLE IF NOT EXISTS product_last_date (
            product_id          TEXT PRIMARY KEY,
            last_collected_date TEXT
        );
        """

        with engine.begin() as conn:
            # SQLite 옵션들
            conn.exec_driver_sql("PRAGMA foreign_keys = ON;")
            conn.exec_driver_sql(CREATE_PRODUCTS)
            conn.exec_driver_sql(CREATE_REVIEWS)
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);")
            conn.exec_driver_sql(CREATE_LASTDATE)


# -------------------------
# 저장 함수
# -------------------------
def save_products(product_df):
    if product_df is None or product_df.empty:
        return

    cols = [
        "product_id", "brandName", "goodsName", "price",
        "reviewCount", "reviewScore", "thumbnail", "goodsLinkUrl", "category"
    ]
    rows = product_df[cols].fillna("").values.tolist()

    conn = get_connection()
    cur = conn.cursor()

    if config.USE_MYSQL:
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
    else:
        # SQLite UPSERT
        sql = """
        INSERT INTO products
        (product_id, brandName, goodsName, price, reviewCount, reviewScore, thumbnail, goodsLinkUrl, category)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(product_id) DO UPDATE SET
          brandName=excluded.brandName,
          goodsName=excluded.goodsName,
          price=excluded.price,
          reviewCount=excluded.reviewCount,
          reviewScore=excluded.reviewScore,
          thumbnail=excluded.thumbnail,
          goodsLinkUrl=excluded.goodsLinkUrl,
          category=excluded.category
        """

    cur.executemany(sql, rows)
    conn.commit()
    conn.close()


def save_reviews(df):
    if df is None or df.empty:
        return

    df = df.copy()
    # Timestamp → "YYYY-MM-DD" 문자열
    df["createDate"] = pd.to_datetime(df["createDate"], errors="coerce").dt.strftime("%Y-%m-%d")
    # NaN 방지 및 타입 보정
    for col in ["review_no", "product_id", "userNickName", "content"]:
        df[col] = df[col].fillna("").astype(str)
    df["grade"] = pd.to_numeric(df["grade"], errors="coerce").fillna(0).astype(int)

    rows = df[["review_no", "product_id", "createDate", "userNickName", "content", "grade"]].values.tolist()

    conn = get_connection()
    cur = conn.cursor()

    if config.USE_MYSQL:
        # MySQL도 문자열 날짜를 안전하게 받아줍니다.
        cur.executemany("""
          REPLACE INTO reviews (review_no, product_id, createDate, userNickName, content, grade)
          VALUES (%s,%s,%s,%s,%s,%s)
        """, rows)
    else:
        # SQLite: ? 플레이스홀더 사용 + ON CONFLICT
        cur.executemany("""
          INSERT INTO reviews (review_no, product_id, createDate, userNickName, content, grade)
          VALUES (?,?,?,?,?,?)
          ON CONFLICT(review_no) DO UPDATE SET
            product_id   = excluded.product_id,
            createDate   = excluded.createDate,
            userNickName = excluded.userNickName,
            content      = excluded.content,
            grade        = excluded.grade
        """, rows)

    conn.commit()
    conn.close()


# -------------------------
# 마지막 리뷰 수집일 관리
# -------------------------
def get_last_collected_date(product_id: str):
    conn = get_connection()
    cur = conn.cursor()

    if config.USE_MYSQL:
        cur.execute("SELECT last_collected_date FROM product_last_date WHERE product_id=%s", (product_id,))
        row = cur.fetchone()
        val = row["last_collected_date"] if row else None
    else:
        cur.execute("SELECT last_collected_date FROM product_last_date WHERE product_id=?", (product_id,))
        row = cur.fetchone()
        val = row[0] if row else None

    conn.close()

    if not val:
        return datetime(2000, 1, 1).date()

    try:
        return datetime.fromisoformat(str(val)).date()
    except Exception:
        return datetime(2000, 1, 1).date()


def update_last_collected_date(product_id: str, latest_date):
    conn = get_connection()
    cur = conn.cursor()

    if config.USE_MYSQL:
        cur.execute("""
          INSERT INTO product_last_date (product_id, last_collected_date)
          VALUES (%s, %s)
          ON DUPLICATE KEY UPDATE last_collected_date = VALUES(last_collected_date)
        """, (product_id, latest_date))
    else:
        cur.execute("""
          INSERT INTO product_last_date (product_id, last_collected_date)
          VALUES (?, ?)
          ON CONFLICT(product_id) DO UPDATE SET last_collected_date = excluded.last_collected_date
        """, (product_id, str(latest_date)))

    conn.commit()
    conn.close()
