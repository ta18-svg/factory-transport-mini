# =========================================================
# FastAPI 本体関連
# =========================================================
from datetime import date, datetime, time
# Depends
# → DI（Dependency Injection）
# → DB接続などを自動注入するために使う
#
# Form
# → HTMLフォームから送られてきた値を受け取る
#
# Request
# → ブラウザから来たリクエスト情報
# → Cookie取得などに使う
from fastapi import Depends, FastAPI, Form, Request
# HTMLResponse
# → HTMLを返すレスポンス
#
# RedirectResponse
# → 別URLへリダイレクトする
from fastapi.responses import HTMLResponse, RedirectResponse
# Jinja2 テンプレートエンジン
# HTMLテンプレート(login.html等)を表示するために使用
from fastapi.templating import Jinja2Templates
# SQLAlchemy の DBセッション型
# DB操作で使う
from sqlalchemy.orm import Session, joinedload
# models.py を読み込む
# テーブル定義(users等)を認識させるために必要
from app import models

# =========================================================
# 認証関連
# =========================================================
from app.auth import (
    # Cookie名
    # 例: access_token
    COOKIE_NAME,
    # ユーザー認証関数
    # username/password を照合する関数
    authenticate_user,
    # JWTトークン生成関数
    create_access_token,
    # Cookie内JWTからログインユーザー取得関数
    get_current_user_from_cookie,
    # 管理者権限チェック関数
    require_admin,
)
# app/db.py の中にある
# Base
# engine
# get_db
# を読み込み
from app.db import Base, engine, get_db

# =========================================================
# FastAPI アプリケーション生成
# =========================================================
# FastAPIアプリケーション本体
app = FastAPI(
    # Swagger UI に表示されるタイトル
    title="Factory Transport Mini",
    # 説明文
    description="工場内搬送依頼管理システム",
    # バージョン情報
    version="0.1.0",
)

# =========================================================
# Jinja2 テンプレート設定
# =========================================================

# app/templates フォルダをテンプレート置き場にする
#
# 例:
# app/templates/login.html
templates = Jinja2Templates(directory="app/templates")

# =========================================================
# 起動時イベント
# =========================================================
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
    # SQLAlchemyモデルを元にテーブル作成
    # Base.metadata.create_all(bind=engine)
    """
    Phase9以降はAlembicでDB管理するため、
    create_all() は使わない。
    """
    pass

# =========================================================
# ルートURL
# =========================================================

@app.get("/")
def root():
    # / にアクセスしたら
    # /login へ飛ばす
    return RedirectResponse(url="/login", status_code=302)
# 起動確認用のエンドポイント
# def health_check():
#     """
#     起動確認用のエンドポイント。
#     ブラウザで http://localhost:8000 にアクセスして確認する。
#     """
#     return {
#         "message": "Factory Transport Mini is running"
#     }

# =========================================================
# ログイン画面表示
# =========================================================
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    # login.html を表示する
    #
    # request は Jinja2Templates では必須
    return templates.TemplateResponse(
        # 表示するHTML
        "login.html",
        # HTMLへ渡す変数
        {
            "request": request,
            # 初回はエラーなしなので None を渡す
            "error": None,
        },
    )

# =========================================================
# ログイン処理
# =========================================================

@app.post("/login")
def login(
    # リクエスト情報
    request: Request,
    # HTMLフォームから username を受け取る
    #
    # Form(...)
    # → 必須入力
    username: str = Form(...),
    # HTMLフォームから password を受け取る
    #
    # Form(...)
    # → 必須入力
    password: str = Form(...),
    # DBセッション自動取得
    #
    # Depends(get_db)
    # → get_db() を自動実行
    db: Session = Depends(get_db),
):
    # ユーザー認証
    #
    # username/password が正しいか確認
    user = authenticate_user(db, username, password)

    # =====================================================
    # 認証失敗
    # =====================================================
    if not user:
        # login.html を再表示
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                # エラーメッセージ表示
                "error": "ユーザー名またはパスワードが違います。",
            },
            # HTTP 401 Unauthorized
            status_code=401,
        )
    # =====================================================
    # JWTトークン生成
    # =====================================================

    token = create_access_token(user)

    # =====================================================
    # ダッシュボードへリダイレクト
    # =====================================================

    response = RedirectResponse(url="/dashboard", status_code=302)

    # =====================================================
    # Cookie保存
    # =====================================================

    response.set_cookie(
        # Cookie名
        key=COOKIE_NAME,
        # 保存するJWTトークン
        value=token,
        # JavaScriptから読めない
        #
        # XSS対策
        httponly=True,
        # CSRF軽減
        #
        # lax:
        # 通常遷移のみCookie送信
        samesite="lax",
        # HTTPS専用
        #
        # 開発環境なのでFalse
        # 本番HTTPSでは True
        secure=False,  # 本番HTTPSでは True
        # 有効期限（秒）
        #
        # 60秒 × 60 = 1時間
        max_age=60 * 60,
    )
    # Cookie付きレスポンス返却
    return response

