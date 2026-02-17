# Edge Optimizer 命名規約

## 1. DBテーブル設計考慮観点

`RequestEngine/{EO_CLOUD}/{EO_CODE_LANG}/instances/*.env` は DBテーブル`eo_re_instances`の1レコードを模した設計。

- `EO_RE_INSTANCE_UUID`（UUIDv7）がサロゲート主キー
- 複合キーを避け、全フィールドは属性として保持
- テナント分離が必要になった段階で `tenant_id` フィールドを追加
- `EO_CLOUD` → `EO_RE_INSTANCE_TYPE` の依存方向（クラウド選定後にサービス種別が決まる）
- `EO_RE_INSTANCE_TYPE` は Lambda, EC2, GKE Pod Container 等、サーバレスに限らない

### 3NF 正規化設計

```sql
-- ルックアップテーブル: リージョン ↔ リージョン短縮コードの1:1マッピング
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

## 2. インスタンス定義スキーマ（instances/*.env）

各 Request Engine インスタンスは `.env` 形式で定義する。
GitHub Actions ワークフローから `cat instances/{file}.env >> $GITHUB_ENV` で環境変数として読み込む。

### フィールド定義

リクエストエンジン1個体に対し、以下のフィールドを定義する。

| フィールド | 説明 | 例 | 備考 |
|---|---|---|---|
| `EO_RE_INSTANCE_UUID` | インスタンス主キー（UUIDv7） | `019503a1-...` | タイムスタンプ+ランダム、時系列ソート可能 |
| `EO_GLOBAL_PRJ_ENV_ID` | プロジェクト環境固定のユニーク識別子 | `a1b2` | グローバル一意必須リソースの命名に使用(半角英数最大4桁。ハイフンやアンダースコア不可。`md5("my-tenant-secret-salt" + "{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}")`) |
| `EO_PROJECT` | プロジェクト識別子 | `eo` | 全環境共通 |
| `EO_COMPONENT` | コンポーネント識別子 | `re` | re = Request Engine |
| `EO_ENV` | 環境識別子 | `d01` | d01=dev01, p01=prod01 |
| `EO_CLOUD` | クラウド識別子 | `aws` | aws / azure / gcp / cf |
| `EO_CODE_LANG` | プログラミング言語識別子 | `py` | py = Python, ts = TypeScript |
| `EO_CODE_LANG_VER` | プログラミング言語バージョン | `314` | Python 3.14, TypeScript 5.0 |
| `EO_IAC` | IaC ツール識別子 | `cfn` | cfn / bicep / terraform / wrangler / pulmi / none |
| `EO_RE_INSTANCE_TYPE` | インスタンス種別 | `lambda` | lambda / funcapp / cloudrun / cfworker |
| `EO_RE_INSTANCE_ID` | インスタンス番号 | `001` | 同一種別内で一意 |
| `EO_REGION` | クラウドリージョン（フル） | `ap-northeast-1` | クラウド固有のリージョン名 |
| `EO_REGION_SHORT` | リージョン短縮コード | `apn1` | 全クラウド統一の短縮形(本来は別テーブル) |
| `created_at` | レコード作成日時 | `2026-02-16T16:00:00+09:00` | ISO 8601、タイムゾーン付き |
| `updated_at` | レコード最終更新日時 | `2026-02-16T16:00:00+09:00` | ISO 8601、タイムゾーン付き |
| `created_by` | 作成者/システムID | `nishilab` | 人間のユーザーID or システム名 |
| `is_deleted` | 論理削除フラグ | `false` | true/false（物理削除しない運用） |

### クラウド4種の定義例

**AWS Lambda** (`RequestEngine/aws/lambda/py/instances/lambda001.env`)
```env
EO_RE_INSTANCE_UUID=<UUIDv7>
EO_GLOBAL_PRJ_ENV_ID=<任意ユニーク値>
EO_PROJECT=eo
EO_COMPONENT=re
EO_ENV=d01
EO_CLOUD=aws
EO_CODE_LANG=py
EO_CODE_LANG_VER=3.14
EO_IAC=cfn
EO_RE_INSTANCE_TYPE=lambda
EO_RE_INSTANCE_ID=001
EO_REGION=ap-northeast-1
EO_REGION_SHORT=apn1
```

**Azure Functions** (`RequestEngine/azure/functions/py/instances/funcapp001.env`)
```env
EO_RE_INSTANCE_UUID=<UUIDv7>
EO_GLOBAL_PRJ_ENV_ID=<任意ユニーク値>
EO_PROJECT=eo
EO_COMPONENT=re
EO_ENV=d01
EO_CLOUD=azure
EO_CODE_LANG=py
EO_CODE_LANG_VER=3.13
EO_IAC=bicep
EO_RE_INSTANCE_TYPE=funcapp
EO_RE_INSTANCE_ID=001
EO_REGION=japaneast
EO_REGION_SHORT=jpe
```

**GCP Cloud Run** (`RequestEngine/gcp/cloudrun/py/instances/cloudrun001.env`)
```env
EO_RE_INSTANCE_UUID=<UUIDv7>
EO_GLOBAL_PRJ_ENV_ID=<任意ユニーク値>
EO_PROJECT=eo
EO_COMPONENT=re
EO_ENV=d01
EO_CLOUD=gcp
EO_CODE_LANG=py
EO_CODE_LANG_VER=3.13
EO_IAC=terraform
EO_RE_INSTANCE_TYPE=cloudrun
EO_RE_INSTANCE_ID=001
EO_REGION=asia-northeast1
EO_REGION_SHORT=an1
```

**Cloudflare Workers** (`RequestEngine/cf/workers/ts/instances/cfworker001.env`)
```env
EO_RE_INSTANCE_UUID=<UUIDv7>
EO_GLOBAL_PRJ_ENV_ID=<任意ユニーク値>
EO_PROJECT=eo
EO_COMPONENT=re
EO_ENV=d01
EO_CLOUD=cf
EO_CODE_LANG=ts
EO_CODE_LANG_VER=5.0
EO_IAC=none
EO_RE_INSTANCE_TYPE=cfworker
EO_RE_INSTANCE_ID=001
EO_REGION=global
EO_REGION_SHORT=global
```

## 3. EO_GLOBAL_PRJ_ENV_ID

プロジェクト環境ごとに固定する任意のユニーク識別子。
グローバル一意が必須なリソース名（Azure Key Vault, Azure Storage Account）に埋め込んで衝突を防止する。

### 文字数制約の逆算

**Azure Key Vault（24文字制限）**

| パターン | `{EO_PROJECT}-kv-{EO_ENV}-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}-{EO_GLOBAL_PRJ_ENV_ID}` |
|---|---|
| 具体例 | `eo-kv-d01-jpe-001-a1b2` (22文字) |
| 内訳 | `eo`(2) + `-`(1) + `kv`(2) + `-`(1) + `d01`(3) + `-`(1) + `jpe`(3) + `-`(1) + `001`(3) + `-`(1) + `a1b2`(4) = 22文字 |
| 文字種 | 小文字英数字 + ハイフン |

**Azure Storage Account（24文字制限、ハイフン不可）**

| パターン | `{EO_PROJECT}rest{EO_ENV}{EO_REGION_SHORT}{EO_RE_INSTANCE_ID}{EO_GLOBAL_PRJ_ENV_ID}` |
|---|---|
| 具体例 | `eorestd01jpe001a1b2` (19文字) |
| 内訳 | `eo`(2) + `rest`(4) + `d01`(3) + `jpe`(3) + `001`(3) + `a1b2`(4) = 19文字 |
| 文字種 | 小文字英数字のみ（ハイフン不可） |

**運用規約: `EO_GLOBAL_PRJ_ENV_ID` 最大4文字、小文字英数字のみ（ハイフン不可）**

Storage Account のハイフン不可制約に合わせ、かつ Key Vault の6文字上限に対しバッファ2文字を確保。

例: `a1b2`, `x9k3`

### 対象リソース

| 対象 | 理由 |
|---|---|
| Azure Key Vault | グローバル一意の DNS 名 |
| Azure Storage Account | グローバル一意の DNS 名 |

AWS, GCP, Cloudflare のリソースはプロジェクト/リージョン内で一意であれば十分なため不使用。

## 4. リージョン短縮コード

全クラウド統一の短縮形。文字制限の厳しいリソース名でも使用可能な長さに統一。

| クラウド | フルリージョン | EO_REGION_SHORT |
|---|---|---|
| AWS | ap-northeast-1 | `apn1` |
| AWS | ap-northeast-3 | `apn3` |
| AWS | us-east-1 | `use1` |
| AWS | us-west-2 | `usw2` |
| Azure | japaneast | `jpe` |
| Azure | eastus | `eus` |
| Azure | westeurope | `weu` |
| GCP | asia-northeast1 | `an1` |
| GCP | asia-northeast2 | `an2` |
| GCP | asia-northeast3 | `an3` |
| GCP | asia-southeast1 | `ase1` |
| GCP | us-east1 | `use1` |
| GCP | us-west1 | `usw1` |
| GCP | europe-west1 | `euw1` |
| Cloudflare | global | `global` |

## 5. リソース命名パターン

### 5.1 基本パターン（文字制限に余裕のあるリソース）

```
{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-{EO_RE_INSTANCE_TYPE}-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}
```
展開例: `eo-re-d01-lambda-apn1-001`

### 5.2 AWS リソース

| リソース | パターン | 例 | 制限 |
|---|---|---|---|
| Lambda 関数 | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-lambda-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | `eo-re-d01-lambda-apn1-001` | 64文字 |
| Lambda Log Group | `/aws/lambda/{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-lambda-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | `/aws/lambda/eo-re-d01-lambda-apn1-001` | |
| Secrets Manager | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-secretsmng-{EO_REGION_SHORT}` | `eo-re-d01-secretsmng-apn1` | 512文字 |
| IAM Role | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-lambda-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}-role` | `eo-re-d01-lambda-apn1-001-role` | 64文字 |
| IAM Policy | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-lambda-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}-{purpose}-iamp` | `eo-re-d01-lambda-apn1-001-basic-exec-iamp` | 128文字 |
| IAM User | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-lambda-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}-iamu` | `eo-re-d01-lambda-apn1-001-iamu` | 64文字 |
| GH Actions Role | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-lambda-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}-ghactions-deploy-iamr` | `eo-re-d01-lambda-apn1-001-ghactions-deploy-iamr` | 64文字 |
| OIDC Provider Tag | `{EO_PROJECT}-ghactions-idp-request-engine-lambda-aws-{EO_REGION_SHORT}` | `eo-ghactions-idp-request-engine-lambda-aws-apn1` | |

### 5.3 Azure リソース

| リソース | パターン | 例 | 制限 |
|---|---|---|---|
| Function App | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-funcapp-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | `eo-re-d01-funcapp-jpe-001` | 60文字 |
| Resource Group | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-resourcegroup-{EO_REGION_SHORT}` | `eo-re-d01-resourcegroup-jpe` | 90文字 |
| **Key Vault** | `{EO_PROJECT}-kv-{EO_ENV}-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}-{EO_GLOBAL_PRJ_ENV_ID}` | `eo-kv-d01-jpe-001-a1b2` | **24文字** |
| **Storage Account** | `{EO_PROJECT}rest{EO_ENV}{EO_REGION_SHORT}{EO_RE_INSTANCE_ID}{EO_GLOBAL_PRJ_ENV_ID}` | `eorestd01jpe001a1b2` | **24文字** |
| Key Vault Secret | `AZFUNC-REQUEST-SECRET` | `AZFUNC-REQUEST-SECRET` | 127文字 |

