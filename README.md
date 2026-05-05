




docker compose up -d --build

docker compose down

### コンテナ内のMySQLでテーブル確認
docker compose exec db mysql -uappuser -papppass factory_transport_db

SELECT DATABASE();

