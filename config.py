import os
from dotenv import load_dotenv
import sqlalchemy

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "jeon99yu")
DB_PASSWORD = os.getenv("DB_PASSWORD", "test1234")
DB_NAME = os.getenv("DB_NAME", "musinsa")
DB_PORT = int(os.getenv("DB_PORT", 3306))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

engine = sqlalchemy.create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)