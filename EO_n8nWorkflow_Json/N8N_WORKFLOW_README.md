# Edge Optimizer n8n Workflow 設定ガイド

このディレクトリには、Edge Optimizer の n8n ワークフロー JSON テンプレートが含まれています。

## ファイル一覧

| ファイル | 説明 |
|---------|------|
| `eo-n8n-workflow-jp.json` | Edge Optimizer メインワークフロー（日本語） |
| `n8n構成図.jpg` | ワークフロー構成図 |
| `N8N_NODE_SETUP.md` | ノード設定ガイド（設定①〜⑩の手順） |
| `NODE175_USERAGENT_README.md` | #175 User-Agent設定ガイド（一覧・サンプル） |
| `NODE180_REQUESTENGINE_README.md` | #180 Request Engine設定ガイド（type_area・accept_language一覧） |

## 1. n8n ユーザー登録

n8n を初めて起動した場合、ユーザー登録が必要です。

1. ブラウザで http://localhost:5678 にアクセス
2. 「Set up n8n」画面が表示される
3. 以下を入力:
   - **Email**: メールアドレス
   - **First Name**: 名前
   - **Last Name**: 姓
   - **Password**: パスワード（8文字以上）
4. 「Next」をクリック
5. 利用規約に同意してセットアップ完了

## 2. ワークフローのインポート

1. n8n にログイン（http://localhost:5678）
2. 右上 オレンジボタン「Create Workflow」→「右上の3点リーダー」→「Import from File」
3. `eo-n8n-workflow-jp.json` を選択してインポート

## 2. Credentials（認証情報）の設定

インポート後、以下いずれかのCredentialsを設定する必要があります。

| Credential名 | 用途 | 設定方法 |
|-------------|------|---------|
| AWS (IAM) | AWS Lambda呼び出し | Access Key ID / Secret Access Key |
| Azure Header Auth | Azure Functions呼び出し | `x-functions-key` ヘッダー |
| GCP Service Account | GCP Cloud Run呼び出し | Service Account JSON Key |
| Cloudflare Access | Cloudflare Workers呼び出し | CF-Access-Client-Id / Secret |

詳細は [RequestEngine/RE_README.md](../RequestEngine/RE_README.md) を参照してください。

## 3. 設定が必要なノード

### Step.0: メインドキュメントURL抽出

| 設定番号 | ノード番号 | ノード名 | 設定内容 |
|---------|----------|---------|---------|
| 設定① | #010 | Step.0 Starter by XML sitemap | XMLサイトマップURLを設定 |
| 設定② | #015-020 | DNS認証ノード | DNS TXTレコードによるドメイン所有権検証（下記参照） |

#### DNS認証ノード（#015-020）の詳細設定

Edge Optimizer は、Warmup対象ドメインの所有権を DNS TXTレコードで検証します。これにより、第三者のサイトへの不正リクエストを防止します。

**1. DNS TXTレコードの作成**

Warmup対象ドメイン（例: `example.com`）のDNS設定で、以下のTXTレコードを追加してください:

| レコード名 | タイプ | 値（任意の認証トークン） |
|-----------|-------|------------------------|
| `_eo-auth.example.com` | TXT | `eo-authorized-sample` |

**注意**: TXTレコードの値は任意の文字列を設定できます。n8n側の `DNSTXT_TOKEN` と同じ値を設定してください。

**2. 複数ドメインを対象とする場合**

各ドメインごとに TXTレコードを設定してください（すべて同じトークン値）:
- `_eo-auth.example.com` → `eo-authorized-sample`
- `_eo-auth.example.org` → `eo-authorized-sample`
- `_eo-auth.sub.example.com` → `eo-authorized-sample`（サブドメインの場合）

**3. DNSレコード設定例（主要プロバイダー）**

| プロバイダー | 設定場所 |
|-------------|---------|
| Cloudflare | DNS > レコード > レコードを追加 > TXT |
| AWS Route 53 | ホストゾーン > レコードを作成 > TXT |
| Google Cloud DNS | Cloud DNS > ゾーン > レコードセットを追加 |
| さくらインターネット | ドメインコントロールパネル > ゾーン編集 |

**4. 設定確認方法**

ターミナルで以下のコマンドを実行して、TXTレコードが正しく設定されているか確認:

```bash
# Linux / macOS
dig TXT _eo-auth.example.com +short

# Windows (PowerShell)
Resolve-DnsName -Name "_eo-auth.example.com" -Type TXT
```

期待される出力: `"eo-authorized-sample"`（設定したトークン値）

**5. n8n側の設定（#020 DNS Auth ノード）**

#020 DNS Auth ノード内のCodeで、認証トークンを設定する必要があります:

```javascript
const DNSTXT_TOKEN = "eo-authorized-sample";  // ← この値を変更
```

この `DNSTXT_TOKEN` の値を、DNS TXTレコードに設定した値と一致させてください。

| 設定箇所 | 設定値 |
|---------|--------|
| DNS TXTレコード | `_eo-auth.example.com` → `your-custom-token` |
| n8n #020ノード | `DNSTXT_TOKEN = "your-custom-token"` |

**6. ワークフロー内での動作**

| ノード | 処理内容 |
|--------|---------|
| #015 DNS Fetch TXT | Google DNS API (`dns.google/resolve`) を使用して `_eo-auth.{domain}` のTXTレコードを取得 |
| #020 DNS Auth | TXTレコードの値が `DNSTXT_TOKEN` と一致するか検証。不一致の場合はエラーで停止 |

**7. 認証エラー時のメッセージ**

DNS認証に失敗すると、以下のエラーが表示されます:
```
【DNS認証拒否】正当な所有権が確認できません。実行を停止します。
```

