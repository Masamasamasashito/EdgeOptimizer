# 🚀 Quick Start Guide - 3分で動作確認

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

## ⚡ 3ステップで起動

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

**✅ 完了！** http://localhost:5678 で n8n にアクセスできます

---

## 🎯 次のステップ

- **詳しく知りたい** → [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- - **Request Engine を設定したい** → [RequestEngine/RE_README.md](../RequestEngine/RE_README.md)
 
  - ---

  **困ったときは→ [Issues](https://github.com/Masamasamasashito/EdgeOptimizer/issues)**
  