> Key Vault と Storage Account はグローバル一意が必須のため `EO_GLOBAL_PRJ_ENV_ID` を末尾に付与。
> Storage Account はハイフン不可のため全結合。
> Key Vault は `EO_COMPONENT` をタグに退避し、名前から省略。

### 5.4 GCP リソース

| リソース | パターン | 例 | 制限 |
|---|---|---|---|
| Cloud Run Service | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-cloudrun-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | `eo-re-d01-cloudrun-an1-001` | 63文字 |
| **Service Account** | `{EO_PROJECT}-gsa-{EO_ENV}-{role}-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | 下記参照 | **30文字** |
| SA (Deployer) | `{EO_PROJECT}-gsa-{EO_ENV}-deploy-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | `eo-gsa-d01-deploy-an1-001` (26文字) | 30文字 |
| SA (Runtime) | `{EO_PROJECT}-gsa-{EO_ENV}-runtime-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | `eo-gsa-d01-runtime-an1-001` (27文字) | 30文字 |
| SA (OAuth2 Invoker) | `{EO_PROJECT}-gsa-{EO_ENV}-oa2inv-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | `eo-gsa-d01-oa2inv-an1-001` (26文字) | 30文字 |
| Artifact Registry | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-ar-{EO_REGION_SHORT}` | `eo-re-d01-ar-an1` | 63文字 |
| Secret Manager | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-secretmng` | `eo-re-d01-secretmng` | 255文字 |
| WIF Pool | `{EO_PROJECT}-gcp-pool-wif-{EO_ENV}` | `eo-gcp-pool-wif-d01` | 32文字 |
| WIF IdP | `{EO_PROJECT}-gcp-idp-gh-oidc-wif-{EO_ENV}` | `eo-gcp-idp-gh-oidc-wif-d01` | 32文字 |

