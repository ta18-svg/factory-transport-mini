# Python 3.12 の軽量イメージを使用
FROM python:3.12-slim

# Pythonのログを即時出力する
ENV PYTHONUNBUFFERED=1

# コンテナ内の作業ディレクトリ
WORKDIR /app

# 依存関係ファイルを先にコピー
COPY requirements.txt .

# Pythonライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体をコピー
COPY ./app ./app

# FastAPIの起動ポート
EXPOSE 8000