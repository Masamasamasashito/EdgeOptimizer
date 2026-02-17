# AZFUNC_XXXXXはdocker-compose.ymlで指定された値が使用される

# Docker Official Image
ARG AZFUNC_DOCKER_IMAGE=python
ARG AZFUNC_DOCKER_IMAGE_TAG=slim-bookworm
FROM ${AZFUNC_DOCKER_IMAGE}:${AZFUNC_DOCKER_IMAGE_TAG}

# Azure Functions ローカル実行用の環境変数（必須ではないが一応セット）
ENV AzureWebJobsScriptRoot=/container_workspace \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# 必要なツール群
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    git \
    libicu-dev \
    && rm -rf /var/lib/apt/lists/*

# Azure Functions Core Tools Install
ARG AZFUNC_CORE_TOOLS_VERSION=4
# Debian 12 (bookworm) 用 Microsoft リポジトリを追加
RUN curl https://packages.microsoft.com/keys/microsoft.asc | \
    gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg && \
    echo "deb [arch=amd64] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/azure-functions.list && \
    apt-get update && \
    apt-get install -y azure-functions-core-tools-${AZFUNC_CORE_TOOLS_VERSION} && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /container_workspace

# Check
RUN python --version && func --version