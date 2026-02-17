# Edge Optimizer Request Engine by cloudflare-worker

Cloudflare Github 連携(独自ドメインのサブドメインでWorker作る場合)

## 手順 1: Worker作成

前提：親ドメイン（例: sample.com）が既にCloudflareに登録されており、ネームサーバーが有効になっていること

1. Cloudflareダッシュボードの左メニューから 「Workers & Pages」 をクリック
2. 「アプリケーションを作成する (Create application)」 → 「Hello Worldを開始する」 をクリック
3. Worker name
  - 例: `eo-re-d01-cfworker-global`を入力、「デプロイ (Deploy)」 をクリック
	- この時点では xxx.<Cloudflareアカウント名>.workers.dev という仮のドメインが割り当てられる

`.github/workflows/deploy-ts-to-cf-worker.yml`とgithub上のシークレットが設定して有れば、WorkerがCloudflare上に無くても、新規Workerが**カスタムドメイン無し**で作成される。

## 手順 2: サブドメインを設定

作成したWorkerの管理画面から設定を行う

1. 「Workers & Pages」 の一覧から、対象のWorkerをクリックして開く
2. 画面上部のタブから 「設定 (Settings)」 をクリック
3. ページ内メニューの 「ドメインとルート (Domains & Routes)」で「+ 追加 (+ Add)」 ボタンをクリック
4. 「カスタムドメイン (Custom Domains)」 を選択 
5. 「ドメイン (Domain)」 の入力欄に、割り当てたいサブドメインを入力
	- 例: `eo-re-d01-cfworker-global.sample.com`
6. 「ドメインを追加 (Add Custom Domain)」 をクリック
7. xxx.<Cloudflareアカウント名>.workers.dev ドメインの3点リーダーをクリック
8. 「ドメインを無効にする」をクリック
9. 「無効にする」をクリック

※ wrangler.toml で `workers_dev = false` を設定しているため、GitHub Actions デプロイ後は自動的に workers.dev ルートが無効化される。上記7〜9は初回手動セットアップ時のみ必要。

## 手順 3: サブドメインWorker作成の完了確認

DNSレコードの画面で確認。

1. Cloudflareが自動的に以下の処理を裏側で行う（数分かかる場合あり）
	- DNSレコードの作成: eo-re-d01-cfworker-global.sample.com のDNSレコード（A/AAAA）を自動生成。
	- SSL証明書の発行: そのサブドメイン用の証明書を発行
2. プロキシステータスが 「プロキシ済み」 になれば完了。
3. ブラウザで https://eo-re-d01-cfworker-global.sample.com にアクセスしてHello World!確認

## 手順 4: Cloudflare ユーザーAPIトークンとアカウントIDの取得

Github ActionsによるWorker自動デプロイを行うため、GitHubにCloudflareへのアクセス権限を与える

1. ユーザーAPIトークン作成
    - Cloudflareダッシュボード「(右上)ユーザー」→「プロフィール」→「APIトークン」
    - 「トークンを作成」**をクリック
    - 「Cloudflare Workers を編集する (Edit Cloudflare Workers)」テンプレートの「使用する」を選択
       - トークン名 の右側にある鉛筆マークをクリック
       - トークン名を変更する　EX) deploy to eo-re-d01-cfworker-global from githubリポジトリ名 yyyymmdd hh:mm
       - 不要権限の削減検証中
    - 特定のアカウントやゾーンに制限したい場合は設定を変更、「概要に進む」→「トークンを作成」をクリック
    - 表示された APIトークン をコピーして控える。この画面を閉じると二度と表示されない
2. アカウントIDの確認:
    - CloudflareのWorkers & Pagesのダッシュボード右側 Account Details で Account ID 確認、控える
    - wrangler whoami コマンドでも取得可能

## 手順 5: GitHubリポジトリへのSecrets設定

1. 取得した認証情報をGitHubリポジトリの環境変数として安全に保存
    - 対象のGitHubリポジトリを開く
    - 「Settings」タブ → 左メニューの「Secrets and variables」 → 「Actions」をクリック
    - 「New repository secret」をクリックし、以下の2つを追加
        1. `EO_CF_WORKER_USER_API_TOKEN_FOR_GITHUB`,手順4でコピーしたユーザーAPIトークン,wranglerデプロイ認証用
        2. `EO_CF_ACCOUNT_ID`,手順4で確認したアカウントID,アカウント識別用