> GCP SA は `labels` 非対応（hashicorp/google v6.50.0 で確認済み）。
> 命名メタデータは `display_name`（100文字）+ `description`（256文字）で保持する。

### 5.5 Cloudflare Workers リソース

| リソース | パターン | 例 | 制限 |
|---|---|---|---|
| Worker 名 | `{EO_PROJECT}-{EO_COMPONENT}-{EO_ENV}-cfworker-{EO_REGION_SHORT}-{EO_RE_INSTANCE_ID}` | `eo-re-d01-cfworker-global-001` | |

## 6. タグ / ラベルスキーマ

全クラウドのリソースに統一の `eo_` プレフィックスタグを付与する。

### 6.1 共通タグ定義

| タグキー | 説明 | 値の例 |
|---|---|---|
| `eo_project` | プロジェクト識別子 | `eo` |
| `eo_component` | コンポーネント識別子 | `re` |
| `eo_env` | 環境識別子 | `d01` |
| `eo_iac` | IaC ツール | `cfn` / `bicep` / `terraform` / `none` |
| `eo_re_instance_type` | インスタンス種別 | `lambda` / `funcapp` / `cloudrun` / `cfworker` |
| `eo_re_instance_id` | インスタンス番号 | `001` |
| `eo_region_short` | リージョン短縮 | `apn1` / `jpe` / `an1` / `global` |
| `eo_re_instance_uuid` | UUIDv7 主キー | `019503a1-...` |
| `eo_global_prj_env_id` | グローバルプロジェクト環境ID | `a1b2` |

