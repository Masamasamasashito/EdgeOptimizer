# n8n ワークフローノード設定ガイド

Request Engine のセットアップ完了後、n8n ワークフローのノードを設定して Edge Optimizer を利用可能にします。

このガイドは**全 Request Engine 共通**です（AWS Lambda / Azure Functions / Cloudflare Workers / GCP Cloud Run）。

> n8n ワークフロー上の**桃色（ピンク）Sticky Note** が設定箇所の目印です。設定1〜9 の番号が振られています。

---

## 目次

- [Step.0 — 起点設定（設定1・設定2）](#step0--起点設定設定1設定2)
- [Step.1 — フィルタリング・バリアント設定（設定3・設定4・設定6）](#step1--フィルタリングバリアント設定設定3設定4設定6)
- [Step.2 — Request Engine 接続設定（設定7・設定8・設定9）](#step2--request-engine-接続設定設定7設定8設定9)
- [Step.3 — 実行とCSV出力](#step3--実行とcsv出力)
- [動作確認](#動作確認)
- [補足: #110 SimpleUrlList で Step.1 から開始する方法](#補足-110-simpleurllist-で-step1-から開始する方法)

---

## Step.0 — 起点設定（設定1・設定2）

### 設定1: #010 XMLサイトマップURL設定

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

### 設定2: #015-020 DNS認証設定

Edge Optimizer は、Warmup対象ドメインの所有権を DNS TXTレコードで検証します（第三者サイトへの不正リクエスト防止）。

**2-1. DNS TXTレコードを追加**

Warmup対象ドメインのDNS設定で、以下のTXTレコードを追加してください：

| レコード名 | タイプ | 値 |
|---|---|---|
| `_eo-auth.example.com` | TXT | `eo-authorized-yourtoken`（任意の文字列） |

複数ドメインを対象とする場合は、各ドメインごとにTXTレコードを設定してください（すべて同じトークン値）：

- `_eo-auth.example.com` → `eo-authorized-yourtoken`
- `_eo-auth.example.org` → `eo-authorized-yourtoken`
- `_eo-auth.sub.example.com` → `eo-authorized-yourtoken`

**2-2. n8n #020ノードのトークンを設定**

1. `020 DNS Auth` ノードをダブルクリック
2. Code 内の `DNSTXT_TOKEN` を、DNS TXTレコードに設定した値と同じ値に変更:

```javascript
const DNSTXT_TOKEN = "eo-authorized-yourtoken"; // ← DNS TXTレコードと同じ値
```

3. 「Save」

**2-3. 設定確認**

```bash
# Linux / macOS
dig TXT _eo-auth.example.com +short

# Windows (PowerShell)
Resolve-DnsName -Name "_eo-auth.example.com" -Type TXT
```

期待される出力: `"eo-authorized-yourtoken"`（設定したトークン値）

> ⚠️ DNS認証に失敗すると「【DNS認証拒否】正当な所有権が確認できません。実行を停止します。」と表示されます。DNSの伝播に時間がかかる場合は数分〜数時間待ってから再試行してください。

---

## Step.1 — フィルタリング・バリアント設定（設定3・設定4・設定6）

### 設定3: #140 ターゲットURLプレフィックス設定

Warmup対象とするURLのプレフィックス（ドメイン＋パス先頭）を設定します。ここで指定したプレフィックスに一致するURLのみがWarmup対象になります。

1. `140` 番台のノード（ターゲットURLプレフィックス設定）をダブルクリック
2. Code 内の `REQUEST_TARGET_URL_PREFIXES` を編集:

```javascript
const REQUEST_TARGET_URL_PREFIXES = [
  'https://example.com',
  // ダブルCDN構成の場合はオリジンドメインも追加
  // 'https://origin.example.com',
];
```

3. 「Save」

> 💡 サイトマップに含まれるURLのうち、ここで指定したプレフィックスに**前方一致**するURLのみがWarmup対象になります。

### 設定4: #155 不要URLパターン設定

Warmup不要なURLや例外URLのパターンを設定して除外します。

1. `155` 番台のノード（不要URLパターン設定）をダブルクリック
2. Code 内の除外対象パターン一覧を編集:

```javascript
// 除外対象パターン一覧（部分一致で除外）
// 例: /wp-json/, /xmlrpc.php, /feed/ など
```

3. 「Save」

> 💡 `/wp-json/`、`/xmlrpc.php`、`/feed/` などCMS系の不要URLや、NitroPackのBlobURLなどを除外できます。

### 設定6: #175 User-Agent 設定

WAFによるブロックを防ぐため、Warmupリクエストで使用するUser-Agentを設定します。

1. `175` 番台のノード（User-Agent付与）をダブルクリック
2. Code 内の User-Agent リストを編集:
   - **mainDocumentUserAgentList**: メインドキュメント（HTML）用
   - **assetUserAgentList**: アセット（CSS/JS/画像/フォント）用

3. 「Save」

> 💡 WAFを考慮すると、メインドキュメントとアセットで**同じUser-Agent**を使う方が弾かれにくいです。UA無しは想定していないため、必ず1つ以上設定してください。
>
> 詳細: [NODE175_USERAGENT_README.md](NODE175_USERAGENT_README.md)

---

## Step.2 — Request Engine 接続設定（設定7・設定8・設定9）

### 設定7: #180 Request Engine 種別・エリア・言語の設定

GEO分散リクエストで使用するクラウド・リージョンとAccept-Language（言語）を設定します。

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

> 詳細・全リージョン一覧: [NODE180_REQUESTENGINE_README.md](NODE180_REQUESTENGINE_README.md)

### 設定8: #280 Request Engine URL設定

n8nからRequest Engineへ HTTP リクエストを送信するためのURL・Credentialを設定します。

1. 使用するクラウドに対応する `#280` 系ノードをダブルクリック:

| ノード名 | クラウド |
|---|---|
| `280AWS` | AWS Lambda |
| `280Azure` | Azure Functions |
| `280CF` | Cloudflare Workers |
| `280GCP` | GCP Cloud Run |

2. URL に Request Engine のエンドポイントURLを設定
3. Credential（認証情報）を設定
4. 「Save」

> 💡 1つの Request Engine だけセットアップした場合は、該当するクラウドの `#280` ノードのみ設定すれば動作します。

### 設定9: #235 GCP Cloud Run を使う場合のみ

GCP Cloud Run をRequest Engineとして使用する場合、IDトークン取得のための追加設定が必要です。

1. `235 Get IDtoken From GCP Service Account Access Token` ノードを設定
2. GCPサービスアカウントのCredentialを設定
3. 「Save」

> ⚠️ GCP Cloud Run を使用しない場合、この設定は不要です。

---

## Step.3 — 実行とCSV出力

### #420 JSON to WarmupHistoryCSV

すべてのノード設定が完了したら、Warmupを実行します。

1. n8n ワークフロー画面で `420 JSON to WarmupHistoryCSV` ノードの「Execute Step」を押下
2. ワークフロー全体が実行され、Warmup結果がCSV形式で出力されます

> 💡 初回は「Test Workflow」で全体の動作を確認してからの実行を推奨します。

---

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

---

## 補足: #110 SimpleUrlList で Step.1 から開始する方法

XMLサイトマップを使わず、URLリストを直接指定してStep.1（HTML解析）から開始することもできます。

1. `110 Step.1 Starter SimpleUrlList` ノードをダブルクリック
2. Code 内の `targetPages` にURLをダブルクォート囲み・カンマ区切りで記述:

```javascript
const targetPages = [
  "https://example.com/page1",
  "https://example.com/page2",
];
```

3. 「Save」
4. `115 Step.1 Separate Starter Dummy` ノードから実行を開始

> 💡 少数ページのみWarmupしたい場合や、テスト時に便利です。

---

## 関連ドキュメント

- [N8N_WORKFLOW_README.md](N8N_WORKFLOW_README.md) - ワークフロー全体設定
- [NODE180_REQUESTENGINE_README.md](NODE180_REQUESTENGINE_README.md) - Request Engine設定ガイド（type_area・accept_language一覧）
- [NODE175_USERAGENT_README.md](NODE175_USERAGENT_README.md) - User-Agent設定ガイド
- [RE_README.md](../RequestEngine/RE_README.md) - Request Engine 全体のセキュリティ設定
