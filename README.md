# Factory Transport Mini

Factory Transport Mini は、工場内で発生する搬送依頼を管理する簡易Webシステムです。

「どの部品を、どこからどこへ、誰が、どの状態で運んでいるか」を見える化することを目的としています。

---

## システム概要

管理者は搬送依頼を登録し、担当者を変更できます。
作業者は全依頼を確認し、ステータスを更新できます。

搬送依頼には、部品名、数量、出発場所、届け先、優先度、メモ、担当者を登録します。

---

## 技術構成

| 分野 | 技術 |
|---|---|
| バックエンド | FastAPI |
| DB | MySQL |
| ORM | SQLAlchemy |
| マイグレーション | Alembic |
| 認証 | JWT × HttpOnly Cookie |
| 画面 | Jinja2 / Bootstrap |
| 環境構築 | Docker Compose |

---

## 主な機能

1. ログイン
2. 搬送依頼登録
3. 搬送依頼一覧
4. ステータス更新
5. 簡易ダッシュボード

---

## 画面

| 画面 | 内容 |
|---|---|
| ログイン画面 | JWT認証によるログイン |
| ダッシュボード画面 | 本日の依頼数、未対応、対応中、完了件数を表示 |
| 搬送依頼一覧画面 | 全搬送依頼の一覧表示、ステータス更新、担当者変更 |
| 搬送依頼登録画面 | 管理者が搬送依頼を登録 |

---

## DB設計

本システムでは以下の3テーブルを使用しています。

- users
- locations
- transport_requests

### ER図

```mermaid
erDiagram
    users ||--o{ transport_requests : "assigned_user_id"
    locations ||--o{ transport_requests : "from_location_id"
    locations ||--o{ transport_requests : "to_location_id"

    users {
        int id PK
        varchar username
        varchar password_hash
        varchar role
        datetime created_at
        datetime updated_at
    }

    locations {
        int id PK
        varchar name
        varchar area_type
        datetime created_at
        datetime updated_at
    }

    transport_requests {
        int id PK
        varchar part_name
        int quantity
        int from_location_id FK
        int to_location_id FK
        varchar priority
        varchar status
        text memo
        int assigned_user_id FK
        datetime created_at
        datetime updated_at
    }
```

docker compose up -d --build

docker compose restart app

docker compose down

### ログイン画面
http://localhost:8000/login


### コンテナ内のMySQLでテーブル確認
docker compose exec db mysql -uappuser -papppass factory_transport_db

SELECT DATABASE();
SHOW TABLES;

docker compose restart app

### seed.py の実行方法
docker compose exec app python -m app.seed
