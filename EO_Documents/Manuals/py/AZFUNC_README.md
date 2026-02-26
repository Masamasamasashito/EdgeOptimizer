# 【事前準備】Azure管理グループ作成

Azureの「グローバル管理者権限」ユーザーはデフォルトでは、管理グループの閲覧すらできないので、「管理グループ」操作権の付与から。

## 「管理グループ」操作権の付与

Entra ID「グローバル管理者」ロールのユーザーで行う必要がある。

1. Azure にサインイン > Entra ID > プロパティ > 画面を一番下までスクロール「Azure リソースのアクセス管理」
2. [はい] に切り替えて、[保存] をクリック

※「グローバル管理者権限」のユーザーに「ユーザー アクセス管理者 (User Access Administrator)」が付与され「全管理グループの支配権」へと昇華されます。

## 「ユーザー アクセス管理者 (User Access Administrator)」確認

1. Azure > サブスクリプション > サブスクリプション > アクセス制御(IAM) > ロールの割り当て
2. 対象のユーザーの役割が「ユーザー  アクセス管理者 (User Access Administrator)」になっていることを確認
3. 対象のユーザーのスコープが「ルート（継承済み）」になっていることを確認

## 管理グループ作成

1. Azure Portal > Resource Manager(管理グループ) > (左サイドバー)組織 > 管理グループ > 「+ 作成」 > 管理グループの作成
2. 命名(ID) `eo-re-d1-azure-mgmt-grp`
3. 作成後、反映するまで少し待つ（遅い）。

## サブスクリプション を管理グループに紐付け

既存もしくは、新規作成したサブスクリプションを管理グループに紐付ける。
今後、この管理グループでサブスクリプションの権限を制限する。
1. Azure Portal > Resource Manager(管理グループ) > (左サイドバー)組織 > 管理グループ > `eo-re-d1-azure-mgmt-grp`
2. 「+ サブスクリプションの追加」
3. 紐付けたいサブスクリプションを選択 > 保存

## ホワイトリスト作成

まだ、作成中であるため、直下の「管理グループで(サブスクリプションIDを)ポリシー制限」を行ってください。

1. Azure > ポリシー > (左サイドバー)作成 > 定義 > 「+ ポリシー定義」
2. スコープ > `eo-re-d1-azure-mgmt-grp` を選択
3. 定義の種類 > ポリシー
4. ポリシーの種類

   - 名前: `eo-re-d1-allowed-locations`
   - 説明: `Allow only specific locations for resources in eo-re-d1-azure-mgmt-grp`
   - カテゴリ: `EdgeOptimizer`

## 管理グループで(サブスクリプションIDを)ポリシー制限

1. Azure Portal > Resource Manager(管理グループ) > (左サイドバー)組織 > 管理グループ > `eo-re-d1-azure-mgmt-grp`
2. (左サイドバー)ガバナンス > ポリシー > 「ポリシーの割り当て」をクリック
3. (タブ)基本情報 > スコープ > `eo-re-d1-azure-mgmt-grp` を選択
4. 基本情報 > ポリシー定義 > `Allowed resource types` を選択 > 追加
5. 次へ(パラメーター)
6. リソースの種類 > 以下を選択（検索機能が非常に非力。sitesなどの最後尾の名称で検索する）
    - 関数アプリ
        - Microsoft.Web　の sites
        - Functionsの本体
    - App Service プラン
        - Microsoft.Web の serverfarms
        - Functionsを実行するサーバー代わりの土台
    - キー コンテナー
        - Microsoft.KeyVault の vaults
        - パスワードや機密情報を守る金庫です。
    - ストレージ アカウント
        - Microsoft.Storage の storageAccounts
        - Functionsのコード保存や実行ログの記録に必須です。
    - 画像外: 監視用（必要なら）
        - Microsoft.Insights/components	Application Insights
        - エラー検知やログ収集に必要です。
7. 次へ(修復)
8. 次へ(マネージドID) > チェックを入れない
    - 【参考】ポリシー自体が「リソースをいじる」場合、ポリシーに「操作権限」を与える必要があり、その「身分証」としてマネージドIDが使われる
9. 次へ(コンプライアンス非対応のメッセージ)
10. コンプライアンス非対応のメッセージ　に以下を入力
    - `[Azure Policy制限] プロジェクト管理ルールにより、許可されたリソースタイプ以外はデプロイできません。追加が必要な場合、該当管理グループのポリシー設定を確認してください。`
11. レビューと作成 > 作成

【参考】割り当て名：使用できるリソースの種類
- スコープ `eo-re-d1-azure-mgmt-grp`
- 定義の種類 `ポリシー`
- パラメーターID `listOfResourceTypesAllowed`
- パラメーター名 `Allowed resource types`
- パラメーター値 `["Microsoft.Web/sites","Microsoft.Web/serverFarms","Microsoft.KeyVault/vaults","Microsoft.Storage/storageAccounts"]`

## 管理グループで(リージョン)ポリシー制限

リソースの作成先リージョンを Japan East のみに制限し、意図しないリージョンへのデプロイを防止する。

1. Azure Portal > Resource Manager(管理グループ) > (左サイドバー)組織 > 管理グループ > `eo-re-d1-azure-mgmt-grp`
2. (左サイドバー)ガバナンス > ポリシー > 「ポリシーの割り当て」をクリック
3. (タブ)基本情報 > スコープ > `eo-re-d1-azure-mgmt-grp` を選択
4. 基本情報 > ポリシー定義 > `Allowed locations` を選択 > 追加
5. 次へ(パラメーター)
6. 許可されている場所 > 以下を選択
    - `Japan East`
    - （必要に応じて `Japan West` も追加）
7. 次へ(修復)
8. 次へ(マネージドID) > チェックを入れない
9. 次へ(コンプライアンス非対応のメッセージ)
10. コンプライアンス非対応のメッセージ　に以下を入力
    - `[Azure Policy制限] プロジェクト管理ルールにより、Japan East 以外のリージョンへのデプロイは許可されていません。追加が必要な場合、該当管理グループのポリシー設定を確認してください。`
11. 次へ > 作成

【参考】割り当て名：許可されている場所
- スコープ `eo-re-d1-azure-mgmt-grp`
- 定義の種類 `ポリシー`
- パラメーターID `listOfAllowedLocations`
- パラメーター名 `Allowed locations`
- パラメーター値 `["japaneast"]`

# Step.1 Azureリソースグループ作成

`eo-re-d1-resource-grp-jpe`

- eoはEdge Optimizerの略称
- reはrequest engineの略称
- d1はdev01の略称。
- jpeはjapan eastの略称

GCPのサービスアカウント名30文字制限が根底にあり、短縮化している。

# Azure Functions 製 Request Engine 関数アプリ作成

`eo-re-d1-funcapp-jpe`

1. リソースグループ: `eo-re-d1-resource-grp-jpe`
2. 概要 > リソース > 作成 > Marketplace > 「Azureサービスのみ』にチェックを入れる > 関数アプリ > 作成 > 関数アプリ
3. ホスティング オプションの選択 > フレックス従量課金 > 選択

   **ホスティングオプションの違いと Request Engine 向けのおすすめ**

   | オプション | 概要・特徴 | 課金 | コールドスタート | 実行時間上限 | VNet | スケール上限 |
   |-----------|------------|------|------------------|--------------|------|--------------|
   | **①フレックス従量課金** (Flex Consumption) | 従量課金の拡張版。常時使用可能インスタンスでコールドスタート軽減、関数ごとスケール、メモリ(512MB/2GB/4GB)選択可。Linux のみ。 | 実行時間＋常時使用時はベースライン課金。無料枠あり。 | 常時使用可能インスタンスで軽減可能 | 実質なし※ | ✅ | 最大1000 |
   | **②Functions Premium** | 常時ウォームなインスタンスでコールドスタートなし。VNet・カスタム Linux コンテナ対応。 | インスタンスのコア秒・メモリ。最低1インスタンス常駐。 | なし | 無制限(60分保証) | ✅ | 20〜100 |
   | **③App Service** (専用プラン) | App Service プラン上で常時稼働。Web アプリと同一プランで混在可能。手動/自動スケール。 | プラン料金（常時稼働分）。 | ほぼなし | 無制限 | ✅ | 10〜30(通常)/100(ASE) |
   | **④Container Apps 環境** | Azure Container Apps 上でコンテナとして関数を実行。他マイクロサービスと同一基盤。 | vCPU秒・メモリ秒・リクエスト数。0スケール時は請求なし。 | あり（ゼロスケール時） | コンテナ基盤に依存 | ✅ | コンテナ基盤の制限 |
   | **⑤従量課金** (Consumption) | 従来のサーバーレス従量課金。実行中のみ課金、ゼロスケール。 | 実行時間・回数のみ。無料枠あり。 | あり | **最大10分** | ❌ | 200(Windows)/100(Linux) |

   ※HTTP トリガーは Azure Load Balancer により応答まで最大約 230 秒の制約あり。長時間処理は非同期パターン検討。

   **Request Engine におすすめのプラン: ①フレックス従量課金**

   - **理由**: Cache Warmup 用の HTTP トリガー・バースト負荷に合い、従量課金のまま「遅延を抑えたい」要望に対応しやすい。
   - 常時使用可能インスタンスでコールドスタートを抑えつつ、使わないときは従量課金でコストを押さえられる。
   - VNet 統合が使えるため、将来的にプライベート通信や他サービスの制限付きアクセスにも対応しやすい。
   - 実行時間上限が実質ないため、n8n からの長時間リクエストにも対応しやすい（②Premium も同様で、常時低レイテンシが必須なら検討可）。