- wrangler.toml は `.github/workflows/deploy-ts-to-cf-worker.yml` の中で EOF により動的生成している
- ルーティングは手順2で設定したカスタムドメインで行うため、wrangler.toml に routes 設定は不要

## 手順 6: Workflowファイルの作成

1. プロジェクトのルートディレクトリに、GitHub Actions用の設定ファイルを作成
    - ファイルパス: `.github/workflows/deploy-ts-to-cf-worker.yml`
2. 以下を参照。
    - Cloudflare公式のアクション cloudflare/wrangler-action を使用するのが最も簡単で推奨される方法

[.github\workflows\deploy-ts-to-cf-worker.yml](.github\workflows\deploy-ts-to-cf-worker.yml)

## 手順 7: Cloudflare WorkerでGithubリポジトリを登録（GitHub Actions運用時は不要）

1. 「Workers & Pages」 の一覧から、対象のWorkerをクリックして開く
2. 画面上部のタブから 「設定 (Settings)」 をクリック
3. ビルド で Gitリポジトリ の接続をクリック
4. 新しいGithub接続
5. Repository access で Only select repositories にて対象リポジトリを選択
6. Save
7. リポジトリに接続 の画面に勝手に戻る
8. リポジトリを選ぶ
9. `main`などのブランチ選ぶ
10. 非本番ブランチのビルド:`無効`
    - 有効にすると、githubリポジトリ上に`cloudflare-workers-and-pages[bot]`によってブランチ作成される。
11. ルート ディレクトリ:`/RequestEngine/cf/workers/ts/funcfiles/`
	- 重要。githubリポジトリ上でWorkerのビルド/デプロイに必要なディレクトリのパスを指定
12. 接続
13. ビルドに Gitリポジトリが表示され、`Git リポジトリにコミットをプッシュして最初のビルドを開始できるようになりました`とでたらOK
14. 監視パスを構築する > `RequestEngine/cf/workers/ts/funcfiles/*`を追加

## localdev/ ディレクトリ（npm install 実行用Docker環境）

`RequestEngine/cf/workers/ts/localdev/` は Cloudflare Workers 用の npm install 実行環境です。

- **用途**: `node:slim` コンテナ内で `funcfiles/package.json` に基づき `npm install` を実行し、`node_modules` を生成
- **サービス名**: `cfworker_npm_installer`
- **ベースイメージ**: `node:slim`
- **本番デプロイ**: GitHub Actions（`.github/workflows/deploy-ts-to-cf-worker.yml`）で Wrangler を使用。この Docker 環境は npm install のみに使用

```
RequestEngine/cf/workers/ts/
├── localdev/
│   ├── Dockerfile           # Node.js イメージ
│   ├── docker-compose.yml   # cfworker_npm_installer サービス定義
│   └── env.example          # Docker イメージ設定テンプレート（cp env.example .env）
└── funcfiles/               # Workers ソースコード（package.json, src/, build.mjs）
```

## 手順 8: npm install 実行

1. `cd RequestEngine/cf/workers/ts/localdev` でlocaldevディレクトリに移動し、`docker compose run --rm cfworker_npm_installer`を実行（ 初期は`node:24-slim`をつかっていた ）。
    - `/RequestEngine/cf/workers/ts/funcfiles/`でnode_modulesフォルダの必要なライブラリをnpm installするため。package.jsonと同じ階層で実施する。
    - package-lock.jsonも作成される
    - package-lock.jsonはgitリポジトリにコミットする
    - node_modulesはgitリポジトリにはコミットしない
2. ローカルのエディタを閉じて開きなおす

## 手順 9: 動作確認

1. 作成した .github/workflows/deploy-ts-to-cf-worker.yml を含めて、変更をコミットし、GitHubの main ブランチへプッシュ
2. GitHubリポジトリの 「Actions」 タブを開く
3. 「Deploy to Cloudflare Workers」というワークフローが実行されていることを確認する
4. 緑色のチェックマーク（Success）がつけばデプロイ完了

## 手順 10: 照合用リクエストシークレット設定

