# Edge Optimizer

**GEO分散 × アセットWarmup × URLフィルタリング × バリアント対応 × 4層セキュリティ**を兼ね備えた、唯一のCDNキャッシュWarmup OSS

CRAFTED BY にしラボ (https://4649-24.com)

## What is Edge Optimizer?

**Edge Optimizer (EO)** は、AWS Lambda / Azure Functions / GCP Cloud Run / Cloudflare Workers のサーバーレス関数からGEO分散リクエストを実行し、世界中のCDNエッジにキャッシュを生成できるOSSです。

n8n（ワークフローオーケストレーション）+ Playwright（ヘッドレスブラウザ）+ Request Engine（サーバーレス関数）の3層アーキテクチャで、メインドキュメント＋全アセット（CSS/JS/画像/フォント）を、任意のUser-Agent/Accept-Languageバリアントで、世界中からWarmupできます。

## こんな経験、ありませんか？

> 💸 広告キャンペーン開始直後、LCPが3秒超えてCVRが激減した
>
> 😱 デプロイ直後の初回アクセスだけ異常に遅い（でも放置してる）
>
> 🌏 「海外からのアクセスが遅い」とクレームが来たが、打つ手がない
>
> 📊 CDN入れたのにキャッシュヒット率が上がらない、原因不明

**原因はすべて同じ：CDNエッジにキャッシュが無い**

既存のCache Warmerは「メインドキュメントだけ」「単一ロケーション」しかWarmupしません。Edge Optimizerは、**世界中のエッジに、全アセットも、想定されたペルソナのバリアントで事前にWarmup**できます。

## 機能比較

| 機能 | 既存Cache Warmer | Edge Optimizer |
|-----|------------------|----------------|
| **アセットWarmup** | ❌ メインドキュメント止まり | ✅ メインドキュメント/CSS/JS/画像/フォント全対応 |
| **GEO分散リクエスト** | ❌ 単一ロケーション | ✅ AWS/Azure/GCP/CF Workers |
| **現地CDNエッジWarmup** | ❌ ツール実行地のみ | ✅ ユーザーが居る現地エッジを直接Warmup |
| **URLフィルタリング** | ❌ XMLサイトマップ全件 | ✅ キャッシュすべきURLのみにフィルタリング |
| **バリアント対応** | ❌ 固定UA or 無配慮 | ✅ User-Agent/Accept-Language自由設定 |
| **セキュリティ** | ⚠️ 簡易的 | ✅ 4層（DNS認証/クラウド認証/トークン照合/レート制御） |
| **オーケストレーション** | ❌ なし | ✅ n8nでノーコード/ローコード自動化 |
| **IaC** | ❌ なし | ✅ CloudFormation, Bicep, GitHub Actions |

## 対応CDN

Request EngineはレスポンスヘッダーからCDNを自動検出します。

| CDN | 検出ヘッダー |
|-----|------------|
| Cloudflare | `cf-ray` |
| AWS CloudFront | `x-amz-cf-id` |
| Azure Front Door | `x-azure-ref` |
| Akamai | `x-akamai-request-id` |
| Fastly | `x-served-by` |
| Vercel | `x-vercel-cache` |
| GCP CDN | `server: google-edge-cache` |
| NitroCDN | `x-nitro-cache` |
| RabbitLoader | `x-rl-cache` |

## コスト

- **維持費**: ゼロ円（OSS/セルフホスティング）
- **稼働コスト**: サーバーレス関数の従量課金 + self hosted n8n実行環境

## ユースケース

Edge Optimizerはキャッシュウォーマーだけではありません。GEO分散リクエスト基盤として、様々な用途に活用できます。

| ユースケース | 説明 |
|-------------|------|
| **CDNキャッシュWarmup** | デプロイ後・キャンペーン前・通常稼働時に世界中のCDNエッジにキャッシュを事前生成 |
| **パフォーマンス計測** | 各リージョンからのレスポンスタイム・TTFB・キャッシュヒット率を定点観測 |
| **CDN設定検証** | Cache-Control、Vary、CDN固有ヘッダーが意図通りに動作しているか確認 |
| **セキュリティ監査** | セキュリティヘッダー（CSP、HSTS、X-Frame-Options等）の設定状況を一括チェック |
| **AI学習データ収集** | Webページのメタデータ・構造化データを世界各地から収集・クレンジング |
| **多言語サイト検証** | Accept-Languageバリアントごとに正しいコンテンツが返されるか確認 |
| **モバイル/デスクトップ検証** | User-Agentバリアントごとにレスポンスの差異を検出 |
| **外形監視** | 定期実行で世界各地からのアクセス可否・レスポンス異常を検知 |

# Quick Start

Pls create work directory.

EX)
```
mkdir ~/work/docker | cd
```

