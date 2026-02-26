# Edge Optimizer 命名規約

> **最終更新**: 2026-02-24
> **更新根拠**: `RequestEngine/` 配下の IaC コード（CFn / Bicep / Terraform / Wrangler）の実装を正とし整合化

**命名の運用負荷低減**: `EO_GLOBAL_PRJ_ENV_ID` と `EO_RE_INSTANCE_ID` を各リソース・クラウドごとに手で組み合わせると運用負荷が高いため、**`MCNE_Documents/`**（MultiCloudNamingEngine）で命名ロジックを専用ライブラリに集約する方針。本ドキュメントは現行ルールの正本であり、将来は当該ライブラリが命名を生成し、IaC 等から参照する想定。概要は [MCNE_Documents/README.md](../../MCNE_Documents/README.md) を参照。

---

## 1. DBテーブル設計考慮観点

`RequestEngine/{EO_CLOUD}/{EO_SERVICE}/{EO_CODE_LANG}/instances_conf/*.env` はDBテーブル `eo_re_instances` の1レコードを模した設計。

- `EO_RE_INSTANCE_UUID`（UUIDv7）がサロゲート主キー
- 複合キーを避け、全フィールドは属性として保持
- テナント分離が必要になった段階で `tenant_id` フィールドを追加
- `EO_CLOUD` → `EO_RE_INSTANCE_TYPE` の依存方向（クラウド選定後にサービス種別が決まる）
- `EO_RE_INSTANCE_TYPE` は Lambda, EC2, GKE Pod Container 等、サーバレスに限らない

### 3NF 正規化設計

```sql
-- ルックアップテーブル: リージョン ↔ リージョン短縮コードの 1:1 マッピング
CREATE TABLE eo_regions (
  region       VARCHAR(32) PRIMARY KEY,
  region_short VARCHAR(8)  NOT NULL UNIQUE,
  cloud        VARCHAR(8)  NOT NULL
);

-- メインテーブル: RE 1個体 = 1レコード
-- .env ファイルは本テーブル + eo_regions を JOIN した非正規化ビュー
CREATE TABLE eo_re_instances (
  eo_re_instance_uuid  UUID        PRIMARY KEY,
  eo_global_prj_env_id VARCHAR(4)  NOT NULL,
  eo_project           VARCHAR(8)  NOT NULL DEFAULT 'eo',
  eo_component         VARCHAR(8)  NOT NULL DEFAULT 're',
  eo_env               VARCHAR(4)  NOT NULL,
  eo_cloud             VARCHAR(8)  NOT NULL,
  eo_code_lang         VARCHAR(4)  NOT NULL,
  eo_code_lang_ver     VARCHAR(8)  NOT NULL,
  eo_iac               VARCHAR(16) NOT NULL,
  eo_re_instance_type  VARCHAR(16) NOT NULL,
  eo_re_instance_id    VARCHAR(4)  NOT NULL,
  eo_region            VARCHAR(32) NOT NULL REFERENCES eo_regions(region),
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by           VARCHAR(64) NOT NULL,
  is_deleted           BOOLEAN     NOT NULL DEFAULT FALSE
);
```

`.env` ファイルに含まれる `EO_REGION_SHORT` は `eo_regions` テーブルから JOIN で導出する非正規化フィールド。

---

## 2. インスタンス定義スキーマ（instances_conf/*.env）

各 Request Engine インスタンスは `.env` 形式で定義する。
GitHub Actions ワークフローから `cat instances_conf/{file}.env >> $GITHUB_ENV` で環境変数として読み込む。

### 2.1 フィールド定義

