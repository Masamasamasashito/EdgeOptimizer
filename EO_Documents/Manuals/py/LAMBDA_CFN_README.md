# AWS Lambda Request Engine - CloudFormation 構築手順

`eo-aws-cfnstack.yml` を使用した AWS Lambda Request Engine インフラストラクチャの構築手順です。

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

---

## 概要

このCloudFormationテンプレートは、Edge Optimizer の AWS Lambda Request Engine に必要な以下のリソースを一括作成します：

- Lambda 関数（Hello World プレースホルダー）
- IAM ロール・ポリシー（Lambda実行用、n8n接続用、GitHub Actions デプロイ用）
- Secrets Manager シークレット（トークン検証用）
- CloudWatch Logs ロググループ（保持期間1日）
- GitHub Actions OIDC プロバイダー

---

## 作成されるリソース一覧

デフォルトパラメータ（`eo-re-d1-*-apne1`）の場合：

| リソース種別 | リソース名 |
|-------------|-----------|
| Lambda 関数 | `eo-re-d1-lambda-apne1` |
| Lambda 実行ロール | `eo-re-d1-lambda-apne1-role` |
| Lambda 基本実行ポリシー | `eo-re-d1-lambda-apne1-basic-exec-iamp` |
| Lambda シークレットアクセスポリシー | `eo-re-d1-lambda-apne1-role-iamp` |
| Secrets Manager | `eo-re-d1-secretsmng-apne1` |
| CloudWatch Logs | `/aws/lambda/eo-re-d1-lambda-apne1` |
| n8n用 IAM ユーザー | `eo-re-d1-lambda-apne1-iamu` |
| n8n用 IAM ポリシー | `eo-re-d1-lambda-apne1-access-key-iamp` |
| GitHub OIDC プロバイダー | `token.actions.githubusercontent.com` |
| GitHub Actions デプロイロール | `eo-re-d1-lambda-apne1-ghactions-deploy-iamr` |
| GitHub Actions デプロイポリシー | `eo-re-d1-lambda-apne1-ghactions-deploy-iamr-iamp` |

---

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

1. Lambda > レイヤー > 「レイヤーを作成」
2. 名前: `eo-re-d1-lambda-python-slim-layer`
3. 説明:  `Python 3.14.3 yyyymmdd v1`
    - Lambda Layer 作成時に確認したpythonバージョンと、バージョン番号を記載しておく。 バージョン毎に説明文を変えることで、バージョン管理が容易になる。
4. zip ファイルをアップロード
5. 互換性のあるアーキテクチャ: `x86_64`
6. 互換性のあるランタイム: `Python 3.14`
7. 「作成」をクリック
8. **バージョンARN をメモ**（例: `arn:aws:lambda:ap-northeast-1:<AWSアカウントID>:layer:eo-re-d1-lambda-python-slim-layer:1`）

詳細手順: [LAMBDA_README.md](LAMBDA_README.md) の Section 8-9 参照

### 1-2. AWS IAM IDプロバイダでGitHub OIDC Provider の確認

Github ActionsでAWSにデプロイする際に、OIDC Providerが必要になります。

**重要**: AWS アカウントに既存の GitHub OIDC Provider がある場合、テンプレートの修正が必要です。

AWS IAMのIDプロバイダは、グローバルリソースなので、リージョンごとに作成する必要はありません。

**確認方法:**
1. AWS コンソール > IAM > ID プロバイダ
2. `token.actions.githubusercontent.com` が存在するか確認

**既存で存在する場合の対応:**
`eo-aws-cfnstack.yml` で以下の2箇所をコメントアウト:

1. `GitHubOIDCProvider` リソース（329-349行目付近）
2. `GitHubOIDCProviderArn` Output（509-513行目付近）

**既存で存在すしない場合の対応:**
STEP 2 で`eo-aws-cfnstack.yml` を実行します。
---

## STEP 2: CloudFormation スタックのデプロイ

### 2-1. AWS コンソールからデプロイ

1. AWS コンソール > CloudFormation > 「スタックの作成」
2. 「既存のテンプレートを選択」を選択
3. 「テンプレートソース」で「テンプレートファイルのアップロード」を選択
4. 「テンプレートファイルのアップロード」で `RequestEngine/aws/lambda/py/CFn/eo-aws-cfnstack.yml` を選択
5. 次へ
6. スタック名: `eo-re-d1-lambda-apne1-stack-yyyymmdd-001`（任意）
7. パラメータを入力:

