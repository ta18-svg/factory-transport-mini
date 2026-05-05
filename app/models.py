# 日時管理で使用（created_at / updated_at）
from datetime import datetime
# SQLAlchemyのカラム型や関数をインポート
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
# ORM関連（型付きORM）
from sqlalchemy.orm import Mapped, mapped_column, relationship
# Baseクラス（すべてのテーブルの親）
from app.db import Base

# =========================================================
# users テーブル
# =========================================================
class User(Base):
    """
    users テーブル

    管理者・作業者のログイン情報を管理する。
    role は admin / worker を想定。
    ■役割
    ・ログインユーザーを管理する
    ・管理者 / 作業者の区別を持つ

    ■ポイント
    ・パスワードは平文ではなくハッシュで保存
    ・roleで権限制御する
    """
    # テーブル名（DB上の名前）
    __tablename__ = "users"

    # -------------------------
    # 主キー（ID）
    # id        : Mapped[int] = mapped_column(...)
    # ↑変数名     ↑型情報         ↑DBカラム定義
    # -------------------------
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True, # 主キー
        index=True        # 検索高速化（WHERE id=...）
    )

    # -------------------------
    # ログインID
    # -------------------------
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,      # 重複禁止
        nullable=False,   # NULL禁止
        index=True        # 検索頻度高いのでインデックス
    )
    # -------------------------
    # パスワード（ハッシュ）
    # -------------------------
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    # -------------------------
    # 権限
    # -------------------------
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="worker"  # デフォルトは作業者
    )
    # -------------------------
    # 作成日時
    # -------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # DB側で現在時刻を自動設定
        nullable=False
    )
    # -------------------------
    # 更新日時
    # -------------------------
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),       # UPDATE時に自動更新
        nullable=False
    )
    # -------------------------
    # リレーション（1対多）
    # -------------------------
    # User 1人に対して、複数の搬送依頼が割り当てられる
    assigned_requests: Mapped[list["TransportRequest"]] = relationship(
        back_populates="assigned_user"
    )

# =========================================================
# locations テーブル
# =========================================================
class Location(Base):
    """
    locations テーブル

    工場内の場所を管理する。
    from_location / to_location を文字列で持たず、
    locations.id を参照することで表記ゆれを防ぐ。
    ■役割
    ・工場内の場所マスタ

    ■重要設計
    ・文字列ではなくIDで管理（超重要）
    """
    # テーブル名（DB上の名前）
    __tablename__ = "locations"
    # 主キー
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    # 場所名（例：第一加工場）
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,     # 重複禁止
        nullable=False
    )
    # 種類（工程 / 倉庫 / 検査）
    area_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    # 作成日時
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    # 更新日時
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    # -------------------------
    # リレーション（出発元）
    # -------------------------
    # この場所を出発場所として使う搬送依頼
    requests_from: Mapped[list["TransportRequest"]] = relationship(
        back_populates="from_location",
        foreign_keys="TransportRequest.from_location_id"
    )
    # -------------------------
    # リレーション（届け先）
    # -------------------------
    # この場所を届け先として使う搬送依頼
    requests_to: Mapped[list["TransportRequest"]] = relationship(
        back_populates="to_location",
        foreign_keys="TransportRequest.to_location_id"
    )

# =========================================================
# transport_requests テーブル
# =========================================================
class TransportRequest(Base):
    """
    transport_requests テーブル

    工場内の搬送依頼を管理する。
    出発場所・届け先は locations テーブルへの外部キーで管理する。
    ■役割
    ・搬送依頼の実体データ

    ■重要
    ・from/toはIDで管理（locationsと外部キー）
    """
    # テーブル名（DB上の名前）
    __tablename__ = "transport_requests"

    # -------------------------
    # 主キー
    # -------------------------
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    # 部品名
    part_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    # 数量
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    # -------------------------
    # 外部キー（出発場所）
    # -------------------------
    from_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False
    )
    # -------------------------
    # 外部キー（届け先）
    # -------------------------
    to_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False
    )
    # 優先度
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NORMAL"
    )
    # ステータス
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="REQUESTED"
    )
    # メモ（NULL許可）
    memo: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    # -------------------------
    # 外部キー（担当者）
    # -------------------------
    assigned_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True   # 未割当を許可
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # -------------------------
    # リレーション（担当者）
    # -------------------------
    assigned_user: Mapped[User | None] = relationship(
        back_populates="assigned_requests"
    )

    # -------------------------
    # リレーション（出発場所）
    # -------------------------
    from_location: Mapped[Location] = relationship(
        back_populates="requests_from",
        foreign_keys=[from_location_id]
    )

    # -------------------------
    # リレーション（届け先）
    # -------------------------
    to_location: Mapped[Location] = relationship(
        back_populates="requests_to",
        foreign_keys=[to_location_id]
    )