**インスタンスレベル変数（instances_conf/*.env に記載）**

| フィールド | 説明 | 例 | 備考 |
|---|---|---|---|
| `EO_RE_INSTANCE_TYPE` | インスタンス種別 | `lambda` | lambda / funcapp / cloudrun / cfworker |
| `EO_RE_INSTANCE_ID` | インスタンス番号 | `001` | 同一種別内で一意 |
| `EO_REGION` | クラウドリージョン（フル） | `ap-northeast-1` | クラウド固有のリージョン名 |
| `EO_REGION_SHORT` | リージョン短縮コード | `apne1` | 全クラウド統一の短縮形（§4参照） |

**プロジェクトレベルシークレット（`.env` に書かない、シークレット管理で保管）**

| フィールド | 説明 | 例 | 備考 |
|---|---|---|---|
| `EO_ORIGINAL_SALT` | `EO_GLOBAL_PRJ_ENV_ID` 生成に使うソルト | `my-tenant-secret-salt` | **絶対に `.env` や Git に含めない。** GitHub Secrets / Secrets Manager 等で管理。紛失すると `EO_GLOBAL_PRJ_ENV_ID` を再生成不能になる。 |
| `EO_GLOBAL_PRJ_ENV_ID` | プロジェクト環境固定のユニーク識別子 | `a1b2` | `md5(EO_ORIGINAL_SALT + "{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}").substring(0, 4)` で生成。Azure KV / Storage Account 命名に使用（§3参照）。 |

> [!CAUTION]
> `EO_ORIGINAL_SALT` を紛失すると `EO_GLOBAL_PRJ_ENV_ID` を同じ値で再生成できなくなる。
> Azure Key Vault / Storage Account はこのIDを含む名前で既にデプロイ済みのため、
> IDが変わると**リソースの再作成（= データ消失）**が必要になる。
> 必ず GitHub Secrets または Secrets Manager に保存し、バックアップを取ること。

> [!NOTE]
> **現在の `.env` ファイルに含まれるフィールドはインスタンスレベルの4項目のみ。**
> DBテーブル設計上のフィールド（`EO_RE_INSTANCE_UUID`, `EO_PROJECT` 等）は
> ワークフローや IaC テンプレートのパラメータとして別途管理する。

### 2.2 ディレクトリパス → IaC の対応

| クラウド | ディレクトリ | IaC | .env ファイル名 |
|---|---|---|---|
| AWS | `RequestEngine/aws/lambda/py/` | CloudFormation (`CFn/`) | `lambda{NNN}.env` |
| Azure | `RequestEngine/azure/functions/py/` | Bicep (`bicep/`) | `funcapp{NNN}.env` |
| GCP | `RequestEngine/gcp/cloudrun/py/` | Terraform (`terraform/`) | `cloudrun{NNN}.env` |
| CF | `RequestEngine/cf/workers/ts/` | Wrangler (`funcfiles/wrangler.toml`) | `cfworker{NNN}.env` |

### 2.3 クラウド4種の実際の .env 定義

**AWS Lambda** (`RequestEngine/aws/lambda/py/instances_conf/lambda001.env`)
```env
# Referenced by (この定義値を使用するファイル):
#   .github/workflows/deploy-py-to-aws-lambda.yml (LAMBDA_FUNCTION_NAME, aws-region)
#   RequestEngine/aws/lambda/py/CFn/eo-aws-cfnstack.yml (パラメータ化済み)
EO_RE_INSTANCE_TYPE=lambda
EO_RE_INSTANCE_ID=001
EO_REGION=ap-northeast-1
EO_REGION_SHORT=apne1
```

**Azure Functions** (`RequestEngine/azure/functions/py/instances_conf/funcapp001.env`)
```env
# Referenced by (この定義値を使用するファイル):
#   .github/workflows/deploy-py-to-az-function.yml (FUNCTION_APP_NAME, RESOURCE_GROUP)
#   RequestEngine/azure/functions/py/bicep/eo-re-d1-azure-funcapp.bicep (パラメータ化済み)
EO_RE_INSTANCE_TYPE=funcapp
EO_RE_INSTANCE_ID=001
EO_REGION=japaneast
EO_REGION_SHORT=jpe
```

**GCP Cloud Run** (`RequestEngine/gcp/cloudrun/py/instances_conf/cloudrun001.env`)
```env
# Referenced by (この定義値を使用するファイル):
#   .github/workflows/deploy-py-to-gcp-cloudrun.yml (EO_GCP_CLOUD_RUN_SERVICE_NAME, EO_GCP_REGION)
#   RequestEngine/gcp/cloudrun/py/terraform/cloud_run.tf (サービス名構築に使用)
#   RequestEngine/gcp/cloudrun/py/terraform/main.tf (name_prefix + EO_REGION_SHORT)
EO_RE_INSTANCE_TYPE=cloudrun
EO_RE_INSTANCE_ID=001
EO_REGION=asia-northeast1
EO_REGION_SHORT=asne1
```

**Cloudflare Workers** (`RequestEngine/cf/workers/ts/instances_conf/cfworker001.env`)
```env
# Referenced by (この定義値を使用するファイル):
#   .github/workflows/deploy-ts-to-cf-worker.yml (wrangler.toml name)
EO_RE_INSTANCE_TYPE=cfworker
EO_RE_INSTANCE_ID=001
EO_REGION=global
EO_REGION_SHORT=global
```

### 2.4 EO_GLOBAL_PRJ_ENV_ID と EO_RE_INSTANCE_ID のリソース名付与基準

`EO_RE_INSTANCE_ID` は `RequestEngine/aws/lambda/py/instances_conf/*.env` や `RequestEngine/azure/functions/py/instances_conf/*.env` など、各クラウドの `RequestEngine/*/*/*/instances_conf/*.env` に存在する。基本的にクラウドとリージョンの中でRequestEngine自体に付与するインスタンスIDであり、リソース名の最後尾に付与することで、リソースのグローバルなユニーク識別子とする。


変数表現例）AzureのFunction App`{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-{EO_SERVERLESS_SERVICE}-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` となり、`EO_RE_INSTANCE_ID`

実名例）AzureのFunction App`eo-re-d1-funcapp-jpe-001`

- **付与する**: コンピュート／関数リソース（Lambda 関数名、Function App、Cloud Run サービス、Worker 名など）— クラウドを問わずリクエストエンジンすべて
- **付与しない**: シークレットサービス（Key Vault、Secrets Manager 等）とストレージ（Storage Account、S3 等）— クラウドを問わず


## 3. EO_GLOBAL_PRJ_ENV_ID

プロジェクト環境ごとに固定する任意のユニーク識別子。
グローバル一意が必須なリソース名（Azure Key Vault, Azure Storage Account）に埋め込んで衝突を防止する。

**順序の原則**: リクエストエンジンは **`EO_GLOBAL_PRJ_ENV_ID` を `EO_RE_INSTANCE_ID` の直前に付与する**（`…-{EO_GLOBAL_PRJ_ENV_ID}-{EO_RE_INSTANCE_ID}` または `…{EO_GLOBAL_PRJ_ENV_ID}{EO_RE_INSTANCE_ID}`）。

### 3.1 文字数制約の逆算

**Azure Key Vault（24文字制限）**

| パターン | `{EO_PROJECT}-{EO_SECRET_SERVICE}-{EO_ENV}-{EO_REGION_SHORT}-{EO_GLOBAL_PRJ_ENV_ID}-{EO_RE_INSTANCE_ID}` |
|---|---|
| Bicep変数名 | `KEY_VAULT_NAME` |
| 具体例 | `eo-kv-d1-jpe-a1b2-001` (21文字) |
| 内訳 | `eo`(2) + `-kv`(3) + `-d1`(3) + `-jpe`(4) + `-a1b2`(5) + `-001`(4) = 21文字 |
| 文字種 | 小文字英数字 + ハイフン |

> **`EO_SECRET_SERVICE` = `kv`（Bicep パラメータ、デフォルト値）**

**Azure Storage Account（24文字制限、ハイフン不可）**

| パターン | `{EO_PROJECT}{EO_COMPONENT}{EO_STORAGE_SERVICE}{EO_ENV}{EO_REGION_SHORT}{EO_GLOBAL_PRJ_ENV_ID}{EO_RE_INSTANCE_ID}` |
|---|---|
| Bicep変数名 | `STORAGE_ACCOUNT_NAME` |
| 具体例 | `eorestd1jpea1b2001` (18文字) |
| 内訳 | `eo`(2) + `re`(2) + `st`(2) + `d1`(2) + `jpe`(3) + `a1b2`(4) + `001`(3) = 18文字 |
| 文字種 | 小文字英数字のみ（ハイフン不可） |

> **`EO_STORAGE_SERVICE` = `st`（Bicep パラメータ、デフォルト値）**

**運用規約: `EO_GLOBAL_PRJ_ENV_ID` 最大4文字、小文字英数字のみ（ハイフン不可）**

Storage Account のハイフン不可制約に合わせ、かつ Key Vault の6文字上限に対しバッファ2文字を確保。

生成方法例: `md5("my-salt" + "{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}").substring(0, 4)`
例: `a1b2`, `x9k3`

### 3.2 対象リソース

| 対象 | 配置スコープ | DNS名前空間 | `EO_GLOBAL_PRJ_ENV_ID` 必要性 |
|---|---|---|---|
| **Azure Key Vault** | リージョン配置 | **グローバル一意** (`{name}.vault.azure.net`) | ✅ 必須 |
| **Azure Storage Account** | リージョン配置 | **グローバル一意** (`{name}.blob.core.windows.net`) | ✅ 必須 |

> [!NOTE]
> **リージョン配置 ≠ リージョン内一意**
>
> Azure Key Vault・Storage Account はリソース自体は指定リージョンに物理配置されるが、
> **DNS 名前空間は Azure 全リージョン・全テナントを跨いだグローバル空間**になっている。
> つまり `eo-kv-d1-jpe-001` というシンプルな名前は自分以外の誰かが既に使用していると作成できない。
>
> `EO_GLOBAL_PRJ_ENV_ID` を **`EO_RE_INSTANCE_ID` の直前に**付加することで、他テナントとの衝突を回避し、リクエストエンジン全体で順序を統一する。

**比較: リージョン内一意で足りるリソース（`EO_GLOBAL_PRJ_ENV_ID` 不使用）**

| クラウド | リソース | 一意スコープ |
|---|---|---|
| AWS | Lambda 関数 | アカウント + リージョン内 |
| AWS | IAM Role / Policy | アカウント内（グローバルだが非 DNS） |
| AWS | Secrets Manager | アカウント + リージョン内 |
| GCP | Cloud Run Service | プロジェクト + リージョン内 |
| GCP | Service Account | プロジェクト内 |
| GCP | Secret Manager | プロジェクト内 |
| Azure | Function App | サブスクリプション内（※ デフォルトホスト名は `.azurewebsites.net` でグローバル一意だが Bicep で明示的に管理） |
| Cloudflare | Worker | アカウント内 |

AWS, GCP, Cloudflare のリソースはプロジェクト/リージョン内で一意であれば十分なため不使用。

---

## 4. リージョン短縮コード

全クラウド統一の短縮形。文字制限の厳しいリソース名でも使用可能な長さに統一。

### AWS

| フルリージョン | EO_REGION_SHORT | 拠点 |
|---|---|---|
| ap-northeast-1 | `apne1` | Tokyo |
| ap-northeast-2 | `apne2` | Seoul |
| ap-northeast-3 | `apne3` | Osaka |
| ap-southeast-1 | `apse1` | Singapore |
| us-east-1 | `use1` | N. Virginia |
| us-west-2 | `usw2` | Oregon |
| eu-west-1 | `euw1` | Ireland |

> **CFn `AllowedValues`**: `apne1, apne2, apne3, apse1, use1, usw2, euw1`

### Azure

| フルリージョン | EO_REGION_SHORT | 拠点 |
|---|---|---|
| japaneast | `jpe` | Tokyo |
| japanwest | `jpw` | Osaka |
| eastus | `eus` | Virginia |
| westus | `wus` | California |
| westeurope | `weu` | Netherlands |

> **Bicep `@allowed`**: `jpe, jpw, eus, wus, weu`

### GCP

| フルリージョン | EO_REGION_SHORT | 拠点 |
|---|---|---|
| asia-northeast1 | `asne1` | Tokyo |
| asia-northeast2 | `asne2` | Osaka |
| asia-northeast3 | `asne3` | Seoul |
| asia-southeast1 | `asse1` | Singapore |
| us-east1 | `use1` | S. Carolina |
| us-west1 | `usw1` | Oregon |
| europe-west1 | `euw1` | Belgium |

> **Terraform `validation`**: `asne1, asne2, asne3, asse1, use1, usw2, euw1`

### Cloudflare Workers

| フルリージョン | EO_REGION_SHORT | 拠点 |
|---|---|---|
| global | `global` | Global Edge |

---

## 5. リソース命名パターン（IaCコード実装準拠）

### 5.1 共通 Locals パターン（GCP Terraform）

```hcl
# main.tf
locals {
  name_prefix  = "${var.project_prefix}-${var.component}-${var.environment}"
  # 例: eo-re-d1
  region_short = var.region_short
}
```

基本パターン: `{name_prefix}-{resource}-{region_short}`

---

### 5.2 AWS リソース（CloudFormation）

IaC: `RequestEngine/aws/lambda/py/CFn/eo-aws-cfnstack.yml`

| リソース | パターン | 例 | 文字制限 |
|---|---|---|---|
| **Lambda 関数** | `{ProjectPrefix}-{Component}-{Environment}-lambda-{RegionShort}` | `eo-re-d1-lambda-apne1` | 64文字 |
| **Lambda Log Group** | `/aws/lambda/{ProjectPrefix}-{Component}-{Environment}-lambda-{RegionShort}` | `/aws/lambda/eo-re-d1-lambda-apne1` | — |
| **Lambda Layer** | `{ProjectPrefix}-{Component}-{Environment}-lambda-python-slim-layer` | `eo-re-d1-lambda-python-slim-layer` | 自動採番あり |
| **Secrets Manager** | `{ProjectPrefix}-{Component}-{Environment}-secretsmng-{RegionShort}` | `eo-re-d1-secretsmng-apne1` | 512文字 |
| **IAM Role (Lambda実行)** | `{ProjectPrefix}-{Component}-{Environment}-lambda-{RegionShort}-role` | `eo-re-d1-lambda-apne1-role` | 64文字 |
| **IAM Policy (基本実行)** | `{ProjectPrefix}-{Component}-{Environment}-lambda-{RegionShort}-basic-exec-iamp` | `eo-re-d1-lambda-apne1-basic-exec-iamp` | 128文字 |
| **IAM Policy (SM アクセス)** | `{ProjectPrefix}-{Component}-{Environment}-lambda-{RegionShort}-role-iamp` | `eo-re-d1-lambda-apne1-role-iamp` | 128文字 |
| **IAM User (n8n呼び出し)** | `{ProjectPrefix}-{Component}-{Environment}-lambda-{RegionShort}-iamu` | `eo-re-d1-lambda-apne1-iamu` | 64文字 |
| **IAM Policy (n8n invoke)** | `{ProjectPrefix}-{Component}-{Environment}-lambda-{RegionShort}-access-key-iamp` | `eo-re-d1-lambda-apne1-access-key-iamp` | 128文字 |
| **IAM Role (GH Actions)** | `{ProjectPrefix}-{Component}-{Environment}-lambda-{RegionShort}-ghactions-deploy-iamr` | `eo-re-d1-lambda-apne1-ghactions-deploy-iamr` | 64文字 |
| **IAM Policy (GH Actions)** | `{ProjectPrefix}-{Component}-{Environment}-lambda-{RegionShort}-ghactions-deploy-iamr-iamp` | `eo-re-d1-lambda-apne1-ghactions-deploy-iamr-iamp` | 128文字 |
| **OIDC Provider Tag** | `{ProjectPrefix}-ghactions-idp-request-engine-lambda-aws-{RegionShort}` | `eo-ghactions-idp-request-engine-lambda-aws-apne1` | — |
| **CFn スタック** | `eo-aws-cfnstack` | `eo-aws-cfnstack` | — |

> [!NOTE]
> Lambda などの各クラウドのサーバレス関数名には `EO_RE_INSTANCE_ID`（`001` 等）を最後尾に含む。
> 1リージョン = 1インスタンス前提ではない。1リージョン=複数インスタンスの場合もありうる。）。

---

### 5.3 Azure リソース（Bicep）

IaC: `RequestEngine/azure/functions/py/bicep/eo-re-d1-azure-funcapp.bicep`

**§2.4 に従い** Function App / Key Vault / Storage Account の名前は一意スコープがグローバルのため、いずれも `EO_GLOBAL_PRJ_ENV_ID-EO_RE_INSTANCE_ID` を含める。

| リソース | パターン（Bicep変数） | 例 | 文字制限 |
|---|---|---|---|
| **Function App** | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-funcapp-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | `eo-re-d1-funcapp-jpe-001` | 60文字 |
| **App Service Plan** | `ASP-{EO_PROJECT}{EO_COMPONENT}{EO_ENV}resourcegrp{EO_REGION_SHORT}` | `ASP-eored1reourcegrpjpe` | — |
| **Key Vault** | `{EO_PROJECT}-{EO_SECRET_SERVICE}-{EO_ENV}-{EO_REGION_SHORT}-{EO_GLOBAL_PRJ_ENV_ID}-{EO_RE_INSTANCE_ID}` | `eo-kv-d1-jpe-a1b2-001` | **24文字** |
| **Storage Account** | `{EO_PROJECT}{EO_COMPONENT}{EO_STORAGE_SERVICE}{EO_ENV}{EO_REGION_SHORT}{EO_GLOBAL_PRJ_ENV_ID}{EO_RE_INSTANCE_ID}` | `eorestd1jpea1b2001` | **24文字** |
| **Key Vault Secret** | `AZFUNC-REQUEST-SECRET` | `AZFUNC-REQUEST-SECRET` | 127文字 |
| **Entra ID App (GH Actions)** | `eo-ghactions-deploy-entra-app-azfunc-{EO_REGION_SHORT}` | `eo-ghactions-deploy-entra-app-azfunc-jpe` | — |
| **Resource Group** | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-resourcegrp-{EO_REGION_SHORT}` | `eo-re-d1-resourcegrp-jpe` | 90文字 |

> [!NOTE]
> Key Vault と Storage Account はグローバル一意が必須のため `EO_GLOBAL_PRJ_ENV_ID` を **`EO_RE_INSTANCE_ID` の直前に**付与（§3 の順序の原則）。
> Storage Account はハイフン不可のため全結合。
> App Service Plan 名は Bicep `variables` 内で自動生成（`ASP-` プレフィックス固定）。

---

### 5.4 GCP リソース（Terraform）

IaC: `RequestEngine/gcp/cloudrun/py/terraform/`

| リソース | パターン（Terraform） | 例 | 文字制限 |
|---|---|---|---|
| **Cloud Run Service** | `{name_prefix}-cloudrun-{region_short}` | `eo-re-d1-cloudrun-asne1` | 63文字 |
| **Artifact Registry** | `{name_prefix}-ar-{region_short}` ※ | `eo-re-d1-ar-asne1` | 63文字 |
| **Secret Manager** | `{name_prefix}-secretmng` | `eo-re-d1-secretmng` | 255文字 |
| **Secret キー名** | `CLOUDRUN_REQUEST_SECRET` | `CLOUDRUN_REQUEST_SECRET` | — |
| **SA (Deployer)** | `{project_prefix}-gsa-{environment}-deploy-{region_short}` | `eo-gsa-d1-deploy-asne1` | **30文字** |
| **SA (Runtime)** | `{project_prefix}-gsa-{environment}-runtime-{region_short}` | `eo-gsa-d1-runtime-asne1` | **30文字** |
| **SA (OAuth2 Invoker)** | `{project_prefix}-gsa-{environment}-oa2inv-{region_short}` | `eo-gsa-d1-oa2inv-asne1` | **30文字** |
| **WIF Pool** | `{project_prefix}-gcp-pool-wif-{environment}` | `eo-gcp-pool-wif-d1` | 32文字 |
| **WIF IdP** | `{project_prefix}-gcp-idp-gh-oidc-wif-{environment}` | `eo-gcp-idp-gh-oidc-wif-d1` | 32文字 |

> [!IMPORTANT]
> **GCP Service Account の命名（§2.4 に準拠）**
> - パターン: `eo-gsa-{env}-{role}-{region_short}`（例: `eo-gsa-d1-runtime-asne1`）
> - 一意スコープがプロジェクト内のため、リソース名に `EO_RE_INSTANCE_ID` は含めない。
>
> [!NOTE]
> **§2.4 に従い** Cloud Run サービス名・SA 名には `EO_RE_INSTANCE_ID` を含めない。
> 一意スコープがプロジェクト＋リージョン（またはプロジェクト内）であり、「1リージョン1インスタンス」を前提とする。

**SA の文字数確認（30文字制限）:**

| SA | 例 | 文字数 | 余裕 |
|---|---|---|---|
| Deployer | `eo-gsa-d1-deploy-asne1` | 22文字 | 8文字 ✅ |
| Runtime | `eo-gsa-d1-runtime-asne1` | 23文字 | 7文字 ✅ |
| OAuth2 Invoker | `eo-gsa-d1-oa2inv-asne1` | 22文字 | 8文字 ✅ |

> [!NOTE]
> GCP SA は `labels` 非対応。命名メタデータは `display_name`（100文字）+ `description`（256文字）で保持。
>
> ```hcl
> resource "google_service_account" "runtime" {
>   account_id   = "eo-gsa-d1-runtime-asne1"
>   display_name = "EO GCP Cloud Run Runtime SA (asne1)"
>   description  = "Cloud Run runtime identity with Secret Manager access"
> }
> ```

---

### 5.5 Cloudflare Workers（Wrangler）

IaC: `RequestEngine/cf/workers/ts/funcfiles/wrangler.toml`（または `wrangler.jsonc`）

**§2.4 に従い** Worker 名は一意スコープがアカウント内で名前で識別するため、`EO_RE_INSTANCE_ID` を含める。

| リソース | パターン | 例 |
|---|---|---|
| **Worker 名** | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-cfworker-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | `eo-re-d1-cfworker-global-001` |

> Cloudflare にはタグ機能がないため、命名メタデータは `wrangler.toml` 内コメントで管理。

---

## 6. タグ / ラベルスキーマ

### 6.1 共通タグ定義

全クラウドのリソースに統一の `eo_` プレフィックス（またはキャメルケース）タグを付与する。

**AWS Tags（CFn）:**

```yaml
Tags:
  - Key: Name
    Value: !Sub "..."
  - Key: Project
    Value: !Ref ProjectPrefix     # eo
  - Key: Environment
    Value: !Ref Environment       # d1
```

**Azure Tags（Bicep）:**

```bicep
var COMMON_TAGS = {
  Project:     EO_PROJECT      // eo
  Component:   EO_COMPONENT    // re
  Environment: EO_ENV          // d1
  ManagedBy:   'Bicep'
}
```

**GCP Labels（Terraform）:**

```hcl
locals {
  eo_gcp_resource_labels = {
    project     = var.project_prefix   # eo
    component   = var.component        # re
    environment = var.environment      # d1
    managed-by  = "terraform"
  }
}
```

### 6.2 クラウド別タグ/ラベル対応

| クラウド | タグ/ラベル機能 | 対応方法 |
|---|---|---|
| **AWS** | Tags（全リソース対応） | `Name`, `Project`, `Environment` を付与 |
| **Azure** | Tags（全リソース対応） | `COMMON_TAGS` 変数でまとめて付与 |
| **GCP** | Labels（リソース依存） | `eo_gcp_resource_labels` でまとめて付与 |
| **GCP SA** | Labels **非対応** | `display_name` + `description` で代替 |
| **Cloudflare** | タグ機能なし | `wrangler.toml` 内コメントで記録 |

---

## 7. 文字数制約サマリー

| リソース | 制限 | 現在の例 | 文字数 | 余裕 |
|---|---|---|---|---|
| **Azure Key Vault** | **24文字** | `eo-kv-d1-jpe-a1b2-001` | 21文字 | 3文字 |
| **Azure Storage Account** | **24文字** | `eorestd1jpea1b2001` | 18文字 | 6文字 |
| **GCP SA (Deployer)** | **30文字** | `eo-gsa-d1-deploy-asne1` | 22文字 | 8文字 |
| **GCP SA (Runtime)** | **30文字** | `eo-gsa-d1-runtime-asne1` | 23文字 | 7文字 |
| **GCP SA (OAuth2 Invoker)** | **30文字** | `eo-gsa-d1-oa2inv-asne1` | 22文字 | 8文字 |
| **GCP WIF Pool/IdP** | 32文字 | `eo-gcp-idp-gh-oidc-wif-d1` | 27文字 | 5文字 |
| **AWS IAM Role** | 64文字 | `eo-re-d1-lambda-apne1-ghactions-deploy-iamr` | 43文字 | 21文字 |
| **AWS IAM Policy** | 128文字 | `eo-re-d1-lambda-apne1-ghactions-deploy-iamr-iamp` | 48文字 | 80文字 |
| **Azure Function App** | 60文字 | `eo-re-d1-funcapp-jpe-001` | 24文字 | 36文字 |
| **Cloud Run Service** | 63文字 | `eo-re-d1-cloudrun-asne1` | 23文字 | 40文字 |

> [!NOTE]
> **GCP SA** は `gcp-sa`→`gsa`、`oa2be-inv`→`oa2inv` の短縮により、いずれも 30文字以内に収まっている。`EO_ENV` を 4文字以上にする場合は文字数再確認すること。

---

## 8. GCP プロジェクト命名

`variables.tf` で `gcp_project_id` の validation パターンが定義されている。

```hcl
validation {
  condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.gcp_project_id))
  error_message = "gcp_project_id must be 6-30 characters, lowercase, numbers, and hyphens."
}
```

**推奨命名パターン:**

| パターン | 例 | 文字数 |
|---|---|---|
| `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-pr-{EO_REGION_SHORT}` | `eo-re-d1-pr-asne1` | 18文字 ✅ |

`-pr-` は "project" の略。