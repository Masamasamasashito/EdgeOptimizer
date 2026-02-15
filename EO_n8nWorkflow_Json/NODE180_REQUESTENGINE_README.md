# #180 RequestEngine Settings 設定ガイド

このノードでは、使用するRequest Engine（サーバーレス関数）のクラウド・リージョンと、Accept-Language（言語設定）を設定します。

## 概要

| 項目 | 説明 |
|-----|------|
| ノード番号 | #180 |
| ノード名 | RequestEngine Settings |
| ノードタイプ | Code（JavaScript） |
| 目的 | GEO分散リクエストのクラウド・リージョン・言語を展開 |

## 設定箇所

ノード内のCodeで、`requestEngineList` 配列を編集します:

```javascript
const requestEngineList = [
  {
    type_area: 'AwsLambda_ap-northeast-1',
    accept_language: 'ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7',
  },
  // ここに追加
];
```

## type_area 一覧（コピペ用）

### AWS Lambda

| type_area | リージョン | 地理的位置 |
|-----------|-----------|-----------|
| `AwsLambda_ap-northeast-1` | 東京 | 日本 |
| `AwsLambda_ap-northeast-2` | ソウル | 韓国 |
| `AwsLambda_ap-northeast-3` | 大阪 | 日本 |
| `AwsLambda_ap-southeast-1` | シンガポール | 東南アジア |
| `AwsLambda_ap-southeast-2` | シドニー | オーストラリア |
| `AwsLambda_ap-south-1` | ムンバイ | インド |
| `AwsLambda_us-east-1` | バージニア北部 | アメリカ東海岸 |
| `AwsLambda_us-west-2` | オレゴン | アメリカ西海岸 |
| `AwsLambda_eu-west-1` | アイルランド | ヨーロッパ西部 |
| `AwsLambda_eu-central-1` | フランクフルト | ヨーロッパ中部 |

### Azure Functions

| type_area | リージョン | 地理的位置 |
|-----------|-----------|-----------|
| `AzureFunctions_japan-east` | 東日本 | 日本 |
| `AzureFunctions_japan-west` | 西日本 | 日本 |
| `AzureFunctions_korea-central` | 韓国中部 | 韓国 |
| `AzureFunctions_east-asia` | 香港 | 東アジア |
| `AzureFunctions_southeast-asia` | シンガポール | 東南アジア |
| `AzureFunctions_east-us` | 米国東部 | アメリカ東海岸 |
| `AzureFunctions_west-us` | 米国西部 | アメリカ西海岸 |
| `AzureFunctions_west-europe` | 西ヨーロッパ | オランダ |
| `AzureFunctions_north-europe` | 北ヨーロッパ | アイルランド |

### GCP Cloud Run / Cloud Functions

| type_area | リージョン | 地理的位置 |
|-----------|-----------|-----------|
| `GcpCloudRun_asia-northeast1` | 東京 | 日本 |
| `GcpCloudRun_asia-northeast2` | 大阪 | 日本 |
| `GcpCloudRun_asia-northeast3` | ソウル | 韓国 |
| `GcpCloudRun_asia-east1` | 台湾 | 台湾 |
| `GcpCloudRun_asia-southeast1` | シンガポール | 東南アジア |
| `GcpCloudRun_us-central1` | アイオワ | アメリカ中部 |
| `GcpCloudRun_us-east1` | サウスカロライナ | アメリカ東海岸 |
| `GcpCloudRun_europe-west1` | ベルギー | ヨーロッパ西部 |

### Cloudflare Workers

| type_area | リージョン | 地理的位置 |
|-----------|-----------|-----------|
| `CloudflareWorkers_global` | グローバル | エッジロケーション自動選択 |

### その他

| type_area | 説明 |
|-----------|------|
| `DirectRequest` | Request Engineを経由せず、n8nから直接リクエスト（テスト用） |

## accept_language 一覧（コピペ用）

### 単一言語

| accept_language | 説明 |
|-----------------|------|
| `ja` | 日本語のみ |
| `en` | 英語のみ |
| `ko` | 韓国語のみ |
| `zh-CN` | 中国語（簡体字） |
| `zh-TW` | 中国語（繁体字） |
| `fr` | フランス語 |
| `de` | ドイツ語 |
| `es` | スペイン語 |
| `pt-BR` | ポルトガル語（ブラジル） |