## 1. git clone
```
git clone https://github.com/Masamasamasashito/EdgeOptimizer.git
```

## 2. Get Ready EO_Infra_Docker/.env

All Docker Compose related files (docker-compose.yml, env.example, caddy/Caddyfile, and service-specific Dockerfiles) are located in the `EO_Infra_Docker` directory.

```
cd EdgeOptimizer/EO_Infra_Docker
cp env.example .env
```

## 3. Generate security keys on EO_Infra_Docker/.env (Crucial step!)

Run the command below for your OS in your terminal to append secrets to `EO_Infra_Docker/.env` (You only need to do this once)

**Note:** Make sure you are in the `EO_Infra_Docker` directory or adjust the paths accordingly.

🍎 macOS / 🐧 Linux (Copy & Paste into Terminal)
```
cd EO_Infra_Docker
echo "" >> .env
echo "N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)" >> .env
echo "N8N_EO_REQUEST_SECRET=$(openssl rand -hex 32)" >> .env
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=')" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=')" >> .env
echo "SEARXNG_CONTAINER_SECRET=$(openssl rand -hex 32)" >> .env
```

🪟 Windows PowerShell (Copy & Paste into PowerShell)
```
cd EO_Infra_Docker
"" | Add-Content .env
$bytes = New-Object byte[] 32; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); $hex = -join ($bytes | ForEach-Object { $_.ToString("x2") }); "N8N_ENCRYPTION_KEY=$hex" | Add-Content .env
$bytes = New-Object byte[] 32; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); $hex = -join ($bytes | ForEach-Object { $_.ToString("x2") }); "N8N_EO_REQUEST_SECRET=$hex" | Add-Content .env
$bytes = New-Object byte[] 32; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); $base64 = [Convert]::ToBase64String($bytes) -replace '[\/+=]', ''; "POSTGRES_PASSWORD=$base64" | Add-Content .env
$bytes = New-Object byte[] 32; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); $base64 = [Convert]::ToBase64String($bytes) -replace '[\/+=]', ''; "REDIS_PASSWORD=$base64" | Add-Content .env
$bytes = New-Object byte[] 32; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); $hex = -join ($bytes | ForEach-Object { $_.ToString("x2") }); "SEARXNG_CONTAINER_SECRET=$hex" | Add-Content .env
```

## 4. Environment Variable Access in n8n Workflows

**Important**: To use environment variables (e.g., `{{ $env.N8N_EO_REQUEST_SECRET }}`) in n8n workflows, you need to configure environment variable access permissions.

### Configuration

#### 1. Set Environment Variable in `EO_Infra_Docker/.env` File

The `N8N_EO_REQUEST_SECRET` value must be set in `EO_Infra_Docker/.env` file. This is automatically generated when you run the commands in **Section 3** above. If you need to set it manually, add the following line to your `EO_Infra_Docker/.env` file:

```
N8N_EO_REQUEST_SECRET=your_secret_value_here
```

#### 2. Docker Compose Configuration

The `EO_Infra_Docker/docker-compose.yml` file includes the following settings:

```yaml
N8N_EO_REQUEST_SECRET: ${N8N_EO_REQUEST_SECRET}
N8N_BLOCK_ENV_ACCESS_IN_NODE: false
```

- **`N8N_EO_REQUEST_SECRET: ${N8N_EO_REQUEST_SECRET}`**: This reads the value from the `EO_Infra_Docker/.env` file (set in step 1) and passes it to the n8n container as an environment variable. It can then be accessed in workflows using `{{ $env.N8N_EO_REQUEST_SECRET }}`.
- **`N8N_BLOCK_ENV_ACCESS_IN_NODE: false`**: This setting allows workflows to access environment variables. Setting it to `true` would block access to all environment variables from expressions and Code nodes.

### Important Notes

