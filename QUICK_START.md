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
2. 2. 初回アクセス時に **オーナーアカウント作成画面** が表示されます
   3. 3. 以下を入力して「Next」をクリック:
      4.    - **First Name**: 任意（例: Admin）
            -    - **Last Name**: 任意（例: User）
                 -    - **Email**: 任意のメールアドレス
                      -    - **Password**: 8文字以上の安全なパスワード
                       
                           - > **⚠️ 注意:** このアカウント情報はローカル環境のPostgreSQLに保存されます。忘れないようにメモしてください。
                             >
                             > ---
                             >
                             > ### Step 5: n8n Workflow インポート（1分）
                             >
                             > n8nのダッシュボードが表示されたら、Edge Optimizerのワークフローをインポートします。
                             >
                             > 1. n8n ダッシュボード右上の **「...」メニュー** または **「Import from File」** をクリック
                             > 2. 2. リポジトリ内の以下のファイルを選択してインポート:
                             >   
                             >    3. ```
                             >       EO_n8nWorkflow_Json/eo-n8n-workflow-jp.json
                             >       ```
                             >
                             > 3. インポート完了後、ワークフロー一覧に Edge Optimizer のワークフローが表示されます
                             >
                             > 4. > **📖 詳細なワークフロー設定ガイド:**
                             >    > > [EO_n8nWorkflow_Json/N8N_WORKFLOW_README.md](./EO_n8nWorkflow_Json/N8N_WORKFLOW_README.md) を参照してください。
                             >    > > > Credentials設定・ノード設定など、詳しい手順が記載されています。
                             >    > > >
                             >    > > > ---
                             >    > > >
                             >    > > > **🎉 セットアップ完了！**
                             >    > > >
                             >    > > > これで Edge Optimizer の基本環境が動作しています。
                             >    > > >
                             >    > > > ---
                             >    > > >
                             >    > > > ## 🎯 次のステップ
                             >    > > >
                             >    > > > - **Request Engine を設定したい** → [RequestEngine/RE_README.md](./RequestEngine/RE_README.md)
                             >    > > > - - **ワークフローの詳細設定** → [N8N_WORKFLOW_README.md](./EO_n8nWorkflow_Json/N8N_WORKFLOW_README.md)
                             >    > > >   - - **User-Agent設定** → [NODE175_USERAGENT_README.md](./EO_n8nWorkflow_Json/NODE175_USERAGENT_README.md)
                             >    > > >     - - **トラブルシューティング** → [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
                             >    > > >      
                             >    > > >       - ---
                             >    > > >
                             >    > > > **困ったときは→ [Issues](https://github.com/Masamasamasashito/EdgeOptimizer/issues)**
                             >    > > > 
