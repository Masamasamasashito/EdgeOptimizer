# 🚀 Quick Start Guide - 5分で動作確認

このガイドは、**初めての方が最速でEdge Optimizerを動作させる**ための手順です。

## 30秒で理解：Edge Optimizerとは？

「CDNのキャッシュが無い状態」で初回アクセスが遅くなる問題を解決します。

```
悪い例：デプロイ直後 → 初回アクセス 3秒以上遅い
        広告キャンペーン開始直後 → LCP超過 → 離脱

良い例：デプロイ直後 → 自動的に全エッジにキャッシュ生成
        キャンペーン開始時には全世界から高速アクセス
```

---

## ⚡ 5ステップで起動

### Step 1: リポジトリをクローン（1分）

```bash
mkdir ~/work/docker
cd ~/work/docker
git clone https://github.com/Masamasamasashito/EdgeOptimizer.git
cd EdgeOptimizer/EO_Infra_Docker
```

### Step 2: 環境設定（1分）

```bash
cp env.example .env

# macOS / Linux:
echo "" >> .env
echo "N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)" >> .env
echo "N8N_EO_REQUEST_SECRET=$(openssl rand -hex 32)" >> .env
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=')" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=')" >> .env
echo "SEARXNG_CONTAINER_SECRET=$(openssl rand -hex 32)" >> .env
```

### Step 3: Docker起動（1分）

```bash
docker compose up -d
```

**✅ Docker起動完了！** http://localhost:5678 で n8n にアクセスできます

---

### Step 4: n8n ユーザー作成（1分）

1. ブラウザで http://localhost:5678 にアクセス
2. 初回アクセス時に **オーナーアカウント作成画面** が表示されます
3. 以下を入力して「Next」をクリック:
   - **First Name**: 任意（例: Admin）
   - **Last Name**: 任意（例: User）
   - **Email**: 任意のメールアドレス
   - **Password**: 8文字以上の安全なパスワード

> **⚠️ 注意:** このアカウント情報はローカル環境のPostgreSQLに保存されます。忘れないようにメモしてください。

---

### Step 5: n8n Workflow インポート（1分）

n8nのダッシュボードが表示されたら、Edge Optimizerのワークフローをインポートします。

1. n8n ダッシュボード右上の **「...」メニュー** または **「Import from File」** をクリック
2. リポジトリ内の以下のファイルを選択してインポート:
   ```
   EO_n8nWorkflow_Json/eo-n8n-workflow-jp.json
   ```
3. インポート完了後、ワークフロー一覧に Edge Optimizer のワークフローが表示されます

> **📖 詳細なワークフロー設定ガイド:**
>
> [EO_Documents/Manuals/n8n/N8N_WORKFLOW_README.md](./EO_Documents/Manuals/n8n/N8N_WORKFLOW_README.md) を参照してください。
>
> Credentials設定・ノード設定など、詳しい手順が記載されています。

---

## ⏩ 次のステップ：Request Engine をセットアップ

ここまでで n8n + Docker の基本環境が動作しています。**次に Request Engine を1つセットアップすれば、Edge Optimizer が利用可能になります。**

### 🥇 推奨：AWS Lambda（CloudFormation 版）

CloudFormation テンプレートで Lambda + IAM + Secrets Manager を**ワンクリック一括作成**できます。初めての方はこちらから始めてください。

**👉 [LAMBDA_CFN_README.md](./EO_Documents/Manuals/py/LAMBDA_CFN_README.md)**

### その他の Request Engine

- **AWS Lambda（手動セットアップ）** → [LAMBDA_README.md](./EO_Documents/Manuals/py/LAMBDA_README.md)
- **Azure Functions** → [AZFUNC_README.md](./EO_Documents/Manuals/py/AZFUNC_README.md)
- **Cloudflare Workers** → [CFWORKER_README.md](./EO_Documents/Manuals/ts/CFWORKER_README.md)
- **GCP Cloud Run** → [CloudRun_README.md](./EO_Documents/Manuals/py/CloudRun_README.md)
- **Request Engine 全体のセキュリティ設定** → [RE_README.md](./EO_Documents/Manuals/RE_README.md)

### ワークフロー詳細設定

- **ワークフロー設定ガイド** → [N8N_WORKFLOW_README.md](./EO_Documents/Manuals/n8n/N8N_WORKFLOW_README.md)
- **User-Agent設定** → [NODE175_USERAGENT_README.md](./EO_Documents/Manuals/n8n/NODE175_USERAGENT_README.md)
- **トラブルシューティング** → [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

**困ったときは→ [Issues](https://github.com/Masamasamasashito/EdgeOptimizer/issues)**