4. 関数アプリ名: `eo-re-d1-funcapp-jpe`
    - 文字数制限有：43文字まで
5. リージョン > Japan East > 選択
6. 基本情報
- リソース名: `eo-re-d1-funcapp-jpe`  
- 提供元: Microsoft / Azure Functions  
- 安全な一意の既定のホスト名: 有効  
- リージョン: Japan East  
- ランタイムスタック: Python 3.13  
- インスタンスサイズ: 512 MB  
- ゾーン冗長: 無効
「次: Storage」をクリック
7. Storage
- ストレージアカウント: 新規作成
- ストレージアカウント名: `eored1storage`
    - 24文字以下
    - 数字と英小文字のみ
- 診断設定
    - Blob Storage 診断設定:後で構成する(カスタムコントロール推奨)
- 「次: Azure OpenAI」をクリック
8. Azure OpenAI
- Azure OpenAI を有効にする > 無効(チェックを付けない)
- 「次: ネットワーク」をクリック
9. ネットワーク
- パブリック アクセスを有効にする　オン
- 仮想ネットワーク統合を有効にする　オフ
- 「次: 監視」をクリック
10. 監視
- Application Insights を有効にする: いいえ
  - **ログ方針について**: EOアーキテクチャに基づくログ方針は後述の「ログ方針」セクションを参照してください
- 「次: デプロイと認証」をクリック
11. デプロイ
- 継続的デプロイ: 無効化
    - 自動で作ると.github/workflows/deploy.ymlファイルのファイルパスを指定できないため、ここでは無効化、後で手動で設定する。
- 認証の設定
    - 基本認証: 無効にする。※後で手動で設定する。
- 「次: 認証」をクリック
12. 認証
- リソース認証
    - ホストストレージ（AzureWebJobsStorage）:`eored1storage`
        - 認証の種類: シークレット
    - デプロイストレージ:`app-package-eo-re-d1-funcapp-jpe-xxxxxx`
        - 認証の種類: シークレット
- 「次: タグ」をクリック
13. タグ
- 設定しない
- 「次: 確認および作成」をクリック
14. 確認及び作成
- 下部で[Automation のテンプレートをダウンロードする]をクリック
- ダウンロードをクリック
- template.zipをダウンロード出来たことを確認
    - `-eo-azfuncapp-yyyymmdd`など語尾をリネームしておくと、後で識別しやすい。
- ダウンロード画面の右上の「✕」をクリックして閉じる
- 「作成」をクリック
- 「デプロイが進行中です」と表示されるので、しばらく待つ。
- デプロイが完了すると、「デプロイが成功しました」と表示される。
- 「デプロイの詳細」をクリック
- 作成されたリソースの一覧が表示される。
- 「次の手順」
- 「リソースに移動」をクリック

## App Service プラン確認

1. リソースグループ > `eo-re-d1-resource-grp-jpe` > 概要 > リソース
2. App Service プランを確認
    - `ASP-eored1resourcegrpjpe-xxxx`

# 関数アプリの関数作成

- ローカルで作成した関数アプリの関数のコードをAzureにデプロイする。
- **初回デプロイもGitHub Actionsから可能です**（Function Appが既に作成されていることが前提）
- Azureの画面上のGUIで直でソースコード編集はできない。

# Azure CLI　と　Azure Functions Core Tools (v4)　のローカルインストール

**注意**: [azfunc_builder](localdev/docker-compose.yml)のdockerコンテナにはAzure CLI (`az`コマンド) はインストールされていません。`az login`などのAzure CLIコマンドはコンテナ外（ホストマシン）で実行してください。funcコマンドはコンテナ内で実行できます。

## PowerShell Azure CLI
```
# インストール（必ず、インストール後にターミナル・PowerShell・エディタ再起動。Path通しは不要）
winget install --exact --id Microsoft.AzureCLI
# ログイン（ローカルで実行）
az login
az account show
az version

# 自動アップデートを有効化（確認プロンプトあり）。おそらく管理者じゃなくても大丈夫。
az config set auto-upgrade.enable=yes

# プロンプトなしで完全に自動化したい場合
az config set auto-upgrade.prompt=no

# Azure CLI 本体に加えて「拡張機能のアップグレード」や「旧バージョンの自動削除」などを含む、より広い意味のアップグレードコマンド
az upgrade --all --yes
```

- アップデート結構長い時間かかる。
- Setup Wizardが表示されるにで、指示にしたがって進める。


## Azure Functions Core Toolsインストール/更新
ローカルでfuncコマンドを使えるようにした。

