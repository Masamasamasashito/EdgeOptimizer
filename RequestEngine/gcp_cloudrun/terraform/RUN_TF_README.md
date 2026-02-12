# GCP Cloud Run Request Engine - Terraform 構築手順

Terraform を使用した GCP Cloud Run Request Engine インフラストラクチャの構築手順です。

※Terraform でうまくできない場合、お手数ですが [RUN_README.md](../ane1/RUN_README.md) の手動手順（gcloud CLI / GUIコンソール）を参照してください。

## 目次

- [概要](#概要)
- [作成されるリソース一覧](#作成されるリソース一覧)
- [STEP 0: 事前準備](#step-0-事前準備)
- [STEP 1: Terraform 初期設定](#step-1-terraform-初期設定)
- [STEP 2: Terraform デプロイ](#step-2-terraform-デプロイ)
- [STEP 3: デプロイ後の設定](#step-3-デプロイ後の設定)
- [STEP 4: GitHub Secrets の設定](#step-4-github-secrets-の設定)
- [STEP 5: GitHub Actions で Cloud Run をデプロイ](#step-5-github-actions-で-cloud-run-をデプロイ)
- [STEP 6: n8n Credentials / ノード設定](#step-6-n8n-credentials--ノード設定)
- [パラメータ一覧](#パラメータ一覧)
- [トラブルシューティング](#トラブルシューティング)
- [関連ドキュメント](#関連ドキュメント)

## 概要

このディレクトリの Terraform テンプレートは、Edge Optimizer の GCP Cloud Run Request Engine に必要な以下のリソースを一括作成します。

### 「プロバイダ」の用語について

本ドキュメントでは **2種類の「プロバイダ」** が登場します。混同しやすいため注意してください。

| 用語 | 正式名称 | 役割 | 本文中の表記 |
|------|---------|------|-------------|
| **Terraform プロバイダ** | Terraform Cloud Provider Plugin | Terraform がクラウド API を操作するためのプラグイン（`hashicorp/google`） | 「Terraform プロバイダ」 |
| **WIF ID プロバイダ (IdP)** | GCP Workload Identity Federation Identity Provider | GitHub Actions OIDC トークンを GCP 認証に変換する ID 連携の窓口 | 「WIF IdP」「ID プロバイダ」 |

### GCP タグキーと EO リソースラベルの使い分け

GCP には**2種類の環境識別の仕組み**があり、EdgeOptimizerでは両方を使用しています。

**1. GCP Resource Manager タグ**（組織レベル）

| 正式名称 | キー | 値 | 管理場所 | 用途 |
|---------|------|-----|---------|------|
| Organization Resource Manager Tag | タグキー `environment` | タグ値 `Development` / `Production` 等（Google 固定4種） | GCP 組織コンソール | 課金レポート・組織ポリシー適用 |

**2. GCP リソースラベル**（リソースレベル）

`eo_gcp_resource_labels`（`main.tf` の `locals` で定義した `map(string)`）を各リソースに `labels = local.eo_gcp_resource_labels` として付与:

```
eo_gcp_resource_labels
  │
  ├── project     = "eo"         ← GCP ラベルキー "project"  に ラベル値 "eo" を設定
  ├── component   = "re"         ← GCP ラベルキー "component" に ラベル値 "re" を設定
  ├── environment = "d01"        ← GCP ラベルキー "environment" に ラベル値 "d01" を設定
  └── managed-by  = "terraform"  ← GCP ラベルキー "managed-by" に ラベル値 "terraform" を設定
        │                │
        │                └─ GCP ラベル値（各リソースに実際に付く value）
        └─ GCP ラベルキー（各リソースに実際に付く key）
```

付与先: Cloud Run / Secret Manager / Artifact Registry
用途: リソース識別・フィルタリング・コスト配分

両者は意図的に異なる値（タグ値 `Development` vs ラベル値 `d01`）を使うことで「どちらの環境識別か」が一目で区別できます。

### Terraform ファイル構成

| ファイル | 説明 |
|---------|------|
| `main.tf` | **Terraform プロバイダ**（`hashicorp/google`）設定、ローカル変数（命名規則） |
| `variables.tf` | 全入力変数の定義（デフォルト値付き） |
| `apis.tf` | 必要な GCP API の有効化（7件） |
| `service_accounts.tf` | Service Account 3件 + 全ロール設定 |
| `secret_manager.tf` | Secret Manager シークレット作成 |
| `wif.tf` | Workload Identity Pool / **WIF IdP**（GitHub Actions OIDC 認証） |
| `artifact_registry.tf` | Artifact Registry リポジトリ |
| `cloud_run.tf` | Cloud Run サービス（プレースホルダー） |
| `outputs.tf` | GitHub Secrets 等に必要な出力値 |
| `terraform.tfvars.example` | 変数の設定例 |

## 作成されるリソース一覧

**命名規則**

- {pj}: プロジェクトプレフィックス（例: `eo`）
- {comp}: コンポーネント名（例: `re` は Request Engine）
- {env}: 環境名（例: `d01` は dev01）
- {region}: リージョン短縮名（例: `ane1` は asia-northeast1）

デフォルトパラメータの場合:

| リソース種別 | リソース名 | 説明 |
|-------------|-----------|------|
| GCP API（7件） | - | cloudfunctions, cloudbuild, artifactregistry, run, secretmanager, iam, iamcredentials |
| Service Account | `{pj}-gcp-sa-{env}-deploy-{region}` | Deployer SA（GitHub Actions デプロイ用） |
| Service Account | `{pj}-gcp-sa-{env}-runtime-{region}` | Runtime SA（Cloud Run 実行 + Secret Manager） |
| Service Account | `{pj}-gcp-sa-{env}-oa2be-inv-{region}` | OAuth2 Invoker SA（n8n 認証用） |
| IAM Bindings | 複数 | SA ごとのプロジェクトレベル / リソースレベルロール |
| Secret Manager | `{pj}-{comp}-{env}-secretmng` | 照合用リクエストシークレット（プレースホルダー） |
| WIF Pool | `{pj}-gcp-pool-wif-{env}` | Workload Identity Pool |
| WIF IdP | `{pj}-gcp-idp-gh-oidc-wif-{env}` | GitHub Actions OIDC ID プロバイダ（※Terraform プロバイダとは別物） |
| Artifact Registry | `cloud-run-source-deploy` | Docker リポジトリ（ソースデプロイ用） |
| Cloud Run Service | `{pj}-{comp}-{env}-cloudrun-{region}` | Request Engine サービス（プレースホルダーイメージ） |

## STEP 0: 事前準備

### 0-1. GCP プロジェクト

以下が完了していること:
- GCP プロジェクトが作成済み
- 課金が有効化済み

### 0-2. 環境変数設定

以降のコマンドで使用する変数を事前に設定します（[RUN_README.md](../ane1/RUN_README.md) と同じ変数名）。

- EX) `export EO_GCP_PROJECT_ID="eo-re-d01-pr-ane1"`

```bash
# GCP プロジェクト
export EO_GCP_PROJECT_ID="<GCPプロジェクトID>"              # 例: "eo-re-d01-pr-ane1"
export EO_GCP_PROJECT_NUMBER="<GCPプロジェクト番号>"         # 例: "123456789012"

# GCP 組織（組織配下のプロジェクトの場合）
export GCP_ORGANIZATION_ID="<GCP組織ID>"                    # 例: "1234567890"

# GitHub
export EO_GCP_PROJECT_GITHUB_ORG_or_USER="<Github組織名orユーザー名>"  # 例: "Masamasamasashito"
export EO_GCP_PROJECT_GITHUB_REPO="<Githubリポジトリ名>"               # 例: "EdgeOptimizer"

# 照合用リクエストシークレット（EO_Infra_Docker/.env の N8N_EO_REQUEST_SECRET と同じ値）
export N8N_EO_REQUEST_SECRET="<N8N_EO_REQUEST_SECRETの値>"
```

プロジェクト番号の確認:

```bash
gcloud projects describe $EO_GCP_PROJECT_ID --format='value(projectNumber)'
```

### 0-3. gcloud CLI 認証とプロジェクト設定

Terraform が GCP API を呼び出すための認証とプロジェクト設定:

```bash
# 1. ADC（Application Default Credentials）認証
#    Terraform 等のツールが GCP API を呼び出すための認証情報を取得
gcloud auth application-default login

# 2. プロジェクト設定 + クォータプロジェクト統一（WARNING 防止）
gcloud config set project $EO_GCP_PROJECT_ID
gcloud auth application-default set-quota-project $EO_GCP_PROJECT_ID

# 3. 環境タグキー設定（組織配下のプロジェクトの場合）
#    組織 ID を確認
gcloud organizations list

#    タグキー「environment」を作成（組織に1回だけ）
gcloud resource-manager tags keys create environment \
  --parent=organizations/$GCP_ORGANIZATION_ID

#    タグ値「development」を作成（タグキーに1回だけ）
gcloud resource-manager tags values create development \
  --parent=$GCP_ORGANIZATION_ID/environment

#    プロジェクトにバインド
gcloud resource-manager tags bindings create \
  --tag-value=$GCP_ORGANIZATION_ID/environment/development \
  --parent=//cloudresourcemanager.googleapis.com/projects/$EO_GCP_PROJECT_NUMBER \
  --location=global
```

### 0-4. Terraform インストール/更新

**Windows (winget):**
```powershell
winget install HashiCorp.Terraform
```

**macOS (Homebrew):**
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

**バージョン確認:**
```bash
terraform --version
# >= 1.5.0 であること
```

## STEP 1: Terraform 初期設定

### 1-1. 変数ファイルの作成

```bash
cd RequestEngine/gcp_cloudrun/terraform/
```

環境変数（STEP 0-2）から `terraform.tfvars` を生成:

```bash
cat <<EOF > terraform.tfvars
gcp_project_id     = "$EO_GCP_PROJECT_ID"
gcp_project_number = "$EO_GCP_PROJECT_NUMBER"
github_org         = "$EO_GCP_PROJECT_GITHUB_ORG_or_USER"
github_repo        = "$EO_GCP_PROJECT_GITHUB_REPO"
EOF
```

> `terraform.tfvars.example` に記載されたパラメータ名と同一です。手動で編集する場合はテンプレートを参照してください。

### 1-2. Terraform 初期化

```bash
terraform init
```

成功すると `Terraform has been successfully initialized!` と表示されます。

## STEP 2: Terraform デプロイ

### 2-1. 実行計画の確認

```bash
terraform plan -var-file=terraform.tfvars
```

作成されるリソースの一覧を確認してください。

### 2-2. デプロイ実行

```bash
terraform apply -var-file=terraform.tfvars
```

確認プロンプトで `yes` を入力してデプロイを開始します。

> 所要時間: 約3〜5分（API有効化に時間がかかる場合があります）

### 2-3. 出力値の確認

デプロイ完了後、以下のコマンドで出力値を確認:

```bash
terraform output
```

表示される値は STEP 4 の GitHub Secrets 設定で使用します。

## STEP 3: デプロイ後の設定

### 3-1. 【重要】Secret Manager 値の更新

Terraform はプレースホルダー値でシークレットを作成しています。実際の値に更新してください。

**Google Cloud Console GUI:**

1. Secret Manager > `eo-re-d01-secretmng`
2. 「+ 新しいバージョン」をクリック
3. `EO_Infra_Docker/.env` の `N8N_EO_REQUEST_SECRET` の値を JSON 形式で入力:
   ```json
   {"CLOUDRUN_REQUEST_SECRET": "<STEP 0-2 で設定した N8N_EO_REQUEST_SECRET の値>"}
   ```
4. 「新しいバージョンを追加」
5. 古いバージョン（プレースホルダー）を「無効」→「破棄」

**gcloud CLI:**

Bash:
```bash
printf '{"CLOUDRUN_REQUEST_SECRET":"%s"}' "$N8N_EO_REQUEST_SECRET" | \
  gcloud secrets versions add eo-re-d01-secretmng --data-file=-
```

PowerShell:
```powershell
'{"CLOUDRUN_REQUEST_SECRET":"' + $env:N8N_EO_REQUEST_SECRET + '"}' | gcloud secrets versions add eo-re-d01-secretmng --data-file=-
```

### 3-2. OAuth2 Invoker SA の JSON キー発行

n8n が Cloud Run を呼び出すための認証キーを発行します。

> **重要**: JSON キーはセキュリティ上 Terraform 管理外としています（state ファイルに秘密鍵を保存しないため）。

1. GCP Console > IAM と管理 > サービス アカウント > `eo-gcp-sa-d01-oa2be-inv-ane1`
2. 「鍵」タブ > 「キーを追加」 > 「新しい鍵を作成」 > **JSON** > 「作成」
3. ダウンロードされた JSON ファイルを保管
   - ファイル名の後方を `-Oauth2_Invoker-jsonkey-yyyymmdd.json` のように変えておくとわかりやすい

## STEP 4: GitHub Secrets の設定

GitHub リポジトリ > Settings > Secrets and variables > Actions に以下を登録:

| シークレット名 | 値の取得方法 | 説明 |
|--------------|-------------|------|
| `EO_GCP_PROJECT_ID` | `terraform output gcp_project_id` | GCP プロジェクト ID |
| `EO_GCP_WIF_PROVIDER_PATH` | `terraform output wif_provider_path` | WIF IdP（ID プロバイダ）の完全パス |
| `EO_GCP_RUN_ANE1_DEPLOY_SA_EMAIL` | `terraform output deploy_sa_email` | Deployer SA のメールアドレス |
| `EO_GCP_RUN_ANE1_RUNTIME_SA_EMAIL` | `terraform output runtime_sa_email` | Runtime SA のメールアドレス |

**一括確認:**

```bash
terraform output -json
```

## STEP 5: GitHub Actions で Cloud Run をデプロイ

Terraform で作成した Cloud Run サービスにはプレースホルダーイメージのみです。GitHub Actions でアプリケーションコードをデプロイします。

### 5-1. GitHub Actions ワークフローの実行

1. GitHub リポジトリ > **Actions** タブ
2. 左サイドバー > **Deploy GCP Cloud Run ane1**
3. 「Run workflow」> ブランチ `main` を選択 > 「Run workflow」
4. ワークフローが完了するまで待機（約5〜10分）

### 5-2. デプロイ結果の確認

```bash
# Cloud Run サービスの状態確認
gcloud run services describe eo-re-d01-cloudrun-ane1 \
  --region asia-northeast1 \
  --format='value(status.url)'
```

または Terraform output:
```bash
terraform output cloud_run_service_url
```

## STEP 6: n8n Credentials / ノード設定

### 6-1. n8n Credential の作成

1. n8n > Personal > Credentials > Create Credential
2. Credential Type: `Google Service Account API`
3. 設定:
   - Name: `EO_RE_GCP_RUN_ane1_OAuth2_Invoker_SA`
   - STEP 3-2 でダウンロードした JSON キーの内容を転記
   - **Service Account Email**: JSON キー内の `client_email` を入力
   - **Private Key**: JSON キー内の `private_key` フィールドの改行文字（`\n`）を含めた**そのままの形式**で貼り付け
   - **Set up for use in HTTP Request node**: 有効化
   - **Scope(s)**: `https://www.googleapis.com/auth/iam`（IAM API へのアクセス用）
4. 「Save」

### 6-2. n8n ワークフローノードの設定

共通のノード設定手順は [N8N_NODE_SETUP.md](../../EO_n8nWorkflow_Json/N8N_NODE_SETUP.md) を参照してください。

GCP Cloud Run 固有の設定:

**ノード 235: OIDC ID Token 取得**

- URL: `https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/<OAuth2_Invoker_SA_EMAIL>:generateIdToken`
- Send Body (JSON):
  ```json
  {
    "audience": "<Cloud Run サービスのデフォルト HTTPS エンドポイント URL>",
    "includeEmail": true
  }
  ```

**【重要】audience URL と リクエスト先 URL の違い**

| ノード | URL に含めるもの | `/requestengine_tail` |
|--------|-----------------|----------------------|
| 235 (ID Token 取得) `audience` | サービス URL のみ | **含めない** |
| 280 (GCP Request) `URL` | サービス URL + パス | **含める** |

> `audience` に `/requestengine_tail` を含めて ID Token を発行すると、Cloud Run 側で宛先不一致とみなされ **401 Unauthorized** エラーが発生します。

詳細は [RUN_README.md](../ane1/RUN_README.md) の「OAuth2 Bearerトークン認証を使用する」セクションを参照してください。

## パラメータ一覧

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| **命名規則** |||
| `project_prefix` | `eo` | プロジェクトプレフィックス |
| `component` | `re` | コンポーネント識別子（Request Engine） |
| `environment` | `d01` | 環境識別子（d01, p01 等） |
| `region_short` | `ane1` | リージョン短縮名 |
| **GCP 設定** |||
| `gcp_project_id` | (入力必須) | GCP プロジェクト ID |
| `gcp_project_number` | (入力必須) | GCP プロジェクト番号 |
| `gcp_region` | `asia-northeast1` | デプロイ先リージョン |
| **GitHub Actions** |||
| `github_org` | (入力必須) | GitHub 組織名 / ユーザー名 |
| `github_repo` | (入力必須) | GitHub リポジトリ名 |
| **Cloud Run 設定** |||
| `cloud_run_memory` | `128Mi` | インスタンスメモリサイズ |
| `cloud_run_cpu` | `1` | インスタンス CPU |
| `cloud_run_max_instances` | `10` | 最大インスタンス数 |
| `cloud_run_min_instances` | `0` | 最小インスタンス数 |
| `cloud_run_timeout` | `300` | リクエストタイムアウト（秒） |
| `cloud_run_port` | `8080` | コンテナポート |
| **Secret Manager** |||
| `secret_name` | `eo-re-d01-secretmng` | シークレット名（コード内定数と一致必須） |
| `secret_key_name` | `CLOUDRUN_REQUEST_SECRET` | シークレットキー名 |

## トラブルシューティング

### terraform apply エラー: "API not enabled"

**原因**: API の有効化が反映されていない（数分かかる場合がある）

**解決**: もう一度 `terraform apply` を実行。API 有効化は冪等なので再実行で問題なし。

### terraform apply エラー: "already exists"

**原因**: 既に同名のリソースが手動で作成されている

**解決**:
1. 既存リソースを Terraform 管理下に取り込む:
   ```bash
   terraform import google_service_account.deployer projects/$EO_GCP_PROJECT_ID/serviceAccounts/<SA_EMAIL>
   ```
2. または既存リソースを削除してから再実行（SA の即時再作成は避ける。RUN_README.md 参照）

### terraform apply エラー: WIF Pool "Permission denied"

**原因**: 認証ユーザーに IAM 権限が不足

**解決**: 以下のロールが必要:
- プロジェクトのオーナー (`roles/owner`)
- または IAM 管理者 (`roles/iam.admin`) + Secret Manager 管理者 等

### Cloud Run サービスに接続できない（401 Unauthorized）

**原因**: OAuth2 Bearer トークンが正しくない

**解決**:
1. n8n Credentials の JSON キーが正しいか確認
2. OAuth2 Invoker SA に Cloud Run Invoker ロールが必要な場合がある:
   ```bash
   gcloud run services add-iam-policy-binding eo-re-d01-cloudrun-ane1 \
     --region=asia-northeast1 \
     --member="serviceAccount:eo-gcp-sa-d01-oa2be-inv-ane1@$EO_GCP_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.invoker"
   ```

### terraform destroy 後に再作成するとエラー

**原因**: SA や Secret の削除後、即時再作成で IAM 伝播遅延が発生

**解決**: 数分〜数時間待ってから再実行。特に SA は削除後30日間は同一IDで再作成不可（Google のポリシー）。

### state ファイルの管理

本テンプレートはローカル state を使用しています。チーム開発の場合は GCS バックエンドの使用を検討してください:

```hcl
terraform {
  backend "gcs" {
    bucket = "<YOUR_STATE_BUCKET>"
    prefix = "terraform/gcp-cloudrun-ane1"
  }
}
```

## 関連ドキュメント

- [RUN_README.md](../ane1/RUN_README.md) - GCP Cloud Run 手動セットアップ手順
- [RE_README.md](../../RE_README.md) - Request Engine 全体のセキュリティ設定
- [N8N_NODE_SETUP.md](../../EO_n8nWorkflow_Json/N8N_NODE_SETUP.md) - n8n ワークフローノード設定ガイド
- [AZFUNC_BICEP_README.md](../../azure_functions/bicep/AZFUNC_BICEP_README.md) - Azure Functions Bicep 構築手順
- [LAMBDA_CFN_README.md](../../aws_lambda/CFn/LAMBDA_CFN_README.md) - AWS Lambda CloudFormation 構築手順
