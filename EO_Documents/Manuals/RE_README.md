# EO Request Engine リクエスト実行セキュリティ設定

EO (Edge Optimizer) のRequest Engineに関するリクエスト実行セキュリティ設定です。

> **設計・開発速度を変える視点**: 「メソッドリクエスト → 統合リクエスト → バックエンド → 統合レスポンス → メソッドレスポンス」を**各ステージのデータ構造**として捉えると、設計が一変する。→ [リクエスト構造から理解する](REQUEST_STRUCTURE_VIEW.md)

1. n8n Credentialsによるn8n→各Request Engineへの接続認証設定
2. 各Request Engineコード内のn8n生成トークン照合用リクエストシークレット設定

## 1. n8n Credentialsによるn8n→各Request Engineへの接続認証設定

**目的**: n8nから各クラウド基盤のサーバレス関数（AWS Lambda、Azure Functions、GCP Cloud Run、Cloudflare Workers）への**アクセスを許可する**ための認証設定

**役割**: 「**誰が**Request Engineにアクセスできるか」を制御する**第1層のセキュリティ**（プラットフォーム側の認証）

**内容**: 各プラットフォームの認証情報をn8n Credentialsとして登録する方法
- AWS Lambda: IAM Access Key
- Azure Functions: Function App Key（`x-functions-key` ヘッダー）
- GCP Cloud Run: Service Account JSON Key（OAuth2 Bearer Token）
- Cloudflare Workers: Cloudflare Access Service Token

## 2. 各Request Engineコード内のn8n生成トークン照合用リクエストシークレット設定

**目的**: 各Request Engineのコード実行内で、n8nワークフローが生成したトークンが**正当なものであることを検証する**ための実装と設定

**役割**: 「**リクエストが正当かどうか**」を検証する**第2層のセキュリティ**（トークン検証）

**検証の流れ**:
1. **n8nワークフロー側**: `170 Secret Key Token Generator` ノードで `SHA-256(url + N8N_EO_REQUEST_SECRET)` を計算してトークンを生成し、各Request Engineに送信
2. **各Request Engine側**: 受け取ったトークンと `SHA-256(url + 各Request Engineが各クラウドのシークレットサービスから取得した照合用リクエストシークレット)` をコード内で照合
   - Azure Functions: `_calc_token()` 関数でトークンを計算して検証（`function_app.py` 165-175行目）
   - AWS Lambda: `_calc_token()` 関数でトークンを計算して検証（`lambda_function.py` 285-297行目）
   - GCP Cloud Run: `_calc_token()` 関数でトークンを計算して検証（`main.py` 1730-1753行目）
   - Cloudflare Workers: `generateSecurityToken()` 関数でトークンを計算して検証（`worker.ts` 398-401行目）

**内容**: 各プラットフォームでの照合用リクエストシークレットの環境定義と命名規則（シークレット名、環境変数名、UUID/ARNなど）、および検証コード内での変数名

# 目次

