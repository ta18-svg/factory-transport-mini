from datetime import date, datetime, time

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app import models
from app.auth import (
    COOKIE_NAME,
    authenticate_user,
    create_access_token,
    get_current_user_from_cookie,
    require_admin,
)
from app.db import Base, engine, get_db

app = FastAPI(
    title="Factory Transport Mini",
    description="工場内搬送依頼管理システム",
    version="0.1.0",
)

templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username, password)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "ユーザー名またはパスワードが違います。",
            },
            status_code=401,
        )

    token = create_access_token(user)
    response = RedirectResponse(url="/dashboard", status_code=302)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60,
    )

    return response


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
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

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
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


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response