# EO Terraform Docker

EO Request Engine の Terraform を **Docker Compose で実行するための基盤**です。Terraform 本体はホストにインストールせず、コンテナ内で実行します。

## ディレクトリ構成

```
EO_Terraform_Docker/
├── README.md                         # このファイル
├── docker-compose.yml                # Terraform 実行用サービス定義
├── docker-compose.override.example.yml # 認証マウント用 override 例
├── env.example                       # 環境変数例
└── terraform/                        # Terraform 実行用イメージ
    └── Dockerfile
```

Terraform のコード（`.tf` や `modules/`）は **リポジトリルートの `terraform/`** にあり、Compose 実行時にそのディレクトリを `/workspace` にマウントします。

## 前提条件

- Docker および Docker Compose が利用できること
- リポジトリルートに `terraform/` ディレクトリがあること（本リポジトリの構成を想定）

## クイックスタート

### 1. 環境ファイルの準備

```bash
cd EO_Terraform_Docker
cp env.example .env
# .env を編集（TERRAFORM_WORKSPACE は通常そのままで可）
```

### 2. 認証を渡す場合（plan / apply でクラウドに接続する場合）

`.env` に認証ディレクトリのパスを設定し、override を有効にします。

```bash
cp docker-compose.override.example.yml docker-compose.override.yml
# .env に以下を設定（使用するクラウドのみ）
# Linux/Mac 例:
# TF_AWS_CREDENTIALS_PATH=/home/yourname/.aws
# TF_AZURE_CREDENTIALS_PATH=/home/yourname/.azure
# TF_GCP_CREDENTIALS_PATH=/home/yourname/.config/gcloud
#
# Windows 例（PowerShell で .env に追記）:
# TF_AWS_CREDENTIALS_PATH=C:\Users\YourName\.aws
```

`docker-compose.override.yml` で使用しないクラウドの volume はコメントアウトしてください。

### 3. イメージのビルド（初回または Dockerfile 変更時）

```bash
docker compose build
```

### 4. Terraform の実行

**EO_Terraform_Docker** をカレントディレクトリにして実行します。

```bash
# 初期化
docker compose run --rm terraform init

# プラン（全体）
docker compose run --rm terraform plan

# プラン（特定プロバイダーのみ）
docker compose run --rm terraform plan -target=module.aws
docker compose run --rm terraform plan -target=module.azure
docker compose run --rm terraform plan -target=module.gcp

# 適用
docker compose run --rm terraform apply

# 破棄
docker compose run --rm terraform destroy

# 出力値の表示
docker compose run --rm terraform output
```

`--rm` で実行後コンテナを削除するため、常に one-shot で使います。

## 変数・認証

- **terraform.tfvars**: リポジトリの `terraform/` 内に配置し、非機密の変数を記載。
- **機密（TF_VAR_req_secret など）**: `.env` の `TF_VAR_req_secret` で渡すか、`docker compose run` の `-e` で渡してください。Compose の `environment` で `.env` の値がコンテナに渡されます。
- **クラウド認証**: 各 CLI（`aws configure` / `az login` / `gcloud auth application-default login`）でホスト側で認証したうえで、上記のとおり `TF_*_CREDENTIALS_PATH` と override でコンテナにマウントします。

## イメージの更新

Dockerfile やベースイメージのバージョンを変えた場合:

```bash
docker compose down
docker compose build --no-cache
docker compose run --rm terraform version
```

EO_Infra_Docker と同様、カスタムイメージ名は `-eo` サフィックス付きです（例: `hashicorp/terraform-eo:1.6`）。

## 関連ドキュメント

- リポジトリの **terraform/README.md** … Terraform の前提・ディレクトリ構成・Docker 単体での実行例
- **terraform/TERRAFORM_GUIDE.md** … セットアップと運用の詳細
- **terraform/BACKEND_NEON_GUIDE.md** … リモートステート（Neon 等）の設定
