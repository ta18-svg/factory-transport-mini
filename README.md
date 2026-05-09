




docker compose up -d --build

docker compose restart app

docker compose down

### コンテナ内のMySQLでテーブル確認
docker compose exec db mysql -uappuser -papppass factory_transport_db

SELECT DATABASE();
SHOW TABLES;

docker compose restart app

### seed.py の実行方法
docker compose exec app python -m app.seed