### 複合言語（優先度付き）

| accept_language | 説明 |
|-----------------|------|
| `ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7` | 日本語優先、英語フォールバック |
| `en-US,en;q=0.9` | アメリカ英語優先 |
| `en-GB,en;q=0.9` | イギリス英語優先 |
| `ko,ko-KR;q=0.9,en-US;q=0.8,en;q=0.7` | 韓国語優先、英語フォールバック |
| `zh-CN,zh;q=0.9,en;q=0.8` | 中国語優先、英語フォールバック |
| `zh-TW,zh;q=0.9,en;q=0.8` | 台湾中国語優先、英語フォールバック |
| `fr-FR,fr;q=0.9,en;q=0.8` | フランス語優先、英語フォールバック |
| `de-DE,de;q=0.9,en;q=0.8` | ドイツ語優先、英語フォールバック |

### 特殊設定

| accept_language | 説明 |
|-----------------|------|
| `nothing` | Accept-Languageヘッダを送信しない |

## 設定例

### 例1: 日本向けサイト（東京リージョンのみ）

```javascript
const requestEngineList = [
  {
    type_area: 'AwsLambda_ap-northeast-1',
    accept_language: 'ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7',
  },
];
```

### 例2: 日本＋韓国向けサイト

```javascript
const requestEngineList = [
  {
    type_area: 'AwsLambda_ap-northeast-1',
    accept_language: 'ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7',
  },
  {
    type_area: 'AwsLambda_ap-northeast-2',
    accept_language: 'ko,ko-KR;q=0.9,en-US;q=0.8,en;q=0.7',
  },
];
```

### 例3: グローバルサイト（マルチリージョン）

```javascript
const requestEngineList = [
  // アジア
  {
    type_area: 'AwsLambda_ap-northeast-1',
    accept_language: 'ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7',
  },
  {
    type_area: 'GcpCloudRun_asia-southeast1',
    accept_language: 'en-US,en;q=0.9',
  },
  // アメリカ
  {
    type_area: 'AwsLambda_us-east-1',
    accept_language: 'en-US,en;q=0.9',
  },
  // ヨーロッパ
  {
    type_area: 'AzureFunctions_west-europe',
    accept_language: 'en-GB,en;q=0.9',
  },
  // グローバルエッジ
  {
    type_area: 'CloudflareWorkers_global',
    accept_language: 'en-US,en;q=0.9',
  },
];
```

### 例4: 同一リージョンで複数言語バリアント

```javascript
const requestEngineList = [
  {
    type_area: 'AwsLambda_ap-northeast-1',
    accept_language: 'ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7',
  },
  {
    type_area: 'AwsLambda_ap-northeast-1',
    accept_language: 'en-US,en;q=0.9',
  },
];
```

### 例5: テスト用（DirectRequest）

```javascript
const requestEngineList = [
  {
    type_area: 'DirectRequest',
    accept_language: 'ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7',
  },
];
```

## 動作説明

1. 1つのURLに対して、`requestEngineList` 内の全エントリでリクエストが展開されます
2. 展開されたリクエストは、`cloud_type_area` に応じて対応するRequest Engineノード（#280AWS, #280AZ, #280GCP, #280CF）にルーティングされます
3. `accept_language` が `nothing` の場合、Accept-Languageヘッダは送信されません

## リクエスト数の計算

```
総リクエスト数 = URL数 × User-Agent数 × Request Engine数
```

例: 100 URL × 2 User-Agent × 4 Request Engine = 800 リクエスト

## 注意事項

- Request Engineを増やすと、リクエスト数が倍増します
- 各クラウドのRequest Engineは事前にデプロイが必要です
- `type_area` の値は、#225 Request Engine Switcher ノードの分岐条件と一致させる必要があります

## #225 Request Engine Switcher ノードとの連携

### Switcherノードの役割

#180で設定した `type_area` の値に基づいて、リクエストを適切なRequest Engineノード（#280系）にルーティングします。

