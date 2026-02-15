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

デフォルトパラメータ（`eo-re-d01-*-apne1`）の場合：

| リソース種別 | リソース名 |
|-------------|-----------|
| Lambda 関数 | `eo-re-d01-lambda-apne1` |
| Lambda 実行ロール | `eo-re-d01-lambda-apne1-role` |
| Lambda 基本実行ポリシー | `eo-re-d01-lambda-apne1-basic-exec-iamp` |
| Lambda シークレットアクセスポリシー | `eo-re-d01-lambda-apne1-role-iamp` |
| Secrets Manager | `eo-re-d01-secretsmng-apne1` |
| CloudWatch Logs | `/aws/lambda/eo-re-d01-lambda-apne1` |
| n8n用 IAM ユーザー | `eo-re-d01-lambda-apne1-iamu` |
| n8n用 IAM ポリシー | `eo-re-d01-lambda-apne1-access-key-iamp` |
| GitHub OIDC プロバイダー | `token.actions.githubusercontent.com` |
| GitHub Actions デプロイロール | `eo-re-d01-lambda-apne1-ghactions-deploy-iamr` |
| GitHub Actions デプロイポリシー | `eo-re-d01-lambda-apne1-ghactions-deploy-iamr-iamp` |

---

## STEP 1: 事前準備（CFnデプロイ前）

### 1-1. Lambda Layer の作成

Lambda Layer は CloudFormation デプロイ**前**に手動で作成する必要があります。

> **💡 WSL2 / Docker 環境が無い場合:**
> Lambda Layer の zip ファイルはリポジトリに同梱されています。Docker でビルドせずに、以下のファイルをそのまま AWS コンソールからアップロードできます：
>
> 📦 [`RequestEngine/aws_lambda/apne1/funcfiles/requests-py314-slim-layer.zip`](../apne1/funcfiles/requests-py314-slim-layer.zip)
>
> この場合、以下の Docker 手順（# 1〜# 4）をスキップし、「AWS コンソールで Layer を作成」の手順から進めてください。

```bash
# 1. ディレクトリ移動
cd RequestEngine/aws_lambda/apne1

# 2. WSL2 Ubuntu 起動
wsl -d Ubuntu

# 3. Docker Compose で Layer zip 作成
docker compose run --rm lambda_layer_builder

# 4. WSL 終了
exit
```

作成された zip ファイル: `funcfiles/requests-py314-slim-layer.zip`

**AWS コンソールで Layer を作成:**

1. Lambda > レイヤー > 「レイヤーを作成」
2. 名前: `eo-re-d01-lambda-py314-slim-layer`
3. zip ファイルをアップロード
4. 互換性のあるランタイム: `Python 3.14`
5. 「作成」をクリック
6. **ARN をメモ**（例: `arn:aws:lambda:ap-northeast-1:123456789012:layer:eo-re-d01-lambda-py314-slim-layer:1`）

詳細手順: [LAMBDA_README.md](../apne1/LAMBDA_README.md) の Section 8-9 参照

### 1-2. GitHub OIDC Provider の確認

**重要**: AWS アカウントに既存の GitHub OIDC Provider がある場合、テンプレートの修正が必要です。

**確認方法:**
1. AWS コンソール > IAM > ID プロバイダ
2. `token.actions.githubusercontent.com` が存在するか確認

**既存の場合の対応:**
`eo-aws-cfnstack.yml` で以下の2箇所をコメントアウト:

1. `GitHubOIDCProvider` リソース（329-349行目付近）
2. `GitHubOIDCProviderArn` Output（509-513行目付近）

---

## STEP 2: CloudFormation スタックのデプロイ

### 2-1. AWS コンソールからデプロイ

1. AWS コンソール > CloudFormation > 「スタックの作成」
2. 「新しいリソースを使用（標準）」を選択
3. 「テンプレートファイルのアップロード」で `eo-aws-cfnstack.yml` を選択
4. スタック名: `eo-re-d01-lambda-apne1-stack`（任意）
5. パラメータを入力:

| パラメータ | 値 | 備考 |
|-----------|-----|------|
| AWSAccountId | `123456789012` | 12桁のAWSアカウントID |
| AWSRegion | `ap-northeast-1` | デプロイ先リージョン |
| GitHubOrg | `your-org` | GitHub組織名またはユーザー名 |
| GitHubRepo | `your-repo` | リポジトリ名 |
| LambdaLayerName | `eo-re-d01-lambda-py314-slim-layer` | STEP 1-1 で作成した Layer 名 |

6. 「次へ」> 「次へ」
7. 「AWS CloudFormation によって IAM リソースが作成される場合があることを承認します」にチェック
8. 「送信」

### 2-2. AWS CLI からデプロイ

