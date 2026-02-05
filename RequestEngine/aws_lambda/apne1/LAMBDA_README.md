# eo-request-engine

**重要**: リクエストエンジン接続認証と照合用リクエストシークレットによるトークン検証に関する命名や設定の詳細は、[RequestEngine\RE_README.md](../RE_README.md) を参照してください。

## 1. Lambda作る

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
## 3. アクセスキー用IAM Policy作成

n8nの280系のリクエストエンジンLambdaノードがIAMユーザーのアクセスキーでLambdaを呼び出すためのポリシーを作成

eo-re-d01-lambda-apne1-access-key-iamp

```
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
## 4. IAM User（n8n HTTPリクエストノードからLambdaへのリクエストの認証用）作成 → アクセスキー発行

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

n8nの280系のリクエストエンジンLambdaノードで使うCredentialを作成

1. n8n 左サイドバー「Personal」 > 「Credentials」 > 「Create Credential」
2. Credential Type: AWS(IAM) を選択 > Continue
3. Name: `EO_RE_AWS_AccessKey` など
4. Region > apne1（ap-northeast-1、your own region）
5. `eo-re-d01-lambda-apne1-iamu_accessKeys.csv`よりAccess Key ID と Secret Access Key を入力
6. 右上の「Save」ボタンをクリック
7. Green で Connection tested successfully が表示されたら成功

n8nの280系のリクエストエンジンLambdaノードにCredentialを設定

1. n8n左サイドバー「Overview」 > 「Workflows」 > 該当のWorkflowを開く
2. `280AWS-apne1 RequestEngine AccessKey`ノードを開く > 「Parameters」タブ > 「Credential to connect with」
3. `EO_RE_AWS_AccessKey`を選択
「EO_RE_AWS_AccessKey」を選択
4. Function Name or ID > Expression > Lambda関数名を入力
EX) `eo-re-d01-lambda-apne1`
5. Workflow画面で「Save」ボタンをクリック

## 6. AWS Secrets Manager 設定

AWS Secrets ManagerでSecretを作成

**重要**: シークレット名は、Lambda関数コード内で使用されている`eo-re-d01-secretsmng-apne1`と一致させる必要があります。

1. 東京リージョン（apne1 / ap-northeast-1）
2. 「新しいシークレットを保存する」を選択
3. 「その他のシークレットのタイプ」を選択
   - シークレットキー：`LAMBDA_REQUEST_SECRET`（Lambda関数コード内の`LAMBDA_REQUEST_SECRET_KEY_NAME`に格納定義しているシークレットキー名）
   - シークレットの値：`EO_Infra_Docker\.env`ファイルの`N8N_EO_REQUEST_SECRET`の値をコピーして設定
4. 暗号化キー
   - `aws/secretsmanager`（デフォルトのKMSキー）
5. **シークレットの名前**
   - **`eo-re-d01-secretsmng-apne1`**（コード内の`LAMBDA_REQUEST_SECRET_NAME`に格納定義しているシークレット名）
6. オプションの説明
   - N8N_EO_REQUEST_SECRET と同じ値を、Lambda Request Engine が SecretsMng から照合用リクエストシークレットとして取得する。n8nとリクエストエンジンで生成した各トークンを照合するため。
7. 「次へ」をクリック
8. 「次へ」をクリック（自動ローテーションは不要）
9. 「保存」をクリック
10. シークレットのARNをメモっておく（IAMポリシーで使用します）

**更新方法**:「シークレットの値を取得する」をクリック、「編集する」をクリックすると値を変更できる。

## 7. AWS Secrets Manager の照合用リクエストシークレットをLambdaで取得するためのIAM Role for Lambda

**IAMポリシー作成**:`eo-re-d01-lambda-apne1-role-iamp`  
`eo-re-d01-lambda-apne1`のLambdaのIAMロールに対して、`eo-re-d01-lambda-apne1-role-iamp` のIAMポリシーを作り、LambdaのIAMロールに対して追加する

- 説明 > AWS Secrets Manager の照合用リクエストシークレットをLambdaで取得するためのIAMポリシー
- `eo-re-d01-lambda-apne1-role-xxxxxxxx` ←CWLogs用のポリシーは勝手に作られる

**重要**: シークレット名は、コード内で使用されている`eo-re-d01-secretsmng-apne1`と一致させる必要があります。

```
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

**注意**: 
- `<AWSアカウントID>`を実際のAWSアカウントIDに置き換えてください
- シークレット名を変えない場合、シークレット名の末尾でワイルドカード（`-*`）を使用することで、シークレットのバージョンに関係なくアクセスできます

## 8. Python 3.14 Lambda Layer を Docker で作る

移動
```
cd RequestEngine\aws_lambda\apne1
```

WSL2 Ubuntu起動(slimのバージョンを調べて、zip名称を変更する)
```
wsl -d Ubuntu
```
docker compose 実行
```
docker compose run --rm lambda_layer_builder
```
WSL終了
```
exit
```

## 9. Lambda Layer 設定

レイヤー名はDockerで作ったzipファイルの名称に合わせる

1. Lambda の レイヤー
2. レイヤーを作成
   - eo-re-d01-lambda-py314-slim-layer
