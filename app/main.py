from fastapi import FastAPI

from app.db import Base, engine
from app import models

# FastAPIアプリケーション本体
app = FastAPI(
    title="Factory Transport Mini",
    description="工場内搬送依頼管理システム",
    version="0.1.0",
)

@app.on_event("startup")
def on_startup():
    """
    アプリ起動時にテーブルを作成する。

    create_all() は、まだ存在しないテーブルを作成する。
    学習初期フェーズでは便利。

    注意：
    既存テーブルのカラム変更までは自動で反映しない。
    実務では後半PhaseでAlembicに切り替える。
    """
    Base.metadata.create_all(bind=engine)


@app.get("/")
def health_check():
    """
    起動確認用のエンドポイント。
    ブラウザで http://localhost:8000 にアクセスして確認する。
    """
    return {
        "message": "Factory Transport Mini is running"
    }