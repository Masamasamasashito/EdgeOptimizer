# Edge Optimizer Request Engine by cloudflare-worker

Cloudflare Github 連携(独自ドメインのサブドメインでWorker作る場合)

## 手順 1: Worker作成

前提：親ドメイン（例: sample.com）が既にCloudflareに登録されており、ネームサーバーが有効になっていること

1. Cloudflareダッシュボードの左メニューから 「Workers & Pages」 をクリック
2. 「アプリケーションを作成する (Create application)」 → 「Hello Worldを開始する」 をクリック
3. Worker name
  - 例: `eo-re-d01-cfworker-global`を入力、「デプロイ (Deploy)」 をクリック
	- この時点では xxx.<Cloudflareアカウント名>.workers.dev という仮のドメインが割り当てられる

`.github/workflows/deploy-to-cf-worker-global.yml`とgithub上のシークレットが設定して有れば、WorkerがCloudflare上に無くても、新規Workerが**カスタムドメイン無し**で作成される。

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
    - 「New repository secret」をクリックし、以下の4つを追加
        1. `EO_CF_WORKER_USER_API_TOKEN_FOR_GITHUB`,手順4でコピーしたユーザーAPIトークン,wranglerデプロイ認証用
        2. `EO_CF_ACCOUNT_ID`,手順4で確認したアカウントID,アカウント識別用
        3. `EO_CF_WORKER_DOMAIN`,Workerのカスタムドメイン（例: `eo-re-d01-cfworker-global.sample.com/*`）,wrangler.toml の routes pattern 用
        4. `EO_CF_WORKER_ZONE_NAME`,親ドメイン（例: `sample.com`）,wrangler.toml の routes zone_name 用

- wrangler.toml は `.github/workflows/deploy-to-cf-worker-global.yml` の中で EOF により動的生成している
- routes の pattern のカスタムドメイン名を GitHub シークレット `EO_CF_WORKER_DOMAIN` から参照する構成

## 手順 6: Workflowファイルの作成

1. プロジェクトのルートディレクトリに、GitHub Actions用の設定ファイルを作成
    - ファイルパス: `.github/workflows/deploy-to-cf-worker-global.yml`
2. 以下を参照。
    - Cloudflare公式のアクション cloudflare/wrangler-action を使用するのが最も簡単で推奨される方法

[.github\workflows\deploy-to-cf-worker-global.yml](.github\workflows\deploy-to-cf-worker-global.yml)

## 手順 7: Cloudflare WorkerでGithubリポジトリを登録

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
11. ルート ディレクトリ:`/RequestEngine/cloudflare_workers/global/funcfiles/`
	- 重要。githubリポジトリ上でWorkerのビルド/デプロイに必要なディレクトリのパスを指定
12. 接続
13. ビルドに Gitリポジトリが表示され、`Git リポジトリにコミットをプッシュして最初のビルドを開始できるようになりました`とでたらOK
14. 監視パスを構築する > `RequestEngine/cloudflare_workers/global/funcfiles/*`を追加

## 手順 8: npm install 実行

1. ローカルのgitリポジトリで `docker compose run --rm cfworker_npm_installer`を実行（ 初期は`node:24-slim`をつかっていた ）。
    - `/RequestEngine/cloudflare_workers/global/funcfiles/`でnode_modulesフォルダの必要なライブラリをnpm installするため。package.jsonと同じ階層で実施する。
    - package-lock.jsonも作成される
    - package-lock.jsonはgitリポジトリにコミットする
    - node_modulesはgitリポジトリにはコミットしない
2. ローカルのエディタを閉じて開きなおす

## 手順 9: 動作確認

1. 作成した .github/workflows/deploy-to-cf-worker-global.yml を含めて、変更をコミットし、GitHubの main ブランチへプッシュ
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
2. 左メニューの Accessコントロール → サービス資格情報 をクリック
3. サービストークンを作成する をクリック
	- サービストークン名（`eo-re-d01-cfworker-global-service-token-for-n8n`）を入力
    - 有効期限：無期限
    - Create Service Token をクリック
    - 重要: ここで表示される Client ID と Client Secret を必ずコピーして控えて。Secretはこの画面を閉じると二度と表示されない

## 手順 12: Cloudflare Access で Worker を保護

Workerのカスタムドメインに対して「Accessアプリケーション」を作成し、サービストークンを持っている場合のみ通す設定

1. Zero Trust ダッシュボードの Accessコントロール → アプリケーション をクリック
2. アプリケーションを追加する →セルフホスト を選択
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

## 手順 13: n8n Credentials登録 と HTTP Requestノードにサービストークン設定

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
  
n8nでWorkerサブドメインとCredentialsをHTTP Requestノードで設定  
  
1. n8n のワークフロー画面で該当するCloudflareのリクエストエンジンのHTTP Requestノードを開く
2. Parameters > URL にCFワーカーで設定したサブドメインを「https://」から始まるURLで末尾に「/」を付けて登録
  - EX) `https://eo-re-d01-cfworker-global.<sample.com>/`
3. Authentication > Generic Credential Typeを選ぶ
4. Generic Auth Type > Custom Authを選ぶ
5. Custom Auth > `EO_RE_CF_HeaderAuth_ServiceToken`を選ぶ

## 手順 14: n8n workflow実行、動作確認

1. Execute workflowを押す
2. n8n workflowが実行される
3. 正常に動作することを確認
    - 420 JSON to WarmupHistoryCSVノードでCSVファイルが生成され、ダウンロード出来ること
    - WarmupHistoryCSVの中にウォームアップリクエストの履歴が記載されていること

# httpsリクエストを受けたWorkerの実行ログ

https://dash.cloudflare.com/606e9bbae0f092fb3070bc34f5eba0f0/workers/services/view/eo-re-d01-cfworker-global/production/observability/logs?workers-observability-view=invocations

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