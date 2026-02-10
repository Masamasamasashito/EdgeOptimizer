ortheast-1
```

## STEP 11. Cloudflare WAFセキュリティカスタムルール設定（オプション）

> ⚠️ **現状、ASNが固定である保証がないため、この設定は推奨しません。** 参考情報として記載しています。

**手順①：AWS AS番号（ASN）の特定**

AWSは複数のASNを使用しており、Lambdaで主に使用されるのは以下の通りです:

- `AS16509` (Amazon.com - グローバルで共通利用)
- `AS14618` (Amazon Data Services Japan - 日本国内向け)

> ※IP範囲は動的に変更されるため、IPアドレスリスト（CIDR）管理は非推奨です。

**手順②：Cloudflare カスタムルール作成**

Cloudflareダッシュボード > ドメインを選択 > Security > セキュリティルール > Custom Rules

| 設定項目 | 値 |
|----------|-----|
| Action | Block |

**式（Expression）の例:**

ロジックの意訳:「ターゲットのパスへのアクセスであり」かつ「正しいヘッダーが無い OR 日本からのアクセスではない OR AWSのASNではない」場合はブロックする。

```
(http.request.uri.path eq "/target-endpoint-path") AND (
  NOT http.request.headers["x-custom-auth-token"] eq "YOUR_SECRET_VALUE_HERE"
    OR NOT ip.geoip.country eq "JP"
      OR NOT ip.geoip.asnum in {16509 14618}
      )
      ```

      ---

      ## 参考: GitHub Actions による自動デプロイ

      GitHubへのPushをトリガーに、OIDC（ID連携）を利用して一時的な認証トークンを取得し、Lambdaコードを自動更新する設定です。

      > 参考: [AWS Lambda が関数のデプロイを簡素化する GitHub Actions をサポート](https://github.com/aws-actions/aws-lambda-deploy)

      ### 参考ステップ1：IDプロバイダの作成

      1. AWSコンソール > IAM >「IDプロバイダ」>「プロバイダを追加」
      2. 以下を設定:

      | 設定項目 | 値 |
      |----------|-----|
      | プロバイダのタイプ | OpenID Connect |
      | プロバイダのURL | `https://token.actions.githubusercontent.com` |
      | 対象者 (Audience) | `sts.amazonaws.com` |
      | タグ | Name: `eo-ghactions-idp-request-engine-lambda-aws-apne1` |

      ### 参考ステップ2：IAMポリシーの作成

      **ポリシー名:** `eo-re-d01-lambda-apne1-ghactions-deploy-iamr-iamp`

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

                                                                                  **ロール名:** `eo-re-d01-lambda-apne1-ghactions-deploy-iamr`

                                                                                  1. IAM > ロール >「ロールを作成」
                                                                                  2. 信頼されたエンティティタイプ:「ウェブアイデンティティ」を選択
                                                                                  3. プロバイダ: `token.actions.githubusercontent.com`
                                                                                  4. Audience: `sts.amazonaws.com`
                                                                                  5. 許可の境界: 設定しない
                                                                                  6. アクセス許可: `eo-re-d01-lambda-apne1-ghactions-deploy-iamr-iamp` を追加

                                                                                  > **重要**: 信頼関係のポリシーで、Conditionの `StringLike` でリポジトリのブランチを `*` 指定できます。

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
                                                                                                                                                                                                
                                                                                                                                                                                                ### 参考ステップ4：GitHub Actions Secrets の設定
                                                                                                                                                                                                
                                                                                                                                                                                                | Secret名 | 値 |
                                                                                                                                                                                                |-----------|-----|
                                                                                                                                                                                                | `EO_LAMBDA_DEPLOY_AWS_APNE1_ROLE_FOR_GITHUB` | `eo-re-d01-lambda-apne1-ghactions-deploy-iamr` のARN |
                                                                                                                                                                                                
                                                                                                                                                                                                ### 参考ステップ5：GitHubワークフロー
                                                                                                                                                                                                
                                                                                                                                                                                                作成済: `.github/workflows/deploy-to-lambda-apne1.yml`
                                                                                                                                                                                                
                                                                                                                                                                                                設定値を確認してください。
                                                                                                                                                                                                
                                                                                                                                                                                                ---
                                                                                                                                                                                                
                                                                                                                                                                                                > **AWS CLI更新**: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#windows-msi