- **Preview Limitation**: When previewing expressions in the n8n UI (manual execution), you may see an "access to env vars denied" error. This is a known limitation and can be ignored. Environment variables work correctly during actual workflow execution (automated runs).
- **Reference**: For more details, see:
  - [n8n Official Documentation: Environment Variables Security](https://docs.n8n.io/hosting/configuration/environment-variables/security/)
  - [n8n Community Discussion: No access to $env](https://community.n8n.io/t/no-access-to-env/20665)

### Usage in Workflows

In your n8n workflows (e.g., the "170 n8n RequestSecret Token Generator" node), you can access environment variables using:

```
{{ $json.url }}{{ $env.N8N_EO_REQUEST_SECRET }}
```

This is required for the Request Engine token generation process.

## 5. Start Containers

Navigate to the `EO_Infra_Docker` directory and start the containers:

```
cd EO_Infra_Docker
docker compose up -d
```

> [!TIP]
> **Running Multiple Instances / Avoiding Port Conflicts**
> By default, ports are bound to `127.0.0.1` (localhost) to ensure security and reduce port conflicts on your host machine.
> You can customize this behavior or the specific ports used by editing the `EO_Infra_Docker/.env` file (e.g., `DOCKER_HOST_BIND_ADDR`, `DOCKER_HOST_PORT_N8N_CONTAINER`).
>
> **⚠️ CRITICAL: Running Multiple Local Environments**
> If you want to run multiple environments on the same machine:
> 1. **Change ALL VOLUME NAMES** in `EO_Infra_Docker/.env` (e.g., add `_v2` suffix) to prevent data collision
> 2. **Change `DOCKER_HOST_BIND_ADDR`** to a different IP (e.g., `127.0.0.2`, `127.0.0.3`) to avoid port binding conflicts
> 3. **Update `N8N_WEBHOOK_URL`** to match the new IP address
> 
> **WARNING**: If you skip changing volume names, multiple environments will share the SAME volumes, causing data corruption, loss, or overwriting. One environment's data may be completely lost when the other is stopped/removed.
> 
> See `EO_Infra_Docker/env.example` for detailed instructions in the "ADVANCED: Running Multiple Local Environments" section.

### Production Setup (with Caddy)
To start with Caddy (Reverse Proxy), use the `prod` profile.
*Ensure `PRODUCTION=true` and valid domain/email settings in `EO_Infra_Docker/.env` if enabling secure cookies/SSL.*

```
cd EO_Infra_Docker
docker compose --profile prod up -d
```

## 6. n8n Launch Check(local self-hosted)

open : [http://localhost:5678](http://localhost:5678)

# 【Recommended to try】n8n Queue Mode Test

we recommend using the n8n Queue Mode Test as a measure to prevent memory exhaustion in n8n.
[n8nQueueModeTest](n8nQueueModeTest)

# 7. Setup Request Engine

Request Engine is an essential component running on Serverless Computing, designed for purposes such as cache performance verification from edge locations, cache warmup, and security checks.

👉 See detailed setup guide here:
- [RE_README.md](RequestEngine/RE_README.md) - Request Engine全体
- [LAMBDA_README.md](RequestEngine/aws_lambda/apne1/LAMBDA_README.md) - AWS Lambda
- [LAMBDA_CFN_README.md](RequestEngine/aws_lambda/CFn/LAMBDA_CFN_README.md) - AWS Lambda CFn 👈 Recommend!
- [AZFUNC_README.md](RequestEngine/azure_functions/jpeast/AZFUNC_README.md) - Azure Functions
- [AZFUNC_BICEP_README.md](RequestEngine/azure_functions/bicep/AZFUNC_BICEP_README.md) - Azure Bicep
- [CFWORKER_README.md](RequestEngine/cloudflare_workers/global/CFWORKER_README.md) - Cloudflare Workers
- [RUN_README.md](RequestEngine/gcp_cloudrun/ane1/RUN_README.md) - GCP Cloud Run

# 8. n8n Workflow Setup

n8nワークフローのインポートと設定ガイドです。

👉 See detailed setup guide here:
- [N8N_WORKFLOW_README.md](EO_n8nWorkflow_Json/N8N_WORKFLOW_README.md) - n8nワークフロー設定ガイド（インポート・Credentials・ノード設定）
- [NODE175_USERAGENT_README.md](EO_n8nWorkflow_Json/NODE175_USERAGENT_README.md) - User-Agent設定ガイド（iOS/Android/Desktop一覧）
- [NODE180_REQUESTENGINE_README.md](EO_n8nWorkflow_Json/NODE180_REQUESTENGINE_README.md) - Request Engine設定ガイド（type_area/accept_language一覧・280ノード作成方法）


