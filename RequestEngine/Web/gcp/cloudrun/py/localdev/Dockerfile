# GCP_CLOUDRUN_XXXXXはdocker-compose.ymlで指定された値が使用される

# Docker Official Image
# Python 3.14 2026/1/16
ARG GCP_CLOUDRUN_DOCKER_IMAGE=python
ARG GCP_CLOUDRUN_DOCKER_IMAGE_TAG=slim
FROM ${GCP_CLOUDRUN_DOCKER_IMAGE}:${GCP_CLOUDRUN_DOCKER_IMAGE_TAG}

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新と必要なツールのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係をインストール
COPY funcfiles/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY funcfiles/main.py .

# Cloud Run は PORT 環境変数でポートを指定
# デフォルトは8080
ENV PORT=8080

# ポートを公開
EXPOSE 8080

# Cloud Run 用のエントリーポイント
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 300 main:app
