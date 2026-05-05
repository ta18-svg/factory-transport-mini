from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.db import SessionLocal
from app.models import User, Location


# パスワードをハッシュ化するための設定
# bcryptを使い、平文パスワードをDBに保存しない
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def get_password_hash(password: str) -> str:
    """
    平文パスワードをハッシュ化する関数。
    例：
    admin123 → bcrypt形式の長い文字列
    """
    return pwd_context.hash(password)


def seed_users(db: Session):
    """
    初期ユーザーを登録する。
    すでに同じusernameが存在する場合は登録しない。
    """

    users = [
        {
            "username": "admin",
            "password": "admin123",
            "role": "admin",
        },
        {
            "username": "worker1",
            "password": "worker123",
            "role": "worker",
        },
        {
            "username": "worker2",
            "password": "worker123",
            "role": "worker",
        },
    ]

    for user_data in users:
        existing_user = (
            db.query(User)
            .filter(User.username == user_data["username"])
            .first()
        )

        if existing_user:
            continue

        user = User(
            username=user_data["username"],
            password_hash=get_password_hash(user_data["password"]),
            role=user_data["role"],
        )

        db.add(user)

    db.commit()


def seed_locations(db: Session):
    """
    初期ロケーションを登録する。
    搬送元・搬送先は文字列ではなく、このlocations.idを参照する。
    """

    locations = [
        {
            "name": "第一加工場",
            "area_type": "工程",
        },
        {
            "name": "第二加工場",
            "area_type": "工程",
        },
        {
            "name": "検査エリア",
            "area_type": "検査",
        },
        {
            "name": "部品倉庫",
            "area_type": "倉庫",
        },
        {
            "name": "出荷場",
            "area_type": "出荷",
        },
    ]

    for location_data in locations:
        existing_location = (
            db.query(Location)
            .filter(Location.name == location_data["name"])
            .first()
        )

        if existing_location:
            continue

        location = Location(
            name=location_data["name"],
            area_type=location_data["area_type"],
        )

        db.add(location)

    db.commit()


def run_seed():
    """
    初期データ投入のメイン処理。
    DBセッションを開き、ユーザーとロケーションを登録する。
    """

    db = SessionLocal()

    try:
        seed_users(db)
        seed_locations(db)
        print("初期データ投入が完了しました。")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()