4. 「カスタムレイヤー」→ さきほど作った `funcfiles/requests-py314-slim-layer.zip` を選択
5. 作成
6. ARNをメモる
7. Lambda関数へ
8. コード
9. （下のほう）レイヤー
10. レイヤーの追加
11. ARNを指定
12. 貼り付け
13. 追加

## 10. Lambda タイムアウト設定

**重要**: Lambda関数のタイムアウトは、HTTPリクエストのタイムアウト（10秒）とリトライ（最大2回）を考慮して、**最低30秒以上**に設定する必要があります。

1. AWSコンソールで該当Lambda関数（`eo-re-d01-lambda-apne1）を開く
2. 「設定」タブ > 「一般設定」 > 「編集」
3. 「タイムアウト」を **30秒以上**（推奨: 60秒）に設定
4. 「保存」

**注意**: 
- HTTPリクエストタイムアウト: 10秒
- 最大リトライ回数: 2回（初回含めて合計3回）
- リトライ待機時間: 0.5秒、1.0秒、2.0秒...
- 最悪の場合の実行時間: 約31.5秒以上
- そのため、Lambda関数のタイムアウトは**最低30秒、推奨60秒**に設定してください

**AWS CLIでタイムアウトを設定する場合**:
```bash
aws lambda update-function-configuration \
  --function-name eo-re-d01-lambda-apne1 \
  --timeout 60 \
  --region ap-northeast-1
```

## 11. Cloudflare WAFセキュリティカスタムルール設定

※ASN固定である保証はないため、現状、やらない。

手順①：AWS AS番号（ASN）の特定  
  
AWSは複数のASNがあり、Lambdaで主に使用されるのは以下  
  
- AS16509 (Amazon.com - グローバルで共通利用)
- AS14618 (Amazon Data Services Japan - 日本国内向け)
  
※IP範囲は動的に変更されるため、IPアドレスリスト（CIDR）管理は非推奨  
  
手順②：Cloudflare セキュリティ > セキュリティルール > カスタムルール作成  
  
Cloudflareダッシュボード > ドメインを選択 > Security > セキュリティルール > Custom Rules  
  
- Action: Block
- Expression Editor:

ロジックの意訳:  
「ターゲットのパスへのアクセスであり」かつ「（正しいヘッダーが無い OR 日本からのアクセスではない OR AWSのASNではない）場合」はブロックする。  
  
式（Expression）の例:  
  
```
(http.request.uri.path eq "/target-endpoint-path")
AND
(
  NOT http.request.headers["x-custom-auth-token"] eq "YOUR_SECRET_VALUE_HERE"
  OR
  NOT ip.geoip.country eq "JP"
  OR
  NOT ip.geoip.asnum in {16509 14618}
)
```

# 参考

- AWS CLI更新
  - [https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#windows-msi](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#windows-msi) からダウンロードインストール

# github workflow AWS Lambda自動デプロイ

GitHubへのPushをトリガーに、OIDC（ID連携）を利用して一時的な認証トークンを取得し、Lambdaコードを更新

- [AWS Lambda が関数のデプロイを簡素化する GitHub Actions をサポート](https://aws.amazon.com/jp/about-aws/whats-new/2025/08/aws-lambda-github-actions-function-deployment/)
- [https://github.com/aws-actions/aws-lambda-deploy](https://github.com/aws-actions/aws-lambda-deploy)

## ステップ1：IDプロバイダの作成

1. AWSコンソールの IAM > IDプロバイダ へ移動。
2. 「プロバイダを追加」をクリック。
    - プロバイダのタイプ: OpenID Connect
    - プロバイダのURL: https://token.actions.githubusercontent.com
    - 対象者 (Audience): sts.amazonaws.com
    - タグ:　Name　→　eo-ghactions-idp-request-engine-lambda-aws-apne1
      - IDプロバイダにつけるタグ

## ステップ2：IAMポリシー作成

命名：`eo-re-d01-lambda-apne1-ghactions-deploy-iamr-iamp`
```
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

## ステップ3：IAMロールの作成

GitHub Actionsが使用する専用ロールを作成します。  
命名：`eo-re-d01-lambda-apne1-ghactions-deploy-iamr`

1. IAM > ロール > [ロールを作成] をクリック。
  - 信頼されたエンティティタイプ > ウェブアイデンティティ を選択。
  - プロバイダ: `token.actions.githubusercontent.com`
  - Audience: `sts.amazonaws.com`
  - ここでリポジトリ等の条件も入力。
  - 許可の境界は、設定しない。
  - `eo-re-d01-lambda-apne1-ghactions-deploy-iamr-iamp`をアクセス許可で追加

**重要**
信頼関係のポリシーでConditionのStringLikeのtoken.actions.githubusercontent.com:subでリポジトリのブランチを以下のように`*`指定可能。

```
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

## ステップ4：

Github Actions secrets に以下を設定
  - `EO_LAMBDA_DEPLOY_AWS_APNE1_ROLE_FOR_GITHUB`
    - `eo-re-d01-lambda-apne1-ghactions-deploy-iamr`のARN

## ステップ5：GitHubワークフローの作成

作成済：`.github/workflows/deploy-to-lambda-apne1.yml`
設定値を確認