n8n保持の照合用リクエストシークレット(docker-compose.ymlの環境変数`N8N_EO_REQUEST_SECRET`の値)とCloudflare Workers(RequestEngine)保持の照合用リクエストシークレットが一致しないと、Warmupリクエスト出来ない様になっている。

1. 「Workers & Pages」 の一覧から、対象のWorkerをクリックして開く
2. 画面上部のタブから 「設定 (Settings)」 をクリック
3. 「変数とシークレット」 >  「+追加」
4. タイプ > シークレット
4. 変数名 > `CFWORKER_REQUEST_SECRET`
5. 値 > `EO_Infra_Docker\.env`ファイルの`N8N_EO_REQUEST_SECRET`の値をコピーして設定
6. デプロイ

**更新方法**:「ローテート」をクリック、新しい値を入力、「デプロイ」をクリック。

(おそらく不要)n8nコンテナ再起動、CF worker再デプロイ。

## 手順 11: Cloudflare Access サービストークン作成

n8nに持たせる「通行手形（IDとパスワード）」を作成し、Cloudflare Access ( Zero Trust ) でWorkerを保護する

1. Cloudflare Zero Trust ダッシュボード にアクセス
2. 左メニューの Accessコントロール > サービス資格情報 をクリック
3. サービストークンを追加する をクリック
	- サービストークン名（`eo-re-d01-cfworker-global-service-token-for-n8n`）を入力
    - 有効期限：無期限
    - Create Service Token をクリック
    - 重要: ここで表示される Client ID と Client Secret を必ずコピーして控えて。Secretはこの画面を閉じると二度と表示されない
4. 保存 をクリック

## 手順 12: Cloudflare Access で Worker を保護

Workerのカスタムドメインに対して「Accessアプリケーション」を作成し、サービストークンを持っている場合のみ通す設定

1. Zero Trust ダッシュボードの Accessコントロール → アプリケーション をクリック
2. アプリケーションを追加する > セルフホスト > 選択する をクリック
3. 基本情報（そのままスルー）
4. Access ポリシー (重要。先にポリシー作る):
	- 新しいポリシーを作成する
	    - ポリシー名: `eo-re-d01-cfworker-global Allow n8n HTTPSrequests ServiceToken`
	    - アクション: Service Auth （※ここ重要です。Allowではありません）

	    - ルールを追加する:
	    	- 包含 
	    	- セレクター: Service Token を選択
	        - 値: サービストークン名（`eo-re-d01-cfworker-global-service-token-for-n8n`）を選択
		- ポリシーテスター
	 		- 1 ユーザー (100%) は ブロック済みです　と出ればOK
	    - 保存をクリック
5. 基本情報に戻って入力を再開
	- Application name: 任意（例: `eo-re-d01-cfworker-global-n8n-auth-app`）
    - セッション時間:15分（Warmupリクエストでは、あまり関係ない）
    - パブリック ホスト名を追加（Workerのカスタムドメインと完全に一致させる）:
		- Subdomain: `eo-re-d01-cfworker-global`
    	- Domain: <sample.com>
    - 既存のポリシーを選択
    - `eo-re-d01-cfworker-global Allow n8n HTTPSrequests ServiceToken`を選ぶ
    - 確認 をクリック
	- ポリシーテスター
		- 1 ユーザー (100%) は ブロック済みです　と出ればOK
  - ログイン方法
		- 利用可能なすべての ID プロバイダーを受け入れる:有効
    - 次へ
    - 次へ
    - 保存

https://eo-re-d01-cfworker-global.<sample.com> にアクセス
```
Forbidden

You don't have permission to view this.

Please contact your system administrator.

View details
```
となったらOK。n8n workflowまわすと、`Error ・ Cloudflare Access`というタイトルページになること。
単純にカスタムドメインをブラウザで叩いて、アクセス出来ないことを確認。

## 手順 13: n8n Credentials登録

n8nからリクエストエンジンにリクエストを送る際、リクエストヘッダにサービストークン情報を載せる設定  
  
n8n Credentials登録  

