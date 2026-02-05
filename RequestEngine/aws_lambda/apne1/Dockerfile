# LAMBDA_LAYER_XXXXXはdocker-compose.ymlで指定された値が使用される

# Docker Official Image
ARG LAMBDA_LAYER_DOCKER_IMAGE=python
ARG LAMBDA_LAYER_DOCKER_IMAGE_TAG=slim
FROM ${LAMBDA_LAYER_DOCKER_IMAGE}:${LAMBDA_LAYER_DOCKER_IMAGE_TAG}

# 必要なパッケージを事前にインストール
RUN apt-get update && \
    apt-get install -y zip && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip

# 作業ディレクトリの設定
WORKDIR /lambda-layer