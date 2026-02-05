# サービスアカウント権限チェックスクリプトの実行方法

## 最も簡単な方法: Google Cloud Shell（推奨）

### 手順

1. **Google Cloud Console にアクセス**
   - https://console.cloud.google.com/ を開く
   - プロジェクト `eo-re-d01-pr-ane1` を選択

2. **Cloud Shell を開く**
   - 画面上部の Cloud Shell アイコン（`>_`）をクリック
   - 初回は数秒待つ（環境が起動するまで）

3. **スクリプトをアップロード**
   - Cloud Shell エディタを開く（右上の鉛筆アイコン）
   - 左側のファイルツリーで `check_service_account_permissions.sh` を探す
   - 見つからない場合は、ローカルからアップロード:
     - Cloud Shell エディタの「アップロード」ボタンで `check_service_account_permissions.sh` を選択

4. **改行コードを変換（Windowsで作成したファイルの場合）**
   ```bash
   # 改行コードをLFに変換（dos2unixが利用可能な場合）
   dos2unix check_service_account_permissions.sh
   
   # または、sedコマンドで変換
   sed -i 's/\r$//' check_service_account_permissions.sh
   ```

5. **実行**
   ```bash
   chmod +x check_service_account_permissions.sh
   ./check_service_account_permissions.sh
   
   # または、直接bashで実行（改行コードの問題を回避）
   bash check_service_account_permissions.sh
   ```

## その他の方法

### WSL (Windows Subsystem for Linux) を使う場合

```bash
# WSLを起動
wsl

# プロジェクトディレクトリに移動
cd /<プロジェクトルートディレクトリ>/RequestEngine/gcp_cloudrun/ane1

# gcloud CLIがインストールされていることを確認
gcloud --version

# 認証（初回のみ）
gcloud auth login
gcloud config set project eo-re-d01-pr-ane1

# 実行
chmod +x check_service_account_permissions.sh
./check_service_account_permissions.sh
```

### Git Bash を使う場合

```bash
# Git Bashを起動

# プロジェクトディレクトリに移動
cd /<プロジェクトルートディレクトリ>/RequestEngine/gcp_cloudrun/ane1

# 認証（初回のみ）
gcloud auth login
gcloud config set project eo-re-d01-pr-ane1

# 実行
bash check_service_account_permissions.sh
```

### PowerShell で個別にコマンドを実行する場合

スクリプトを使わず、PowerShellから直接gcloudコマンドを実行:

```powershell
# 環境変数設定
$env:EO_GCP_PROJECT_ID = "eo-re-d01-pr-ane1"
$env:EO_GCP_PROJECT_NUMBER = "<GCPプロジェクト番号>"
$DEPLOY_SA = "eo-gcp-sa-d01-deploy-ane1@${env:EO_GCP_PROJECT_ID}.iam.gserviceaccount.com"
$RUNTIME_SA = "eo-gcp-sa-d01-runtime-ane1@${env:EO_GCP_PROJECT_ID}.iam.gserviceaccount.com"
$OAUTH2_INVOKER_SA = "eo-gcp-sa-d01-oa2be-inv-ane1@${env:EO_GCP_PROJECT_ID}.iam.gserviceaccount.com"
$COMPUTE_DEFAULT_SA = "${env:EO_GCP_PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# 1. Deployer SAのプロジェクトレベルロール確認
Write-Host "=== Deployer SA のプロジェクトレベルロール ===" -ForegroundColor Cyan
gcloud projects get-iam-policy $env:EO_GCP_PROJECT_ID `
    --flatten="bindings[].members" `
    --filter="bindings.members:serviceAccount:$DEPLOY_SA" `
    --format="table(bindings.role)"

# 2. Runtime SAのプロジェクトレベルロール確認
Write-Host "`n=== Runtime SA のプロジェクトレベルロール ===" -ForegroundColor Cyan
gcloud projects get-iam-policy $env:EO_GCP_PROJECT_ID `
    --flatten="bindings[].members" `
    --filter="bindings.members:serviceAccount:$RUNTIME_SA" `
    --format="table(bindings.role)"

# 3. Deployer SAのリソースレベルロール確認 (WIF等)
Write-Host "`n=== Deployer SA のリソースレベルロール ===" -ForegroundColor Cyan
gcloud iam service-accounts get-iam-policy $DEPLOY_SA --project=$env:EO_GCP_PROJECT_ID

# 4. Compute Engine デフォルト SA のリソースレベルロール確認 (Deployer からの借用)
Write-Host "`n=== Compute Engine デフォルト SA のリソースレベルロール ===" -ForegroundColor Cyan
gcloud iam service-accounts get-iam-policy $COMPUTE_DEFAULT_SA --project=$env:EO_GCP_PROJECT_ID