1. n8n 左サイドバー「Personal」 > 「Credentials」 > 「Create Credential」
2. Credential Type: Custom Auth (account) を選択
3. Name: `EO_RE_CF_HeaderAuth_ServiceToken` など
4. 以下のようにJSON登録
```
{
  "headers": {
    "CF-Access-Client-Id": "手順11のClient ID",
    "CF-Access-Client-Secret": "手順11のClient Secret"
  }
}
```

## 手順 14: n8n 280CF-global RequestEngine ZeroTrustノードでWorkerサブドメインとCredentials設定  
  
1. n8n のワークフロー画面で280CF-global RequestEngine ZeroTrustノードのCloudflareリクエストエンジンのHTTP Requestノードを開く
2. Parameters > URL にCFワーカーで設定したカスタムドメインを「https://」から始まるURLで末尾に「/」を付けて登録
  - EX) `https://eo-re-d01-cfworker-global.<sample.com>/`
3. Authentication > Generic Credential Typeを選ぶ
4. Generic Auth Type > Custom Authを選ぶ
5. Custom Auth > `EO_RE_CF_HeaderAuth_ServiceToken`を選ぶ

## 手順 15: n8n workflow実行、動作確認

1. Execute workflowを押す
2. n8n workflowが実行される
3. 正常に動作することを確認
    - 420 JSON to WarmupHistoryCSVノードでCSVファイルが生成され、ダウンロード出来ること
    - WarmupHistoryCSVの中にウォームアップリクエストの履歴が記載されていること

# httpsリクエストを受けたWorkerの実行ログ

`https://dash.cloudflare.com/<CF_ACCOUNT_ID>/workers/services/view/eo-re-d01-cfworker-global/production/observability/logs?workers-observability-view=invocations`

Cloudflareダッシュボード > Workers & Pages > eo-re-d01-cfworker-global > Observability > Logs からもアクセス可能。

# ファイル構成（Python版と同一構造）

Python版 Request Engine（AWS Lambda / Azure Functions / GCP Cloud Run）の `common/` + プラットフォーム固有ハンドラー構造を TypeScript で再現。

## Python版（参考）

```
RequestEngine/common/                          ← 全プラットフォーム共通（Python）
├── request_engine_core.py                     ← 共通コアロジック
└── extensions/
    └── _ext_security.py                       ← security 拡張

RequestEngine/gcp/cloudrun/py/funcfiles/     ← プラットフォーム固有（例: GCP）
├── _01_imports.py                             ← imports
└── _03_gcp_cloudrun_handler.py                ← ハンドラー
```

Python版はワークフローで `cat` コマンドにより `_ext_*.py` を直接結合（中間ファイルなし）。

## CF Workers版

```
RequestEngine/common/ts/                                ← CF Workers共通
├── request_engine_core.ts                              ← 共通コアロジック（Python版 request_engine_core.py 相当）
└── extensions/
    └── _ext_security.ts                                ← security 拡張（Python版 _ext_security.py 相当）

RequestEngine/cf/workers/ts/funcfiles/src/  ← プラットフォーム固有
├── _01_types.ts                                        ← 型定義・インターフェース
├── _02_extensions.ts                                   ← ワークフローで動的生成（.gitignore対象）
├── _03_cf_worker_handler.ts                            ← メインハンドラー
└── worker.ts                                           ← エントリポイント（re-export のみ）
```

**ビルドの仕組み**: esbuild（`RequestEngine/cf/workers/ts/funcfiles/build.mjs`）が `bundle: true` で全 `import` を解決し、`dist/worker.js` に1ファイルにバンドル。Python版の `cat` 結合と同等の最終成果物。

## `_02_extensions.ts` の動的生成

`_02_extensions.ts` はリポジトリに含まれず（`.gitignore` 対象）、`.github/workflows/deploy-ts-to-cf-worker.yml` のデプロイ時に動的生成される。Python版のワークフローにおける `_ext_*.py` の条件付き cat 結合と同等。

生成例（`ext_security=true` の場合）:
```typescript
// Auto-generated by deploy-ts-to-cf-worker.yml
// Extension imports that register themselves with the extension registry.
// Matches Python: GitHub Actions cat-merge of extensions/_ext_*.py

import "../../../common/extensions/_ext_security";
```

## Extension の追加方法