この場合、以下を確認してください:
- DNS TXTレコードが正しく設定されているか（設定確認方法参照）
- n8n #020ノードの `DNSTXT_TOKEN` 値がDNS TXTレコードと一致しているか
- DNSの伝播に時間がかかっている場合は、数分〜数時間待ってから再試行

### Step.1: アセット抽出・フィルタリング・バリアント設定

| 設定番号 | ノード番号 | ノード名 | 設定内容 | 詳細ガイド |
|---------|----------|---------|---------|-----------|
| 設定③ | #125 | HTTP Req to MainDoc URL locs | Playwright利用の有無を選択 | - |
| 設定④ | #140 | Resource URLs Discovery from DOM | Warmup対象ドメインを設定 | - |
| 設定⑤ | #155 | Excluded Patterns Filter | 除外URLパターンを設定 | - |
| 設定⑥ | #175 | Assign UserAgents | User-Agentリストを設定 | [NODE175_USERAGENT_README.md](NODE175_USERAGENT_README.md) |
| 設定⑦ | #180 | RequestEngine Settings | クラウド・リージョン・言語を設定 | [NODE180_REQUESTENGINE_README.md](NODE180_REQUESTENGINE_README.md) |

#### #175 User-Agent設定の概要

URLタイプ別にWarmupするUser-Agentバリアントを設定します。

```javascript
// 例: iOS Safari と Android Chrome の2バリアント
const mainDocumentUserAgentList = [
  { label: 'ios_safari_17', ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) ...' },
  { label: 'android_chrome_pixel', ua: 'Mozilla/5.0 (Linux; Android 13; Pixel 7) ...' },
];
```

詳細なUser-Agent一覧は [NODE175_USERAGENT_README.md](NODE175_USERAGENT_README.md) を参照。

#### #180 Request Engine設定の概要

GEO分散リクエストで使用するクラウド・リージョンとAccept-Language（言語）を設定します。

```javascript
// 例: AWS東京 + Azure日本東部
const requestEngineList = [
  { type_area: 'AwsLambda_ap-northeast-1', accept_language: 'ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7' },
  { type_area: 'AzureFunctions_japan-east', accept_language: 'ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7' },
];
```

詳細なtype_area・accept_language一覧は [NODE180_REQUESTENGINE_README.md](NODE180_REQUESTENGINE_README.md) を参照。

### Step.2: GEO分散リクエスト

| 設定番号 | ノード番号 | ノード名 | 設定内容 |
|---------|----------|---------|---------|
| 設定⑧ | #225 | RequestEngine Switcher | クラウド別ルーティング設定 |
| 設定⑨ | #235 | Get IDtoken From GCP Service Account | GCP Cloud Run 使用時のみ |
| 設定⑩ | #280AWS | AWS-apne1 RequestEngine | Lambda関数名を設定 |
| 設定⑩ | #280AZ | AZ-japan-east RequestEngine | Azure Functions URLを設定 |
| 設定⑩ | #280CF | CF-global RequestEngine | Cloudflare Workers URLを設定 |
| 設定⑩ | #280GCP | GCP-asia-northeast1 RequestEngine | Cloud Run URLを設定 |
| - | #340 | Random Sleep (ms) | スリープ時間を調整（デフォルト: 1000-3999ms） |

### Step.3: 結果出力

| ノード番号 | ノード名 | 設定内容 |
|----------|---------|---------|
| #420 | JSON to RequestResultsCSV | CSV出力パスを設定 |

## 4. ワークフロー構成概要

```
Step.0 (#001-099): XMLサイトマップからメインドキュメントURL抽出
    ↓
Step.1 (#100-199): Playwrightでアセット抽出、フィルタリング、バリアント設定
    ↓
Step.2 (#200-399): GEO分散リクエスト実行（AWS/Azure/GCP/CF）
    ↓
Step.3 (#400-):    結果をCSV/JSON出力
```

## 5. 初回実行前のチェックリスト

- [ ] n8n Credentials設定完了
- [ ] Request Engine（サーバーレス関数）デプロイ完了
- [ ] 各Request Engineにシークレット設定完了（`N8N_EO_REQUEST_SECRET`と同じ値）
- [ ] DNS TXTレコード設定完了（`_eo-auth.{domain}` に認証トークン設定）
- [ ] n8n #020ノードの `DNSTXT_TOKEN` をDNS TXTレコードと同じ値に設定
- [ ] XMLサイトマップURL設定完了
- [ ] 使用するクラウド・リージョン選択完了

## 6. 関連ドキュメント

- [RE_README.md](../RequestEngine/RE_README.md) - Request Engineセキュリティ設定
- [LAMBDA_CFN_README.md](../RequestEngine/aws_lambda/CFn/LAMBDA_CFN_README.md) - AWS Lambda CFn
- [AZFUNC_BICEP_README.md](../RequestEngine/azure_functions/bicep/AZFUNC_BICEP_README.md) - Azure Bicep
- [RUN_README.md](../RequestEngine/gcp_cloudrun/ane1/RUN_README.md) - GCP Cloud Run
- [CFWORKER_README.md](../RequestEngine/cloudflare_workers/global/CFWORKER_README.md) - Cloudflare Workers

## 7. トラブルシューティング

### ワークフローが動作しない

1. **Credentials確認**: 各クラウドのCredentialsが正しく設定されているか
2. **シークレット照合エラー**: `N8N_EO_REQUEST_SECRET`と各クラウドのシークレットが一致しているか
3. **URL設定**: 各Request EngineノードのURLが正しいか

### トークン検証エラー（401）

- `EO_Infra_Docker/.env`の`N8N_EO_REQUEST_SECRET`と各クラウドのシークレット値が一致しているか確認

詳細は [RE_README.md](../RequestEngine/RE_README.md) のトラブルシューティングセクションを参照。
