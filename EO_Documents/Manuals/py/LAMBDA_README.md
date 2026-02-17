# AWS Lambda Request Engine - 手動セットアップ手順

> **📋 概要**
>
> このドキュメントは、Edge Optimizer の AWS Lambda Request Engine を **手動で** セットアップする手順です。
>
> | 項目 | 内容 |
> |------|------|
> | ⏱ 所要時間 | 約 60〜90 分（初回） |
> | 📊 難易度 | ⭐⭐⭐（中〜上級） |
> | 🔧 ステップ数 | 全 11 ステップ |
> | 🐧 必要環境 | WSL2 + Docker（Lambda Layer 作成時） |

> **⚡ CloudFormation（CFn）版を強く推奨します**
>
> 手動セットアップは 11 ステップあり、IAM ポリシー・ロール・Secrets Manager など多くの AWS リソースを個別に作成する必要があります。
>
> **[CloudFormation 版](LAMBDA_CFN_README.md)** を使えば、Lambda Layehr 作成以外のリソースを **ワンクリックで一括作成** できます。
>
> - ✅ IAM ユーザー・ポリシー・ロールを自動作成
> - ✅ Secrets Manager を自動作成
> - ✅ GitHub Actions OIDC 連携を自動設定
> - ✅ 命名規則の統一を自動保証
>
> 👉 **初めての方は [CloudFormation 版の手順](LAMBDA_CFN_README.md) を使ってください。**

---

## 前提条件チェックリスト

セットアップを始める前に、以下が揃っていることを確認してください：

- [ ] AWS アカウントを持っている
- [ ] AWS マネジメントコンソールに管理者権限でアクセスできる
- [ ] Edge Optimizer のインフラ（Docker + n8n）が起動済み（[QUICK_START.md](../../../QUICK_START.md) の Step 1〜3 完了）
- [ ] `EO_Infra_Docker/.env` ファイルの `N8N_EO_REQUEST_SECRET` の値を確認できる
- [ ] WSL2 + Docker が使える環境がある（Lambda Layer 作成のため）
- [ ] n8n ワークフロー JSON をインポート済み（[QUICK_START.md](../../../QUICK_START.md) の Step 5）

---

**重要**: リクエストエンジン接続認証と照合用リクエストシークレットによるトークン検証に関する命名や設定の詳細は、[RE_README.md](../RE_README.md) を参照してください。

---

## 目次

