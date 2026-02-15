# CF_WORKER_XXXXXはdocker-compose.ymlで指定された値が使用される

# Docker Official Image
ARG CF_WORKER_DOCKER_IMAGE=node
ARG CF_WORKER_DOCKER_IMAGE_TAG=slim
FROM ${CF_WORKER_DOCKER_IMAGE}:${CF_WORKER_DOCKER_IMAGE_TAG}

# 必要に応じて、OSレベルのパッケージが必要ならここに追加
# 例: RUN apt-get update && apt-get install -y git

# コンテナ内の作業ディレクトリ
WORKDIR /app