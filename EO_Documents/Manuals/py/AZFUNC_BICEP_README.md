# Azure Functions Request Engine - Bicep 構築手順

`eo-re-d01-azure-funcapp.bicep`と`eo-re-d01-azure-mgmt-group.bicep` を使用した Azure Functions Request Engine インフラストラクチャの構築手順です。

※bicepやjsonのテンプレートでうまくできない場合、お手数ですが[AZFUNC_README.md](AZFUNC_README.md) の手動手順を参照してください。特にSTEP 0は、個人契約だと権限不足でazure cliがエラーになります。

## 目次

- [概要](#概要)
- [作成されるリソース一覧](#作成されるリソース一覧)
- [STEP 0: 管理グループとポリシーのデプロイ（オプション）](#step-0-管理グループとポリシーのデプロイオプション)
- [STEP 1: 事前準備（Bicepデプロイ前）](#step-1-事前準備bicepデプロイ前)
- [STEP 2: Bicep テンプレートのデプロイ](#step-2-bicep-テンプレートのデプロイ)
- [STEP 3: デプロイ後の設定](#step-3-デプロイ後の設定)
- [STEP 4: GitHub Actions OIDC 設定](#step-4-github-actions-oidc-設定)
- [STEP 5: GitHub Actions で Function App をデプロイ](#step-5-github-actions-で-function-app-をデプロイ)
- [STEP 6: n8n Credentials 設定](#step-6-n8n-credentials-設定)
- [パラメータ一覧](#パラメータ一覧)
- [トラブルシューティング](#トラブルシューティング)

---

## 概要

このディレクトリには3つのBicepテンプレートがあります：

### 1. `eo-re-d01-azure-mgmt-group.bicep`（管理グループ作成とサブスクリプション紐付け）

管理グループを作成し、サブスクリプションを紐付けます（テナントスコープ）：

- Management Group（`eo-re-d01-azure-mgmt-group`）
- サブスクリプションの管理グループへの紐付け

### 2. `eo-re-d01-azure-mgmt-group-policies.bicep`（管理グループへのポリシー割り当て）

管理グループにポリシーを割り当てます（管理グループスコープ）：

- Allowed locations ポリシー（Japan East のみ許可）
- Allowed resource types ポリシー（Function App, Storage, Key Vault 等のみ許可）

**目的**: GitHub Secrets にサブスクリプションIDを登録する際のリスク軽減

### 3. `eo-re-d01-azure-funcapp.bicep`（Function App 等のリソース作成）

Edge Optimizer の Azure Functions Request Engine に必要な以下のリソースを一括作成します：

- Function App（フレックス従量課金プラン、Python 3.13）
- App Service Plan（Flex Consumption）
- Storage Account（Function App 用）
- Key Vault（シークレット管理）
- Key Vault Secret（トークン検証用シークレットのプレースホルダー）
- RBAC ロール割り当て（Function App → Key Vault シークレットユーザー）

**注意**: Entra ID アプリケーション（GitHub Actions OIDC 用）は Bicep で直接作成できないため、手動で作成が必要です。

---

## 作成されるリソース一覧

**命名**

- {pj}: プロジェクトプレフィックス（例: `eo` Edge Optimizer）
- {comp}: コンポーネント名（例: `re` は Request Engine）
- {env}: 環境名（例: `d01` は dev01）
- {region}: リージョン名（例: `jpeast` は Japan East）

デフォルトパラメータ（`eo-re-d01-funcapp-jpeast`）の場合：

| リソース種別 | リソース名パターン | グローバル一意命名 | 文字制約 |
|-------------|-------------------|---------------|----------|
| Function App | `{pj}-{comp}-{env}-funcapp-{region}` | ✅ 必須 | 2-60文字、英数字とハイフン |
| App Service Plan | `ASP-{pj}{comp}{env}resourcegroup{region}` | - | 1-40文字、英数字とハイフン |
| Storage Account | `{pj}{comp}{env}storage` | ✅ 必須 | 3-24文字、**英小文字と数字のみ**（ハイフン不可） |
| Key Vault | `{pj}-{comp}-{env}-kv-{region}` | ✅ 必須 | 3-24文字、英数字とハイフン、英字で開始 |
| Key Vault Secret | `AZFUNC-REQUEST-SECRET` | - | 1-127文字、英数字とハイフン |
| RBAC 割り当て | Function App → Key Vault シークレットユーザー | - | - |

**⚠️ 重要: グローバル一意リソースについて**

以下のリソースは文字制約に注意しながら **Azure 全体でグローバルに一意** である必要があります：

- **Key Vault**: `https://{name}.vault.azure.net/` の `{name}` 部分
- **Storage Account**: `{name}.blob.core.windows.net` の `{name}` 部分
- **Function App**: `{name}.azurewebsites.net` の `{name}` 部分

**対策**: パラメータを変更して一意の名前を生成してください：
- `projectPrefix` を変更（例: `eo` → `myeo`）
- `environment` を変更（例: `d01` → `dev01`）
- または組織固有のプレフィックスを追加

---

## 【参考】Entra ID , Azure 階層構造

- テナント (Entra ID) ★カスタムドメイン（組織のドメイン）
    - ユーザー ★『グローバル管理者（デフォルトはID(人)に関する権限だけ、「管理グループ」の閲覧権限無し、サブスクリプションの中身の操作権無し）』
    - Entra App (アプリの登録 / サービスプリンシパル) ★システムのユーザーアカウント
    - 管理グループ:「Tenant Root Group」 (全ての管理グループの親玉。最初はこれしかない)
        - 作成した管理グループ (「プロジェクト用」などの名前で作る箱) ★Policy (ガードレール) を設定
            - サブスクリプション (支払い単位：ここから下が Azure リソースの世界) ★財布
                - リソースグループ (プロジェクト内の「道具箱」)
                    - 個々のリソース ★必要で有ればリソースロック

⚠️ 管理グループから見るロール、Entra IDから見るロールなど、ロールを見るサービスで見られるロールが異なる（見られないロールが有る）ので要注意！

## STEP 0: 管理グループとポリシーのデプロイ

サブスクリプションに対するポリシー制限を Bicep で設定します。GitHub Secrets にサブスクリプションIDを登録する際のセキュリティリスクを軽減として行います。

**手動で設定する場合**: [AZFUNC_README.md](AZFUNC_README.md) の「Azure管理グループ作成」セクションを参照

### 0-1. 前提条件

以下の権限が必要です：

1. **Azure AD グローバル管理者ロール**
2. **「Azure リソースのアクセス管理」の有効化**:
   - Azure Portal > Entra ID > プロパティ > 画面を一番下までスクロール
   - 「Azure リソースのアクセス管理」を「はい」に切り替えて保存

### 0-2. デプロイ方法（2段階）

管理グループ作成と管理グループのポリシー割り当ては**スコープが異なる**ため、2段階でデプロイします。

| ステップ | ファイル | スコープ |
|---------|---------|---------|
| Step 1 | `eo-re-d01-azure-mgmt-group.bicep` | 管理グループ作成(テナントスコープ) |
| Step 2 | `eo-re-d01-azure-mgmt-group-policies.bicep` | 管理グループのポリシー割り当て |

**⚠️ 注意**: 個人Microsoftアカウント（ゲストユーザー）ではテナントスコープのデプロイに権限エラーが発生する場合があります。その場合は Azure Portal（GUI）で手動設定してください。

#### Azure CLI でデプロイ

**Bash（Linux / macOS / Git Bash / WSL）:**
```bash
# Azure にログイン ※個人契約の場合、テナントは「既定のディレクトリ」という名前になる
az login

# サブスクリプションIDを確認
az account show --query id -o tsv

# 移動
cd RequestEngine/azure/functions/bicep/

# Step 1: 管理グループ作成（テナントスコープ）
az deployment tenant create \
  --location japaneast \
  --template-file eo-re-d01-azure-mgmt-group.bicep \
  --parameters subscriptionId='<YOUR_SUBSCRIPTION_ID>'

# Step 2: ポリシー割り当て（管理グループスコープ）
az deployment mg create \
  --location japaneast \
  --management-group-id eo-re-d01-azure-mgmt-group \
  --template-file eo-re-d01-azure-mgmt-group-policies.bicep
```

**PowerShell（Windows）:**
```powershell
# Azure にログイン
az login

# サブスクリプションIDを確認
az account show --query id -o tsv

# 移動
cd RequestEngine/azure/functions/bicep/

# Step 1: 管理グループ作成（テナントスコープ）
az deployment tenant create --location japaneast --template-file eo-re-d01-azure-mgmt-group.bicep --parameters subscriptionId='<YOUR_SUBSCRIPTION_ID>'

# Step 2: ポリシー割り当て（管理グループスコープ）
az deployment mg create --location japaneast --management-group-id eo-re-d01-azure-mgmt-group --template-file eo-re-d01-azure-mgmt-group-policies.bicep
```

#### Azure Portal（GUI）で設定する場合

Azure Portal のテンプレートデプロイはテナントスコープに対応していないため、**手動で設定**する必要があります。

👉 **[AZFUNC_README.md](AZFUNC_README.md)** の「Azure管理グループ作成」セクションを参照してください。

### 0-3. パラメータ

**eo-re-d01-azure-mgmt-group.bicep（管理グループ）**

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| `subscriptionId` | (必須) | 管理グループに紐付けるサブスクリプションID |

**eo-re-d01-azure-mgmt-group-policies.bicep（ポリシー）**

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| `allowedLocations` | `['japaneast']` | 許可するリージョン |
| `allowedResourceTypes` | Function App, App Service Plan, Key Vault, Storage Account | 許可するリソースタイプ |
| `enableApplicationInsights` | `false` | Application Insights を許可するか |

### 0-4. カスタマイズ例

**Japan West も許可する場合:**

Bash:
```bash
az deployment mg create \
  --location japaneast \
  --management-group-id eo-re-d01-azure-mgmt-group \
  --template-file eo-re-d01-azure-mgmt-group-policies.bicep \
  --parameters allowedLocations='["japaneast","japanwest"]'
```

PowerShell:
```powershell
az deployment mg create --location japaneast --management-group-id eo-re-d01-azure-mgmt-group --template-file eo-re-d01-azure-mgmt-group-policies.bicep --parameters allowedLocations='["japaneast","japanwest"]'
```

**Application Insights を許可する場合:**

Bash:
```bash
az deployment mg create \
  --location japaneast \
  --management-group-id eo-re-d01-azure-mgmt-group \
  --template-file eo-re-d01-azure-mgmt-group-policies.bicep \
  --parameters enableApplicationInsights=true
```

PowerShell:
```powershell
az deployment mg create --location japaneast --management-group-id eo-re-d01-azure-mgmt-group --template-file eo-re-d01-azure-mgmt-group-policies.bicep --parameters enableApplicationInsights=true
```

### 0-5. デプロイ結果の確認

Bash:
```bash
# 管理グループの確認
az account management-group show --name eo-re-d01-azure-mgmt-group

# ポリシー割り当ての確認
az policy assignment list \
  --scope /providers/Microsoft.Management/managementGroups/eo-re-d01-azure-mgmt-group \
  --query "[].{name:name, displayName:displayName}" -o table
```

PowerShell:
```powershell
# 管理グループの確認
az account management-group show --name eo-re-d01-azure-mgmt-group

# ポリシー割り当ての確認
az policy assignment list --scope /providers/Microsoft.Management/managementGroups/eo-re-d01-azure-mgmt-group --query "[].{name:name, displayName:displayName}" -o table
```

---

## STEP 1: 事前準備（Bicepデプロイ前）

### 1-1. リソースグループの作成

Bicep デプロイ先のリソースグループを作成します。

**Azure Portal:**
1. Azure Portal > リソースグループ > 「+ 作成」
2. リソースグループ名: `eo-re-d01-resource-group-jpeast`
3. リージョン: `(Asia Pacific) Japan East`
4. 「レビューと作成」> 「作成」

**Azure CLI (Bash):**
```bash
az group create \
  --name eo-re-d01-resource-group-jpeast \
  --location japaneast
```

**Azure CLI (PowerShell):**
```powershell
az group create --name eo-re-d01-resource-group-jpeast --location japaneast
```

### 1-2. Entra ID アプリケーションの作成（GitHub Actions OIDC 用）

**重要**: Entra ID アプリケーションは Bicep で作成できないため、手動で作成します。

1. Azure Portal > Microsoft Entra ID > 概要 > +追加 > アプリを登録
2. 名前: `eo-ghactions-deploy-entra-app-azfunc-jpeast`
3. サポートされているアカウントの種類: **この組織ディレクトリのみに含まれるアカウント**
   - ⚠️「個人用 Microsoft アカウントのみ」は選択しない（OIDC認証でエラーになる）
4. リダイレクト URI: 設定不要
5. 「登録」をクリック
6. 以下の値をメモ:
   - **アプリケーション (クライアント) ID** → GitHub Secrets `EO_AZ_FUNC_JPEAST_DEPLOY_ENTRA_APP_ID_FOR_GITHUB`
   - **ディレクトリ (テナント) ID** → GitHub Secrets `EO_AZ_TENANT_ID` および Bicep パラメータ `tenantId`

### 1-3. テナント ID の確認

Bicep デプロイに必要なテナント ID を確認します。  
※Entra IDでも確認可能: Azure Portal > Microsoft Entra ID > 概要 > 基本情報 > テナントID
```bash
az account show --query tenantId -o tsv
```

---

## STEP 2: Funcapp Bicep テンプレートのデプロイ

### 2-1. パラメータファイルの作成（オプション）

`eo-re-d01-azure-funcapp.parameters.json` を作成:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "projectPrefix": { "value": "eo" },
    "component": { "value": "re" },
    "environment": { "value": "d01" },
    "regionShort": { "value": "jpeast" },
    "location": { "value": "japaneast" },
    "tenantId": { "value": "<YOUR_TENANT_ID>" },
    "pythonVersion": { "value": "3.13" },
    "instanceMemoryMB": { "value": 512 },
    "maximumInstanceCount": { "value": 100 },
    "softDeleteRetentionDays": { "value": 7 }
  }
}
```

### 2-2. デプロイ方法

Function App 等のリソースは**リソースグループスコープ**でデプロイします。Azure CLI または Azure Portal から実行できます。

RequestEngine\azure\functions\bicep ディレクトリに移動してから実行してください。

#### 方法A: Azure CLI でデプロイ

**パラメータを直接指定 (Bash):**
```bash
az deployment group create \
  --name eo-azure-funcapp-deployment \
  --resource-group eo-re-d01-resource-group-jpeast \
  --template-file eo-re-d01-azure-funcapp.bicep \
  --parameters \
    tenantId='<YOUR_TENANT_ID>' \
    projectPrefix='eo' \
    component='re' \
    environment='d01' \
    regionShort='jpeast' \
    location='japaneast'
```

**パラメータを直接指定 (PowerShell):**
```powershell
az deployment group create --name eo-azure-funcapp-deployment --resource-group eo-re-d01-resource-group-jpeast --template-file eo-re-d01-azure-funcapp.bicep --parameters tenantId='<YOUR_TENANT_ID>' projectPrefix='eo' component='re' environment='d01' regionShort='jpeast' location='japaneast'
```

**パラメータファイルを使用 (Bash):**
```bash
az deployment group create \
  --name eo-azure-funcapp-deployment \
  --resource-group eo-re-d01-resource-group-jpeast \
  --template-file eo-re-d01-azure-funcapp.bicep \
  --parameters @eo-re-d01-azure-funcapp.parameters.json
```

**パラメータファイルを使用 (PowerShell):**
```powershell
az deployment group create --name eo-azure-funcapp-deployment --resource-group eo-re-d01-resource-group-jpeast --template-file eo-re-d01-azure-funcapp.bicep --parameters '@eo-re-d01-azure-funcapp.parameters.json'
```

#### 方法B: Azure Portal でデプロイ

**⚠️ 重要**: Azure Portal の「カスタム テンプレートのデプロイ」は **JSON (ARM テンプレート)** のみ対応しています。Bicep ファイルは事前に JSON に変換が必要です。

**手順1: Bicep → JSON 変換**

Bash / PowerShell 共通:
```bash
# Bicep を JSON (ARM テンプレート) にコンパイル
az bicep build --file eo-re-d01-azure-funcapp.bicep

# 出力: eo-re-d01-azure-funcapp.json が生成される
```

**手順2: Azure Portal でデプロイ**
1. Azure Portal 上部の検索バーで「カスタム テンプレートのデプロイ」を検索してクリック
2. 「エディターで独自のテンプレートを作成する」をクリック
3. 生成された `eo-re-d01-azure-funcapp.json` の内容を貼り付け
4. 「保存」をクリック
5. **カスタム デプロイ** 画面で設定:
   - **サブスクリプション**: デプロイ先のサブスクリプションを選択
   - **リソースグループ**: `eo-re-d01-resource-group-jpeast`（STEP 1-1 で作成済み）
   - **リージョン**: `Japan East`
   - **Tenant Id**: STEP 1-3 で確認したテナントID
   - **Project Prefix**: `eo`（デフォルト）
   - **Component**: `re`（デフォルト）
   - **Environment**: `d01`（デフォルト）
   - **Region Short**: `jpeast`（デフォルト）
   - **Location**: `japaneast`（デフォルト）
   - **Python Version**: `3.13`（デフォルト）
   - **Instance Memory MB**: `512`（デフォルト）
   - **Maximum Instance Count**: `100`（デフォルト）
   - **Soft Delete Retention Days**: `7`（デフォルト）
6. 「レビューと作成」>「作成」
7. デプロイ完了後、「出力」タブで以下の値をメモ:
   - `functionAppName`: Function App 名
   - `keyVaultUri`: Key Vault URI（GitHub Secrets `EO_AZ_RE_KEYVAULT_URL` に設定）

#### 方法C: リソースグループ画面からデプロイ

1. 上記 **方法B 手順1** で JSON に変換済みであること
2. Azure Portal > リソースグループ > `eo-re-d01-resource-group-jpeast`
3. 「+ 作成」> 検索バーで「テンプレート」と入力 > 「テンプレートのデプロイ（カスタムテンプレートを使用したデプロイ）」
4. 以降は **方法B** の手順2以降と同様

---

## STEP 3: デプロイ後の設定

### 3-1. 【重要】Key Vault アクセス権を人間に付与

- Bicep で Function App のマネージド ID にのみ Key Vault アクセス権を付与、Key Vault と シークレットを作成  
- GUIで人間がシークレット値を更新する場合、権限付与が必要

Azure Portal で自分に権限を付与します。

1. Key Vault > eo-re-d01-kv-jpeast > アクセス制御 (IAM)
2. 「+ 追加」> 「ロールの割り当ての追加」
3. ロール: `キー コンテナー シークレット責任者`（Key Vault Secrets Officer）
    - `シークレットの読み取り・書き込み・削除（管理者用）`
4. メンバー: 自分のアカウント を選択
5. Description: `Key Vault で シークレットを閲覧、作成、更新など権限を人間に付与 `
5. 「レビューと割り当て」

### 3-2. Key Vault シークレットの更新

1. Azure Portal > Key Vault > `eo-re-d01-kv-jpeast`
2. オブジェクト > シークレット > `AZFUNC-REQUEST-SECRET`
3. 「+ 新しいバージョン」をクリック
4. シークレット値: `EO_Infra_Docker/.env` の `N8N_EO_REQUEST_SECRET` の値
5. 「作成」

**Azure CLI (Bash):**
```bash
az keyvault secret set \
  --vault-name eo-re-d01-kv-jpeast \
  --name AZFUNC-REQUEST-SECRET \
  --value '<N8N_EO_REQUEST_SECRET の値>'
```

**Azure CLI (PowerShell):**
```powershell
az keyvault secret set --vault-name eo-re-d01-kv-jpeast --name AZFUNC-REQUEST-SECRET --value '<N8N_EO_REQUEST_SECRET の値>'
```
---

## STEP 4: GitHub Actions OIDC 設定

### 4-1. フェデレーション資格情報の設定

1. Azure Portal > Microsoft Entra ID > アプリの登録 > `eo-ghactions-deploy-entra-app-azfunc-jpeast`
2. 証明書とシークレット > フェデレーション資格情報 > 「+ 資格情報の追加」
3. シナリオ: 「Azure リソースをデプロイする Github Actions」
4. 設定:
   - 組織: GitHub ユーザー名または組織名
   - リポジトリ: リポジトリ名
   - エンティティ型: ブランチ
   - GitHub ブランチ名: `main`
   - 名前: `eo-azfunc-jpeast-ghactions-main-deploy-federation`
5. 「追加」

### 4-2. サービスプリンシパルへのデプロイ権限付与

1. Azure Portal > リソースグループ > `eo-re-d01-resource-group-jpeast` > アクセス制御 (IAM)
2. 「+ 追加」> 「ロールの割り当ての追加」
3. ロール: `Web サイト共同作成者`
4. アクセスの割り当て先: **ユーザー、グループ、またはサービス プリンシパル**
5. メンバー: `eo-ghactions-deploy-entra-app-azfunc-jpeast` のApplicationを検索して選択
6. 「レビューと割り当て」

### 4-3. GitHub Secrets の設定

GitHub リポジトリ > Settings > Secrets and variables > Actions:

| シークレット名 | 値 | 説明 |
|--------------|-----|------|
| `EO_AZ_FUNC_JPEAST_DEPLOY_ENTRA_APP_ID_FOR_GITHUB` | アプリケーション (クライアント) ID | Entra ID アプリの Client ID |
| `EO_AZ_TENANT_ID` | ディレクトリ (テナント) ID | Azure AD テナント ID |
| `EO_AZURE_SUBSCRIPTION_ID` | Azure サブスクリプション ID | デプロイ先のサブスクリプション |
| `EO_AZ_RE_KEYVAULT_URL` | Bicep Output の `keyVaultUri` 値 | Key Vault URI（語尾スラッシュ不要）|

**Key Vault URI の確認方法**:

Bash:
```bash
# デプロイ後に Output から取得
az deployment group show \
  --name eo-azure-funcapp-deployment \
  --resource-group eo-re-d01-resource-group-jpeast \
  --query properties.outputs.keyVaultUri.value -o tsv
```

PowerShell:
```powershell
az deployment group show --name eo-azure-funcapp-deployment --resource-group eo-re-d01-resource-group-jpeast --query properties.outputs.keyVaultUri.value -o tsv
```

または Azure Portal > Key Vault > 概要 > 「コンテナーの URI」

---

## STEP 5: GitHub Actions で Function App をデプロイ

Bicep で作成した Function App にはまだ関数コードがありません。GitHub Actions でデプロイします。

### 5-1. GitHub Actions ワークフローの実行

1. GitHub リポジトリ > **Actions** タブ
2. 左サイドバー > **Deploy Azure Functions jpeast**
3. 「Run workflow」> ブランチ `main` を選択 > 「Run workflow」
4. ワークフローが完了するまで待機（約2-3分）

### 5-2. デプロイ結果の確認

1. Azure Portal > Function App > `eo-re-d01-funcapp-jpeast`
2. 左サイドバー > **関数** をクリック
3. `requestengine_func` が表示されていれば成功

**表示されない場合**: GitHub Actions のログを確認し、エラーがないかチェックしてください。

---

## STEP 6: n8n Credentials 設定

### 6-1. Function App Key の取得

1. Azure Portal > Function App > `eo-re-d01-funcapp-jpeast`
2. 関数 > `requestengine_func`
3. 「関数の URL の取得」> `default` (ファンクション キー) を選択
4. URL をコピー（`?code=...` まで含む）

### 6-2. n8n Credential の作成

1. n8n > Personal > Credentials > Create Credential
2. Credential Type: `Header Auth`
3. 設定:
   - Name: `EO_RE_Func_jpeast_AppKey`
   - Header Name: `x-functions-key`
   - Header Value: Function Key の値（URL の `?code=` 以降の部分）
4. 「Save」

### 6-3. n8n ワークフローノードの設定

1. `280AZ-japan-east RequestEngine KeyVault` ノードを開く
2. URL: Function App の URL（`?code=...` 付き、または `x-functions-key` ヘッダーで認証）
3. 「Save」

### 6-4. 280AZ...ノード Parameters URL設定

1. n8n > `280AZ-japan-east RequestEngine KeyVault` ノードを開く
2. **Parameters** > **URL** に Function App の URL を設定:
   ```
   https://eo-re-d01-funcapp-jpeast.azurewebsites.net/api/requestengine_func
   ```
3. 「Save」

**URL の確認方法**:
- Azure Portal > 関数アプリ > `eo-re-d01-funcapp-jpeast` > 関数 > `requestengine_func`
- 「関数の URL の取得」> `default` (ファンクション キー) の URL から `?code=...` を除いた部分

**認証の補足**:
- URL に `?code=...` を含める方法と、Header Auth で `x-functions-key` を設定する方法の2通りがある
- 6-2 で Header Auth を設定済みの場合、URL には `?code=...` 不要

---

## パラメータ一覧

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| **命名規則** |||
| projectPrefix | `eo` | プロジェクトプレフィックス |
| component | `re` | コンポーネント識別子（Request Engine） |
| environment | `d01` | 環境識別子（dev01, prod01 等） |
| regionShort | `jpeast` | リージョン短縮名 |
| **Azure 設定** |||
| location | `japaneast` | デプロイ先リージョン |
| tenantId | (入力必須) | Azure AD テナント ID |
| **Function App 設定** |||
| pythonVersion | `3.13` | Python ランタイムバージョン |
| instanceMemoryMB | `512` | インスタンスメモリサイズ（MB） |
| maximumInstanceCount | `100` | 最大インスタンス数 |
| **Key Vault 設定** |||
| softDeleteRetentionDays | `7` | 論理削除の保持日数 |

---

## トラブルシューティング

### デプロイエラー: "The subscription is not registered to use namespace 'Microsoft.Web'"

**解決**: リソースプロバイダーを登録

Bash / PowerShell 共通:
```bash
az provider register --namespace Microsoft.Web
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.KeyVault
```

### デプロイエラー: Key Vault 名が既に使用されている

**原因**: Key Vault 名はグローバルで一意である必要がある

**解決**:
1. `environment` パラメータを変更（例: `d01` → `d02`）
2. または論理削除された Key Vault を完全削除:
   ```bash
   # Bash / PowerShell 共通
   az keyvault purge --name eo-re-d01-kv-jpeast --location japaneast
   ```

### Function App から Key Vault にアクセスできない

**原因**: RBAC ロール割り当ての反映に時間がかかる場合がある

**解決**:
1. 数分待ってから再試行
2. Azure Portal で RBAC 割り当てを確認:
   - Key Vault > アクセス制御 (IAM) > ロールの割り当て
   - Function App のマネージド ID に「キー コンテナー シークレット ユーザー」が割り当てられているか確認

### GitHub Actions OIDC エラー: "AADSTS7000229"

**原因**: サービスプリンシパルが存在しない

**解決**:
```bash
# Bash / PowerShell 共通
az ad sp create --id <APPLICATION_ID>
```

### n8n から 401 Unauthorized エラー

**原因**: Function Key が正しくない、または含まれていない

**解決**:
1. Azure Portal で Function Key を再取得
2. n8n の URL に `?code=...` が含まれているか確認
3. または Header Auth で `x-functions-key` ヘッダーが設定されているか確認

詳細: [AZFUNC_README.md](AZFUNC_README.md) の「トラブルシューティング」セクション参照

---

## 関連ドキュメント

- [AZFUNC_README.md](AZFUNC_README.md) - Azure Functions 詳細セットアップ手順
- [RE_README.md](../RE_README.md) - Request Engine 全体のセキュリティ設定
- [LAMBDA_CFN_README.md](LAMBDA_CFN_README.md) - AWS Lambda CloudFormation 構築手順
