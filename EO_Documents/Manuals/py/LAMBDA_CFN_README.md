# AWS Lambda Request Engine - CloudFormation 構築手順

`RequestEngine\aws\lambda\py\CFn\re-aws-cfnstack.yml` を使用した AWS Lambda Request Engine 構築手順です。

## 目次

- [概要](#概要)
- [作成されるリソース一覧](#作成されるリソース一覧)
- [STEP 1: 事前準備（CFnデプロイ前）](#step-1-事前準備cfnデプロイ前)
- [STEP 2: CloudFormation スタックのデプロイ](#step-2-cloudformation-スタックのデプロイ)
- [STEP 3: デプロイ後の設定](#step-3-デプロイ後の設定)
- [STEP 4: n8n Credentials 設定](#step-4-n8n-credentials-設定)
- [STEP 5: GitHub Actions 設定](#step-5-github-actions-設定)
- [STEP 6: n8n ワークフローノード設定](#step-6-n8n-ワークフローノード設定)
- [パラメータ一覧](#パラメータ一覧)
- [トラブルシューティング](#トラブルシューティング)

## 概要

このCloudFormationテンプレートは、Edge Optimizer の AWS Lambda Request Engine に必要な以下のリソースを一括作成します：

- Lambda 関数（デフォルトHello Worldのソースコードであるため、CFn実施後にGithub Actionsでソースコード更新が必要）
- IAM ロール・ポリシー（Lambda実行用、n8n接続用、GitHub Actions デプロイ用）
- Secrets Manager シークレット（仮valueであるため、CFn実施後にN8N_EO_REQUEST_SECRETの値に更新が必要）
- CloudWatch Logs ロググループ（保持期間1日）
- GitHub Actions OIDC プロバイダー

## 作成されるリソース一覧

デフォルトパラメータ

| リソース種別 | リソース名 |
|-------------|-----------|
| Lambda 関数 | `re-d1-lambda-apne1` |
| Lambda 実行ロール | `re-d1-lambda-apne1-role` |
| Lambda 基本実行ポリシー | `re-d1-lambda-apne1-basic-exec-iamp` |
| Lambda シークレットアクセスポリシー | `re-d1-lambda-apne1-role-iamp` |
| Secrets Manager | `re-d1-secretsmng-apne1` |
| CloudWatch Logs | `/aws/lambda/re-d1-lambda-apne1` |
| n8n用 IAM ユーザー | `re-d1-lambda-apne1-iamu` |
| n8n用 IAM ポリシー | `re-d1-lambda-apne1-access-key-iamp` |
| GitHub OIDC プロバイダー | `token.actions.githubusercontent.com` |
| GitHub Actions デプロイロール | `re-d1-lambda-apne1-ghactions-deploy-iamr` |
| GitHub Actions デプロイポリシー | `re-d1-lambda-apne1-ghactions-deploy-iamr-iamp` |



## STEP 1: 事前準備（CFnデプロイ前）

### 1-1. Lambda Layer 作成

Lambda Layer は CloudFormation デプロイ**前**に手動で作成する必要があります。

> **💡 WSL2 / Docker 環境が無い場合:**
> Lambda Layer の zip ファイルはリポジトリに同梱されています。Docker でビルドせずに、以下のファイルをそのまま AWS コンソールからアップロードできます：
>
> 📦 [`RequestEngine/aws/lambda/py/funcfiles/requests-py314-slim-layer.zip`](../../../RequestEngine/aws/lambda/py/funcfiles/requests-py314-slim-layer.zip)
>
> この場合、以下の Docker 手順（# 1〜# 4）をスキップし、「AWS コンソールで Layer を作成」の手順から進めてください。

```bash
# 1. ディレクトリ移動
cd RequestEngine/aws/lambda/py/localdev

# 2. (ローカルにDockerがインストールされていない場合)WSL2 Ubuntu 起動して、Ubuntu内のdockerを使う
wsl -d Ubuntu

# 3. Docker Compose で Layer zip 作成
docker compose run --rm lambda_layer_builder

# 4. 実行結果の先頭のあたりで以下の様にpythonバージョンが表示される(Docker DesktopのImagesからも確認可能)

docker compose run --rm lambda_layer_builder
Container localdev-lambda_layer_builder-run-xxxxxxxxxxxx Creating 
Container localdev-lambda_layer_builder-run-xxxxxxxxxxxx Created 
================PYTHON VERSION================
Python 3.14.3
==============================================

# CFn実行時に必要なため、メモしておく
# バージョン固定は`EO_RequestEngine/aws/lambda/py/localdev/env.example`を複製した`.env`の`COMMON_LAMBDA_LAYER_DOCKER_IMAGE_TAG`で`python3.14-slim`のように指定可能
# Edge Optimizer のDockerは、各種バージョンをすべて.envで管理出来るようになっています。

# 5. (ローカルにDockerがインストールされていない場合)WSL 終了
exit
```

作成された zip ファイル: `EO_RequestEngine/aws/lambda/py/funcfiles/requests-python-slim-layer.zip`

**AWS コンソールで Layer を作成:**

AWSリージョン ap-northeast-1の場合:

1. Lambda > レイヤー > 「レイヤーを作成」
2. 名前: `re-d1-lambda-python-slim-layer`
3. 説明:  `Request Engine Python 3.14.3 yyyymmdd v1`
    - Lambda Layer 作成時に確認したpythonバージョンと、バージョン番号を記載しておく。 バージョン毎に説明文を変えることで、バージョン管理が容易になる。
4. zip ファイルをアップロード
5. 互換性のあるアーキテクチャ: `x86_64`
6. 互換性のあるランタイム: `Python 3.14`
7. 「作成」をクリック
8. **バージョンARN をメモ**（例: `arn:aws:lambda:ap-northeast-1:<AWSアカウントID>:layer:re-d1-lambda-python-slim-layer:1`）

詳細手順: [LAMBDA_README.md](LAMBDA_README.md) の Section 8-9 参照

### 1-2. AWS IAM IDプロバイダでGitHub OIDC Provider の確認

Github ActionsでAWSにデプロイする際に、OIDC Providerが必要になります。

**重要**: AWS アカウントに既存の GitHub OIDC Provider がある場合、テンプレートの修正が必要です。

AWS IAMのIDプロバイダは、グローバルリソースなので、リージョンごとに作成する必要はありません。

**確認方法:**
1. AWS コンソール > IAM > ID プロバイダ
2. `token.actions.githubusercontent.com` が存在するか確認

**既存で`token.actions.githubusercontent.com` が存在する場合:**
`re-aws-cfnstack.yml` で以下の2箇所をコメントアウト:

1. `GitHubOIDCProvider` リソース（329-349行目付近）
2. `GitHubOIDCProviderArn` Output（509-513行目付近）

**既存で`token.actions.githubusercontent.com` が存在しない場合:**
STEP 2 で`re-aws-cfnstack.yml` を実行。

## STEP 2: CloudFormation スタックのデプロイ

### 2-1. AWS コンソールからデプロイ

1. AWS コンソール > CloudFormation > 「スタックの作成」
2. 「既存のテンプレートを選択」を選択
3. 「テンプレートソース」で「テンプレートファイルのアップロード」を選択
4. 「テンプレートファイルのアップロード」で `RequestEngine/aws/lambda/py/CFn/re-aws-cfnstack.yml` を選択
5. 次へ
6. スタック名: `re-d1-lambda-apne1-stack-yyyymmdd-001`（任意）
7. 各種パラメータを入力:

| パラメータ | 値 | 備考 |
|-----------|-----|------|
| EoProject | `re` | プロジェクト識別子（Request Engine） |
| EoEnvironment | `d1` | 環境識別子（dev01 等） |
| EoAreaShort | `apne1` | エリア短縮名 |
| EoServiceServerless | `lambda` | サーバレス識別子（AWS Lambda） |
| AWSAccountId | `<AWSアカウントID>` | 12桁のAWSアカウントID(※空欄にしてあるので必ず入力) |
| EoArea | `ap-northeast-1` | デプロイ先リージョン（フルネーム） |
| EoReRuntimeVer | `python3.14` | Lambda ランタイム（小数第2位まで記載） |
| EoReLambdaLayerSuffix | `python-slim-layer` | STEP 1-1 で作成した Layer 名のサフィックス |
| EoReLambdaLayerVer | `1` | Layer バージョン |
| GitHubOrg | `your-org` | GitHub組織名またはユーザー名 |
| EoGitHubRepo | `your-repo` | リポジトリ名 |

8. 「次へ」
9. 「AWS CloudFormation によって IAM リソースが作成される場合があることを承認します」にチェックを入れる > 「次へ」
10. 「送信」

### 2-2. AWS CLI からデプロイ

```bash
aws cloudformation create-stack \
  --stack-name re-d1-lambda-apne1-stack-yyyymmdd-001 \
  --template-body file://RequestEngine/aws/lambda/py/CFn/re-aws-cfnstack.yml \
  --parameters \
    ParameterKey=EoProject,ParameterValue=re \
    ParameterKey=EoEnvironment,ParameterValue=d1 \
    ParameterKey=EoAreaShort,ParameterValue=apne1 \
    ParameterKey=EoServiceServerless,ParameterValue=lambda \
    ParameterKey=EoServiceSecret,ParameterValue=secretsmng \
    ParameterKey=EoRequestSecretName,ParameterValue=LAMBDA_REQUEST_SECRET \
    ParameterKey=AWSAccountId,ParameterValue=<AWSアカウントID> \
    ParameterKey=EoArea,ParameterValue=ap-northeast-1 \
    ParameterKey=EoReRuntimeVer,ParameterValue=python3.14 \
    ParameterKey=EoReLambdaLayerSuffix,ParameterValue=python-slim-layer \
    ParameterKey=EoReLambdaLayerVer,ParameterValue=1 \
    ParameterKey=EoReTimeout,ParameterValue=30 \
    ParameterKey=EoReMemorySize,ParameterValue=128 \
    ParameterKey=GitHubOrg,ParameterValue=your-org \
    ParameterKey=EoGitHubRepo,ParameterValue=your-repo \
    ParameterKey=EoCreateGitHubOIDCProvider,ParameterValue=true \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

- 新規に OIDC プロバイダーを作る場合: `EoCreateGitHubOIDCProvider=true` のまま。`ExistingGitHubOIDCProviderArn` は省略でOK。
- 既存の GitHub OIDC プロバイダーを使う場合: `EoCreateGitHubOIDCProvider` を `false` にし、`ParameterKey=ExistingGitHubOIDCProviderArn,ParameterValue=arn:aws:iam::<AWSアカウントID>:oidc-provider/token.actions.githubusercontent.com` を追加してください。
- コマンド実行時は、`--template-body file://RequestEngine/aws/lambda/py/CFn/re-aws-cfnstack.yml` のパスがテンプレートの実際の場所を指すようにしてください（上記はリポジトリルートで実行する場合の相対パスです）。

## STEP 3: デプロイ後の設定

### 3-1. Secrets Manager の値を更新

CFn で作成されたシークレットにはプレースホルダー値が入っています。実際の値に更新してください。

1. AWS コンソール > Secrets Manager > `re-d1-secretsmng-apne1`
2. 「シークレットの値を取得する」をクリック
3. 「編集」をクリック
4. シークレットキー`LAMBDA_REQUEST_SECRET` のシークレットの値を `EO_Infra_Docker/.env` の `N8N_EO_REQUEST_SECRET` の値に変更
5. 「保存」

**AWS CLI の場合:**

```bash
aws secretsmanager put-secret-value \
  --secret-id re-d1-secretsmng-apne1 \
  --secret-string '{"LAMBDA_REQUEST_SECRET": "実際のシークレット値"}' \
  --region ap-northeast-1
```

### 3-2. IAM Access Key の作成

n8n から Lambda を呼び出すためのアクセスキーを作成します。

1. AWS コンソール > IAM > ユーザー > `re-d1-lambda-apne1-iamu`
2. 「セキュリティ認証情報」タブ
3. 「アクセスキーを作成」
4. 「AWS の外部で実行されるアプリケーション」を選択
5. 説明タグ: `re-d1-lambda-apne1-iamu-access-key`
6. 「アクセスキーを作成」
7. **CSV をダウンロード**（`re-d1-lambda-apne1-iamu_accessKeys.csv`）

## STEP 4: n8n Credentials 設定

`QUICK_START.md`を参照ください。

- `EO_Infra_Docker\docker-compose.yml` で Docker上 の n8n を構築/起動します。
- Playwrightコンテナなど、デフォルトのn8nに追加でEdgeOptimizer用の機能を充実させているため、`EO_Infra_Docker\docker-compose.yml`の利用を推奨します。
- セキュリティを考慮し、常にlatestバージョンでDockerイメージなどを起動するようにしています。
- Dockerイメージなどのバージョン指定が必要な場合、`EO_Infra_Docker\env.example`を複製してつくった`.env`で`COMMON_EO_DOCKER_*_IMAGE_TAG`（例: `COMMON_EO_DOCKER_N8N_IMAGE_TAG`）のバージョンを書き換えてください。
- EdgeOptimizerが利用するDockerイメージは、識別しやすくするために、すべて「正規のDockerイメージ名`-eo`」としてDockerイメージ名を工夫しています。
  - 例: `n8nio/n8n-eo:latest`、`mcr.microsoft.com/playwright-eo:noble`  
- EdgeOptimizerは、`127.0.0.1:5678`などがローカルで他のDockerと競合した場合も.envファイルの中で、`DOCKER_HOST_BIND_ADDR`と`DOCKER_HOST_PORT_*****`と`PLAYWRIGHT_CONTAINER_LISTEN_PORT`を変更するだけで競合を解消出来るようになっています。
- EdgeOptimizerのDockerボリュームは、`eo_infra_docker_`プレフィックスがすべてのDockerボリュームに付与されており、Dockerイメージ更新時にデータが引き継がれるようになっています。

`EO_Infra_Docker\.env`を作成後、同`EO_Infra_Docker`ディレクトリ内で`docker compose up -d`にてEdgeOptimizer用のn8n環境を起動できます。デフォルトでは、ブラウザで`http://127.0.0.1:5678/`にてn8n画面を確認できます。

**【重要】n8n画面で更新通知を受け取った場合、以下の手順で更新してください**

「正規のDockerイメージ名`-eo`」としてDockerイメージ名を工夫しているため、Dockerイメージ更新は
`EO_Documents\Manuals\EO_Infra_Docker_README.md`の手順で行う必要があります。
※`EO_Documents\Manuals\EO_Infra_Docker_README.md`の手順ではなく、普通にDockerイメージを更新した場合、`eo_infra_docker_`プレフィックス付きDockerボリューム削除してなければリカバリ可能です。

### 4-1. n8n Credential の作成

1. n8n 左サイドバー > Personal > Credentials > Create Credential
2. Credential Type: `AWS (IAM)` を選択
3. 設定:
   - Name: `EO_RE_Lambda_apne1_AccessKey`
   - Region: `ap-northeast-1`
   - Access Key ID: （STEP 3-2 でダウンロードした CSV から）
   - Secret Access Key: （STEP 3-2 でダウンロードした CSV から）
4. 「Save」
5. 緑色で「Connection tested successfully」が表示されれば成功

### 4-2. n8n ワークフローノードの設定

1. `280AWS-apne1 RequestEngine AccessKey` ノードを開く
2. Credential to connect with: `EO_RE_Lambda_apne1_AccessKey`
3. Function Name or ID: `re-d1-lambda-apne1`
4. 「Save」



## STEP 5: GitHub Actions 設定

### 5-1. GitHub Secrets の設定

CloudFormation Outputs から `GitHubActionsDeployRoleArn` の値を取得し、GitHub に設定します。

**ARN の確認:**
- AWS コンソール > CloudFormation > スタック > 出力タブ > `GitHubActionsDeployRoleArn`
- 例: `arn:aws:iam::<AWSアカウントID>:role/re-d1-lambda-apne1-ghactions-deploy-iamr`

**GitHub への設定:**
1. GitHub リポジトリ > Settings > Secrets and variables > Actions
2. 「New repository secret」
3. Name: `EO_LAMBDA_DEPLOY_AWS_APNE1_ROLE_FOR_GITHUB`
4. Secret: 上記で取得した ARN
5. 「Add secret」

### 5-2. GitHub Actions ワークフローの確認

`.github/workflows/deploy-to-aws-lambda-apne1.yml` が設定済みであることを確認してください。
同yml内の`LAMBDA_RUNTIME_PYTHON_VERSION`と`LAMBDA_FUNCTION_NAME`に正しい値が入っているか確認してください。これらの値は、`re-aws-cfnstack.yml` で設定した値と一致している必要があり、`LAMBDA_RUNTIME_PYTHON_VERSION`は小数第2位までを記載してください。

詳細: [LAMBDA_README.md](LAMBDA_README.md) の「github workflow AWS Lambda自動デプロイ」セクション参照


## STEP 6: n8n ワークフローノード設定

STEP 4 で Credential と #280AWS ノードの設定が完了しました。次に、ワークフローを実行するために必要なノ### 3-5. n8n ワークフロー設定（重要！）

**`EO_n8nWorkflow_Json/eo-n8n-workflow-jp.json` のピンク色スティッキーノートの設定①から⑧と⑩を実施してください。**

以下に、ワークフロー内の設定手順を抜粋します（詳細は n8n 画面内の付箋を確認してください）。

#### **設定① 010 Step.0 Starter by XML sitemap**
- **XMLサイトマップURL記載**
- Start by XML sitemapノードをダブルクリック。右上の鉛筆マークをクリックして、XMLサイトマップURLを以下形式のJSONで書き換えてください。
```json
[
    {
        "Website" : "https://sample.com/sitemap.xml"
    }
]
```

#### **設定② #015-020 DNS認証設定**
- ドメイン所有権のDNS TXTレコード検証を設定します。
- **DNSレコード追加**:
    - ホスト名: `_eo-dns-txt-auth.sample.com`
        - ※ご自身のドメインに合わせて変更してください
    - 値 (内容): 任意のランダムな文字列 (例: `eo-dns-txt-value-check-sampletxt`)
- **n8nノード設定**:
    - **020 DNS TXT Check**: 「DNSTXT_TOKEN」の Value に、上記で設定した値 (`eo-dns-txt-value-check-sampletxt`) を設定します。
- **目的**: 誤って管理外のドメインへ大量リクエストを送らないための安全装置です。

#### **設定③ 125-1 HTTP Req to MainDoc URL locs through Playwright**
- Playwrightによるヘッドレスブラウザ（dockerコンテナ）を使わない場合、`125-2 HTTP Req to MainDoc URL locs without Playwright` に入れ替えてください。
- **注意**: Playwrightを使わない場合、JavaScriptによる動的生成コンテンツのリンクが取得できず、Target URLリスト抽出網羅性が下がります。

#### **設定④ 140 Resource URLs Discovery from DOM**
- 取得したDOMデータから、正規表現やDOM解析を用いて「サブリンク（画像、CSS、JSなど）」を抽出します。
- **ドメインホワイトリスト**の設定を確認し、意図しない外部ドメインへのリクエストを防ぐ設定になっているか確認してください。

#### **設定⑤ 155 Excluded Patterns Filter**
- `/wp-admin/` や `contact` 、特殊なBlob URLなど、リクエストしたくないパスを除外設定します。
- 必要に応じて「部分一致」や「完全一致」の条件を追加してください。

#### **設定⑥ 175 Assign UserAgents**
- アセット用とメインドキュメント用で適切な User-Agent を設定します。
- **重要**: UA無しは想定されていないため、必ず1つ以上設定してください。

#### **設定⑦ 180 RequestEngine Settings**
- クラウド種別、エリア、言語設定を定義します。
- 例:
    - `AwsLambda_ap-northeast-1` / `ja,ja-JP...`
    - `CloudflareWorkers_global` / ...
- ここで定義した `type_area` を後続の **225 Switcher** で使用します。

#### **設定⑧ 225 RequestEngine Switcher**
- **本n8nワークフローのインテリジェンス層です。**
- 「どのリクエストを」「どこから（どのクラウド/エリア）」送るかを決定します。
- **重要**: 今回作成した AWS Lambda (ap-northeast-1) を利用するために、`AwsLambda_ap-northeast-1` へのルーティング設定が有効になっていることを確認してください。

#### **設定⑨ 235 Get IDtoken [今回はスキップ]**
- Google Cloud Run を使用しない場合は設定不要です。

#### **設定⑩ 280系 RequestEngine(Lambda)設定**
- AWS Lambdaへリクエスト(Warmupリクエストの指示)を送るn8nノード設定です。
- **LambdaにWarmupリクエストを送るn8nノード設定**:
    - ノード `280AWS-ap-northeast1 RequestEngine` を開く
    - Parameters
    - **Credential to connect with**: `EO_RE_Lambda_apne1_AccessKey` を選択
    - Operation: `Invoke` を選択
    - Function Name or ID: `re-d1-lambda-apne1`を入力
    - Qualifier: `LATEST` を選択
    - Invocation Type: `Wait for Results` を選択
    -JSON Input: `{{ $json.data }}` を入力

## STEP 7: github actions workflow実行

まだ、AWS Lambdaにデプロイしていないので、github actions workflowは実行できません。
github actions workflowでデプロイします。

1. 該当リポジトリのgithub で > (タブ)Actions
2. (左メニュー)All workflows > (ワークフロー名) Deploy AWS Lambda
3. 「Run workflow ▼」ボタンをクリック
4. (ドロップダウン)Branch:mainを選択
5. (緑色ボタン)Run workflow
6. workflow完了を確認する



## STEP 8: n8n workflow実行

Lambdaだけ実行可能な状態です。Lambda以外を使わない場合、180 RequestEngine Settingsノードで非該当のrequestEngineListをコメントアウトするか、削除してください。※おすすめはメンテナンス性を考慮して、コメントアウトです。

## パラメータ一覧

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| **命名規則** |||
| EoProject | `re` | プロジェクト識別子（Request Engine） |
| EoEnvironment | `d1` | 環境識別子（dev01 等） |
| EoAreaShort | `apne1` | エリア短縮名 |
| EoServiceServerless | `lambda` | サーバレス識別子（AWS Lambda） |
| EoServiceSecret | `secretsmng` | シークレットサービス識別子（Secrets Manager） |
| EoRequestSecretName | `LAMBDA_REQUEST_SECRET` | シークレット内のキー名（値は REPLACE_WITH_N8N_EO_REQUEST_SECRET を本番値に置換） |
| **AWSアカウント** |||
| AWSAccountId | (入力必須) | 12桁のAWSアカウントID |
| EoArea | `ap-northeast-1` | デプロイ先リージョン |
| **Lambda設定** |||
| EoReRuntimeVer | `python3.14` | リクエストエンジン (Lambda) Python ランタイムバージョン |
| EoReLambdaLayerSuffix | `python-slim-layer` | Lambda Layer 名サフィックス（CFn では EoProject-EoEnvironment-EoServiceServerless-{Suffix} で結合） |
| EoReLambdaLayerVer | `1` | Lambda Layer バージョン |
| EoReTimeout | `30` | タイムアウト（秒） |
| EoReMemorySize | `128` | メモリサイズ（MB） |
| **GitHub Actions OIDC** |||
| EoCreateGitHubOIDCProvider | `true` | 新規 OIDC プロバイダーを作成するか |
| ExistingGitHubOIDCProviderArn | (EoCreateGitHubOIDCProvider が false 時必須) | 既存 OIDC プロバイダー ARN |
| GitHubOrg | `your-github-org` | GitHub組織名/ユーザー名 |
| EoGitHubRepo | `your-repo-name` | リポジトリ名 |



## トラブルシューティング

### EntityAlreadyExists エラー（OIDC Provider）

```
Resource handler returned message: "EntityAlreadyExists"
```

**原因**: AWS アカウントに既存の GitHub OIDC Provider が存在
**解決**: テンプレートの `GitHubOIDCProvider` リソースと `GitHubOIDCProviderArn` Output をコメントアウト

### Lambda Layer が見つからない

```
Resource handler returned message: "Layer version arn:aws:lambda:... does not exist"
```

**原因**: Lambda Layer が未作成、または名前/バージョンが一致しない
**解決**:
1. Lambda Layer が作成済みか確認
2. `EoReLambdaLayerSuffix` と `EoReLambdaLayerVer` パラメータが正しいか確認

### IAM ロール/ポリシー名の重複

```
Resource handler returned message: "Role/Policy with name ... already exists"
```

**原因**: 同じ名前のリソースが既に存在
**解決**:
1. 既存リソースを削除してから再デプロイ
2. または `EoEnvironment` パラメータを変更（例: `d1` → `d02`）

### Secrets Manager の値が反映されない

**原因**: Lambda がシークレットをキャッシュしている
**解決**: Lambda 関数を再デプロイ（GitHub Actions でプッシュ、または手動デプロイ）



## 関連ドキュメント

- [N8N_NODE_SETUP.md](../n8n/N8N_NODE_SETUP.md) - n8nワークフローノード設定ガイド（#010/DNS認証/#180/動作確認）
- [LAMBDA_README.md](LAMBDA_README.md) - Lambda 詳細セットアップ手順
- [RE_README.md](../RE_README.md) - Request Engine 全体のセキュリティ設定
- [N8N_WORKFLOW_README.md](../n8n/N8N_WORKFLOW_README.md) - n8nワークフロー設定ガイド
- [NODE180_REQUESTENGINE_README.md](../n8n/NODE180_REQUESTENGINE_README.md) - Request Engine設定ガイド（type_area・accept_language一覧）
- [NODE175_USERAGENT_README.md](../n8n/NODE175_USERAGENT_README.md) - User-Agent設定ガイド