### 6.2 クラウド別対応状況

| クラウド | タグ/ラベル機能 | 対応方法 |
|---|---|---|
| **AWS** | Tags（全リソース対応） | 上記タグをそのまま付与 |
| **Azure** | Tags（全リソース対応） | 上記タグをそのまま付与（Key Vault 含む） |
| **GCP** | Labels（一部リソース） | Cloud Run, Artifact Registry 等はラベル付与 |
| **GCP SA** | Labels **非対応** | `display_name` + `description` で代替 |
| **Cloudflare** | タグ機能なし | wrangler.toml 内コメントで記録 |

### 6.3 GCP SA のメタデータ代替

GCP Service Account は `labels` 非対応のため、`display_name` + `description` で命名メタデータを保持する。

```hcl
resource "google_service_account" "deployer" {
  account_id   = "eo-gsa-d01-deploy-an1-001"
  display_name = "EO GCP Deployer SA (an1-001)"
  description  = "eo_project=eo, eo_component=re, eo_env=d01, eo_re_instance_type=cloudrun, eo_re_instance_id=001, eo_region_short=an1"
}
```

## 7. 文字数制約サマリー

| リソース | 制限 | ボトルネック | 対策 |
|---|---|---|---|
| Azure Key Vault 名 | **24文字** | EO_GLOBAL_PRJ_ENV_ID 最大6文字 | `EO_COMPONENT` をタグに退避、EO_GLOBAL_PRJ_ENV_ID 運用上限4文字 |
| Azure Storage Account 名 | **24文字** | ハイフン不可 | 全結合、EO_GLOBAL_PRJ_ENV_ID 運用上限4文字 |
| GCP Service Account ID | **30文字** | Labels 非対応 | `display_name` + `description` で代替 |
| GCP WIF Pool/Provider ID | 32文字 | | リージョン不含パターン |
| AWS IAM Role 名 | 64文字 | | 基本パターンで収まる |
| AWS IAM Policy 名 | 128文字 | | 基本パターンで収まる |