| パラメータ | 値 | 備考 |
|-----------|-----|------|
| AWSAccountId | `<AWSアカウントID>` | 12桁のAWSアカウントID |
| Region Short Name | `apne1` | デプロイ先リージョン（短縮名） |
| AWSRegion | `ap-northeast-1` | デプロイ先リージョン（フルネーム）  |
| PythonRuntime | `python3.14` | Lambdaランタイム(小数第2位までを記載してください) |
| GitHubOrg | `your-org` | GitHub組織名またはユーザー名 |
| GitHubRepo | `your-repo` | リポジトリ名 |
| LambdaLayerName | `eo-re-d1-lambda-python-slim-layer` | STEP 1-1 で作成した Layer 名 |

8. 「次へ」> 「次へ」
9. 「AWS CloudFormation によって IAM リソースが作成される場合があることを承認します」にチェック
10. 「送信」

### 2-2. AWS CLI からデプロイ

```bash
aws cloudformation create-stack \
  --stack-name eo-re-d1-lambda-apne1-stack-yyyymmdd-001 \
  --template-body file://eo-aws-cfnstack.yml \
  --parameters \
    ParameterKey=AWSAccountId,ParameterValue=<AWSアカウントID> \
    ParameterKey=AWSRegion,ParameterValue=ap-northeast-1 \
    ParameterKey=GitHubOrg,ParameterValue=your-org \
    ParameterKey=GitHubRepo,ParameterValue=your-repo \
    ParameterKey=LambdaLayerName,ParameterValue=eo-re-d1-lambda-python-slim-layer \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

---

## STEP 3: デプロイ後の設定

### 3-1. Secrets Manager の値を更新

CFn で作成されたシークレットにはプレースホルダー値が入っています。実際の値に更新してください。

1. AWS コンソール > Secrets Manager > `eo-re-d1-secretsmng-apne1`
2. 「シークレットの値を取得する」をクリック
3. 「編集」をクリック
4. `LAMBDA_REQUEST_SECRET` の値を `EO_Infra_Docker/.env` の `N8N_EO_REQUEST_SECRET` の値に変更
5. 「保存」

**AWS CLI の場合:**

```bash
aws secretsmanager put-secret-value \
  --secret-id eo-re-d1-secretsmng-apne1 \
  --secret-string '{"LAMBDA_REQUEST_SECRET": "実際のシークレット値"}' \
  --region ap-northeast-1