- [https://github.com/Azure/azure-functions-core-tools](https://github.com/Azure/azure-functions-core-tools) で　`func-cli-x64.msi`　ダウンロードできる

```
# Azure Functions Core Toolsバージョン確認
func --version

# インストール/更新
winget install Microsoft.Azure.FunctionsCoreTools
```
# localdev/ ディレクトリ（Azure Functions ローカル開発用Docker環境）

`RequestEngine/azure/functions/py/localdev/` は Azure Functions ローカル開発用のDocker環境です。

- **用途**: `python:slim-bookworm` ベースに Azure Functions Core Tools（`func` CLI）をインストールしたコンテナで、`func start` によるローカルテストが可能
- **サービス名**: `azfunc_builder`
- **ベースイメージ**: `python:slim-bookworm` + Azure Functions Core Tools v4
- **ポート**: `7071`（Azure Functions デフォルト）
- **本番デプロイ**: GitHub Actions（`.github/workflows/deploy-py-to-az-function.yml`）で実行。この Docker 環境はローカル開発のみに使用

```
RequestEngine/azure/functions/py/
├── localdev/
│   ├── Dockerfile           # Python + func CLI インストール済みイメージ
│   ├── docker-compose.yml   # azfunc_builder サービス定義
│   └── env.example          # Docker イメージ・ポート設定テンプレート（cp env.example .env）
└── funcfiles/               # Azure Functions コード（function_app.py, host.json, requirements.txt）
```

# ローカルDockerでAzure Functions 初期化/開発環境構築

- [Dockerfile](localdev/Dockerfile)
- [docker-compose.yml](localdev/docker-compose.yml)
- [env.example](localdev/env.example)

## ローカルDocker起動と関数作成

### ⚠️ 重要: 初回セットアップ時のみの手順

**以下の手順は、開発を開始する最初の一回のみ実行してください。**
**既に`funcfiles/`ディレクトリに開発済の3ファイル`host.json`、`function_app.py`、`requirements.txt`などが存在する場合は、この手順をスキップしてください。**
**`func init . --python`を実行すると、既存のファイルが上書きされる可能性があります。**
**開発済3ファイルなどが有る場合に、`func init . --python`を実行したい場合、既存ファイルを退避してから実行してください。**
### 初回セットアップ手順(基本的にリポジトリクローン時は不要。手順4以降を実行してください。)

- `cd RequestEngine\azure\functions\py\localdev`
- `mkdir ../funcfiles`
- `cp env.example .env`
- .env を編集する
- イメージビルド（コンテナ常駐`docker compose up -d`は、今回は使わない）
  - `docker compose build`
      - **【重要】`docker compose build`は、初回セットアップ時またはDockerfileを変更した場合のみ実行してください。**
      - **既にdockerイメージが存在する場合は、この手順をスキップして構いません。**
      - **`docker compose build`を実行しても、`funcfiles/`ディレクトリの内容（`host.json`、`function_app.py`、`requirements.txt`）は消えません。**
      - 【参考】（デフォルト）Docker Image 命名規則: {プロジェクト名}-{サービス名}（ハイフンで結合）
        - プロジェクト名: localdev（docker-compose.ymlがあるディレクトリ名）
        - docker compose サービス名: azfunc_builder
        - 結果: localdev-azfunc_builder
- コンテナ中に入る
  - `docker compose run --rm azfunc_builder bash`
  - `func --version`
  - `python --version`
- Azure FuncCoreTools でPythonプロジェクト作成/初期化（**初回セットアップ時のみ**）
  - `func init . --python`
    - **【警告】このコマンドは初回セットアップ時のみ実行してください。**
    - **既に`funcfiles/`に`host.json`、`function_app.py`、`requirements.txt`が存在する場合は、このコマンドを実行しないでください。**
    - **`func init . --python`を実行すると、既存のファイルが上書きされる可能性があります。**
    - **開発済3ファイルなどが有る場合に、`func init . --python`を実行したい場合、既存ファイルを退避してから実行してください。**
    - **開発済3ファイルなどを退避する方法**
      - `mv funcfiles/ funcfiles.backup/`
      - `func init . --python`
    - ローカルにPythonインストールしてないとfuncコケるため、Dockerfileでコンテナ内にてfunc使えるようにしてある
  - 以下の3ファイルを`funcfiles/`ディレクトリに配置
    - `host.json`
    - `function_app.py`
    - `requirements.txt`
      - 【注意】`host.json`の`Microsoft.Azure.Functions.ExtensionBundle`のバージョンは、`funcfiles/`で`func init . --python`の結果を確認、最新となるように記載。他は上書きでOK
  - (必要であれば)作成されたプロジェクトの中に関数アプリの関数を1つ追加。基本的に不要
    - `func new --name requestengine_func --template "HTTP trigger"`
    - Auth Level
    - 「1. FUNCTION」を選択する。URLクエリパラメータで関数キーを付与する必要あり。

### 2回目以降の開発手順

既に`funcfiles/`ディレクトリにファイルが存在する場合：

1. `cd RequestEngine\azure\functions\py\localdev`
2. コンテナ中に入る
   - `docker compose run --rm azfunc_builder bash`
3. 開発作業
   - `funcfiles/`内のファイル（`function_app.py`、`host.json`、`requirements.txt`）を編集
   - ローカルでテスト: `func start`
4. **`func init . --python`は実行しないでください**（既存ファイルが上書きされます）

### `docker compose build`を再実行する場合

以下の場合のみ`docker compose build`を再実行してください：
- Dockerfileを変更した場合
- イメージを再ビルドする必要がある場合

**`docker compose build`を実行しても、`funcfiles/`ディレクトリの内容は消えません。**（ボリュームマウントのため）

【参考】ビルドキャッシュ削除
`docker builder prune`  

## シークレット設定

1. Azure > キーコンテナー（Key Vault）> 作成
2. サブスクリプション
    - 従量課金
3. リソースグループ
    - `eo-re-d1-resource-grp-jpe`
4. Key Vault 名
    - `eo-re-d1-kv-jpe`
5. 地域
    - `Japan East`
6. 価格レベル
    - `標準（Standard）`...ソフトウェアベースの場合。
    - Premiumは、HSM(Hardware Security Module)の場合。
    - 基本的に標準を選ぶ。
7. 削除されたコンテナーを保持する日数
    - 7 （最小）
8. 消去保護
    - 消去保護を無効にする
9. 確認および作成
10. 作成

## 確認画面

| 項目                         | 値                                                 |
|------------------------------|----------------------------------------------------|
| 基本                         |                                                    |
| サブスクリプション           | 従量課金                                           |
| リソース グループ            | eo-re-d1-resource-grp-jpe   |
| Key Vault 名                 | eo-re-d1-kv-jpe |
| 地域                         | Japan East                                         |
| 価格レベル                   | Standard                                           |
| 論理的な削除                 | 有効                                              |
| 保持期間中の消去保護         | 無効                                              |
| 削除されたコンテナーの保持日数 | 7 日                                              |
| アクセス構成                 |                                                    |
| Azure Virtual Machines（展開用） | 無効                                           |
| Azure Resource Manager（テンプレート展開用） | 無効                   |
| Azure Disk Encryption（ボリューム暗号化用） | 無効                     |
| アクセス許可モデル           | Azure ロールベースのアクセス制御                  |
| ネットワーク                 |                                                    |
| 接続方法                     | パブリック エンドポイント（すべてのネットワーク） |

## Function App用「システム割り当てマネージドID」（サービス プリンシパル）を有効化

関数アプリ(Function App)のオブジェクト (プリンシパル) IDを有効にする。

1. 該当の関数にいく
2. 設定 > ID
3. システム割り当て済み
4. 状態
5. オンにする
6. 保存
7. はい

## キーコンテナ(Key Vault)のアクセス構成モードの確認

1. 該当のキーコンテナにいく
2. アクセスポリシー
3. 「ロールベースのアクセス制御」であることを確認する。以下のようなメッセージが表示されていればOK
```
アクセス ポリシーを利用できません。
このキー コンテナーのアクセス構成は、ロールベースのアクセス制御に設定されています。アクセス ポリシーを追加または管理するには、アクセス制御 (IAM) ページに移動してください。
```

## Azure RBAC(ロールベースのアクセス制御)で Key Vault に Function App の オブジェクト (プリンシパル) ID に対する権限割り当て

1. 該当のキーコンテナにいく
2. アクセス制御 (IAM)
3. 「+ 追加」>「ロールの割り当ての追加」
4. `キー コンテナー シークレット ユーザー`（スペース等も含んで検索）を選択
5. 次へ
6. 選択されたロール > キー コンテナー シークレット ユーザー であること。
7. (タブ)メンバー > アクセスの割り当て先 > マネージド ID
8. メンバー > +メンバーを選択する > マネージドID で 関数アプリ を選択 > 該当する関数アプリ`eo-re-d1-funcapp-jpe`を選択する
9. メンバー > 名前 に 選択した関数アプリ`eo-re-d1-funcapp-jpe`が表示されていること。
10. Description にメンテナンス向けに、目的、背景、対象リソース、理由、設定日、設定者　などを入力
    ```
    目的: Azure Functions Request Engine が Key Vault から照合用リクエストシークレットを取得するため
    背景: セキュアな照合用リクエストシークレット管理のため Key Vault を使用
    対象リソース: eo-re-d1-kv-jpe
    理由: N8N_EO_REQUEST_SECRET と同じ値を Key Vault から取得し、n8nとリクエストエンジンで生成した各トークンを照合する必要があるため
    設定日: yyyy-mm-dd hh:mm
    設定者: [Your Name/Team]
    ```
11. レビューと割り当て　をクリック
12. 表示された内容を確認
13. もう一回　レビューと割り当て　をクリック

## 割り当て出来たか、確認

1. 該当のキーコンテナにいく
2. (左サイドバー)アクセス制御 (IAM)
3. ロールの割り当て
4. (タブ)すべて
5. 一覧で、キーコンテナーシークレットユーザーに該当の関数アプリ名`eo-re-d1-funcapp-jpe`、役割に`キー コンテナー シークレット ユーザー`が有ればOK

## Azure内でシークレット作成する作業者にキーコンテナ “データプレーン権限” を付与

Key Vault には 2 種類の権限層がある

| 種類                           | 内容                                   |
| ---------------------------- | ------------------------------------ |
| **管理プレーン（Management Plane）** | Key Vault の作成、削除、設定変更など              |
| **データプレーン（Data Plane）**      | シークレットの Get / List / Set / Delete など |

- Azureの管理者は、管理プレーン権限のみしか持ってない。
- データプレーン権限の付与する必要あり。

やり方
1. Key Vault > 該当するキーコンテナー > アクセス制御 (IAM)
2. 「ロールの割り当て」
3. 「+ 追加」> 「ロールの割り当ての追加」
4. 「ロール」タブ
5. `キー コンテナー シークレット責任者`を選択 > 次へ
6. 「メンバー」タブ
7. 選択されたロール > `キー コンテナー シークレット責任者` を確認
8. アクセスの割り当て先 > ユーザー、グループ、またはサービス プリンシパル
9. メンバー >  +メンバーを選択する > メンバーを選択する > シークレットを書き込む作業者を割り当てる
10. 選択をクリック
11. Description にメンテナンス向けに、目的、背景、対象リソース、理由、設定日、設定者　などを入力
    ```
    目的: Azure Functions Request Engine が Key Vault からシークレットを取得する。そのシークレットを登録するため。
    背景: セキュアなシークレット管理のため Key Vault を使用
    対象リソース: eo-re-d1-kv-jpe
    理由: N8N_EO_REQUEST_SECRET を Key Vault から取得する必要があるため
    設定日: yyyy-mm-dd hh:mm
    設定者: [Your Name/Team]
    ```
12. メンバーの名前に作業者が表示されたことを確認
13. レビューと割り当て　をクリック
14. 表示された内容を確認
15. もう一回　レビューと割り当て　をクリック

## キーコンテナー(Key Vault)にシークレットを作成

この操作は RBAC で許可されていません。ロールの割り当てが最近変更された場合は、ロールの割り当てが有効になるまで数分お待ちください。
と表示されている。

1. 該当するキーコンテナー`eo-re-d1-kv-jpe`にいく
2. オブジェクト > シークレット
3. 上部の「+ 生成/インポート」をクリック
4. アップロードオプション > 手動
5. 名前（シークレット名に使用できるのは、英数字とダッシュのみ）
    - `AZFUNC-REQUEST-SECRET`
6. シークレット値
    - `EO_Infra_Docker\.env`ファイルの`N8N_EO_REQUEST_SECRET`の値をコピーして設定
7. コンテンツの種類
    - リクエストエンジンがリクエストを送るためのシークレット
    ```
    目的: Azure Functions Request Engine が コード内でn8n生成トークン検証を行う、検証でKeyVaultから取得した照合用リクエストシークレットを使い照合するため。
    背景: リクエストエンジンでトークン検証を行うため
    対象リソース: eo-re-d1-kv-jpe　の　AZFUNC-REQUEST-SECRET
    設定日: yyyy-mm-dd hh:mm
    設定者: [Your Name/Team]
    ```
8. 有効
    - はい
9. 作成
10. 該当するキーコンテナー`eo-re-d1-kv-jpe`の「概要」で、コンテナーのURL`https://eo-re-d1-kv-jpe.vault.azure.net/`を取得。
    - シークレット識別子(URL) ではないので注意

**更新方法**:「+ 新しいバージョン」をクリック、新しい値を入力、「作成」をクリックするとシークレット値を変更できる。古いバージョンの保管は無料。

## Function App のアプリケーション設定に EO_AZ_RE_KEYVAULT_URL を追加

**重要**: GitHub Actionsでデプロイする場合、`local.settings.json`に`EO_AZ_RE_KEYVAULT_URL`を記載することで、自動的にアプリケーション設定として設定されます。手動での設定は不要です。

### GitHub Actionsでの自動設定（推奨）

GitHub Actionsのワークフローが、デプロイ前に`local.settings.json`を自動生成し、`EO_AZ_RE_KEYVAULT_URL`を含めます。

**必要な設定**:
1. GitHubリポジトリ → Settings → Secrets and variables → Actions
2. 「New repository secret」をクリック
3. シークレット名: `EO_AZ_RE_KEYVAULT_URL`
4. 値: Key Vault(コンテナー)のURL（語尾のスラッシュ不要。例: `https://eo-re-d1-kv-jpe.vault.azure.net`）
5. 「Add secret」をクリック

**セキュリティについて**:
- `EO_AZ_RE_KEYVAULT_URL`はKey VaultのURLだけで、シークレットではありません
- しかし、GitHub Secretsに保存することで、リポジトリに直接含めることなく管理できます
- デプロイ時に`local.settings.json`が自動生成され、アプリケーション設定として設定されます

### Azure Portalから手動で設定する場合（初回のみ、またはトラブルシューティング時）

GitHub Actionsを使用しない場合、または初回設定時：

1. Azure Portal → Function App (`eo-re-d1-funcapp-jpe`)
2. 左サイドバー → **設定** → **環境変数** → **アプリ設定** タブ
3. **+ 追加** をクリック
4. 以下の値を設定：
   - **名前**: `EO_AZ_RE_KEYVAULT_URL`
   - **値**: Key VaultのURI（語尾のスラッシュ不要。例: `https://eo-re-d1-kv-jpe.vault.azure.net`）
5. **適用** をクリック

**注意**: GitHub Actionsでデプロイする場合、`local.settings.json`に`EO_AZ_RE_KEYVAULT_URL`が含まれていないと、デプロイ時に既存の設定が削除される可能性があります。必ずGitHub Secretsに`EO_AZ_RE_KEYVAULT_URL`を設定してください。

# ローカルDockerで一度ビルド／起動チェック

```
cd RequestEngine\azure\functions\py\localdev
docker compose run --rm azfunc_builder bash
func start
```

# Azure ログイン

階層構造イメージ
```
Microsoftアカウント（個人用） / 組織アカウント（= ログインID）
      ↓
Microsoft Entra ID (Azure AD)テナント・・・ ドメイン名（XXXXXX.onmicrosoft.com）
      ↓
Azure Plan(従量課金)サブスクリプション
      ↓
リソースグループ（フォルダ）
      ↓
リソース（Function App, Key Vault, etc）
```

課金アカウント (MCA) のログイン方法（コンテナの外でpwsh7で行う）
```
# コンテナの中から抜ける
exit

# ログイン確認
az account show
az login --tenant TENANT_ID
```

# GitHub Actions による自動デプロイ

## 手順 1: Azure AD アプリケーション（サービスプリンシパル）の作成

GitHub ActionsからAzure Functionsにデプロイするため、Azure ADアプリケーションを作成し、OIDC認証を設定する

### 新規作成する場合

1. Azure Portal → Microsoft Entra ID → 概要 → +追加 → アプリを登録 → 新規登録
2. 名前: `eo-ghactions-deploy-entra-app-azfunc-jpe` など
3. サポートされているアカウントの種類: **この組織ディレクトリのみに含まれるアカウント** を選択
   - ⚠️ 「個人用 Microsoft アカウントのみ」は選択しない（OIDC認証でエラーになる）
4. リダイレクト URI: 設定不要（OIDC認証のため）
5. 登録をクリック
6. アプリケーション（クライアント）ID をコピーして控える（GitHub Secretsの`EO_AZ_FUNC_JPE_DEPLOY_ENTRA_APP_ID_FOR_GITHUB`に使用）
7. ディレクトリ（テナント）ID をコピーして控える（GitHub Secretsの`EO_AZ_TENANT_ID`に使用）
8. サブスクリプションID をコピーして控える（GitHub Secretsの`EO_AZURE_SUBSCRIPTION_ID`に使用）

### 既存のアプリケーションの設定を変更する場合（「個人用Microsoftアカウントのみ」から変更）

既存のアプリケーションが「個人用Microsoftアカウントのみ」に設定されている場合、マニフェストを編集して変更する：

1. Azure Portal
2. `eo-ghactions-deploy-entra-app-azfunc-jpe` を検索
3. 左サイドバー → **マニフェスト** をクリック
4. `signInAudience` プロパティを探す
5. 値を `"AzureADMyOrg"` に変更（現在は `"PersonalMicrosoftAccount"` になっている）
6. **保存** をクリック

`eo-ghactions-deploy-entra-app-azfunc-jpe`までのたどり着く手順
1. Entra ID
2. 左サイドバー > 管理 > アプリの登録
3. (タブ)すべてのアプリケーション
4. 検索ボックスに`eo-ghactions-deploy-entra-app-azfunc-jpe`を入力

### サービスプリンシパルの作成（エラー `AADSTS7000229` が発生する場合）

Azure ADアプリケーションに対応するサービスプリンシパルが存在しない場合、以下のコマンドで作成する：

```bash
# Azure CLIでログイン
az login

# サービスプリンシパルを作成（APPLICATION_IDはアプリケーション（クライアント）ID）
az ad sp create --id <APPLICATION_ID>
```

例：
```bash
az ad sp create --id 12345678-1234-1234-1234-123456789abc
```

**注意**: サービスプリンシパルの作成には数分かかる場合があります。作成後、GitHub Actionsのワークフローを再実行してください。

## 手順 2: フェデレーション資格情報の設定（OIDC認証）

1. 作成したアプリケーション
   - `eo-ghactions-deploy-entra-app-azfunc-jpe`で検索
2. (左サイドバー)概要 > 基本 > クライアントの視覚情報 > 証明書またはシークレットの追加
3. (タブ)フェデレーション資格情報 > 資格情報の追加
4. フェデレーション資格情報のシナリオ > Azure リソースをデプロイする Github Actions > を選択
5. 組織: GitHubのユーザー名または組織名
6. リポジトリ: `<Githubリポジトリ名>`（実際のリポジトリ名に置き換え）
7. エンティティ型: ブランチ
8. Github ブランチ名: `main`
9. 名前: `eo-azfunc-jpe-ghactions-main-deploy-federation` など
10. 説明:
    ```
    目的: GitHub Actions mainブランチからAzure Functionsへのデプロイフェデレーション用
    対象リソース: eo-azfunc-jpe-ghactions-main-deploy-federation
    設定日: yyyy-mm-dd hh:mm
    設定者: [Your Name/Team]
    ```
11. 追加をクリック

**重要**: 
1ブランチしか適用できないので、ブランチごとにEntraアプリ`eo-ghactions-deploy-entra-app-azfunc-jpe`の視覚情報作成が必要

## 手順 3: Azure RBAC でサービスプリンシパルにデプロイ権限を付与（リソースグループレベル）

GitHub ActionsからOIDC認証でログインするため、サービスプリンシパル（Azure ADアプリケーション）にリソースグループへの権限を付与する。

**推奨**: リソースグループレベルで権限を付与します。最小権限の原則に従い、必要なリソースグループのみに権限を付与できます。

1. Azure Portal → リソースグループ (`eo-re-d1-resource-grp-jpe`) → アクセス制御 (IAM)
2. 「+ 追加」→「ロールの割り当ての追加」
3. ロール: `Web サイト共同作成者` を選択
4. 次へ
5. (タブ)メンバー → アクセスの割り当て先 → **ユーザー、グループ、またはサービス プリンシパル**
6. メンバー → +メンバーを選択する
7. 検索ボックスに `eo-ghactions-deploy-entra-app-azfunc-jpe` を入力して検索
8. 該当のサービスプリンシパルを選択 → 選択
9. Description にメンテナンス向けに、目的、背景、対象リソース、理由、設定日、設定者　などを入力
    ```
    目的: GitHub ActionsからAzure Functionsへのデプロイ用。Entraアプリにリソースグループへの権限を付与するため。
    対象リソース: eo-ghactions-deploy-entra-app-azfunc-jpe
    設定日: yyyy-mm-dd hh:mm
    設定者: [Your Name/Team]
    ```
10. レビューと割り当て → レビューと割り当て

**注意**: 権限の反映には数分かかる場合があります。設定後、GitHub Actionsのワークフローを再実行してください。

## 手順 4: GitHub リポジトリへの Secrets 設定

1. GitHubリポジトリ → Settings → Secrets and variables → Actions
2. 「New repository secret」をクリックし、以下の3つを追加：

| シークレット名 | 値 | 説明 |
|--------------|-----|------|
| `EO_AZ_FUNC_JPE_DEPLOY_ENTRA_APP_ID_FOR_GITHUB` | 上記で取得したアプリケーション（クライアント）ID | Azure ADアプリケーションのClient ID |
| `EO_AZ_TENANT_ID` | 上記で取得したディレクトリ（テナント）ID | Azure ADテナントID |
| `EO_AZURE_SUBSCRIPTION_ID` | AzureサブスクリプションID | デプロイ先のサブスクリプションID |
| `EO_AZ_RE_KEYVAULT_URL` | Key VaultのURI（語尾のスラッシュ不要。例: `https://eo-re-d1-kv-jpe.vault.azure.net`） | Key VaultのURI（デプロイ時に`local.settings.json`に含まれ、アプリケーション設定として自動設定されます） |

## 手順 5: ワークフローファイルの確認

`.github/workflows/deploy-to-az-function-jpe.yml` が正しく配置されていることを確認

**重要な設定**:
- ワークフローは `func azure functionapp publish` コマンドを使用してデプロイします
- Python v2モデル（`func.FunctionApp()`）に対応しています
- OIDC認証を使用してAzureにログインします

## 手順 6: 初回デプロイと動作確認

### 初回デプロイ

1. `RequestEngine/azure/functions/py/funcfiles/function_app.py`、`requirements.txt`、または`host.json`を変更
2. `main`ブランチにプッシュ
3. GitHubリポジトリの「Actions」タブを開く
4. 「Deploy Azure Functions」ワークフローが実行されていることを確認
5. ワークフローが成功（緑色のチェックマーク）することを確認
6. Azure Portalで確認:
   - Function App (`eo-re-d1-funcapp-jpe`) → **Functions**
   - `requestengine_func` 関数が表示されていることを確認

### 通常のデプロイ（コード変更時）

1. `RequestEngine/azure/functions/py/funcfiles/` ディレクトリ内のファイルを変更
2. `main`ブランチにプッシュ
3. GitHub Actionsが自動的にデプロイを実行
4. デプロイ完了後、Azure Portalで関数が更新されていることを確認

**注意**: 
- 初回デプロイもGitHub Actionsから実行可能です（Function Appが既に作成されていることが前提）
- ローカルからの直接デプロイはトラブルシューティング時のみ使用してください

## トラブルシューティング

### エラー: "Encountered an error (InternalServerError) from host runtime"

このエラーは、Function Appの実行時に内部エラーが発生したことを示します。以下の手順で原因を特定してください。

#### 1. ログの確認

Azure Portalでログを確認：

1. Azure Portal → Function App (`eo-re-d1-funcapp-jpe`)
2. 左サイドバー → **監視** → **ログストリーム** をクリック
3. リアルタイムログを確認してエラーメッセージを特定

または、**監視** → **ログ** から Application Insights のログを確認

#### 2. 環境変数の確認

`EO_AZ_RE_KEYVAULT_URL` が正しく設定されているか確認：

1. Azure Portal → Function App (`eo-re-d1-funcapp-jpe`)
2. 左サイドバー → **設定** → **環境変数** → **アプリ設定**
3. `EO_AZ_RE_KEYVAULT_URL` が存在し、正しいKey Vault URLが設定されているか確認
   - 形式: `https://<KeyVault名>.vault.azure.net`（語尾のスラッシュ不要）
   - 例: `https://eo-re-d1-kv-jpe.vault.azure.net`

#### 3. Key Vaultへのアクセス権限の確認

Function AppのマネージドIDがKey Vaultにアクセスできるか確認：

1. Azure Portal → Key Vault → アクセス制御 (IAM) → ロールの割り当て → このサブスクリプションにおける割り当ての数 
2. Function AppのマネージドIDに「キー コンテナー シークレット ユーザー」ロールが割り当てられているか確認
3. 割り当てられていない場合は、手順「Azure RBAC(ロールベースのアクセス制御)で Key Vault に Function App の オブジェクト (プリンシパル) ID に対する権限割り当て」を実行

#### 4. 依存関係の確認

`requirements.txt` のパッケージが正しくインストールされているか確認：

1. Azure Portal → Function App → **開発ツール** → **高度なツール (Kudu)** → **移動**
2. **Debug console** → **CMD** を選択
3. `site/wwwroot` に移動
4. `pip list` でインストールされているパッケージを確認

必要なパッケージ：
- `azure-functions`
- `requests`
- `azure-identity`
- `azure-keyvault-secrets`

#### 5. コードの構文エラーの確認

ローカルでコードをテスト：

```bash
cd RequestEngine/azure/functions/py/funcfiles
python -m py_compile function_app.py
```

#### 6. 関数の再デプロイ

上記を確認しても解決しない場合、関数を再デプロイ：

**方法1: GitHub Actionsから再デプロイ（推奨）**

該当ファイルを変更して`main`ブランチにプッシュすると、自動的にデプロイされます。

**方法2: ローカルから直接デプロイ（トラブルシューティング用）**

GitHub Actionsでのデプロイが失敗する場合のトラブルシューティングとして、ローカルから直接デプロイ：

```bash
cd RequestEngine/azure/functions/py/funcfiles
func azure functionapp publish eo-re-d1-funcapp-jpe
```

**注意**: 通常はGitHub Actionsからデプロイするため、この方法はトラブルシューティング時のみ使用してください。

### エラー: "The client does not have authorization to perform action"

- 手順3のRBAC権限設定を確認
- Function Appのリソースグループに対する権限も確認

### エラー: "Failed to get secret from Key Vault"

- Function Appのシステム割り当てマネージドIDが有効になっているか確認
- Key Vaultのアクセス制御（IAM）で、Function AppのマネージドIDに「キー コンテナー シークレット ユーザー」ロールが割り当てられているか確認
- 環境変数 `EO_AZ_RE_KEYVAULT_URL` が正しく設定されているか確認

### エラー: "OIDC token exchange failed"

- 手順2のフェデレーション資格情報の設定を確認
- リポジトリ名、ブランチ名が正しいか確認

### エラー: n8n から呼ぶと 401 Unauthorized（body が空・JSON が返らない）

n8n の `280AZ-japan-east RequestEngine KeyVault` ノードで Azure Functions を呼んだときに、`statusCode: 401`, `statusMessage: "Unauthorized"` のみが返り、body が空（または EO のコードが返す `INVALID_TOKEN` などの JSON が出ない）場合、**Function Key がリクエストに含まれていない、または誤っている**ため、Azure が関数コードに到達する前に 401 を返しています。

**対処手順**:

1. Azure Portal で該当の **関数アプリ** (`eo-re-d1-funcapp-jpe`) → **関数** → **requestengine_func** を開く。
2. 関数の詳細画面で **「Get Function URL」**（関数の URL の取得）をクリックする。
3. キー選択のドロップダウンが表示されます。次のいずれかが出ます：
   - **`_master` (ホスト キー)** … 管理用。n8n からの通常呼び出しには使わない。
   - **`default` (ホスト キー)** … 関数アプリ全体に効く。動作するが権限が広い。
   - **`default` (ファンクション キー)** … この関数専用。**n8n から呼ぶときはここを選ぶ。**
4. **`default` (ファンクション キー)** を選択し、表示された **完全な URL**（`https://.../api/requestengine_func?code=xxxxx...` の形）をコピーする。
5. n8n の **280AZ-japan-east RequestEngine KeyVault** ノードを開き、**URL** に上記の URL をそのまま貼り付ける（`?code=...` まで含める）。  
   別設定で「Header Auth」の `x-functions-key` にだけキーを入れている場合は、**URL が `?code=...` 付きの完全形になっているか**を確認する。
6. ワークフローを再実行する。この段階で 401 が解消され、200 または EO トークン検証による 401（`INVALID_TOKEN` 等の JSON）が返るようになります。

**まとめ**: n8n 用には **「Get Function URL」で `default` (ファンクション キー) を選んだ URL** を使う。

# ローカルからAzure Functionsへの直接デプロイ（Functions Core Tools）コンテナの外で行う

**注意**: 通常はGitHub Actionsから自動デプロイされます。この方法はトラブルシューティング時のみ使用してください。

## 前提条件

1. Azure CLIがインストールされていること
2. Azure Functions Core Tools (v4) がインストールされていること
3. Azureにログインしていること（`az login`）

## デプロイ手順

```bash
cd RequestEngine\azure\functions\py\funcfiles
func azure functionapp publish eo-re-d1-funcapp-jpe --python
```

**重要なポイント**:
- `--python`フラグはPython v2モデル（`func.FunctionApp()`）を使用する場合に必須です
- デプロイ前に、`requirements.txt`の依存関係がインストールされていることを確認してください

# キーコンテナアクセス確認

```
az keyvault secret list --vault-name <KeyVault名>
```

シークレット中身

```
az keyvault secret show --vault-name <キーコンテナ(Key vault)名前> --name <シークレット名前>
```

ビルドしてコンテナに入る
```
docker compose build

docker compose run --rm azfunc_builder bash
# docker compose run はデフォルトでは ports 設定を無視するため上記ではなく、以下コマンドで入る
docker compose run --rm --service-ports azfunc_builder bash
```

rootになったことを確認し、requestsをコンテナ内でinstall
```
pip install -r requirements.txt
```
func startする

```
func start
```

以下が見えれば成功

```
Functions:

        requestengine_func: [POST] http://localhost:7071/api/requestengine_func

```

別ターミナルでcurl出来ることを確認する
```
curl.exe -X POST http://localhost:7071/api/requestengine_func -H "Content-Type: application/json" -d '{"data": {"url": "https://example.com", "token": "<YOUR_TOKEN>", "httpRequestNumber": 1, "httpRequestUUID": "550e8400-e29b-41d4-a716-446655440000", "httpRequestRoundID": 1737123456}}'
```

**注意**: 
- `token`は`SHA-256(url + N8N_EO_REQUEST_SECRET)`で計算する必要があります
  - **計算方法**:
    1. `url`と`N8N_EO_REQUEST_SECRET`を文字列連結（間に区切り文字なし）
    2. UTF-8でエンコード
    3. SHA-256ハッシュを計算
    4. 16進数文字列（hexdigest）として返す（64文字）
  - **実装例（Python）**:
    ```python
    import hashlib
    url = "https://example.com"
    secret = "my-secret-key"  # N8N_EO_REQUEST_SECRET の値
    token = hashlib.sha256(f"{url}{secret}".encode()).hexdigest()
    # 結果: "a1b2c3d4e5f6..." (64文字の16進数文字列)
    ```
  - **実装例（n8n Codeノード）**:
    ```javascript
    const url = "https://example.com";
    const secret = $env.N8N_EO_REQUEST_SECRET;
    const crypto = require('crypto');
    const token = crypto.createHash('sha256').update(url + secret).digest('hex');
    ```
  - **生成AIへのプロンプト例（トークン計算からPowerShell curlテストまで）**:
    ```
    以下の手順で、Azure Functions Request Engine のトークンを計算し、PowerShellでcurlコマンドを実行してテストしてください：
    
    【ステップ1: SHA-256トークンの計算】
    
    【計算条件】
    - URL: https://sample.com
    - シークレット: <YOUR_N8N_EO_REQUEST_SECRET>（実際のN8N_EO_REQUEST_SECRETの値に置き換えてください）
    
    【計算手順】
    1. URLとシークレットを文字列連結（間に区切り文字なし）
       例: "https://sample.com" + "your-secret-key" = "https://sample.comyour-secret-key"
    2. 連結した文字列をUTF-8でエンコード
    3. SHA-256ハッシュを計算
    4. 16進数文字列（hexdigest）として返す（64文字、小文字）
    
    【実装例（Python）】
    import hashlib
    url = "https://sample.com"
    secret = "your-secret-key"  # 実際のN8N_EO_REQUEST_SECRETの値に置き換え
    token = hashlib.sha256(f"{url}{secret}".encode()).hexdigest()
    print(token)  # 64文字の16進数文字列を出力
    
    【ステップ2: 計算結果の確認】
    - 出力されたトークンが64文字の16進数文字列（小文字）であることを確認
    - 例: "af82dadb6a6c64df4ee2c577e9039918d6af1cdcd6ec5ee749bd608966881c1c"
    
    【ステップ3: Azure Functions Function Keyの取得手順】
    
    Azure PortalからFunction Keyを取得する手順：
    
    1. Azure Portal (https://portal.azure.com/) にログインします
    
    2. 左側のメニューから「リソースグループ」を選択するか、検索バーで「リソースグループ」を検索します
    
    3. リソースグループ一覧から `eo-re-d1-resource-grp-jpe` をクリックします
    
    4. リソース一覧から、関数アプリ `eo-re-d1-funcapp-jpe` をクリックします
    
    5. 関数アプリの詳細画面で、左側のメニューから「関数」を選択します
    
    6. 関数一覧から、目的の関数名 `requestengine_func` をクリックします
    
    7. 関数の詳細画面で、左側のメニューから「関数キー (Function Keys)」を選択します
    
    8. 関数キーの一覧が表示されます。以下のいずれかを選択します：
       - **推奨**: 名前が `default` のキーを使用（関数専用のキー）
       - または、既存のキーがない場合は「+ 新しい関数キー」をクリックして新規作成
    
    9. キー名が `default` のキーの「値」列をクリックしてコピーします（表示された場合は「クリックして表示」をクリック）
    
    10. コピーしたFunction Keyの値をメモします（後で`<YOUR_FUNCTION_KEY>`に置き換えます）
    
    ⚠️ **重要な注意事項**:
    - 「関数キー (Function Keys)」セクションのキーを使用してください
    - 「ホストキー (Host Keys)」セクションにもキーが表示されますが、これは関数アプリ全体に適用されるキーです
    - セキュリティの観点から、特定の関数 (`requestengine_func`) にのみ適用される「関数キー (Function Keys)」のキーを使用することを推奨します
    
    【ステップ4: PowerShell curlテストコマンドの完成形を作成】
    
    以下の情報を基に、PowerShellで実行可能なcurlテストコマンドの完成形を作成してください：
    
    - Function URL: https://eo-re-d1-funcapp-jpe-<ランダム文字列>.japaneast-01.azurewebsites.net/api/requestengine_func
    - Function Key: <YOUR_FUNCTION_KEY>（ステップ3で取得したFunction Keyに置き換える）
    - 計算したトークン: <CALCULATED_TOKEN>（ステップ1で計算したトークンに置き換える）
    - テストURL: https://sample.com
    
    以下の形式で、実行可能なPowerShellコマンドの完成形を出力してください：
    
    ```powershell
    # 変数の設定
    $functionUrl = "https://eo-re-d1-funcapp-jpe-<ランダム文字列>.japaneast-01.azurewebsites.net/api/requestengine_func"
    $functionKey = "<YOUR_FUNCTION_KEY>"  # 人間がAzure Portalから取得したFunction Keyに置き換える
    $token = "<CALCULATED_TOKEN>"  # ステップ1で計算したトークンに置き換える
    
    # JSONデータの準備（PowerShell変数を使用してエスケープ問題を回避）
    $jsonData = @{
        data = @{
            url = "https://sample.com"
            token = $token
            headers = @{}
            httpRequestNumber = 1
            httpRequestUUID = "550e8400-e29b-41d4-a716-446655440000"
            httpRequestRoundID = 1737123456
            urltype = "main_document"  # オプショナル: "main_document", "asset", "exception"
        }
    } | ConvertTo-Json -Depth 10 -Compress
    
    # curlコマンドの実行（人間が実行する）
    curl.exe -X POST $functionUrl `
        -H "Content-Type: application/json" `
        -H "x-functions-key: $functionKey" `
        -d $jsonData `
        -v
    ```
    
    【注意】
    - 生成AIはコマンドの完成形を作成するだけで、実際の実行は人間が行います
    - `<YOUR_FUNCTION_KEY>`と`<CALCULATED_TOKEN>`は、人間が実際の値に置き換えてから実行してください
    
    【ステップ5: 人間が実行後のレスポンス確認】
    - 成功時: HTTP 200 OK と共にJSONレスポンスが返る
      - レスポンスには以下のメタデータが含まれます（論理的な順序で整理）:
        
        **基本HTTP情報**:
        - `headers.general.status-code`: HTTPステータスコード
        - `headers.general.status-message`: HTTPステータスメッセージ
        - `headers.general.request-url`: リクエストURL
        - `headers.general.http-request-method`: HTTPメソッド（GET）
        
        **リクエスト識別情報**:
        - `eo.meta.http-request-number`: リクエスト番号
        - `eo.meta.http-request-uuid`: リクエストUUID
        - `eo.meta.http-request-round-id`: ラウンドID
        
        **実行環境・タイムスタンプ情報**:
        - `eo.meta.re-area`: 実行エリア（japan-east）
        - `eo.meta.execution-id`: 実行環境識別子（Azure Functions実行ID、取得可能な場合）
        - `eo.meta.request-start-timestamp`: リクエスト開始時刻（UNIXタイムスタンプ、秒単位）
        - `eo.meta.request-end-timestamp`: レスポンス終了時刻（UNIXタイムスタンプ、秒単位）
        
        **プロトコル情報**:
        - `eo.meta.http-protocol-version`: HTTPプロトコルバージョン（HTTP/1.1, HTTP/2, HTTP/3など）
        - `eo.meta.tls-version`: TLSバージョン（TLSv1.2, TLSv1.3など）
        
        **計測値**:
        - `eo.meta.duration-ms`: 総処理時間（ミリ秒単位）
        - `eo.meta.ttfb-ms`: TTFB（Time To First Byte、ミリ秒単位）
        - `eo.meta.actual-content-length`: コンテンツサイズ（バイト単位）
        - `eo.meta.redirect-count`: リダイレクト回数

        **CDN検出情報**（CDN検出時のみ）:
        - `eo.meta.cdn-header-name`: CDN検出に使用したヘッダー名
        - `eo.meta.cdn-header-value`: CDN検出ヘッダーの値
        - `eo.meta.cdn-cache-status`: CDNキャッシュステータス（HIT/MISS等）
        
        **セキュリティ情報**:
        - `eo.security.is_https`: HTTPS接続かどうか
        - `eo.security.hsts_present`: HSTSヘッダーの有無
        - `eo.security.csp_present`: CSPヘッダーの有無
        - その他のセキュリティヘッダー情報
        
        **ヘッダー情報**:
        - `headers.request-headers.*`: リクエストヘッダー
        - `headers.response-headers.*`: レスポンスヘッダー
    - 認証エラー時: HTTP 401 Unauthorized が返る（Function Keyが間違っている場合）
    - トークンエラー時: HTTP 401 Unauthorized と "Invalid Request Secret" が返る（トークンが間違っている場合）
    
    【トラブルシューティング】
    - エスケープエラーが発生する場合: PowerShell変数を使用した方法（上記）を推奨
    - 401エラーが返る場合: Function Keyとトークンの両方を再確認
    - 接続エラーが発生する場合: ネットワーク接続とURLを確認
    ```
- `httpRequestUUID`と`httpRequestRoundID`はオプショナルですが、n8nワークフローから送信される場合は含まれます
- `urltype`はオプショナルですが、n8nワークフロー（210ノード）から送信される場合は含まれます（`main_document`, `asset`, `exception`）。`eo.meta.urltype` としてレスポンスにパススルーされます

トークン無しで叩いた場合 (正常動作)
```
{
  "headers.general.status-code": 401,
  "headers.general.status-message": "Invalid Request Secret",
  "headers.general.request-url": "https://example.com",
  "headers.general.http-request-method": "GET",
  "eo.meta.re-area": "japan-east",
  "eo.meta.duration-ms": 0.0,
  "eo.meta.http-request-number": null,
  "eo.meta.http-request-uuid": null,
  "eo.meta.http-request-round-id": null,
  "headers.request-headers.x-eo-re": "azure",
  ...
}
```

正しいトークンを計算して叩いた場合（レスポンスは論理的な順序で整理されています）
```
{
  "headers.general.status-code": 200,
  "headers.general.status-message": "OK",
  "headers.general.request-url": "https://sample.com",
  "headers.general.http-request-method": "GET",
  "eo.meta.http-request-number": 1,
  "eo.meta.http-request-uuid": "550e8400-e29b-41d4-a716-446655440000",
  "eo.meta.http-request-round-id": 1737123456,
  "eo.meta.re-area": "japan-east",
  "eo.meta.execution-id": "<execution-id-if-available>",
  "eo.meta.request-start-timestamp": 1768679573.8576665,
  "eo.meta.request-end-timestamp": 1768679580.6783333,
  "eo.meta.http-protocol-version": "HTTP/1.1",
  "eo.meta.tls-version": "TLSv1.2",
  "eo.meta.cdn-header-name": "cf-ray",
  "eo.meta.cdn-header-value": "xxxxxxxx-NRT",
  "eo.meta.cdn-cache-status": "HIT",
  "eo.meta.duration-ms": 820.67,
  "eo.meta.ttfb-ms": 272.66,
  "eo.meta.actual-content-length": 126823,
  "eo.meta.redirect-count": 0,
  "eo.security.is_https": true,
  "eo.security.hsts_present": true,
  "eo.security.hsts_value": "max-age=31536000; includeSubDomains; preload",
  "eo.security.csp_present": false,
  "eo.security.x_content_type_options_present": true,
  "headers.request-headers.x-eo-re": "azure",
  "headers.response-headers.content-type": "text/html; charset=UTF-8",
  "headers.response-headers.content-encoding": "gzip",
  ...
}
```

Azureへのデプロイ（コンテナの外でローカルpwsh7で行う）

**注意**: 通常はGitHub Actionsから自動デプロイされます。この方法はトラブルシューティング時のみ使用してください。

## 前提条件

1. Azure CLIがインストールされていること
2. Azure Functions Core Tools (v4) がインストールされていること
3. Azureにログインしていること（`az login`）

## デプロイ手順

```bash
cd RequestEngine\azure\functions\py\funcfiles
func azure functionapp publish eo-re-d1-funcapp-jpe --python
```

**重要なポイント**:
- `--python`フラグはPython v2モデル（`func.FunctionApp()`）を使用する場合に必須です
- デプロイ前に、`requirements.txt`の依存関係がインストールされていることを確認してください



デプロイが完了すると、Invoke url が表示される。関数アプリの「リソースjson」でも`invoke_url_template`として確認できる。
その URL に対して 以下のようなcurl でリクエストを送り、今度は 500 エラーではなく 401 Invalid Request Secret 等、
Key Vault へのアクセス成功を示すレスポンスが返ってくることを確認する

キーをヘッダで送るcurl
```
curl.exe -X POST <INVOKE_URL> `
  -H "Content-Type: application/json" `
  -H "x-functions-key: <YOUR_FUNCTION_KEY>" `
  -d '{"data": {"url": "https://example.com", "token": "<YOUR_TOKEN>", "httpRequestNumber": 1, "httpRequestUUID": "550e8400-e29b-41d4-a716-446655440000", "httpRequestRoundID": 1737123456}}'
```

**注意**: 
- `token`は`SHA-256(url + N8N_EO_REQUEST_SECRET)`で計算する必要があります
  - 詳細な計算方法・実装例・生成AIへのプロンプト例については、上記「ローカルDockerでAzure Functions 初期化/開発環境構築」セクションの「生成AIへのプロンプト例」を参照してください


# Azure Functionsデプロイ後の確認コマンド

**PowerShellでの実行方法（推奨）**:
```powershell
$jsonData = '{"data": {"url": "https://sample.com", "token": "<YOUR_TOKEN>", "httpRequestNumber": 1, "httpRequestUUID": "550e8400-e29b-41d4-a716-446655440000", "httpRequestRoundID": 1737123456}}'
curl.exe -X POST https://eo-re-d1-funcapp-jpe-<ランダム文字列>.japaneast-01.azurewebsites.net/api/requestengine_func -H "Content-Type: application/json" -H "x-functions-key:<YOUR_FUNCTION_KEY>" -d $jsonData
```

**cmd.exeでの実行方法**:
```cmd
curl.exe -X POST https://eo-re-d1-funcapp-jpe-<ランダム文字列>.japaneast-01.azurewebsites.net/api/requestengine_func -H "Content-Type: application/json" -H "x-functions-key:<YOUR_FUNCTION_KEY>" -d "{\"data\": {\"url\": \"https://sample.com\", \"token\": \"<YOUR_TOKEN>\", \"httpRequestNumber\": 1, \"httpRequestUUID\": \"550e8400-e29b-41d4-a716-446655440000\", \"httpRequestRoundID\": 1737123456}}"
```

**注意**: 
- PowerShellでは、JSONデータを変数に格納してから`-d`に渡すことで、エスケープの問題を回避できます
- `token`は`SHA-256(url + N8N_EO_REQUEST_SECRET)`で計算する必要があります
  - 詳細な計算方法・実装例・生成AIへのプロンプト例については、上記「ローカルDockerでAzure Functions 初期化/開発環境構築」セクションの「生成AIへのプロンプト例」を参照してください

# キーコンテナ(Key Vault)URLの変更コマンド
az functionapp config appsettings set --name eo-re-d1-funcapp-jpe --resource-group eo-re-d1-resource-grp-jpe --settings EO_AZ_RE_KEYVAULT_URL="https://eo-re-d1-kv-jpe.vault.azure.net"

# 再デプロイ
func azure functionapp publish eo-re-d1-funcapp-jpe --python
# Azure Functions アプリキー/関数キー（Azure Functions へのアクセス認証）

🔐Request Engine へのアクセス権そのものであり、漏洩してはいけない機密情報

280AZ-japan-east RequestEngine KeyVaultノードで Header Auth Accountに設定する値

- キー名： x-functions-key
    - これは決まりで変えられない。
- キー値
    - 以下の手順で取得 

1. Azure Portal で該当の 関数アプリ (eo-re-d1-funcapp-jpe) へ移動します。
2. 左側のメニューから 関数 を選択します。
3. 目的の関数名 (requestengine_func) をクリックします。
4. 関数の詳細画面で、「関数のURLの取得」 を選択します。
5. 表示されたキーの一覧のうち、名前が `default` の(ファンクション キー)の値を使用してください。
    - `_master` (ホスト キー) や `default` (ホスト キー) ではなく、**ファンクション キー**の `default` を選ぶと、n8n の HTTP Requestの`280AZ-japan-east RequestEngine KeyVault`ノードの URL にそのまま貼れる完全な URL（`?code=xxxxx` 付き）が得られます。

⚠️Host Keys (ホストキー) のセクションにもキーが表示されますが、それは関数アプリ全体に適用されるキーです。セキュリティの観点から、特定の関数 (requestengine_func) にのみ適用される Function Keys のセクションにあるキーを使用するのがベストプラクティスです。

# ログ方針

EOアーキテクチャに基づくログ方針について説明します。アーキテクチャ図（`Architecture/eo-architecture.drawio`）で定義されているログ経路に従います。

## ログ経路の種類

EOアーキテクチャでは、以下の2つのログ経路が定義されています：

### 1. 正規ログ経路（推奨）

**概要**: 各種クラウドのネイティブログ基盤を経由するログ経路

**フロー**:
```
stdout（標準出力） → Application Insights → Log Sink → BigQuery
```

**特徴**:
- レイテンシを考慮し、Azureのネイティブログ基盤（Application Insights）を経由します
- Application Insightsがパフォーマンス・エラー・依存関係のテレメトリを自動収集します
- 統合監視・アラート・ダッシュボード機能が利用できます
- Log Sink経由でBigQueryと統合可能です

**適用条件**:
- エンタープライズ向けの運用が求められる場合
- リアルタイム監視・アラートが必要な場合
- 複数のRequest Engineを運用し、統合監視が必要な場合

**設定方法**:
- Function App作成時: 「監視」セクションで「Application Insights を有効にする: はい」を選択
- 既存Function App: Azure Portal → Function App → 設定 → Application Insights → 有効化

**注意事項**:
- コスト: データインジェスト量に応じて従量課金されます（約$2.30/GB、日本リージョン）
- パフォーマンス: テレメトリ送信によるわずかなオーバーヘッド（数ms〜数十ms）
- 設定: サンプリング率やデータキャップの設定が推奨されます（後述）

### 2. 簡易ログ経路

**概要**: ネイティブログ基盤を経由しないログ経路

**フロー**:
```
stdout（標準出力） → Geminiで分析
```

**特徴**:
- Application Insightsを経由しません
- コストが低い（ログ基盤の料金が不要）
- パフォーマンスオーバーヘッドが小さい
- 分析はGeminiなどで行います

**適用条件**:
- 小規模・個人利用の場合
- リアルタイム監視が不要な場合
- コストを最小化したい場合

**設定方法**:
- Function App作成時: 「監視」セクションで「Application Insights を有効にする: いいえ」を選択
- 既存Function App: Application Insightsを無効化または削除

## 本実装でのログ出力

本Request Engine実装では、Python標準の`logging`モジュールを使用しています：

```python
import logging

# エラーログ
logging.error("Request Secret validation failed: {str(e)}")

# 警告ログ
logging.warning("Content size exceeds {MAX_CONTENT_SIZE_FOR_ANALYSIS} bytes")
```

**特徴**:
- Application Insightsの有効/無効に関わらず動作します
- `stdout`に出力されるため、Application Insightsが有効な場合は自動的に収集されます
- ログレベルは`host.json`で制御できます

## 推奨設定

### Application Insightsを有効にする場合（正規ログ経路）

1. **サンプリング率の設定**: 大量リクエストの場合、コスト削減のためサンプリングを有効化
2. **ログレベルの調整**: `Warning`以上のみを記録（`Information`/`Debug`は除外）
3. **データキャップの設定**: 日次/月次のデータ上限を設定
4. **アラートルールの設定**: エラー率・レスポンスタイムのアラート設定

詳細は後述の「課金抑制」セクションを参照してください。

### Application Insightsを無効にする場合（簡易ログ経路）

- `stdout`への出力のみを使用
- ログレベルは必要に応じて調整
- 分析は外部ツール（Geminiなど）で行う

## ログデータの活用

### BigQueryでの分析

- 正規ログ経路: Application Insights → Log Sink → BigQuery経由でデータを取得
- 簡易ログ経路: `stdout`ログを手動でBigQueryにインポート

### メトリクスの記録

本Request Engineは、以下のメトリクスをJSONレスポンスで返します：
- TTFB（Time To First Byte）
- FCP近似値（First Contentful Paint）
- LCP要素（Largest Contentful Paint）
- リトライ情報
- リソース種別（main_document/asset）
- HTTP/TLSプロトコル情報

これらのメトリクスは、ログ経路とは独立して、リクエストレスポンスとして返されます。

# 課金抑制

## 課金増の原因になりやすい

- Application Insights
  - ログの取り込み量（GB単位）で課金
  - デフォルトで大量の requests, dependencies, traces を送信
  - Functions との連携時は特にログが爆増しやすい
- Azure Functions
  - 実行回数に応じてログが発生
  - 成功リクエストや依存関係ログが大量に送られる
  - Application Insights に自動で送信されるため、サンプリングやフィルタリングがないと課金爆増

## 課金抑制アクション

- Application Insights
  - `eo-re-d1-funcapp-jpe`
    - 保持期間を 30 日に設定（無料枠）
    - Adaptive Sampling を有効化
    - 不要なログ（成功リクエストなど）を除外
- 関数アプリ
  - `eo-re-d1-funcapp-jpe`
    - `host.json`でログレベルを調整（`Warning`以上に）
    - `ILogger`の使い方を見直す（`Information` や `Trace` を減らす）
    - `Application Insights`SDK のフィルタリングを活用

## Log Analytics 30日（無料枠）手順

データ保持期間を 30 日に設定（無料枠）
- Azure Portal にログイン
- 左上「すべてのサービス」→ Log Analytics ワークスペース を開く
- 対象の Workspace をクリック
- 左メニュー → 使用量と推定コスト
- 上部タブ → データ保持
- スライダーを 30 日 に設定
- 保存

## ログレベルを Warning 以上にする

host.json
```
{
  "logging": {
    "logLevel": {
      "default": "Warning"
    }
  }
}
```

## Application Insights のサンプリングを有効化（Adaptive Sampling）

host.json
```
{
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 5
      }
    }
  }
}
```

## 成功リクエスト（200）を Application Insights に送らない

Python 3.13 の Azure Functions で「成功リクエスト（200）」を Application Insights に送らない方法で壁打ちの必要アリ。やってない。

---

# 今後の改善課題

## 1. Headless Chrome（Playwright/Puppeteer）の導入

**目的**: 「データの受信」ではなく、仮想ブラウザで「ピクセルの描画」を計測する

**現状の課題**:
- 現在の実装はサーバーサイドでのHTTPリクエストのみ
- 実際のブラウザでのレンダリング時間（FCP, LCP）を正確に計測できない
- JavaScriptの実行やCSSの適用による描画ブロッキングを検出できない

**実装方針**:
- PlaywrightまたはPuppeteerを使用したHeadless Chromeの導入
- 仮想ブラウザでページをロードし、実際の描画タイミングを計測
- Performance API（`performance.getEntriesByType('paint')`）を活用
- レンダリングブロッキングリソースの影響を可視化

**技術的考慮事項**:
- Azure FunctionsでのHeadless Chrome実行環境の構築
- メモリ使用量とコールドスタート時間の増加
- 実行時間の制限（Azure Functionsのタイムアウト）
- コスト増加（より重い実行環境が必要）

**参考実装**:
- Playwright: `playwright` Pythonパッケージ
- Puppeteer: `pyppeteer` または `playwright`（推奨）

---

## 2. TLS 1.2/1.3の強制

**目的**: 脆弱な通信を拒否し、最新の暗号化をサポートする

**現状の課題**:
- 現在の実装では、サーバーが提供するTLSバージョンをそのまま使用
- TLS 1.0やTLS 1.1などの脆弱なバージョンでも接続が成功してしまう
- セキュリティベストプラクティスに準拠していない

**実装方針**:
- `requests`ライブラリの`SSLContext`を使用してTLS 1.2/1.3のみを許可
- TLS 1.0/1.1での接続を明示的に拒否
- 接続失敗時は適切なエラーメッセージを返す

**実装例**:
```python
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

class TLS12Adapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('https://', TLS12Adapter())
```

**技術的考慮事項**:
- 古いサーバー（TLS 1.0/1.1のみサポート）への接続が失敗する可能性
- エラーハンドリングの追加が必要
- 設定を環境変数で制御可能にする（後方互換性のため）