```
#180 RequestEngine Settings
    ↓ cloud_type_area を付与
#225 Request Engine Switcher
    ├→ DirectRequest        → #280DirectRequest
    ├→ AwsLambda_*          → #280AWS
    ├→ AzureFunctions_*     → #280AZ
    ├→ CloudflareWorker_*   → #280CF
    └→ GcpCloudRun_*  → #280GCP（#235経由）
```

### デフォルトの分岐条件

| 出力 | 条件（cloud_type_area） | 接続先ノード |
|-----|------------------------|-------------|
| 0 | `DirectRequest` | #280DirectRequest |
| 1 | `AwsLambda_ap-northeast-1` | #280AWS |
| 2 | `AzureFunctions_japan-east` | #280AZ |
| 3 | `CloudflareWorkers_global` | #280CF |
| 4 | `GcpCloudRun_asia-northeast1` | #280GCP（#235経由） |

### 新しいリージョンを追加する場合

**例: AWS ソウルリージョンを追加**

1. **#180 で type_area を追加**
```javascript
const requestEngineList = [
  { type_area: 'AwsLambda_ap-northeast-1', accept_language: 'ja,...' },
  { type_area: 'AwsLambda_ap-northeast-2', accept_language: 'ko,...' },  // 追加
];
```

2. **#225 Switcher に分岐条件を追加**
   - ノードをダブルクリックして編集
   - 「Add Output」をクリック
   - 条件を追加: `{{ $json.data.cloud_type_area }}` equals `AwsLambda_ap-northeast-2`

3. **#280AWS-Seoul ノードを作成（#280AWSをコピー）**
   - Lambda関数名をソウルリージョンのものに変更
   - #225 Switcher の新しい出力と接続

### 同一リージョンで複数のRequest Engineを使う場合

**例: 東京リージョンのLambdaを2つ使う（負荷分散）**

方法A: 異なるtype_areaで区別
```javascript
const requestEngineList = [
  { type_area: 'AwsLambda_ap-northeast-1_primary', accept_language: 'ja,...' },
  { type_area: 'AwsLambda_ap-northeast-1_secondary', accept_language: 'ja,...' },
];
```
→ #225に2つの分岐条件を追加し、それぞれ別の280ノードに接続

方法B: 同じtype_areaで同一ノードに流す（同じLambda関数を共有）
```javascript
const requestEngineList = [
  { type_area: 'AwsLambda_ap-northeast-1', accept_language: 'ja,...' },
  { type_area: 'AwsLambda_ap-northeast-1', accept_language: 'en-US,...' },  // 言語違い
];
```
→ 既存の#225分岐条件のまま、同じ#280AWSノードに流れる

### 設定例: 東京以外のリージョンを追加

**例: シンガポール（AWS）+ 香港（Azure）を追加**

1. **#180 RequestEngine Settings**
```javascript
const requestEngineList = [
  // 日本
  { type_area: 'AwsLambda_ap-northeast-1', accept_language: 'ja,...' },
  // シンガポール
  { type_area: 'AwsLambda_ap-southeast-1', accept_language: 'en-US,...' },
  // 香港
  { type_area: 'AzureFunctions_east-asia', accept_language: 'zh-TW,...' },
];
```

2. **#225 Request Engine Switcher に追加**

| 追加する出力 | 条件 |
|-------------|------|
| 5 | `AwsLambda_ap-southeast-1` |
| 6 | `AzureFunctions_east-asia` |

3. **新しい280ノードを作成**

| ノード名 | 設定内容 |
|---------|---------|
| #280AWS-Singapore | Lambda関数: `eo-re-d01-lambda-apse1` |
| #280AZ-HongKong | Azure Functions URL: `https://eo-re-d01-funcapp-eastasia.azurewebsites.net/...` |

### #225 Switcher ノードの編集手順

1. n8nワークフロー画面で「225 Request Engine Switcher」ノードをダブルクリック
2. 右側の「Rules」セクションで分岐条件を確認
3. 「Add Output」で新しい分岐を追加
4. 条件を設定:
   - Field: `{{ $json.data.cloud_type_area }}`
   - Operation: `equals`
   - Value: `AwsLambda_ap-southeast-1`（例）
5. 新しい出力を対応する280ノードに接続

### type_area命名規則

一貫性のため、以下の命名規則を推奨:

```
{クラウド種別}_{リージョン識別子}[_サフィックス]
```

| パターン | 例 |
|---------|-----|
| 基本形 | `AwsLambda_ap-northeast-1` |
| サフィックス付き | `AwsLambda_ap-northeast-1_primary` |
| カスタム名 | `AwsLambda_tokyo_for_mobile` |

**注意**: type_areaの値は自由に設定できますが、#225 Switcherの分岐条件と完全一致させる必要があります。

## #280 Request Engine ノードの作成方法

新しいリージョンを追加する場合、対応する280ノードを作成する必要があります。

### 280ノードの種類

| クラウド | ノードタイプ | 認証方式 |
|---------|------------|---------|
| AWS Lambda | AWS Lambda | IAM Access Key |
| Azure Functions | HTTP Request | Header Auth（x-functions-key） |
| Cloudflare Workers | HTTP Request | Custom Auth（CF-Access） |
| GCP Cloud Run | HTTP Request | OAuth2 Bearer Token |
| DirectRequest | HTTP Request | なし |

### AWS Lambda ノードの作成

1. **ノードを追加**: 「AWS Lambda」ノードを検索して追加
2. **ノード名**: `280AWS-{リージョン略称} RequestEngine AccessKey`（例: `280AWS-apse1 RequestEngine AccessKey`）
3. **設定項目**:

| 項目 | 設定値 |
|-----|--------|
| Credential | AWS (IAM) を選択（事前に作成が必要） |
| Function | Lambda関数名（例: `eo-re-d01-lambda-apse1`） |
| Payload | `={{ $json.data }}` |

4. **接続**: 出力を `295 JSON result REMOVER` または `340 Random Sleep (ms)` に接続

```
AWS Lambda関数名の命名規則: eo-re-{env}-lambda-{region}
例: eo-re-d01-lambda-apne1 (東京)
    eo-re-d01-lambda-apse1 (シンガポール)
```

### Azure Functions ノードの作成

1. **ノードを追加**: 「HTTP Request」ノードを検索して追加
2. **ノード名**: `280AZ-{リージョン} RequestEngine KeyVault`（例: `280AZ-east-asia RequestEngine KeyVault`）
3. **設定項目**:

| 項目 | 設定値 |
|-----|--------|
| Method | POST |
| URL | Azure FunctionsのエンドポイントURL |
| Authentication | Generic Credential Type → Header Auth |
| Credential | HTTP Header Auth を選択（`x-functions-key` ヘッダー） |

4. **Headers**:
```
User-Agent: ={{ $json.data.headers["User-Agent"] }}
Accept-Language: ={{ $json.data.headers["Accept-Language"] }}
```

5. **Body** (JSON):
```json
{
  "targetUrl": "{{ $json.data.targetUrl }}",
  "tokenCalculatedByN8n": "{{ $json.data.tokenCalculatedByN8n }}",
  "headers": {{ $json.data.headers }},
  "httpRequestNumber": "{{ $json.data.httpRequestNumber }}",
  "httpRequestUUID": "{{ $json.data.httpRequestUUID }}",
  "httpRequestRoundID": "{{ $json.data.httpRequestRoundID }}",
  "urltype": "{{ $json.data.urltype }}"
}
```

6. **Options**:
   - Redirect: Max Redirects = 5
   - Response: Full Response = true, Never Error = true
   - Timeout: 180000 (3分)

7. **接続**: 出力を `300 AZ Arranger` または `340 Random Sleep (ms)` に接続

### Cloudflare Workers ノードの作成

1. **ノードを追加**: 「HTTP Request」ノードを検索して追加
2. **ノード名**: `280CF-{識別子} RequestEngine ZeroTrust`（例: `280CF-global RequestEngine ZeroTrust`）
3. **設定項目**:

| 項目 | 設定値 |
|-----|--------|
| Method | GET（デフォルト） |
| URL | Cloudflare WorkersのカスタムドメインURL |
| Authentication | Generic Credential Type → Custom Auth |
| Credential | HTTP Custom Auth を選択（CF-Access-Client-Id/Secret） |