```

### 3-2. IAM Access Key の作成

n8n から Lambda を呼び出すためのアクセスキーを作成します。

1. AWS コンソール > IAM > ユーザー > `eo-re-d1-lambda-apne1-iamu`
2. 「セキュリティ認証情報」タブ
3. 「アクセスキーを作成」
4. 「AWS の外部で実行されるアプリケーション」を選択
5. 説明タグ: `eo-re-d1-lambda-apne1-iamu-access-key`
6. 「アクセスキーを作成」
7. **CSV をダウンロード**（`eo-re-d1-lambda-apne1-iamu_accessKeys.csv`）

---

## STEP 4: n8n Credentials 設定

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
3. Function Name or ID: `eo-re-d1-lambda-apne1`
4. 「Save」

---

## STEP 5: GitHub Actions 設定

### 5-1. GitHub Secrets の設定

CloudFormation Outputs から `GitHubActionsDeployRoleArn` の値を取得し、GitHub に設定します。

**ARN の確認:**
- AWS コンソール > CloudFormation > スタック > 出力タブ > `GitHubActionsDeployRoleArn`
- 例: `arn:aws:iam::<AWSアカウントID>:role/eo-re-d1-lambda-apne1-ghactions-deploy-iamr`

**GitHub への設定:**
1. GitHub リポジトリ > Settings > Secrets and variables > Actions
2. 「New repository secret」
3. Name: `EO_LAMBDA_DEPLOY_AWS_APNE1_ROLE_FOR_GITHUB`
4. Secret: 上記で取得した ARN
5. 「Add secret」

### 5-2. GitHub Actions ワークフローの確認

`.github/workflows/deploy-to-aws-lambda-apne1.yml` が設定済みであることを確認してください。
同yml内の`LAMBDA_RUNTIME_PYTHON_VERSION`と`LAMBDA_FUNCTION_NAME`に正しい値が入っているか確認してください。これらの値は、`eo-aws-cfnstack.yml` で設定した値と一致している必要があり、`LAMBDA_RUNTIME_PYTHON_VERSION`は小数第2位までを記載してください。

詳細: [LAMBDA_README.md](LAMBDA_README.md) の「github workflow AWS Lambda自動デプロイ」セクション参照
---

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

#### **設定⑩ 280系 RequestEngine設定**
- 各クラウド（AWS Lambda, Azure Functions, Cloudflare Workers, GCP Cloud Run）へリクエストを送るノードの設定です。
- **今回構築した Lambdaの設定**:
    - ノード `280AWS-ap-northeast1 RequestEngine` を開く
    - **Authentication**: `Header Auth` を選択
    - **Header Auth**: STEP 3-4 で設定した `Header Auth` (IAM Access Key) を選択
    - **URL**: STEP 3-1 でメモした API Gateway のURL、または Lambda 関数URLを入力
        - ※ 本構成では `lambda:InvokeFunction` を直接叩く場合、n8n の AWS Lambda ノードを使用しますが、このワークフローは HTTP Request ノードで統一されているため、通常は **Function URL (関数URL)** を発行して設定するか、API Gateway経由で設定します。
        - **補足**: `eo-aws-cfnstack.yml` では IAM User を作成しましたが、Function URL は作成していません。
            - **方法A (推奨)**: Lambda コンソール > 設定 > 関数URL > 「関数URLを作成」 > 認証タイプ `AWS_IAM` を選択。このURLを n8n の URL 欄に設定。
            - **方法B**: n8n の `AWS Lambda` ノードに置き換えて、Function Name を指定して実行（要ワークフロー修正）。
    - **Headers**:
        - `x-aws-lambda-token`: `{{ $json.tokenCalculatedByN8n }}` (変更不要)

設定が完了したら、n8n 画面右上の「Save」を押して保存してください。


## STEP 7: github actions workflow実行

まだ、AWS Lambdaにデプロイしていないので、github actions workflowは実行できません。
github actions workflowでデプロイします。

1. 該当リポジトリのgithub で > (タブ)Actions
2. (左メニュー)All workflows > (ワークフロー名) Deploy AWS Lambda
3. Run workflow
4. (ドロップダウン)main
5. Run workflow
6. workflow完了を確認する

---

## STEP 8: n8n workflow実行

Lambdaだけ実行可能な状態です。Lambda以外を使わない場合、180 RequestEngine Settingsノードで非該当のrequestEngineListをコメントアウトするか、削除してください。※おすすめはメンテナンス性を考慮して、コメントアウトです。

## パラメータ一覧

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| **命名規則** |||
| ProjectPrefix | `eo` | プロジェクトプレフィックス |
| Component | `re` | コンポーネント識別子（Request Engine） |
| Environment | `d1` | 環境識別子（dev01 等） |
| RegionShort | `apne1` | リージョン短縮名 |
| **AWSアカウント** |||
| AWSAccountId | (入力必須) | 12桁のAWSアカウントID |
| AWSRegion | `ap-northeast-1` | デプロイ先リージョン |
| **Lambda設定** |||
| PythonRuntime | `python3.14` | Pythonランタイムバージョン |
| LambdaLayerName | `eo-re-d1-lambda-python-slim-layer` | Lambda Layer 名 |
| LambdaLayerVersion | `1` | Lambda Layer バージョン |
| LambdaTimeout | `30` | タイムアウト（秒） |
| LambdaMemorySize | `128` | メモリサイズ（MB） |
| **GitHub Actions** |||
| GitHubOrg | `your-github-org` | GitHub組織名/ユーザー名 |
| GitHubRepo | `your-repo-name` | リポジトリ名 |

---

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
2. `LambdaLayerName` と `LambdaLayerVersion` パラメータが正しいか確認

### IAM ロール/ポリシー名の重複

```
Resource handler returned message: "Role/Policy with name ... already exists"
```

**原因**: 同じ名前のリソースが既に存在
**解決**:
1. 既存リソースを削除してから再デプロイ
2. または `Environment` パラメータを変更（例: `d1` → `d02`）

### Secrets Manager の値が反映されない

**原因**: Lambda がシークレットをキャッシュしている
**解決**: Lambda 関数を再デプロイ（GitHub Actions でプッシュ、または手動デプロイ）

---

## 関連ドキュメント

- [N8N_NODE_SETUP.md](../n8n/N8N_NODE_SETUP.md) - n8nワークフローノード設定ガイド（#010/DNS認証/#180/動作確認）
- [LAMBDA_README.md](LAMBDA_README.md) - Lambda 詳細セットアップ手順
- [RE_README.md](../RE_README.md) - Request Engine 全体のセキュリティ設定
- [N8N_WORKFLOW_README.md](../n8n/N8N_WORKFLOW_README.md) - n8nワークフロー設定ガイド
- [NODE180_REQUESTENGINE_README.md](../n8n/NODE180_REQUESTENGINE_README.md) - Request Engine設定ガイド（type_area・accept_language一覧）
- [NODE175_USERAGENT_README.md](../n8n/NODE175_USERAGENT_README.md) - User-Agent設定ガイド