1. [Lambda 関数の作成](#1-lambda作る)
2. [CloudWatch Logs 保持期間の設定](#2-テストを1回実行しログ作って保持設定期間を1日にする)
3. [アクセスキー用 IAM Policy 作成](#3-アクセスキー用iam-policy作成)
4. [IAM User 作成・アクセスキー発行](#4-iam-usern8n-httpリクエストノードからlambdaへのリクエストの認証用-作成--アクセスキー発行)
5. [n8n Credential 設定](#5-n8n-280系リクエストエンジンlambdaノード用credential設定)
6. [AWS Secrets Manager 設定](#6-aws-secrets-manager-設定)
7. [Lambda 用 IAM Role ポリシー追加](#7-aws-secrets-manager-の照合用リクエストシークレットをlambdaで取得するためのiam-role-for-lambda)
8. [Lambda Layer 作成（Docker）](#8-python-314-lambda-layer-を-docker-で作る)
9. [Lambda Layer 設定](#9-lambda-layer-設定)
10. [Lambda タイムアウト設定](#10-lambda-タイムアウト設定)
11. [Cloudflare WAF ルール設定（オプション）](#step-11-cloudflare-wafセキュリティカスタムルール設定オプション)

---

## 1. Lambda作る

> 💡 **CFn版の場合**: この手順は CloudFormation が自動で実行します。[CFn版 STEP 2](LAMBDA_CFN_README.md) を参照。

- IAMポリシーにLambdaのARNが必要だからLambdaを先に作る必要あり
- 付随して作られるCWLogsロググループの保持期間とIAMポリシーに注意が必要

- 関数名
  - eo-re-d01-lambda-apne1
      - eoはEdge Optimizerの略称
      - reはRequest Engineの略称
      - d01はdev01の略称
      - apne1はap-northeast-1の略称
- ランタイム
  - Python3.14
- タグ
  - Name: eo-re-d01-lambda-apne1

※GCPサービスアカウント名30文字制限が根底にあり、短縮化している。

## 2. テストを1回実行し、ログ作って、保持設定(期間)を1日にする

> 💡 **CFn版の場合**: CloudWatch Logs ロググループは CloudFormation が保持期間 1 日で自動作成します。

## 3. アクセスキー用IAM Policy作成

> 💡 **CFn版の場合**: IAM ポリシーは CloudFormation が自動作成します。

n8nの280系のリクエストエンジンLambdaノードがIAMユーザーのアクセスキーでLambdaを呼び出すためのポリシーを作成

eo-re-d01-lambda-apne1-access-key-iamp

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:ap-northeast-1:<AWSアカウントID>:function:eo-re-d01-lambda-apne1",
                "arn:aws:lambda:ap-northeast-1:<AWSアカウントID>:function:eo-re-d01-lambda-apne1:*"
            ]
        }
    ]
}
```

## 4. IAM User（n8n HTTPリクエストノードからLambdaへのリクエストの認証用） 作成 → アクセスキー発行

> 💡 **CFn版の場合**: IAM ユーザーは CloudFormation が自動作成します。アクセスキーのみ手動発行が必要です（[CFn版 STEP 3-2](LAMBDA_CFN_README.md)）。

1. IAMユーザー
    - eo-re-d01-lambda-apne1-iamu
2. AWS マネジメントコンソールへのユーザーアクセスを提供する
    - チェックしない
3. ユーザーグループ無し
4. ポリシーを直接アタッチする
    - eo-re-d01-lambda-apne1-access-key-iamp
5. IAMU作ったら、セキュリティ認証情報でアクセスキー/シークレットアクセスキーを作成
    1. AWS の外部で実行されるアプリケーション
        - n8nからLambdaを呼び出すため
    2. 説明タグ値
        - eo-re-d01-lambda-apne1-iamu-access-key
    3. csvでアクセスキー/シークレットアクセスキーをダウンロードする
        - eo-re-d01-lambda-apne1-iamu_accessKeys.csv
6. 完了を押下

## 5. n8n 280系リクエストエンジンLambdaノード用Credential設定

> 💡 **CFn版の場合**: この手順は手動・CFn版共通です。[CFn版 STEP 4](LAMBDA_CFN_README.md) を参照。

n8nの280系のリクエストエンジンLambdaノードで使うCredentialを作成

1. n8n 左サイドバー「Personal」 > 「Credentials」 > 「Create Credential」
2. Credential Type: AWS(IAM) を選択 > Continue
3. Name: EO_RE_AWS_AccessKey など
4. Region > apne1（ap-northeast-1、your own region）
5. eo-re-d01-lambda-apne1-iamu_accessKeys.csvよりAccess Key ID と Secret Access Key を入力
6. 右上の「Save」ボタンをクリック
7. Green で Connection tested successfully が表示されたら成功

n8nの280系のリクエストエンジンLambdaノードにCredentialを設定

1. n8n左サイドバー「Overview」 > 「Workflows」 > 該当のWorkflowを開く
2.  280AWS-apne1 RequestEngine AccessKeyノードを開く > 「Parameters」タブ > 「Credential to connect with」
3.  EO_RE_AWS_AccessKeyを選択
   「EO_RE_AWS_AccessKey」を選択
4. Function Name or ID > Expression > Lambda関数名を入力
   EX) eo-re-d01-lambda-apne1
5. Workflow画面で「Save」ボタンをクリック

## 6. AWS Secrets Manager 設定

> 💡 **CFn版の場合**: Secrets Manager シークレットは CloudFormation が自動作成します。値の更新のみ手動で行います（[CFn版 STEP 3-1](LAMBDA_CFN_README.md)）。

AWS Secrets ManagerでSecretを作成

**重要**: シークレット名は、Lambda関数コード内で使用されている`eo-re-d01-secretsmng-apne1`と一致させる必要があります。

東京リージョン（apne1 / ap-northeast-1）

1. 「新しいシークレットを保存する」を選択
2. 「その他のシークレットのタイプ」を選択
3. シークレットキー：`LAMBDA_REQUEST_SECRET`（Lambda関数コード内のLAMBDA_REQUEST_SECRET_KEY_NAMEに格納定義しているシークレットキー名）
4. シークレットの値：`EO_Infra_Docker\.env`ファイルの`N8N_EO_REQUEST_SECRET`の値をコピーして設定
5. 暗号化キー
   - aws/secretsmanager（デフォルトのKMSキー）
6. シークレットの名前
   - `eo-re-d01-secretsmng-apne1`（コード内のLAMBDA_REQUEST_SECRET_NAMEに格納定義しているシークレット名）
7. オプションの説明
   - N8N_EO_REQUEST_SECRET と同じ値を、Lambda Request Engine が SecretsMng から照合用リクエストシークレットとして取得する。n8nとリクエストエンジンで生成した各トークンを照合するため。
8. 「次へ」をクリック
9. 「次へ」をクリック（自動ローテーションは不要）
10. 「保存」をクリック
11. シークレットのARNをメモっておく（IAMポリシーで使用します）

更新方法:「シークレットの値を取得する」をクリック、「編集する」をクリックすると値を変更できる。

## 7. AWS Secrets Manager の照合用リクエストシークレットをLambdaで取得するためのIAM Role for Lambda

> 💡 **CFn版の場合**: IAM ロール・ポリシーは CloudFormation が自動作成します。

IAMポリシー作成:`eo-re-d01-lambda-apne1-role-iamp`

eo-re-d01-lambda-apne1のLambdaのIAMロールに対して、eo-re-d01-lambda-apne1-role-iamp のIAMポリシーを作り、LambdaのIAMロールに対して追加する

説明 > AWS Secrets Manager の照合用リクエストシークレットをLambdaで取得するためのIAMポリシー

eo-re-d01-lambda-apne1-role-xxxxxxxx ←CWLogs用のポリシーは勝手に作られる

**重要**: シークレット名は、コード内で使用されている`eo-re-d01-secretsmng-apne1`と一致させる必要があります。

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowReadRequestSecret",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:ap-northeast-1:<AWSアカウントID>:secret:eo-re-d01-secretsmng-apne1-*"
        }
    ]
}
```

> 注意:
> - `<AWSアカウントID>`を実際のAWSアカウントIDに置き換えてください
> - シークレット名を変えない場合、シークレット名の末尾でワイルドカード（`-*`）を使用することで、シークレットのバージョンに関係なくアクセスできます

## 8. Python 3.14 Lambda Layer を Docker で作る

> ⚠️ **この手順は手動・CFn版共通で必須です。** Lambda Layer は CloudFormation では作成できないため、手動で作成する必要があります。
>
> **必要環境**: WSL2 + Docker（Windows の場合）

```bash
# 1. ディレクトリ移動
cd RequestEngine/aws/lambda/py

# 2. WSL2 Ubuntu起動(slimのバージョンを調べて、zip名称を変更する)
wsl -d Ubuntu

# 3. docker compose 実行
docker compose run --rm lambda_layer_builder

# 4. WSL終了
exit
```

## 9. Lambda Layer 設定

> 💡 **CFn版の場合**: Lambda Layer の関数へのアタッチは CloudFormation が自動で行います。Layer の作成（Step 8）のみ手動で行ってください。

レイヤー名はDockerで作ったzipファイルの名称に合わせる

1. Lambda の レイヤー
2. レイヤーを作成
   - `eo-re-d01-lambda-py314-slim-layer`
3. 「カスタムレイヤー」→ さきほど作った `funcfiles/requests-py314-slim-layer.zip` を選択
4. 作成
5. ARNをメモる
6. Lambda関数へ
7. コード （下のほう）レイヤー
8. レイヤーの追加
9. ARNを指定
10. 貼り付け
11. 追加

## 10. Lambda タイムアウト設定

> 💡 **CFn版の場合**: タイムアウトは CloudFormation パラメータ `LambdaTimeout` で設定済み（デフォルト 30 秒）。

**重要**: Lambda関数のタイムアウトは、HTTPリクエストのタイムアウト（10秒）とリトライ（最大2回）を考慮して、最低30秒以上に設定する必要があります。

1. AWSコンソールで該当Lambda関数（`eo-re-d01-lambda-apne1`）を開く
2. 「設定」タブ > 「一般設定」 > 「編集」
3. 「タイムアウト」を 30秒以上（推奨: 60秒）に設定
4. 「保存」

> **タイムアウト計算の根拠:**
> - HTTPリクエストタイムアウト: 10秒
> - 最大リトライ回数: 2回（初回含めて合計3回）
> - リトライ待機時間: 0.5秒、1.0秒、2.0秒...
> - 最悪の場合の実行時間: 約31.5秒以上
> - そのため、Lambda関数のタイムアウトは最低30秒、推奨60秒に設定してください

AWS CLIでタイムアウトを設定する場合:

```bash
aws lambda update-function-configuration \
  --function-name eo-re-d01-lambda-apne1 \
  --timeout 60 \
  --region ap-northeast-1
```

## STEP 11. Cloudflare WAFセキュリティカスタムルール設定（オプション）

> ⚠️ **現状、ASNが固定である保証がないため、この設定は推奨しません。** 参考情報として記載しています。

**手順①：AWS AS番号（ASN）の特定**

AWSは複数のASNを使用しており、Lambdaで主に使用されるのは以下の通りです：

- `AS16509`（Amazon.com - グローバルで共通利用）
- `AS14618`（Amazon Data Services Japan - 日本国内向け）

> ※IP範囲は動的に変更されるため、IPアドレスリスト（CIDR）管理は非推奨です。

**手順②：Cloudflare カスタムルール作成**

Cloudflareダッシュボード > ドメインを選択 > Security > セキュリティルール > Custom Rules

| 設定項目 | 値 |
|----------|------|
| Action | Block |

**式（Expression）の例:**

ロジックの意訳: 「ターゲットのパスへのアクセスであり」かつ「（正しいヘッダーが無い OR 日本からのアクセスではない OR AWSのASNではない）場合」はブロックする。

```
(http.request.uri.path eq "/target-endpoint-path") AND (
  NOT http.request.headers["x-custom-auth-token"] eq "YOUR_SECRET_VALUE_HERE"
  OR NOT ip.geoip.country eq "JP"
  OR NOT ip.geoip.asnum in {16509 14618}
)
```

---

## 参考: GitHub Actions による自動デプロイ

> 💡 **CFn版の場合**: OIDC プロバイダーと IAM ロールは CloudFormation が自動作成します。GitHub Secrets の設定のみ手動で行います（[CFn版 STEP 5](LAMBDA_CFN_README.md)）。

GitHubへのPushをトリガーに、OIDC（ID連携）を利用して一時的な認証トークンを取得し、Lambdaコードを自動更新する設定です。

> 参考: [AWS Lambda が関数のデプロイを簡素化する GitHub Actions をサポート](https://github.com/aws-actions/aws-lambda-deploy)

### 参考ステップ1：IDプロバイダの作成

AWSコンソールの IAM > IDプロバイダ へ移動。

1. 「プロバイダを追加」をクリック
2. プロバイダのタイプ: OpenID Connect
3. プロバイダのURL: `https://token.actions.githubusercontent.com`
4. 対象者 (Audience): `sts.amazonaws.com`
5. タグ: Name → `eo-ghactions-idp-request-engine-lambda-aws-apne1`

### 参考ステップ2：IAMポリシー作成

命名：`eo-re-d01-lambda-apne1-ghactions-deploy-iamr-iamp`

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LambdaDeploymentPermissions",
            "Effect": "Allow",
            "Action": [
                "lambda:GetFunctionConfiguration",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "lambda:GetFunction"
            ],
            "Resource": "arn:aws:lambda:ap-northeast-1:<AWSアカウントID>:function:eo-re-d01-lambda-apne1"
        }
    ]
}
```

### 参考ステップ3：IAMロールの作成

GitHub Actionsが使用する専用ロールを作成します。

命名：`eo-re-d01-lambda-apne1-ghactions-deploy-iamr`

1. IAM > ロール > [ロールを作成] をクリック
2. 信頼されたエンティティタイプ > ウェブアイデンティティ を選択
3. プロバイダ: `token.actions.githubusercontent.com`
4. Audience: `sts.amazonaws.com`
5. 許可の境界: 設定しない
6. アクセス許可に `eo-re-d01-lambda-apne1-ghactions-deploy-iamr-iamp` を追加

> **重要**: 信頼関係のポリシーで、ConditionのStringLikeの`token.actions.githubusercontent.com:sub`でリポジトリのブランチを `*` 指定可能。

**信頼関係ポリシーの例:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::<AWSアカウントID>:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:<Github組織名orユーザー名>/<Githubリポジトリ名>:ref:refs/heads/*"
                }
            }
        }
    ]
}
```

### 参考ステップ4： GitHub Actions Secrets の設定

| Secret名 | 値 |
|----------|------|
| `EO_LAMBDA_DEPLOY_AWS_APNE1_ROLE_FOR_GITHUB` | `eo-re-d01-lambda-apne1-ghactions-deploy-iamr` のARN |

### 参考ステップ5：GitHubワークフロー

作成済：`.github/workflows/deploy-to-lambda-apne1.yml`

設定値を確認してください。

---

## 関連ドキュメント

- [CloudFormation 版セットアップ手順（推奨）](LAMBDA_CFN_README.md)
- [Request Engine セキュリティ設定](../RE_README.md)
- [QUICK_START.md（全体の導入ガイド）](../../../QUICK_START.md)
