# n8n ワークフローノード設定ガイド

Request Engine のセットアップ完了後、n8n ワークフローのノードを設定して Edge Optimizer を利用可能にします。

このガイドは**全 Request Engine 共通**です（AWS Lambda / Azure Functions / Cloudflare Workers / GCP Cloud Run）。

> n8n ワークフロー上の**桃色（ピンク）Sticky Note** が設定箇所の目印です。設定①〜⑩ の番号が振られています。

## 目次

- [Step.0 — 起点設定](#step0--起点設定)
- [Step.1 — フィルタリング・バリアント設定](#step1--フィルタリングバリアント設定)
- [Step.2 — Request Engine 接続設定](#step2--request-engine-接続設定)
- [Step.3 — 実行とCSV出力](#step3--実行とcsv出力)
- [動作確認](#動作確認)
- [補足: #110 SimpleUrlList で Step.1 から開始する方法](#補足-110-simpleurllist-で-step1-から開始する方法)

## Step.0 — 起点設定

### 設定①: #010 XMLサイトマップURL設定

Warmup対象サイトのXMLサイトマップURLを設定します。

1. `010 Step.0 Starter by XML sitemap` ノードをダブルクリック
2. 鉛筆マークをクリックして、以下の **JSON形式** でサイトマップURLを設定:

```json
[
  {
    "Website": "https://example.com/sitemap.xml"
  }
]
```

3. 「Save」

> 💡 現在のリリースでは XMLサイトマップ **1個** のみ対応です。
> サイトマップURLが不明な場合は `https://あなたのドメイン/sitemap.xml` または `/sitemap_index.xml` を確認してください。

### 設定②: #015-020 DNS認証設定

Edge Optimizer は、Warmup対象ドメインの所有権を DNS TXTレコードで検証します（第三者サイトへの不正リクエスト防止）。

**②-1. DNS TXTレコードを追加**

Warmup対象ドメインのDNS設定で、以下のTXTレコードを追加してください：

| レコード名 | タイプ | 値 |
|---|---|---|
| `_eo-auth.example.com` | TXT | `eo-authorized-yourtoken`（任意の文字列） |

複数ドメインを対象とする場合は、各ドメインごとにTXTレコードを設定してください（すべて同じトークン値）：

- `_eo-auth.example.com` → `eo-authorized-yourtoken`
- `_eo-auth.example.org` → `eo-authorized-yourtoken`
- `_eo-auth.sub.example.com` → `eo-authorized-yourtoken`

**②-2. n8n #020ノードのトークンを設定**

1. `020 DNS Auth` ノードをダブルクリック
2. Code 内の `DNSTXT_TOKEN` を、DNS TXTレコードに設定した値と同じ値に変更:

```javascript
const DNSTXT_TOKEN = "eo-authorized-yourtoken"; // ← DNS TXTレコードと同じ値
```

3. 「Save」

**②-3. 設定確認**

```bash
# Linux / macOS
dig TXT _eo-auth.example.com +short

# Windows (PowerShell)
Resolve-DnsName -Name "_eo-auth.example.com" -Type TXT
```

期待される出力: `"eo-authorized-yourtoken"`（設定したトークン値）

> ⚠️ DNS認証に失敗すると「【DNS認証拒否】正当な所有権が確認できません。実行を停止します。」と表示されます。DNSの伝播に時間がかかる場合は数分〜数時間待ってから再試行してください。

## Step.1 — フィルタリング・バリアント設定

### 設定③: #125 Playwright利用の選択

メインドキュメントURLからDOMデータを取得する方法を選択します。

- `125-1 HTTP Req to MainDoc URL locs through Playwright`: Playwrightコンテナのヘッドレスブラウザでレンダリングし、JavaScript による後発生成 DOM 確定後の DOM データを取得
- `125-2 HTTP Req MainDoc URL locs without Playwright`: Playwright を使わず HTTP リクエストのみで DOM を取得

Playwright を使わない場合は、`125-1` を `125-2` に入れ替えてください。

> ⚠️ Playwright を使わない場合、**Target URLリスト抽出の網羅性は下がります**（JavaScript 実行で生成される URL が取得できないため）。
> Playwright コンテナのポートがローカル Docker で競合しているとエラーになります。

### 設定④: #140 Resource URLs Discovery from DOM

メインドキュメントの DOM からサブリンク（アセット含む）を抽出し、Warmup対象のリクエスト候補リストを生成します。

**処理フロー:**

1. **準備**: item から MainDocURL の「生DOM」取得
2. **全サブリンク取得**
   - 戦略A：無差別抽出（絶対URLスキャン）
   - 戦略B：構造解析（相対パススキャンからURL復元）
3. **フィルタリング**: ドメインホワイトリストと URL スキーム
4. **重複排除と親子関係構築**
   - 親: MainDocURL
   - 子: ResourceURLs（MainDoc の DOM から抽出したサブリンク）

**ユーザー設定箇所:**

1. `140 Resource URLs Discovery from DOM` ノードをダブルクリック
2. Code 内の `REQUEST_TARGET_URL_PREFIXES`（ドメインホワイトリスト）を編集:

```javascript
const REQUEST_TARGET_URL_PREFIXES = [
  'https://example.com',
  // ダブルCDN構成の場合はオリジンドメインも追加
  // 'https://origin.example.com',
];
```

3. 「Save」

> 💡 基本的にドメインホワイトリストだけ設定すれば OK です。140 ノードにより、後続ノードは**「ゴミがなく、ドメインも正しく、重複もない、純粋なリクエスト候補リスト」**を受け取ることができます。

### 設定⑤: #155 Excluded Patterns Filter

Warmup不要な URL を「**部分一致**」もしくは「**完全一致**」で除外します。

1. `155 Excluded Patterns Filter` ノードをダブルクリック
2. Code 内の除外対象パターン一覧を編集:

```javascript
// 除外対象パターン一覧
// 部分一致: /wp-json/, /xmlrpc.php, /feed/ など
// 完全一致: 特定URLをピンポイントで除外
```

3. 「Save」

> 💡 `/wp-admin/`、`/wp-json/`、`/xmlrpc.php`、`/feed/` など CMS 系の不要 URL や、NitroPackの BlobURL などを除外できます。

### 設定⑥: #175 User-Agent 設定

実際のユーザーによるリクエストになるべく近づけるため、Warmup リクエストで使用する User-Agent を設定します。

1. `175 Assign UserAgents` ノードをダブルクリック
2. Code 内の User-Agent リストを編集:
   - **mainDocumentUserAgentList**: メインドキュメント（HTML）用
   - **assetUserAgentList**: アセット（CSS/JS/画像/フォント）用

URLタイプ別の動作:
1. `asset` → アセット用 UA リスト
2. `main_document` → メイン用 UA リスト
3. `exception` → 破棄（出力しない）

3. 「Save」

> 💡 WAF を考慮すると、メインドキュメントとアセットで**同じ User-Agent** を使う方が弾かれにくいです。UA 無しは想定していないため、必ず1つ以上設定してください。
>
> 詳細: [NODE175_USERAGENT_README.md](NODE175_USERAGENT_README.md)

## Step.2 — Request Engine 接続設定

### 設定⑦: #180 Request Engine 種別・エリア・言語の設定

GEO分散リクエストで使用するクラウド・リージョンと Accept-Language（言語）を設定します。

1. `180 RequestEngine Settings` ノードをダブルクリック
2. Code 内の `requestEngineList` を編集:

```javascript
const requestEngineList = [
  {
    type_area: 'AwsLambda_ap-northeast-1',
    accept_language: 'ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7',
  },
];
```

3. 「Save」

| Request Engine | type_area 例 |
|---|---|
| AWS Lambda（東京） | `AwsLambda_ap-northeast-1` |
| Azure Functions（東日本） | `AzureFunctions_japan-east` |
| Cloudflare Workers | `CloudflareWorker_global` |
| GCP Cloud Run（東京） | `GcpCloudFunctions_asia-northeast1` |
| テスト用（n8nから直接） | `DirectRequest` |

> 💡 280系ノードで設定を合わせる必要があります。
>
> 詳細・全リージョン一覧: [NODE180_REQUESTENGINE_README.md](NODE180_REQUESTENGINE_README.md)

### 設定⑧: #225 RequestEngine Switcher

設定⑦で指定した `cloud_type_area` に基づいて、リクエストを適切な #280 系 Request Engine ノードにルーティングします。

1. `225 RequestEngine Switcher` ノードをダブルクリック
2. 「Parameters」の「Routing Rules」で分岐条件を確認・編集

デフォルトでは以下の分岐が設定済みです：

| 出力 | 条件（cloud_type_area） | 接続先ノード |
|-----|------------------------|-------------|
| 0 | `DirectRequest` | 280DirectRequest |
| 1 | `AwsLambda_ap-northeast-1` | 280AWS |
| 2 | `AzureFunctions_japan-east` | 280AZ |
| 3 | `CloudflareWorkers_global` | 280CF |
| 4 | `GcpCloudRun_asia-northeast1` | 280GCP（#235経由） |

> 💡 Request Engine 無しで使う場合は、`280DirectRequest` だけ利用してください。
> 280系ノードを増減させることで、Request Engine をクラウド種類別・エリア別で自由に増減できます。

### 設定⑨: #235 GCP Cloud Run を使う場合のみ

GCP Cloud Run を Request Engine として使用する場合、ID トークン取得のための追加設定が必要です。

1. `235 Get IDtoken From GCP Service Account Access Token` ノードを設定
2. Authentication で `Google Service Account API` の該当の Credential を設定
3. 「Save」

> ⚠️ GCP Cloud Run を使用しない場合、この設定は不要です。
>
> 詳細は [CloudRun_README.md](../EO_Documents/Manuals/py/CloudRun_README.md)、[RE_README.md](../EO_Documents/Manuals/RE_README.md) を参照。

### 設定⑩: #280系 Request Engine URL・Credential設定

n8n から Request Engine へ HTTP リクエストを送信するための URL・Credential を設定します。

1. 使用するクラウドに対応する `#280` 系ノードをダブルクリック:

| ノード名 | クラウド | 認証方式 |
|---|---|---|
| `280AWS` | AWS Lambda | IAM ユーザーのアクセスキー |
| `280AZ` | Azure Functions | 関数キーによる `x-functions-key` ヘッダー |
| `280CF` | Cloudflare Workers | Cloudflare Access (Zero Trust) サービストークン |
| `280GCP` | GCP Cloud Run | OAuth2 Bearer トークン |

2. URL に Request Engine のエンドポイント URL を設定
3. Credential（認証情報）を設定
4. 「Save」

> 💡 1つの Request Engine だけセットアップした場合は、該当するクラウドの `#280` ノードのみ設定すれば動作します。
> 設定⑦の `type_area` と設定⑧の Routing Rules に対応する 280 系ノードが必要です。

## Step.3 — 実行とCSV出力

### #420 JSON to RequestResultsCSV

すべてのノード設定が完了したら、Warmup を実行します。

1. n8n ワークフロー画面で `420 JSON to RequestResultsCSV` ノードの「Execute Step」を押下
2. ワークフロー全体が実行され、Warmup 結果が CSV 形式で出力されます

> 💡 初回は「Test Workflow」で全体の動作を確認してからの実行を推奨します。

## 動作確認

すべてのノード設定が完了したら、ワークフローをテスト実行します。

1. n8n ワークフロー画面で「**Test Workflow**」をクリック
2. 各ノードが順次実行され、結果が表示されます
3. `#280` 系ノード（例: `280AWS`）でレスポンスが返ってくれば成功です

### よくあるエラーと対処

| エラー | 原因 | 対処 |
|---|---|---|
| 401エラー | シークレット不一致 | `.env` の `N8N_EO_REQUEST_SECRET` と各クラウドのシークレット値が一致しているか確認 |
| DNS認証拒否 | DNS TXTレコード不一致 | DNS TXTレコードと #020ノードの `DNSTXT_TOKEN` が一致しているか確認 |
| Warmup対象が0件 | ターゲットURLプレフィックス不一致 | #140 の `REQUEST_TARGET_URL_PREFIXES` がサイトのURLと一致しているか確認 |
| Lambda/Functions実行エラー | コード未デプロイ | GitHub Actions で最新コードをプッシュ、または手動デプロイ |
| Credential エラー | 認証情報の設定ミス | n8n Credentials の Access Key / Secret が正しいか確認 |

## 補足: #110 SimpleUrlList で Step.1 から開始する方法

XMLサイトマップを使わず、URL リストを直接指定して Step.1（HTML解析）から開始することもできます。

1. `110 Step.1 Starter SimpleUrlList` ノードをダブルクリック
2. Code 内の `targetPages` に URL をダブルクォート囲み・カンマ区切りで記述:

```javascript
const targetPages = [
  "https://example.com/page1",
  "https://example.com/page2",
];
```

3. 「Save」
4. `115 Step.1 Separate Starter Dummy` ノードから実行を開始

> 💡 少数ページのみWarmupしたい場合や、テスト時に便利です。

## 関連ドキュメント

- [N8N_WORKFLOW_README.md](N8N_WORKFLOW_README.md) - ワークフロー全体設定
- [NODE180_REQUESTENGINE_README.md](NODE180_REQUESTENGINE_README.md) - Request Engine設定ガイド（type_area・accept_language一覧）
- [NODE175_USERAGENT_README.md](NODE175_USERAGENT_README.md) - User-Agent設定ガイド
- [RE_README.md](../EO_Documents/Manuals/RE_README.md) - Request Engine 全体のセキュリティ設定