```bash
aws cloudformation create-stack \
  --stack-name eo-re-d01-lambda-apne1-stack \
  --template-body file://eo-aws-cfnstack.yml \
  --parameters \
    ParameterKey=AWSAccountId,ParameterValue=123456789012 \
    ParameterKey=AWSRegion,ParameterValue=ap-northeast-1 \
    ParameterKey=GitHubOrg,ParameterValue=your-org \
    ParameterKey=GitHubRepo,ParameterValue=your-repo \
    ParameterKey=LambdaLayerName,ParameterValue=eo-re-d01-lambda-py314-slim-layer \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

---

## STEP 3: デプロイ後の設定

### 3-1. Secrets Manager の値を更新

CFn で作成されたシークレットにはプレースホルダー値が入っています。実際の値に更新してください。

1. AWS コンソール > Secrets Manager > `eo-re-d01-secretsmng-apne1`
2. 「シークレットの値を取得する」をクリック
3. 「編集」をクリック
4. `LAMBDA_REQUEST_SECRET` の値を `EO_Infra_Docker/.env` の `N8N_EO_REQUEST_SECRET` の値に変更
5. 「保存」

**AWS CLI の場合:**

```bash
aws secretsmanager put-secret-value \
  --secret-id eo-re-d01-secretsmng-apne1 \
  --secret-string '{"LAMBDA_REQUEST_SECRET": "実際のシークレット値"}' \
  --region ap-northeast-1
```

### 3-2. IAM Access Key の作成

n8n から Lambda を呼び出すためのアクセスキーを作成します。

1. AWS コンソール > IAM > ユーザー > `eo-re-d01-lambda-apne1-iamu`
2. 「セキュリティ認証情報」タブ
3. 「アクセスキーを作成」
4. 「AWS の外部で実行されるアプリケーション」を選択
5. 説明タグ: `eo-re-d01-lambda-apne1-iamu-access-key`
6. 「アクセスキーを作成」
7. **CSV をダウンロード**（`eo-re-d01-lambda-apne1-iamu_accessKeys.csv`）

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
3. Function Name or ID: `eo-re-d01-lambda-apne1`
4. 「Save」

---

## STEP 5: GitHub Actions 設定

### 5-1. GitHub Secrets の設定

CloudFormation Outputs から `GitHubActionsDeployRoleArn` の値を取得し、GitHub に設定します。

**ARN の確認:**
- AWS コンソール > CloudFormation > スタック > 出力タブ > `GitHubActionsDeployRoleArn`
- 例: `arn:aws:iam::123456789012:role/eo-re-d01-lambda-apne1-ghactions-deploy-iamr`

**GitHub への設定:**
1. GitHub リポジトリ > Settings > Secrets and variables > Actions
2. 「New repository secret」
3. Name: `EO_LAMBDA_DEPLOY_AWS_APNE1_ROLE_FOR_GITHUB`
4. Secret: 上記で取得した ARN
5. 「Add secret」

### 5-2. GitHub Actions ワークフローの確認

`.github/workflows/deploy-to-aws-lambda-apne1.yml` が設定済みであることを確認してください。

詳細: [LAMBDA_README.md](../apne1/LAMBDA_README.md) の「github workflow AWS Lambda自動デプロイ」セクション参照

---

## STEP 6: n8n ワークフローノード設定

STEP 4 で Credential と #280AWS ノードの設定が完了しました。次に、ワークフローを実行するために必要なノード設定を行います。

**👉 [N8N_NODE_SETUP.md](../../../EO_n8nWorkflow_Json/N8N_NODE_SETUP.md)** を参照してください。

以下の設定を行います（全 Request Engine 共通）：

1. **#010 XMLサイトマップURL設定** — Warmup対象サイトのサイトマップURLを設定
2. **#015-020 DNS認証設定** — ドメイン所有権のDNS TXTレコード検証を設定
3. **#180 Request Engine 設定** — クラウド・リージョン・言語を設定
4. **動作確認** — ワークフローをテスト実行

---

## パラメータ一覧

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| **命名規則** |||
| ProjectPrefix | `eo` | プロジェクトプレフィックス |
| Component | `re` | コンポーネント識別子（Request Engine） |
| Environment | `d01` | 環境識別子（dev01, prod01等） |
| RegionShort | `apne1` | リージョン短縮名 |
| **AWSアカウント** |||
| AWSAccountId | (入力必須) | 12桁のAWSアカウントID |
| AWSRegion | `ap-northeast-1` | デプロイ先リージョン |
| **Lambda設定** |||
| PythonRuntime | `python3.14` | Pythonランタイムバージョン |
| LambdaLayerName | `eo-re-d01-lambda-py314-slim-layer` | Lambda Layer 名 |
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
2. または `Environment` パラメータを変更（例: `d01` → `d02`）

### Secrets Manager の値が反映されない

**原因**: Lambda がシークレットをキャッシュしている
**解決**: Lambda 関数を再デプロイ（GitHub Actions でプッシュ、または手動デプロイ）

---

## 関連ドキュメント

- [N8N_NODE_SETUP.md](../../../EO_n8nWorkflow_Json/N8N_NODE_SETUP.md) - n8nワークフローノード設定ガイド（#010/DNS認証/#180/動作確認）
- [LAMBDA_README.md](../apne1/LAMBDA_README.md) - Lambda 詳細セットアップ手順
- [RE_README.md](../../RE_README.md) - Request Engine 全体のセキュリティ設定
- [N8N_WORKFLOW_README.md](../../../EO_n8nWorkflow_Json/N8N_WORKFLOW_README.md) - n8nワークフロー設定ガイド
- [NODE180_REQUESTENGINE_README.md](../../../EO_n8nWorkflow_Json/NODE180_REQUESTENGINE_README.md) - Request Engine設定ガイド（type_area・accept_language一覧）
- [NODE175_USERAGENT_README.md](../../../EO_n8nWorkflow_Json/NODE175_USERAGENT_README.md) - User-Agent設定ガイド
