from fastapi import FastAPI

# FastAPIアプリケーション本体
app = FastAPI(
    title="Factory Transport Mini",
    description="工場内搬送依頼管理システム",
    version="0.1.0",
)


@app.get("/")
def health_check():
    """
    起動確認用のエンドポイント。
    ブラウザで http://localhost:8000 にアクセスして確認する。
    """
    return {
        "message": "Factory Transport Mini is running"
    }