# 5. Runtime SAのリソースレベルロール確認 (Build Executors からの借用)
Write-Host "`n=== Runtime SA のリソースレベルロール ===" -ForegroundColor Cyan
gcloud iam service-accounts get-iam-policy $RUNTIME_SA --project=$env:EO_GCP_PROJECT_ID

# 6. OAuth2_Invoker SA のリソースレベルロール確認 (n8n からの ID トークン生成を許可)
Write-Host "`n=== OAuth2_Invoker SA のリソースレベルロール ===" -ForegroundColor Cyan
# この SA 自身に roles/iam.serviceAccountTokenCreator が付与されている必要があります
gcloud iam service-accounts get-iam-policy $OAUTH2_INVOKER_SA --project=$env:EO_GCP_PROJECT_ID

# 7. Cloud Run への Invoker 権限確認
Write-Host "`n=== OAuth2_Invoker SA の Cloud Run Invokerロール ===" -ForegroundColor Cyan
gcloud run services get-iam-policy eo-re-d01-cloudrun-ane1 `
    --region=asia-northeast1 `
    --project=$env:EO_GCP_PROJECT_ID
```

## 期待される結果

スクリプトが正常に実行されると、以下のような出力が表示されます:

```
==========================================
GCP Service Account 権限チェック
==========================================
プロジェクトID: eo-re-d01-pr-ane1
プロジェクト番号: <GCPプロジェクト番号>

----------------------------------------
[Deployer SA] プロジェクトレベルロール確認
----------------------------------------
実際に設定されているロール:
  ✓ roles/run.admin
  ✓ roles/cloudbuild.builds.editor
  ...

期待されるロールとの比較:
  ✓ roles/run.admin (Cloud Run 管理者)
  ✓ roles/cloudbuild.builds.editor (Cloud Build 編集者)
  ...

✓ すべての期待されるロールが設定されています
```

## トラブルシューティング

### エラー: "command not found: gcloud"

gcloud CLIがインストールされていません。以下のいずれかを実行:

1. **Google Cloud Shell を使用**（gcloud CLIが既にインストール済み）
2. **ローカルにインストール**:
   ```powershell
   # Windows用インストーラーをダウンロード
   (New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
   & $env:Temp\GoogleCloudSDKInstaller.exe
   ```

### エラー: "Permission denied"

スクリプトに実行権限がありません:

```bash
chmod +x check_service_account_permissions.sh
```

### エラー: "cannot execute: required file not found"

このエラーは、Windowsで作成されたスクリプトファイルの改行コードがCRLF（Windows形式）になっている場合に発生します。

**解決方法1: bashで直接実行（推奨）**

```bash
# shebang行を無視してbashで直接実行
bash check_service_account_permissions.sh
```

**解決方法2: 改行コードをLFに変換**

```bash
# dos2unixが利用可能な場合
dos2unix check_service_account_permissions.sh
chmod +x check_service_account_permissions.sh
./check_service_account_permissions.sh

# または、sedコマンドで変換
sed -i 's/\r$//' check_service_account_permissions.sh
chmod +x check_service_account_permissions.sh
./check_service_account_permissions.sh
```

**解決方法3: Cloud Shellエディタで再作成**

1. Cloud Shellエディタで `check_service_account_permissions.sh` を開く
2. 内容をコピー＆ペーストして新規ファイルとして保存
3. 実行:
   ```bash
   chmod +x check_service_account_permissions.sh
   ./check_service_account_permissions.sh
   ```

### エラー: "You do not currently have an active account selected"

認証が必要です:

```bash
gcloud auth login
gcloud config set project eo-re-d01-pr-ane1
```

### 警告: "Project 'eo-re-d01-pr-ane1' lacks an 'environment' tag"

この警告は**無視して問題ありません**。プロジェクトの設定は正常に更新されています。

環境タグは推奨事項であり、必須ではありません。設定したい場合は以下のコマンドを実行:

```bash
# 環境タグを作成（初回のみ）
gcloud resource-manager tags keys create environment \
    --parent=organizations/<GCP組織ID>

# タグ値を設定（Development環境の場合）
gcloud resource-manager tags values create Development \
    --parent=organizations/<GCP組織ID>/environment

# プロジェクトにタグをバインド
gcloud resource-manager tags bindings create \
    --tag-value=organizations/<GCP組織ID>/environment/Development \
    --parent=//cloudresourcemanager.googleapis.com/projects/<GCPプロジェクト番号>
```

**注意**: 組織ID (`<GCP組織ID>`) とプロジェクト番号 (`<GCPプロジェクト番号>`) は実際の値に置き換えてください。

この警告を無視して、権限チェックスクリプトを実行しても問題ありません。

