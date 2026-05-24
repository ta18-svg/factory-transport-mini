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
# FastAPIのレスポンス関連
# =========================================================

# StreamingResponse を読み込む。
#
# 通常のHTML返却ではなく、
# 「ファイルダウンロード用レスポンス」を返すために使う。
#
# 今回は CSVファイル をブラウザへ返す用途。
#
# 例:
# transport_requests.csv をダウンロードさせる
#
# FastAPIの通常レスポンス:
# return {"message": "OK"}
#
# CSV出力:
# return StreamingResponse(...)
#
from fastapi.responses import StreamingResponse


# =========================================================
# CSV操作ライブラリ
# =========================================================

# Python標準ライブラリの csv。
#
# CSV形式を書き込むために使う。
#
# 例:
# ID,部品名,数量
# 1,モーター,10
#
# writer.writerow([...])
# で1行ずつCSVへ出力する。
#
# pandasを使わなくても、
# 軽量にCSV出力できる。
#
import csv


# =========================================================
# メモリ上ファイル（重要）
# =========================================================

# Python標準ライブラリの io。
#
# StringIO を使うために必要。
#
# StringIO は
# 「メモリ上の仮想テキストファイル」。
#
# 通常ファイル:
#
# open("sample.csv", "w")
#
# はディスクへ保存する。
#
# しかし今回は、
# 一時的にCSVを生成して
# そのままブラウザへ返したい。
#
# そのため、
# メモリ上にCSVを作る。
#
import io
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
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """
    搬送依頼一覧画面。

    status クエリパラメータで絞り込み可能。

    例:
    /requests
    /requests?status=REQUESTED
    /requests?status=IN_PROGRESS
    /requests?status=DONE
    """

    current_user = get_current_user_from_cookie(request, db)

    allowed_statuses = ["REQUESTED", "IN_PROGRESS", "DONE"]

    query = (
        db.query(models.TransportRequest)
        .options(
            joinedload(models.TransportRequest.from_location),
            joinedload(models.TransportRequest.to_location),
            joinedload(models.TransportRequest.assigned_user),
        )
    )

    # status が指定されていて、許可された値なら絞り込み
    if status in allowed_statuses:
        query = query.filter(models.TransportRequest.status == status)
    else:
        status = None

    requests = (
        query
        .order_by(models.TransportRequest.updated_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "request_list.html",
        {
            "request": request,
            "current_user": current_user,
            "requests": requests,
            "selected_status": status,
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

@app.get("/requests/{request_id}/edit", response_class=HTMLResponse)
def edit_request_page(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = get_current_user_from_cookie(request, db)

    transport_request = (
        db.query(models.TransportRequest)
        .options(
            joinedload(models.TransportRequest.from_location),
            joinedload(models.TransportRequest.to_location),
            joinedload(models.TransportRequest.assigned_user),
        )
        .filter(models.TransportRequest.id == request_id)
        .first()
    )

    if not transport_request:
        return RedirectResponse(url="/requests", status_code=302)

    workers = (
        db.query(models.User)
        .filter(models.User.role == "worker")
        .order_by(models.User.id)
        .all()
    )

    return templates.TemplateResponse(
        "request_edit.html",
        {
            "request": request,
            "current_user": current_user,
            "transport_request": transport_request,
            "workers": workers,
        },
    )


@app.post("/requests/{request_id}/edit")
def update_request(
    request_id: int,
    request: Request,
    status: str = Form(...),
    assigned_user_id: str = Form(""),
    memo: str = Form(""),
    db: Session = Depends(get_db),
):
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

    # 管理者・作業者どちらもステータス更新可能
    transport_request.status = status

    # メモも更新可能
    transport_request.memo = memo

    # 担当者変更は管理者のみ
    if current_user.role == "admin":
        transport_request.assigned_user_id = (
            int(assigned_user_id) if assigned_user_id else None
        )

    db.commit()

    return RedirectResponse(url="/requests", status_code=302)
# =========================================================
# CSVダウンロード用API
# =========================================================

# GETリクエスト
# URL例:
# /requests/export/csv
# /requests/export/csv?status=DONE
# ブラウザからアクセスすると
# CSVファイルをダウンロードする。
#
@app.get("/requests/export/csv")
def export_requests_csv(
    # -----------------------------------------------------
    # FastAPI Request オブジェクト
    # -----------------------------------------------------
    # Cookie取得などに使用。
    # 今回はJWT Cookie認証確認で使う。
    #
    request: Request,
    # -----------------------------------------------------
    # ステータスフィルタ
    # -----------------------------------------------------
    # クエリパラメータ。
    # 例:
    # /requests/export/csv?status=DONE
    # の場合:
    # status = "DONE"
    # 指定なしなら None。
    #
    status: str | None = None,
    # -----------------------------------------------------
    # DBセッション
    # -----------------------------------------------------
    # Depends(get_db)
    # DB接続を取得する。
    # これがないとDBにアクセスできない。
    db: Session = Depends(get_db),
):
    # =====================================================
    # ログインユーザー取得
    # =====================================================
    # HttpOnly Cookie のJWTから
    # ログインユーザーを取得。
    #
    current_user = get_current_user_from_cookie(request, db)
    # =====================================================
    # 許可するステータス一覧
    # =====================================================
    # 不正値対策。
    # 例:
    # ?status=AAAA
    # を防ぐ。
    #
    allowed_statuses = ["REQUESTED", "IN_PROGRESS", "DONE"]
    # =====================================================
    # SQLAlchemy Query作成
    # =====================================================
    # transport_requests テーブル取得。
    # joinedload を使い、
    # 関連テーブルもまとめて取得。
    #
    query = (
        # ---------------------------------------------
        # transport_requests テーブル
        # ---------------------------------------------
        db.query(models.TransportRequest)
        # ---------------------------------------------
        # relatedデータ先読み
        # ---------------------------------------------
        # N+1問題対策。
        # これがないと、ループ内で関連テーブルを都度クエリ発行してしまう。
        .options(
            # 出発場所
            joinedload(models.TransportRequest.from_location),
            # 届け先
            joinedload(models.TransportRequest.to_location),
            # 担当者
            joinedload(models.TransportRequest.assigned_user),
        )
    )
    # =====================================================
    # ステータスフィルタ
    # =====================================================
    # status が有効値なら絞り込み。
    # 例:
    # status = "DONE"
    # ↓
    # WHERE status = 'DONE'
    #
    if status in allowed_statuses:
        query = query.filter(models.TransportRequest.status == status)
    # =====================================================
    # DB取得
    # =====================================================
    # updated_at 降順。
    # 最近更新されたものを上へ表示。
    #
    requests = (
        query
        # ORDER BY updated_at DESC
        # これがないと、ID順（昇順）で古いものが上に来てしまう。
        .order_by(models.TransportRequest.updated_at.desc())
        # 全件取得
        .all()
    )
    # =====================================================
    # メモリ上CSVファイル作成
    # =====================================================
    # StringIO を使い、
    # メモリ上の仮想ファイル。
    # ディスク保存せず、
    # 一時的にCSVを生成する。
    #
    output = io.StringIO()
    # =====================================================
    # CSV Writer作成
    # =====================================================
    # output にCSVを書き込むためのオブジェクト。
    #
    writer = csv.writer(output)
    # =====================================================
    # CSVヘッダー行
    # =====================================================
    # CSVの1行目。
    # Excelで開いた時の列名。
    #
    writer.writerow([
        "ID",
        "部品名",
        "数量",
        "出発場所",
        "届け先",
        "優先度",
        "ステータス",
        "担当者",
        "メモ",
        "作成日時",
        "更新日時",
    ])
    # =====================================================
    # CSVデータ行
    # =====================================================
    # requests を1件ずつCSVへ書き込む。
    #
    for req in requests:
        writer.writerow([
            # 搬送依頼ID
            req.id,
            # 部品名
            req.part_name,
            # 数量
            req.quantity,
            # 出発場所名
            req.from_location.name,
            # 届け先名
            req.to_location.name,
            # 優先度
            req.priority,
            # ステータス
            req.status,
            # 担当者名（未割当なら "未割当"）
            req.assigned_user.username if req.assigned_user else "未割当",
            # メモ（空なら空文字）None対策。
            req.memo or "",
            # 作成日時
            # datetime → 文字列変換
            req.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            # 更新日時
            # datetime → 文字列変換
            req.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])
    # =====================================================
    # 読み込み位置を先頭へ戻す
    # =====================================================
    # seek(0)
    # ファイルポインタを先頭へ戻す。
    # これしないと
    # 空CSVになることがある。
    output.seek(0)
    # =====================================================
    # CSVダウンロードレスポンス
    # =====================================================
    # StreamingResponse を使い、
    # ブラウザへCSVファイル返却。
    #
    return StreamingResponse(
        # ---------------------------------------------
        # CSV文字列
        # ---------------------------------------------
        # output.getvalue()
        # StringIO内の全文字列取得。
        #
        iter([output.getvalue()]),
        # ---------------------------------------------
        # MIME Type
        # ---------------------------------------------
        # text/csv
        # utf-8-sig
        # Excel文字化け対策。
        #
        media_type="text/csv; charset=utf-8-sig",
        # ---------------------------------------------
        # HTTPヘッダー
        # ---------------------------------------------
        # attachment
        # → ダウンロード扱い
        # filename=
        # → 保存ファイル名
        #
        headers={
            "Content-Disposition": "attachment; filename=transport_requests.csv"
        },
    )

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