- [n8n Credentialsによるn8n→各Request Engineへの接続認証設定](#n8n Credentialsによるn8n→各Request Engineへの接続認証設定)
  - [RequestEngine AWS IAMuser access key](#requestengine-aws-iamuser-access-key)
  - [RequestEngine Azure Functions App Key](#requestengine-azure-functions-app-key)
  - [RequestEngine Worker Cloudflare Access Secret](#requestengine-worker-cloudflare-access-secret)
  - [RequestEngine GCP Service Account Json key To Get Acces Token](#requestengine-gcp-service-account-json-key-to-get-acces-token)
- [各Request Engineコード内のn8n生成トークン照合用リクエストシークレット設定](#各Request Engineコード内のn8n生成トークン照合用リクエストシークレット設定)
  - [リクエストエンジンで扱う照合用リクエストシークレットの環境定義表](#リクエストエンジンで扱う照合用リクエストシークレットの環境定義表)
  - [補足説明](#補足説明)
  - [共通事項](#共通事項)
- [セキュリティ実装](#セキュリティ実装)
- [詳細ドキュメントへのリンク](#詳細ドキュメントへのリンク)
- [トラブルシューティング](#トラブルシューティング)

# n8n Credentialsによるn8n→各Request Engineへの接続認証設定

n8nから各クラウド基盤のサーバレス関数（Request Engine）へのアクセス許可をするための認証設定

## RequestEngine AWS IAMuser access key

**EO_RE_Lambda_apne1_AccessKey**

`*************_accessKeys.csv`

- AWS (IAM)
    - Region
    - Access Key ID
    - Secret Access Key

- `280AWS-apne1 RequestEngine AccessKey`ノード
    - Parameters > Function Name or ID > Expression
    - Lambda関数名を入力 > `eo-re-d01-lambda-apne1`

## RequestEngine Azure Functions App Key

**EO_RE_Func_jpe_AppKey**

Azure > Function App > (FunctionName) > Function > App Key(must) > Host Key > `default` ( Do not select `_master` )

- Header Auth
    - Name:`x-functions-key`
    - Value:上記defaultの値を入力

- `280AZ-japan-east RequestEngine KeyVault`ノード
    - Parameters > URL
    - Azure > 関数アプリ > 関数 > リソースJSON > invoke_url_template
     `https://eo-re-d01-funcapp-jpe-xxxxxxxxxxxxxxxx.japaneast-01.azurewebsites.net/api/requestengine_func`

## RequestEngine Worker Cloudflare Access Secret

**EO_RE_Worker_global_HeaderAuth_ServiceToken**

- Custom Auth(Header Auth)
    - JSON
```
{
  "headers": {
    "CF-Access-Client-Id": "XXXXXXXXXXXXXXXXXXXXXXX.access",
    "CF-Access-Client-Secret": "YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
  }
}
```

- `280CF-global RequestEngine ZeroTrust`ノード

## RequestEngine GCP Service Account Json key To Get Acces Token

**EO_RE_GCP_RUN_asne1_OAuth2_Invoker_SA**

- **権限の参照**: GCP Cloud Run のサービスアカウント（Deployer / Compute Engine Default / Runtime / OAuth2 Invoker）のロール・権限一覧と設定手順は [EO_Documents/Manuals/py/CloudRun_README.md](py/CloudRun_README.md) を参照。

個人GCPメール > IAMと管理 > サービスアカウント > `eo-gsa-d01-oa2inv-asne1`を選択 > 鍵

`********************-xxxxxxxxxxxx.json`

- Google Service Account API
    - Region
    - Service Account Email
    - ( Project Service Account .json > private_key ) Private Key
      - `\n`を含み、そのまま `private_key` 内容を貼り付ける
    - Set up for use in HTTP Request node : Enable
    - Scope(s) : `https://www.googleapis.com/auth/iam`

- `235 Get IDtoken From GCP Service Account Access Token`ノード



# 各Request Engineコード内のn8n生成トークン照合用リクエストシークレット設定

## リクエストエンジンで扱う照合用リクエストシークレットの環境定義表

### 基本情報の比較

| クラウド名 | リージョン | クラウドのシークレットサービス | リクエストエンジンコード内環境変数 | ランタイム |
|---|---|---|---|---|
| **Azure** | Japan East (jpe) | Key Vault: `eo-re-d01-kv-jpe`<br>シークレット: `AZFUNC-REQUEST-SECRET` | `AZFUNC_REQUEST_SECRET_NAME` | Python 3.13 |
| **AWS** | apne1 (ap-northeast-1) | Secrets Managerのシークレット名: `eo-re-d01-secretsmng-apne1`<br>シークレットキー: `LAMBDA_REQUEST_SECRET` | `LAMBDA_REQUEST_SECRET_NAME`<br>`LAMBDA_REQUEST_SECRET_KEY_NAME` | Python 3.14 |
| **GCP** | asne1 (asia-northeast1) | Secret Managerのシークレット名: `eo-re-d01-secretmng`<br>シークレットキー: `CLOUDRUN_REQUEST_SECRET` | `CLOUDRUN_REQUEST_SECRET_NAME`<br>`CLOUDRUN_REQUEST_SECRET_KEY_NAME` | Python (Flask) |
| **Cloudflare** | global (Edge) | `CFWORKER_REQUEST_SECRET` | `env.CFWORKER_REQUEST_SECRET` | TypeScript (V8) |

### 詳細情報

#### Azure Functions

- **リクエストエンジン名**: リソースグループ: `eo-re-d01-resource-group-jpe`、関数アプリ: `eo-re-d01-funcapp-jpe`、関数名: `requestengine_func`
- **Key Vault URI**: `https://eo-re-d01-kv-jpe.vault.azure.net/` (GitHubシークレット: `EO_AZ_RE_KEYVAULT_URL`)
- **シークレット識別子**: `https://eo-re-d01-kv-jpe.vault.azure.net/secrets/AZFUNC-REQUEST-SECRET/{VERSION}`
- **Key Vault**: `eo-re-d01-kv-jpe`
- **シークレット**: `AZFUNC-REQUEST-SECRET`
- **シークレット取得方法**: Azure Key Vault Secrets API (`SecretClient`)
- **保存方式**: テキスト
- **認証**: Managed Identity (System-assigned)
- **備考**: キーコンテナURIはGitHubのシークレットに記載。

#### AWS Lambda

- **リクエストエンジン名**: Lambda関数: `eo-re-d01-lambda-apne1`
- **ARN**: `arn:aws:secretsmanager:ap-northeast-1:{AWSアカウントID}:secret:eo-re-d01-secretsmng-apne1-{RANDOM}`
- **シークレット**: `eo-re-d01-secretsmng-apne1`
- **シークレットキー**: `LAMBDA_REQUEST_SECRET`
- **シークレット取得方法**: AWS Secrets Manager API (`boto3.client('secretsmanager')`)
- **保存方式**: シークレットキーの値はテキストだが、シークレットはJSON形式
- **認証**: IAM Role for Lambda
- **命名制約**: 英数字 + `/ _ + = . @ -` のみ、1-512文字、ハイフン+6文字で終わる名前は避ける
- **備考**: AWS Secrets Managerは1シークレットあたり USD 0.40/月の固定料金あり（リクエストなしでも発生）。GCP Secret Managerもアクティブなバージョンあたり USD 0.06/月の固定料金あり。Azure Key VaultとCloudflare Workers Secretsは固定料金なしで操作数ベースのAPIコール課金のみ。

#### GCP Cloud Run

- **リクエストエンジン名**: 組織: `<組織ドメイン>`、プロジェクト名: `eo-re-d01-pr-asne1`、Cloud Runサービス: `eo-re-d01-cloudrun-asne1`
- **リソース名**: `projects/eo-re-d01-pr-asne1/secrets/eo-re-d01-secretmng/versions/{VERSION}`
- **シークレット**: `eo-re-d01-secretmng`
- **シークレットキー**: `CLOUDRUN_REQUEST_SECRET`
- **保存方式**: シークレットキーの値はテキストだが、シークレットはJSON形式
- **シークレット取得方法**: GCP Secret Manager API (`google.cloud.secretmanager`)
- **認証**: Service Account (IAM)
- **命名制約**: 英数字 + ハイフン + アンダースコア、最大255文字。リソース名にはバージョンが含まれ1から始まる、環境変数ではバージョンを指定しない。
- **備考**: GCP Secret Managerもシークレットのアクティブなバージョンあたり USD 0.06/月の固定料金がある。エリアの概念無しで使える、使う。

#### Cloudflare Workers

- **リクエストエンジン名**: Workersアプリケーション: `eo-re-d01-cfworker-global`、カスタムドメイン: `eo-re-d01-cfworker-global.sample.com`
- **保存方式**: テキスト（環境変数として自動管理）
- **シークレット設定方法**: `npx wrangler secret put CFWORKER_REQUEST_SECRET` または Cloudflare Dashboard
- **シークレット取得方法**: 環境変数として `env.CFWORKER_REQUEST_SECRET` で直接参照（Worker起動時にメモリに読み込まれる）
- **認証**: Cloudflare Workers Secrets API (自動管理)
- **命名制約**: 空白を含めない、英数字 + アンダースコア/ハイフン。
- **備考**: 環境変数（Secrets）はWorker起動時にメモリに読み込まれるため、リクエスト毎にAPIを呼び出していない。

### 共通事項

- **照合用リクエストシークレットの値**: すべてのクラウドのシークレットサービスで `EO_Infra_Docker/.env` の `N8N_EO_REQUEST_SECRET` と同じ値を使用
- **トークン生成**: n8nワークフローで `SHA-256(url + N8N_EO_REQUEST_SECRET)` を計算して各Request Engineに送信
- **検証**: 各Request Engineでn8nから受け取ったトークンと `SHA-256(url + 各Request Engineが各クラウドのシークレットサービスから取得した照合用リクエストシークレット)` を照合

## セキュリティ実装

### 2層のセキュリティアーキテクチャ

EOのRequest Engineは、**EOのn8n以外からのすべてのリクエストを却下する**ために、2層のセキュリティを実装しています。

#### 第1層: プラットフォーム側の認証（n8n Credentials）

各クラウドプラットフォームの認証機能により、n8nからのリクエストのみを許可します。

| プラットフォーム | 認証方式 | 却下される場合 |
|---|---|---|
| **AWS Lambda** | IAM Access Key（n8n Credentials） | IAM Access Keyがない、または不正な場合 |
| **Azure Functions** | Function App Key（`x-functions-key` ヘッダー） | Function App Keyがない、または不正な場合（401エラー） |
| **GCP Cloud Run** | OAuth2 Bearer Token（Service Account） | OAuth2 Bearer Tokenがない、または不正な場合（401エラー） |
| **Cloudflare Workers** | Cloudflare Access Service Token（`CF-Access-Client-Id/Secret` ヘッダー） | Service Tokenがない、または不正な場合（403エラー） |

#### 第2層: トークン検証（コード内）

各Request Engineのコード内で、n8nから送信されたトークンを検証します。

**n8nワークフロー側のトークン生成**:
- `170 Secret Key Token Generator` ノードで `SHA256(url + N8N_EO_REQUEST_SECRET)` を計算
- このトークンを各Request Engineに送信

**各Request Engine側のトークン検証**:
- 受け取ったトークンと `SHA-256(url + 各Request Engineが各クラウドのシークレットサービスから取得した照合用リクエストシークレット)` を照合
- トークンが一致しない場合、401エラーを返却

### セキュリティの強度

#### ✅ 却下されるケース（EOのn8n以外からのリクエスト）

1. **認証失敗（プラットフォーム側で401/403）**
   - AWS Lambda: IAM Access Keyがない、または不正な場合
   - Azure Functions: Function App Keyがない、または不正な場合
   - GCP Cloud Run: OAuth2 Bearer Tokenがない、または不正な場合
   - Cloudflare Workers: Access Service Tokenがない、または不正な場合

2. **トークン検証失敗（コード内で401）**
   - トークンが送信されていない場合
   - トークンが `SHA-256(url + 照合用リクエストシークレット)` と一致しない場合

#### ⚠️ 理論上のリスク（両方の情報が漏洩した場合）

**リスク**: n8n Credentials（IAM Access Key、Function App Key、Service Account JSON Key、Cloudflare Access Service Token）と `N8N_EO_REQUEST_SECRET` が同時に漏洩した場合、攻撃者はリクエストを通過させられる可能性があります。

**実務上の担保**:
- **n8n Credentials**: n8nのCredentials機能により、n8n内で暗号化されて保存されます
- **照合用リクエストシークレット**: `EO_Infra_Docker/.env` に保存され、各プラットフォームのシークレットサービス（Azure Key Vault、AWS Secrets Manager、GCP Secret Manager、Cloudflare Workers Secrets）に同じ値が設定されます
- **2層のセキュリティ**: 認証層とトークン検証層の両方が突破されない限り、不正なリクエストは通過しません

※照合用リクエストシークレットについて、Dockerの.envではなくn8n Credentialsで保持する方法はあるが、平文でノードからOUTPUT/INPUTされるため、対策開発が必要。

### 結論

**実務上、EOのn8n以外からのすべてのリクエストは却下されます。**

2層のセキュリティ（プラットフォーム側の認証 + コード内のトークン検証）により、EOのn8n以外からのアクセスは実質的にブロックされます。

## トークン生成と検証の流れ
1. **n8n側**: `SHA-256(url + N8N_EO_REQUEST_SECRET)` を計算してトークンを生成
2. **Request Engine側**: シークレットサービスから照合用リクエストシークレットを取得して `SHA-256(url + 取得した照合用リクエストシークレット)` を計算してトークンを生成
3. **検証**: リクエストエンジンで「n8nから受け取ったトークン」と「リクエストエンジン自身で生成したトークン」を照合して一致しない場合、401などのエラーを返却

## 詳細ドキュメントへのリンク

- **設計視点（推奨）**: [リクエスト構造から理解する — API Gateway / Request Engine](REQUEST_STRUCTURE_VIEW.md) — 各ステージの入力/出力構造で設計・開発を揃える視点

各プラットフォームの詳細なセットアップ手順やトラブルシューティングについては、以下のドキュメントを参照してください：

- **AWS Lambda**: [`EO_Documents/Manuals/py/LAMBDA_README.md`](py/LAMBDA_README.md)
- **Azure Functions**: [`EO_Documents/Manuals/py/AZFUNC_README.md`](py/AZFUNC_README.md)
- **GCP Cloud Run**: [`EO_Documents/Manuals/py/CloudRun_README.md`](py/CloudRun_README.md) — サービスアカウント（Deployer / Compute Engine Default / Runtime / OAuth2 Invoker）の各種権限・ロールの詳細はここを参照
- **Cloudflare Workers**: [`EO_Documents/Manuals/ts/CFWorker_Overview_README.md`](ts/CFWorker_Overview_README.md)

## トラブルシューティング

### よくある問題と解決方法

#### 1. トークン検証エラー（401 Invalid Token）

**症状**: Request Engineから `invalid_token` エラーが返される

**原因と解決方法**:
- **原因1**: n8nの `N8N_EO_REQUEST_SECRET` と各プラットフォームのシークレット値が一致していない
  - **解決**: `EO_Infra_Docker/.env` の `N8N_EO_REQUEST_SECRET` の値を確認し、各プラットフォームのシークレットサービスに同じ値が設定されていることを確認してください
- **原因2**: シークレットサービスから正しくシークレットを取得できていない（権限不足など）
  - **解決**: 各プラットフォームの認証設定（Managed Identity、IAM Role、Service Account、Secrets API）を確認してください
- **原因3**: URLエンコーディングの問題
  - **解決**: n8nワークフローでのトークン生成時とRequest Engineでの検証時で、URLのエンコーディングが一致していることを確認してください

#### 2. シークレット取得エラー（500 Missing Secret）

**症状**: Request Engineから `missing_secret` エラーが返される

**原因と解決方法**:
- **原因1**: 環境変数が設定されていない（Cloudflare Workers）
  - **解決**: `npx wrangler secret put CFWORKER_REQUEST_SECRET` を実行してシークレットを設定してください
- **原因2**: シークレット名が間違っている
  - **解決**: 各プラットフォームのコード内で使用されているシークレット名（`*_NAME` 変数）と、実際のシークレットサービス上のシークレット名が一致していることを確認してください
- **原因3**: JSON形式のシークレットでキー名が間違っている（AWS Lambda、GCP Cloud Run）
  - **解決**: `*_JSON_KEY` 変数の値と、JSON内の実際のキー名が一致していることを確認してください

#### 3. 認証エラー（401/403）

**症状**: n8nからRequest Engineへのリクエストが認証エラーになる

**原因と解決方法**:
- **AWS Lambda**: IAMユーザーのアクセスキーとシークレットキーが正しく設定されているか確認
- **Azure Functions**: Function App Key (`x-functions-key` ヘッダー) が正しく設定されているか確認
- **GCP Cloud Run**: 
  - Service AccountのJSONキーと認証トークンが正しく生成されているか確認
  - n8n で `PERMISSION_DENIED: Permission 'iam.serviceAccounts.getOpenIdToken' denied` が発生する場合、そのサービスアカウント自身に対して `roles/iam.serviceAccountTokenCreator` (SA トークン作成者) が付与されているか確認（詳細は [CloudRun_README.md](py/CloudRun_README.md) 参照）
- **Cloudflare Workers**: Cloudflare AccessのService Token（`CF-Access-Client-Id` と `CF-Access-Client-Secret`）が正しく設定されているか確認

#### 4. シークレットキャッシュの問題

**症状**: シークレット値を変更したが、Request Engineで古い値が使われ続ける

**原因と解決方法**:
- **Azure Functions / AWS Lambda / GCP Cloud Run**: グローバル変数でキャッシュされているため、関数を再起動（再デプロイ）する必要があります
- **Cloudflare Workers**: 環境変数（Secrets）を更新した後、Workerを再デプロイしてください

#### 5. コスト関連

**AWS Secrets Manager / GCP Secret Manager**: シークレットあたりの固定料金があるため、複数のシークレットを管理する場合はJSON形式で1つのシークレットにまとめることでコストを削減できます。現在、AWS LambdaではJSON形式を使用しています。



# リクエストエンジンのデータフローと処理ロジックの統一

各プラットフォーム（Azure, AWS, GCP, Cloudflare）における、n8nとのやり取りおよびターゲットへのリクエスト処理（Warmup）の流れを以下に整理します。

## 1. データフローの構造

| 実行場所 | フェーズ | 内容 | 通信形式 | 主要なデータ構造 |
| :--- | :--- | :--- | :--- | :--- |
| **n8nリクエストエンジンノード** | リクエスト送信 | Warmupリクエスト実行用パラメータ送信 | HTTP POST (with Cloud Platform Auth) | `{ "data": { "url": "...", "token": "...", "headers": { "User-Agent": "..." }, "urltype": "...", "httpRequestNumber": "...", "httpRequestUUID": "...", "httpRequestRoundID": "..." } }` |
| **Request Engineサーバレス** | 命令受信 | 1. クラウド基盤による接続認証<br>2. Warmupリクエスト実行用パラメータ解析 3. HASH照合 | HTTP POST (JSON) | 同上。<br>※EOの仕様により `[{ "data": { ... } }]` のように配列やdataキーでラップされるため、各エンジンで中身を抽出（正規化）してパース。<br>※n8n生成済 `token`(HASH) の受信と、サーバレス側のクラウドシークレットサービスから取得したシークレットでHASHトークンを生成し、2者を照合（SHA-256）し、正当性を検証。 |
| **Request Engineサーバレス** | Warmup実行 | ターゲットURLへWarmupリクエスト | HTTP GET | **Request Headers Detail:**<br>1. **継承**: n8nで指定した `User-Agent`, `Accept-Language`, `type_area` 等<br>2. **識別**: `x-eo-re` (WAFバイパス用)<br>3. **自動**: `Accept-Encoding: gzip, br` 等 (ライブラリ自動付与)<br>4. **除外**: `Host`, `httpRequestNumber` 等 (送出前に除去) |
| **Target Site** | リクエスト受信 | Warmupリクエストの着信と処理 | HTTP GET (Incoming) | **Received Headers Detail:**<br>1. **User-Agent**: デバイス偽装用（iPhone, Androidなどデバイス別の挙動確認）<br>2. **Accept-Language**: 地域/言語属性（多言語サイトの出し分け確認）<br>3. **type_area**: 環境識別（クラウド種別と地域によるオリジン/CDNの挙動特定）<br>4. **x-eo-re**: WAFバイパス（`azure`, `aws`, `gcp`, `cloudflare` のいずれか） |
| **Target Site** | レスポンス返却 | Warmupリクエストに対する応答 | HTTP Response | **Response Data Detail:**<br>・`HTTP Status`<br>・`Response Headers`<br>・`Response Body`<br>・`Network Metrics` (TTFB, Duration, etc.) |
| **Request Engineサーバレス** | 結果返却 | n8nへWarmupリクエスト結果をそのまま送信（リクエストエンジンではデータ処理しない様にする） | HTTP Response (JSON) | **Flat JSON:**<br>`headers.general.*`, `headers.request-headers.*`, `headers.response-headers.*`, `eo.meta.*`, `eo.security.*`, `error.*` |
| **n8nリクエストエンジンノード** | 結果受信 | 後続ノードでのデータ利用 | HTTP Response Parsing | 受け取った Flat JSON を各セルやシートへ展開 |
 
## 2. 主要な処理ロジックと信頼性設計
 
データフローの各工程において、システムの信頼性と解析品質を担保するための以下のロジックが実装されています。
 
### 2.1 信頼性・効率化ロジック
- **自律リトライ制御 (Python系)**:
  - ネットワーク一時エラーや 5xx サーバーエラーに対し、最大 3 回（指数バックオフ付き：0.5s, 1s, 2s...）のリトライを実行。
  - 4xx クライアントエラー（リクエスト不備等）はリトライ対象外として迅速にエラー復帰。
- **通信タイムアウト管理**:
  - ターゲットへのリクエストは一律 10 秒で強制終了。ゾンビプロセスの発生とリソース占有を防止。
- **メモリ保護 (5MB 制限)**:
  - レスポンスボディが 5MB を超える場合、メモリ溢れ防止のためコンテンツ読み込みを自動的にスキップ。基本メトリクス取得のみに限定して継続。
- **プロトコル・TLS 検出**:
  - HTTP プロトコルバージョン（HTTP/1.1~3）および TLS バージョンの精密な特定。
- **CDN 自動検出（16社対応）**:
  - レスポンスヘッダーから CDN プロバイダーを自動検出。Cloudflare, CloudFront, Akamai, Azure Front Door, Fastly, Vercel, さくらウェブアクセラレータ, Bunny CDN, Alibaba Cloud CDN, CDNetworks, KeyCDN 等。

### 2.2 n8n 側でのインテリジェントな後処理
- **キャッシュ消失検知 (Eviction Detector)**:
  - リクエストエンジンが返却した `CF-Cache-Status` と `Age` ヘッダーを突き合わせ、「意図しないキャッシュ消失（Eviction）」を自動判定。
  - `HIT` かつ `Age` が極端に若い場合の警告表示など、CDN 挙動の統計分析をサポート。
 
### 2.3 基盤設計とコスト最適化
本システムは、高い解析・セキュリティ性能を維持しつつ、ランニングコストを最小化するための設計を採用しています。
- **VPC 外実行 (Public Serverless)**:
  - AWS Lambda / GCP Cloud Run / Azure Functions のいずれも、VPC 内には配置せず「VPC 外（パブリック実行環境）」で動作させています。
  - **理由**: NAT Gateway や VPC インターフェースエンドポイントなどのコストを現状では抑えるため。
  - **セキュリティ**: EOユーザー顧客のセキュリティポリシーに応じてVPC内に配置する場合は、変更可能です。
- **シークレット管理の集約**:
  - シークレット管理サービス（Secrets Manager等）は料金を抑えるため、複数の設定値を一つの JSON に集約し、 1 スロット、セッション内キャッシュでAPIリクエスト回数を制御しています。
 
## 3. ロジックの統一化に向けた検討
 
 プラットフォーム固有の制約（イベント形式、シークレット取得）を除き、以下のロジックは全プラットフォームで統一可能です。
 
 ### 統一済みの要素（Python版3プラットフォーム）
 1. **ヘッダー正規化 (Normalization)**:
    - 転送不要なヘッダー（Hostなど）の除外ルール。
    - キーの小文字統一、User-Agent の優先取得ロジック。
 2. **トークン算出 (Token Calculation)**:
    - `SHA-256(url + secret)` の算出アルゴリズム。
 3. **メタデータ出力 (Metadata Output)**:
    - `httpRequestUUID`, `httpRequestRoundID`, `urltype` 等のパススルー。
 4. **出力フォーマット (Flat JSON Mapping)**:
    - n8n が受け取る JSON のキー名（`headers.general.*`, `eo.meta.*`, `eo.security.*`）。
    - CDN検出（`eo.meta.cdn-*`）を含む統一された3名前空間構造。

 ### 未統一の要素（Cloudflare Workers）
 - Cloudflare Workers（TypeScript版）はレスポンス構造の統一が未完了。Phase 1 として対応予定。
 
 ### 統一化のメリット
 - **デバッグの容易性**: プラットフォームに関わらず、n8n に返却されるデータの構造が完全に一致する。
 - **メンテナンス性の向上**: 共通コア (`request_engine_core.py`) への変更が全プラットフォームへ自動的に反映される。
 - **3名前空間の明確な責務**: `headers.*`（生HTTP）、`eo.meta.*`（メタデータ+計測）、`eo.security.*`（セキュリティ分析）。

