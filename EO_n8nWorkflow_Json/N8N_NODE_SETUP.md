# n8n ワークフローノード設定ガイド

Request Engine のセットアップ完了後、n8n ワークフローのノードを設定して Edge Optimizer を利用可能にします。

このガイドは**全 Request Engine 共通**です（AWS Lambda / Azure Functions / Cloudflare Workers / GCP Cloud Run）。

## 目次

- [1. #010 XMLサイトマップURL設定](#1-010-xmlサイトマップurl設定)
- [2. #015-020 DNS認証設定](#2-015-020-dns認証設定)
- [3. #180 Request Engine 設定](#3-180-request-engine-設定)
- [4. 動作確認](#4-動作確認)

---

## 1. #010 XMLサイトマップURL設定

Warmup対象サイトのXMLサイトマップURLを設定します。

1. n8n ワークフロー画面で **`010 Step.0 Starter by XML sitemap`** ノードをダブルクリック
2. Code 内の URL を、Warmup対象サイトのXMLサイトマップURLに変更:
   ```javascript
   // 例: あなたのサイトのサイトマップURL
   const sitemapUrl = "https://example.com/sitemap.xml";
   ```
3. 「Save」

> **💡 ヒント:** サイトマップURLが不明な場合は、`https://あなたのドメイン/sitemap.xml` または `https://あなたのドメイン/sitemap_index.xml` を確認してください。

---

## 2. #015-020 DNS認証設定

Edge Optimizer は、Warmup対象ドメインの所有権を DNS TXTレコードで検証します（第三者サイトへの不正リクエスト防止）。

### 2-1. DNS TXTレコードを追加

Warmup対象ドメインのDNS設定で、以下のTXTレコードを追加してください：

| レコード名 | タイプ | 値 |
|-----------|-------|-----|
| `_eo-auth.example.com` | TXT | `eo-authorized-yourtoken`（任意の文字列） |

複数ドメインを対象とする場合は、各ドメインごとにTXTレコードを設定してください（すべて同じトークン値）：

- `_eo-auth.example.com` → `eo-authorized-yourtoken`
- `_eo-auth.example.org` → `eo-authorized-yourtoken`
- `_eo-auth.sub.example.com` → `eo-authorized-yourtoken`

### 2-2. n8n #020ノードのトークンを設定

1. **`020 DNS Auth`** ノードをダブルクリック
2. Code 内の `DNSTXT_TOKEN` を、DNS TXTレコードに設定した値と同じ値に変更:
   ```javascript
   const DNSTXT_TOKEN = "eo-authorized-yourtoken"; // ← DNS TXTレコードと同じ値
   ```
3. 「Save」

### 2-3. 設定確認

```bash
# Linux / macOS
dig TXT _eo-auth.example.com +short

# Windows (PowerShell)
Resolve-DnsName -Name "_eo-auth.example.com" -Type TXT
```

期待される出力: `"eo-authorized-yourtoken"`（設定したトークン値）

> **⚠️ 認証エラー時:**
> DNS認証に失敗すると「【DNS認証拒否】正当な所有権が確認できません。実行を停止します。」と表示されます。
> DNS TXTレコードと #020ノードの `DNSTXT_TOKEN` が一致しているか確認してください。
> DNSの伝播に時間がかかる場合は、数分〜数時間待ってから再試行してください。

> 詳細: [N8N_WORKFLOW_README.md](N8N_WORKFLOW_README.md) の「DNS認証ノード（#015-020）の詳細設定」参照

---

## 3. #180 Request Engine 設定

GEO分散リクエストで使用するクラウド・リージョンとAccept-Language（言語）を設定します。

1. **`180 RequestEngine Settings`** ノードをダブルクリック
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

> **💡 ヒント:** 1つの Request Engine だけセットアップした場合は、該当するクラウド・リージョンのみを設定すれば動作します。

### type_area の例

| Request Engine | type_area 例 |
|---------------|-------------|
| AWS Lambda（東京） | `AwsLambda_ap-northeast-1` |
| Azure Functions（東日本） | `AzureFunctions_japan-east` |
| Cloudflare Workers | `CloudflareWorker_global` |
| GCP Cloud Run（東京） | `GcpCloudFunctions_asia-northeast1` |
| テスト用（n8nから直接） | `DirectRequest` |

> 全リージョン一覧・複数リージョン設定・言語設定の詳細は [NODE180_REQUESTENGINE_README.md](NODE180_REQUESTENGINE_README.md) を参照してください。

---

## 4. 動作確認

すべてのノード設定が完了したら、ワークフローをテスト実行します。

1. n8n ワークフロー画面で **「Test Workflow」** をクリック
2. 各ノードが順次実行され、結果が表示されます
3. #280 系ノード（例: #280AWS）でレスポンスが返ってくれば成功です

### よくあるエラーと対処

| エラー | 原因 | 対処 |
|-------|------|------|
| **401エラー** | シークレット不一致 | `.env` の `N8N_EO_REQUEST_SECRET` と各クラウドのシークレット値が一致しているか確認 |
| **DNS認証拒否** | DNS TXTレコード不一致 | DNS TXTレコードと #020ノードの `DNSTXT_TOKEN` が一致しているか確認 |
| **Lambda/Functions実行エラー** | コード未デプロイ | GitHub Actions で最新コードをプッシュ、または手動デプロイ |
| **Credential エラー** | 認証情報の設定ミス | n8n Credentials の Access Key / Secret が正しいか確認 |

---

## 関連ドキュメント

- [N8N_WORKFLOW_README.md](N8N_WORKFLOW_README.md) - ワークフロー全体設定
- [NODE180_REQUESTENGINE_README.md](NODE180_REQUESTENGINE_README.md) - Request Engine設定ガイド（type_area・accept_language一覧）
- [NODE175_USERAGENT_README.md](NODE175_USERAGENT_README.md) - User-Agent設定ガイド
- [RE_README.md](../RequestEngine/RE_README.md) - Request Engine 全体のセキュリティ設定
