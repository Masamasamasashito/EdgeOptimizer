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

> **💡 WSL2 / Docker 環境が無い場合:** Lambda Layer の zip ファイルはリポジトリに同梱されています。Docker でビルドせずに、以下のファイルをそのまま AWS コンソールからアップロードできます：
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