1. `RequestEngine/common/ts/extensions/_ext_<name>.ts` を作成
2. ファイル内で `registerExtension()` を呼び出す（自己登録パターン）
3. `.github/workflows/deploy-ts-to-cf-worker.yml` に以下を追加:
   - `workflow_dispatch.inputs` に `ext_<name>` ブール入力を追加
   - `Generate _02_extensions.ts` ステップに条件付き import 行を追加

# デプロイワークフロー入力パラメータ

`.github/workflows/deploy-ts-to-cf-worker.yml` の `workflow_dispatch` 入力:

| 入力名 | 型 | デフォルト | 説明 |
|--------|------|-----------|------|
| `ext_security` | boolean | `true` | Security Extension（`eo.security.*`）の有効/無効 |

GitHub Actions > Run workflow から手動実行時に、Extension の ON/OFF を切り替え可能。

# warmup対象URLについて

ユーザーエージェントをモバイルとデスクトップに別けてウォームアップリクエストを行う必要あり。

1. XMLサイトマップのURL一覧へのWarmup
2. XMLサイトマップで確認できるURL一覧に対してサブリンクとなるcss/javascript/画像/フォントのURL一覧を抽出、重複を排除、サブリンクとなるcss/javascript/画像/フォントのURL一覧へのWarmup

# warmup対象URLsの生成

現状は2パターン可能

## 1. XMLサイトマップを登録

- 010 Step.0 Starter by XML sitemapノード
```
[
  {
    "Website": "https://sample.com/wp-sitemap.xml"
  }
]
```

### ユースケース

サイト全体をWarmupする場合など。

## 2.httpsのURLでダブルクォート囲み、カンマ区切りで入力

- 110 Step.1 Starter SimpleUrlListノード
```
// ▼ Step.1 (HTML解析) から始めたいURLリストをここに記述
const targetPages = [
  "https://sample.com/",
  //"https://sample.com/services/",
];
```

1. 記載後、Step.0の最終ノードとStep.1の最初のノードを切断
2. Step.1の115ノードに110ノードを接続
3. Execute workflowを押す

### ユースケース

広告キャンペーン開始前にランディングページ、コンバージョンに貢献しやすい重点ページをピンポイントでWarmupする場合など。

### 注意点

Cloudflare製のリクエストエンジンは、エリア指定できないglobalであるため、n8nを実行したエリアに近いCDN EdgeがWarmupされる。

# その他

1. オリジンホストのレート制限
    1. ランダム秒間リクエスト機能
    2. ユーザーエージェント分散機能

# Workers fetch API の制約事項（プロトコル/TLS情報）

Cloudflare Workers の Request Engine では、以下のメタデータキーに固定値を出力する。

| キー | 出力値 |
|------|--------|
| `eo.meta.http-protocol-version` | 固定値（下記参照） |
| `eo.meta.tls-version` | 固定値（下記参照） |

**固定値**: `"unavailable: Workers fetch API does not expose outgoing connection info (https://developers.cloudflare.com/workers/runtime-apis/request/#incomingrequestcfproperties)"`

## 理由

Workers の `request.cf.httpProtocol` / `request.cf.tlsVersion` はクライアント→Worker間（incoming）の接続情報のみ提供する。Worker→ターゲットURL間（outgoing）の `fetch()` API レスポンスにはプロトコル/TLS情報が含まれない。

Python版 Request Engine（AWS Lambda / Azure Functions / GCP Cloud Run）では `requests` ライブラリの `response.raw` オブジェクトから outgoing のプロトコル/TLS情報を取得可能だが、Workers の `fetch()` API にはこの機能がない。

## 公式ドキュメント

- https://developers.cloudflare.com/workers/runtime-apis/request/#incomingrequestcfproperties
  - `request.cf` は incoming request の情報のみ
- https://developers.cloudflare.com/workers/runtime-apis/response/
  - Response オブジェクトにプロトコル/TLS プロパティなし
- https://developers.cloudflare.com/workers/runtime-apis/fetch/
  - fetch() API に outgoing 接続情報の公開なし

# 【参考】wpfixfast製 cf workers に投げるリクエスト1URLだけシンプル

- Cloudflare Workersで日本のTier1 NRTをCache Warm
    - https://4649-24.com/core-web-vitals/warm-japan-nrt-by-cf-worker/