4. **Query Parameters**:
```
targetUrl: ={{ $json.data.targetUrl }}
tokenCalculatedByN8n: ={{ $json.data.tokenCalculatedByN8n }}
httpRequestNumber: ={{ $json.data.httpRequestNumber }}
httpRequestUUID: ={{ $json.data.httpRequestUUID }}
httpRequestRoundID: ={{ $json.httpRequestRoundID }}
```

5. **Headers**:
```
User-Agent: ={{ $json.data.headers["User-Agent"] }}
Accept-Language: ={{ $json.data.headers["Accept-Language"] }}
```

6. **Options**:
   - Redirect: Max Redirects = 5
   - Response: Full Response = true

7. **Retry設定**:
   - Retry On Fail: true
   - Wait Between Tries: 5000ms

8. **接続**: 出力を `340 Random Sleep (ms)` に接続

### GCP Cloud Run ノードの作成

GCPはOAuth2認証が必要なため、追加のノードが必要です。

**必要なノード構成**:
```
#225 Switcher
    ├→ #230 data Keeper for GCP（データ保持）
    └→ #235 Get IDtoken From GCP Service Account Access Token
           ↓
       #240 IDtoken to json
           ↓
       #245 data and GCP IDtoken Merger（マージ）
           ↓
       #280GCP-{リージョン} RequestEngine Oauth2 Bearer
```

1. **280GCPノードを追加**: 「HTTP Request」ノードを検索して追加
2. **ノード名**: `280GCP-{リージョン} RequestEngine Oauth2 Bearer`（例: `280GCP-asia-southeast1 RequestEngine Oauth2 Bearer`）
3. **設定項目**:

| 項目 | 設定値 |
|-----|--------|
| Method | POST |
| URL | Cloud RunのサービスURL + エンドポイントパス |
| Authentication | なし（Headerで Bearer Token を送信） |

4. **Headers**:
```
User-Agent: ={{ $json.data.headers["User-Agent"] }}
Accept-Language: ={{ $json.data.headers["Accept-Language"] }}
Authorization: ={{ 'Bearer ' + $json.gcf.idToken }}
Content-Type: application/json
```

5. **Body** (JSON):
```json
{
  "targetUrl": "{{ $json.data.targetUrl }}",
  "tokenCalculatedByN8n": "{{ $json.data.tokenCalculatedByN8n }}",
  "headers": "{{ $json.data.headers }}",
  "httpRequestNumber": "{{ $json.data.httpRequestNumber }}",
  "httpRequestUUID": "{{ $json.data.httpRequestUUID }}",
  "httpRequestRoundID": "{{ $json.data.httpRequestRoundID }}",
  "urltype": "{{ $json.data.urltype }}"
}
```

6. **Options**:
   - Redirect: Max Redirects = 5
   - Response: Full Response = true
   - Timeout: 180000 (3分)

7. **接続**: 出力を `305 GCP Arranger` に接続

### Credentials の事前設定

各ノードで使用するCredentialは事前に作成が必要です。

| クラウド | Credential名 | 設定内容 |
|---------|-------------|---------|
| AWS Lambda | AWS (IAM) | Access Key ID / Secret Access Key |
| Azure Functions | HTTP Header Auth | Name: `x-functions-key`, Value: Function Key |
| Cloudflare Workers | HTTP Custom Auth | `CF-Access-Client-Id` / `CF-Access-Client-Secret` |
| GCP Cloud Run | Google API (Service Account) | Service Account JSON Key |

詳細は [RE_README.md](../EO_Documents/Manuals/RE_README.md) を参照。

### 280ノード作成後のチェックリスト

- [ ] ノード名が命名規則に従っている
- [ ] Credentialが正しく設定されている
- [ ] URL/関数名が正しいリージョンを指している
- [ ] #225 Switcherの分岐条件と接続が完了している
- [ ] 出力が適切なArrangerノードまたはSleepノードに接続されている
- [ ] Request Engineがデプロイ済みで動作確認が完了している

## 関連ドキュメント

- [N8N_WORKFLOW_README.md](N8N_WORKFLOW_README.md) - ワークフロー全体設定
- [NODE175_USERAGENT_README.md](NODE175_USERAGENT_README.md) - User-Agent設定
- [RE_README.md](../EO_Documents/Manuals/RE_README.md) - Request Engineデプロイ
