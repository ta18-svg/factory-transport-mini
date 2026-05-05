import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()


# SQLAlchemy 2系のベースクラス
# すべてのモデルはこのBaseを継承する
class Base(DeclarativeBase):
    pass


# .env からDB接続情報を取得
MYSQL_HOST = os.getenv("MYSQL_HOST", "db")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "factory_transport_db")
MYSQL_USER = os.getenv("MYSQL_USER", "appuser")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppass")


# PyMySQLを使ってMySQLへ接続するURL
DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)


# DBエンジンを作成
engine = create_engine(
    DATABASE_URL,
    echo=True,          # SQLログを表示。学習中はTrueでOK
    pool_pre_ping=True  # DB接続切れを事前確認
)


# DBセッション作成用
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# FastAPIでDBセッションを使うための依存関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()