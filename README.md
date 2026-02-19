# Edge Optimizer

![Edge Optimizer — 世界中のCDNエッジを100%キャッシュ化するOSS Warmup基盤](EO_Documents/Images/EdgeOptimizer_thum_20260213.png)

**GEO分散 × アセットWarmup × URLフィルタリング × バリアント対応 × 4層セキュリティ**を兼ね備えた、唯一のCDNキャッシュWarmup OSS

CRAFTED BY [にしラボ / Nishi Labo](https://4649-24.com)

## 🎬 YOUTUBE

https://youtu.be/XYEp38gtJlU

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
| **IaC** | ❌ なし | ✅ CloudFormation, Bicep, Terraform, GitHub Actions |

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

## 実行結果・実証データ

実際のEdge Optimizer実行結果（AWS Lambda + Azure Functions → Cloudflare CDN）を分析したレポートです。1回目のWarmupでキャッシュMISS 231件を検知・修復し、2回目で全504リクエストがキャッシュHIT 100%を達成。市場における競合比較・ビジネスポテンシャルの考察も含みます。

👉 [ANALYSIS_REPORT.md](RequestResults/ANALYSIS_REPORT.md)

## 📖 ドキュメント索引

### Getting Started

- [QUICK_START.md](QUICK_START.md)

### Infrastructure

- [EO_Documents/Manuals/EO_Infra_Docker_README.md](EO_Documents/Manuals/EO_Infra_Docker_README.md) - Docker Image 更新

### Request Engine

- [EO_Documents/Manuals/RE_README.md](EO_Documents/Manuals/RE_README.md) - リクエストエンジン実行セキュリティ設定

**AWS Lambda**

- [EO_Documents/Manuals/py/LAMBDA_README.md](EO_Documents/Manuals/py/LAMBDA_README.md) - 手動セットアップ
- [EO_Documents/Manuals/py/LAMBDA_CFN_README.md](EO_Documents/Manuals/py/LAMBDA_CFN_README.md) - CloudFormation 構築 👈 Recommend!

**Azure Functions**

- [EO_Documents/Manuals/py/AZFUNC_README.md](EO_Documents/Manuals/py/AZFUNC_README.md) - 手動セットアップ
- [EO_Documents/Manuals/py/AZFUNC_BICEP_README.md](EO_Documents/Manuals/py/AZFUNC_BICEP_README.md) - Bicep 構築

**GCP Cloud Run**

- [EO_Documents/Manuals/py/CloudRun_README.md](EO_Documents/Manuals/py/CloudRun_README.md) - 手動セットアップ
- [EO_Documents/Manuals/py/CloudRun_TF_README.md](EO_Documents/Manuals/py/CloudRun_TF_README.md) - Terraform 構築
- [EO_Documents/Manuals/py/CloudRun_check_permissions.md](EO_Documents/Manuals/py/CloudRun_check_permissions.md) - 権限チェック

**Cloudflare Workers**

- [EO_Documents/Manuals/ts/CFWORKER_README.md](EO_Documents/Manuals/ts/CFWORKER_README.md) - 手動セットアップ
- [EO_Documents/Manuals/ts/CFWorker_Overview_README.md](EO_Documents/Manuals/ts/CFWorker_Overview_README.md) - 概要

### n8n Workflow

- [EO_Documents/Manuals/n8n/N8N_WORKFLOW_README.md](EO_Documents/Manuals/n8n/N8N_WORKFLOW_README.md) - インポート・Credentials・ノード設定
- [EO_Documents/Manuals/n8n/N8N_NODE_SETUP.md](EO_Documents/Manuals/n8n/N8N_NODE_SETUP.md) - ノード設定ガイド
- [EO_Documents/Manuals/n8n/NODE175_USERAGENT_README.md](EO_Documents/Manuals/n8n/NODE175_USERAGENT_README.md) - User-Agent設定
- [EO_Documents/Manuals/n8n/NODE180_REQUESTENGINE_README.md](EO_Documents/Manuals/n8n/NODE180_REQUESTENGINE_README.md) - Request Engine設定
- [n8nQueueModeTest/README.md](n8nQueueModeTest/README.md) - Queue Mode テスト

---

## 🚀 Quick Start

**👉 [QUICK_START.md](QUICK_START.md) を参照してください。**

Docker + n8n 環境の起動から、ワークフローのインポートまで、5ステップで完了します。

---

## 📋 詳細設定ガイド

Quick Start 完了後、以下の追加設定が必要な場合に参照してください。

### n8n 環境変数アクセス設定

n8n ワークフローで環境変数（例: `{{ $env.N8N_EO_REQUEST_SECRET }}`）を使用するには、環境変数アクセスの許可設定が必要です。

`EO_Infra_Docker/docker-compose.yml` に以下の設定が含まれています：

```yaml
N8N_EO_REQUEST_SECRET: ${N8N_EO_REQUEST_SECRET}
N8N_BLOCK_ENV_ACCESS_IN_NODE: false
```

- **`N8N_EO_REQUEST_SECRET`**: `.env` ファイルの値を n8n コンテナに渡し、ワークフロー内で `{{ $env.N8N_EO_REQUEST_SECRET }}` としてアクセス可能にします
- **`N8N_BLOCK_ENV_ACCESS_IN_NODE: false`**: ワークフローからの環境変数アクセスを許可します

> **📝 注意:** n8n UI でのプレビュー実行時に「access to env vars denied」エラーが表示される場合がありますが、これは既知のエラーです。Webhook起動や定期実行などの自動実行時は正常に動作します。手動実行（UI上でのプレビュー）で、エラーは出ますが実行出来ます。
>
> **参考:** [n8n 公式ドキュメント: Environment Variables Security](https://docs.n8n.io/hosting/configuration/environment-variables/security/) / [n8n Community: No access to $env](https://community.n8n.io/t/no-access-to-env/20665)

ワークフロー内での使用例（「170 n8n RequestSecret Token Generator」ノード）：

```
{{ $json.url }}{{ $env.N8N_EO_REQUEST_SECRET }}
```

### Production Setup（Caddy リバースプロキシ）

Caddy を使用した本番環境の起動方法です。`EO_Infra_Docker/.env` で `PRODUCTION=true` およびドメイン・メール設定を行ってから実行してください。

```bash
cd EO_Infra_Docker
docker compose --profile prod up -d
```

### 複数環境の同時実行

同一マシンで複数の EO 環境を動かす場合は、以下の変更が必要です：

1. `EO_Infra_Docker/.env` の **全てのボリューム名** を変更（例: `_v2` サフィックス追加）
2. `DOCKER_HOST_BIND_ADDR` を別の IP に変更（例: `127.0.0.2`）
3. `N8N_WEBHOOK_URL` を新しい IP に合わせて更新
4. n8n ワークフローの **#125-1 ノード**、Playwrightコンテナへのリクエスト先URLのポートが他環境と重複しないように変更

> ⚠️ ボリューム名を変更しないと、複数環境で同じボリュームを共有し、データ破損や消失の原因になります。詳細は `EO_Infra_Docker/env.example` の「ADVANCED: Running Multiple Local Environments」セクションを参照。

---

## 【Recommended to try】n8n Queue Mode Test

n8n のメモリ枯渇対策として、Queue Mode Test の利用を推奨します。

👉 [n8nQueueModeTest](n8nQueueModeTest)