# =========================================================
# ダッシュボード画面
# =========================================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    # Request必要
    # Cookie取得に使う
    request: Request,
    # DBセッション自動取得
    db: Session = Depends(get_db),
):
    # =====================================================
    # Cookieからログインユーザー取得
    # =====================================================
    current_user = get_current_user_from_cookie(request, db)

    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    today_count = (
        db.query(models.TransportRequest)
        .filter(models.TransportRequest.created_at >= today_start)
        .filter(models.TransportRequest.created_at <= today_end)
        .count()
    )

    requested_count = (
        db.query(models.TransportRequest)
        .filter(models.TransportRequest.status == "REQUESTED")
        .count()
    )

    in_progress_count = (
        db.query(models.TransportRequest)
        .filter(models.TransportRequest.status == "IN_PROGRESS")
        .count()
    )

    done_count = (
        db.query(models.TransportRequest)
        .filter(models.TransportRequest.status == "DONE")
        .count()
    )
    # =====================================================
    # HTML表示
    # =====================================================
    return templates.TemplateResponse(
        # 表示HTML
        "dashboard.html",
        # HTMLへ渡す変数
        {
            "request": request,
            # 現在ログイン中ユーザー
            "current_user": current_user,
            "today_count": today_count,
            "requested_count": requested_count,
            "in_progress_count": in_progress_count,
            "done_count": done_count,
        },
    )
@app.get("/requests", response_class=HTMLResponse)
def request_list(
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = get_current_user_from_cookie(request, db)

    requests = (
        db.query(models.TransportRequest)
        .options(
            joinedload(models.TransportRequest.from_location),
            joinedload(models.TransportRequest.to_location),
            joinedload(models.TransportRequest.assigned_user),
        )
        .order_by(models.TransportRequest.id.desc())
        .all()
    )

    workers = (
        db.query(models.User)
        .filter(models.User.role == "worker")
        .order_by(models.User.id)
        .all()
    )

    return templates.TemplateResponse(
        "request_list.html",
        {
            "request": request,
            "current_user": current_user,
            "requests": requests,
            "workers": workers,
        },
    )


@app.get("/requests/new", response_class=HTMLResponse)
def request_new_page(
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = get_current_user_from_cookie(request, db)
    require_admin(current_user)

    locations = db.query(models.Location).order_by(models.Location.id).all()

    workers = (
        db.query(models.User)
        .filter(models.User.role == "worker")
        .order_by(models.User.id)
        .all()
    )

    return templates.TemplateResponse(
        "request_form.html",
        {
            "request": request,
            "current_user": current_user,
            "locations": locations,
            "workers": workers,
        },
    )


@app.post("/requests/new")
def create_request(
    request: Request,
    part_name: str = Form(...),
    quantity: int = Form(...),
    from_location_id: int = Form(...),
    to_location_id: int = Form(...),
    priority: str = Form(...),
    assigned_user_id: str = Form(""),
    memo: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = get_current_user_from_cookie(request, db)
    require_admin(current_user)

    assigned_id = int(assigned_user_id) if assigned_user_id else None

    transport_request = models.TransportRequest(
        part_name=part_name,
        quantity=quantity,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        priority=priority,
        status="REQUESTED",
        assigned_user_id=assigned_id,
        memo=memo,
    )

    db.add(transport_request)
    db.commit()

    return RedirectResponse(url="/requests", status_code=302)
@app.post("/requests/{request_id}/status")
def update_status(
    request_id: int,
    request: Request,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    ステータス更新。

    管理者・作業者の両方が更新可能。
    実務では REQUESTED → IN_PROGRESS → DONE の順序制御を
    より厳密に入れることもできる。
    """

    current_user = get_current_user_from_cookie(request, db)

    allowed_statuses = ["REQUESTED", "IN_PROGRESS", "DONE"]

    if status not in allowed_statuses:
        return RedirectResponse(url="/requests", status_code=302)

    transport_request = (
        db.query(models.TransportRequest)
        .filter(models.TransportRequest.id == request_id)
        .first()
    )

    if not transport_request:
        return RedirectResponse(url="/requests", status_code=302)

    transport_request.status = status
    db.commit()

    return RedirectResponse(url="/requests", status_code=302)

@app.post("/requests/{request_id}/assign")
def update_assigned_user(
    request_id: int,
    request: Request,
    assigned_user_id: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    担当者変更。

    管理者のみ実行可能。
    """

    current_user = get_current_user_from_cookie(request, db)
    require_admin(current_user)

    transport_request = (
        db.query(models.TransportRequest)
        .filter(models.TransportRequest.id == request_id)
        .first()
    )

    if not transport_request:
        return RedirectResponse(url="/requests", status_code=302)

    transport_request.assigned_user_id = (
        int(assigned_user_id) if assigned_user_id else None
    )

    db.commit()

    return RedirectResponse(url="/requests", status_code=302)
# =========================================================
# ログアウト処理
# =========================================================
@app.get("/logout")
def logout():
    # ログアウト後はログイン画面へリダイレクト
    response = RedirectResponse(url="/login", status_code=302)
    # Cookie削除
    #
    # ブラウザ側のJWTを消す
    response.delete_cookie(COOKIE_NAME)
    return response