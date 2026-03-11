# n8nをGoogleドライブに接続する手順

Edge Analyzerとして、Looker Studio で分析するため、Googleドライブをデータストレージとして使うためのAPI連携手順

## 1. GCP プロジェクト作成

- `プロジェクト名 (Project Name)` と `プロジェクトID (Project ID)` は 同じにする
    - `プロジェクトID (Project ID)`は、最初にプロジェクトを作る時、GCPのGUIで「たたまれている」ので、わかりにくい。見にくいため、展開したほうがいい。
    - `プロジェクト名 (Project Name)`は後から変更可能だが、`プロジェクトID (Project ID)`は変更不可
    - `プロジェクトID (Project ID)`
      - グローバル一意
      - 6〜30文字の小文字、数字、ハイフンのみ使用可。小文字で始まり、ハイフンで終わるのは不可。
      - 一般的な命名パターン: `{企業/組織識別子}-{サービス/アプリケーション識別子}-{環境識別子}`
      - EO推奨命名パターン: `{EA_PROJECT}-{EA_COMPONENT}-{EA_ENV}-pr-{EA_REGION_SHORT}`
      - 例: `ea-ds-d1-pr-asne1` (ea-ds-d1-pr-asne1)
        - ea : Edge Analyzer
        - ds : Data Storage
        - d1 : dev01
        - pr : Project
        - asne1 : Asia Northeast1
    - `プロジェクト番号 (Project Number)`
      - Google Cloudによって自動生成される一意の数字のID
- 請求先アカウントを設定し、課金を有効にする
- 組織を設定し、スコープを組織内に制限する

## 2. gcloudコマンド環境変数設定

以降のコマンドで使用する変数を事前に設定します

- EX) `export EA_GCP_PROJECT_ID="ea-ds-d1-pr-asne1"`

```bash
# GCP プロジェクト
export EA_GCP_PROJECT_ID="<GCPプロジェクトID>"         # 例: "ea-ds-d1-pr-asne1"
export EA_GCP_PROJECT_NUMBER="<GCPプロジェクト番号>"   # 例: "123456789012"

# GCP 組織（組織配下のプロジェクトの場合）
export EA_GCP_ORGANIZATION_ID="<GCP組織ID>"           # 例: "1234567890"

# プロジェクト番号の確認:
gcloud projects describe $EA_GCP_PROJECT_ID --format='value(projectNumber)'

# デフォルトで有効になっているAPIの確認
gcloud services list --enabled --format="value(TITLE,STATE)"
```

## 3. 使用するAPIの有効化

1. GCPでサイドメニューの [APIとサービス] > [ライブラリ] に移動
2. 以下のAPIを検索、 [有効にする] をクリック
    - Google Drive API
    - Google Sheets API
    - (必要に応じて) Google Docs API
    - (必要に応じて) YouTube Data API v3

```bash
# APIを有効化
# Google Drive OAuth2 API （CSVのアップロード用）
gcloud services enable drive.googleapis.com
# Google Sheets OAuth2 API （スプレッドシートの操作用）
gcloud services enable sheets.googleapis.com

# (必要に応じて) APIを有効化
gcloud services enable docs.googleapis.com
gcloud services enable youtube.googleapis.com
```

```bash
# 有効になっているAPIの確認
gcloud services list --enabled --format="value(TITLE,STATE)"

# 返された結果
Analytics Hub API       ENABLED
App Optimize API        ENABLED
BigQuery API    ENABLED
BigQuery Connection API ENABLED
BigQuery Data Policy API        ENABLED
BigQuery Data Transfer API      ENABLED
BigQuery Migration API  ENABLED
BigQuery Reservation API        ENABLED
BigQuery Storage API    ENABLED
Gemini for Google Cloud API     ENABLED
Google Cloud APIs       ENABLED
Cloud Asset API ENABLED
Cloud Trace API ENABLED
Dataform API    ENABLED
Cloud Dataplex API      ENABLED
Cloud Datastore API     ENABLED
Google Drive API        ENABLED # 追加されている
Gemini Cloud Assist API ENABLED
Cloud Logging API       ENABLED
Cloud Monitoring API    ENABLED
Recommender API ENABLED
Service Management API  ENABLED
Service Usage API       ENABLED
Google Sheets API       ENABLED # 追加されている
Cloud SQL       ENABLED
Google Cloud Storage JSON API   ENABLED
Cloud Storage   ENABLED
Cloud Storage API       ENABLED
```

## 4. OAuth 同意画面 (OAuth Consent Screen) の設定

EgeOptimizerのn8n から GoogleドライブのSheetsにRequestRsultsデータを書き込むための認可（Authorization）を行う。

1. GCP[APIとサービス] > [OAuth 同意画面] を開く
2. [概要] > [開始] をクリック
3. アプリ情報の入力
    - アプリ名
      - `Edge Analyzer d1 n8n Google Drive Authorization`
    - ユーザーサポートメール
    -　対象
      - `外部`
        - ローカルホスト内のself-hosted n8n が認可を求める場合、オーディエンスの「対象」の「ユーザーの種類」は、外部を選択する必要がある
        - 【参考】`内部`は、組織のGoogle Workspace（旧G Suite）やCloud Identityで管理されているユーザーアカウント、もしくはサービスアカウントを使用する場合に選択。
    - 連絡先情報(メールアドレス)
    - 作成

## 5. 承認済みドメインの追加

**ローカルホスト上のDockerでn8nを動かしている場合、このステップは不要(設定できない)**

1. GCP[APIとサービス] > [OAuth 同意画面]
2. [概要] > [ブランディング] をクリック
3. [承認済みドメイン] を入力

## 6. 承認済みのリダイレクト URI　の確認

1. n8nにログイン > Overview > Credentials
2. Create Credential > `Google Drive OAuth2 API` を選ぶ
3. n8n Credential名の例
  - `EA Google Drive OA2 API for csv uploads`
4. `OAuth Redirect URL`の値のURLをコピーしておく

**Google Cloudの例外: 本来、OAuthのリダイレクトURIは https 必須ですが、http://localhost だけは例外的に許可されている**

## 7. OAuth 2.0 クライアント ID の作成 と JSONダウンロード

1. GCP[APIとサービス] > [認証情報] に移動
2. [認証情報を作成] > [OAuth クライアント ID] を選択
3. アプリケーションの種類 を [ウェブ アプリケーション] に設定
4. 名前
  - `Edge Analyzer d1 n8n local Oa2Client`
5. 承認済みのリダイレクト URI に 「承認済みのリダイレクト URI　の確認」でコピーしたURLを設定する
6. 作成
7. 「OAuth クライアントを作成しました」と表示されるため、「JSONをダウンロード」を実施。
  - クライアントシークレットは、この時しか得られないので注意。
  -　`client_secret_<プロジェクト番号>-<ランダム文字列>.apps.googleusercontent.com.json`がダウンロードされる

## 8. テストユーザーの追加

1. GCP[APIとサービス] > [OAuth 同意画面]
2. [概要] > [対象] > (画面下方にスクロール)[テストユーザー] > Add users
3. 連携したいGoogleドライブのGoogleアカウントのGメールアドレスを追加（後に「n8nへの資格情報の入力と認証」でも同じGメールアドレスを使う）

※アプリを「公開」しない限り、ここで追加したユーザーのみが認証可能です。

## 9. n8nへの資格情報の入力と認証

1. 「OAuth 2.0 クライアント ID の作成 と JSONダウンロード」のJSONからGoogle Cloudで発行された クライアント ID と クライアント シークレット をコピー
2. n8nの Credentials にて「承認済みのリダイレクト URI　の確認」でつくったCredentialを選ぶ
3. `Client ID` と `Client Secret`を貼り付け
4. `Allowed HTTP Request Domains`で
5. [Sign in with Google] をクリック
6. 連携したいGoogleドライブのGoogleアカウントでログインしてアクセスを許可
7. 「Connection successful」と表示されれば完了

### Googleドライブ側の連携解除方法

連携したGoogleアカウントそのものの権限設定から、n8nのアクセス権を取り消す

1. https://myaccount.google.com/security?hl=ja にアクセス
2. 下にスクロールし、「サードパーティ製のアプリとサービスへの接続」　>　「すべての接続を表示」をクリック
3.　該当するアプリ名（例：Edge Analyzer d1 n8n...）を探してクリック
4. 「Edge Analyzer d1 n8n... との接続をすべて削除」を選択

## 10. Googleドライブの保存先指定

### 1. デフォルトのアップロード先
  - n8nのGoogle Driveノードで「Parent ID（親フォルダID）」を指定しない場合、接続したGoogleアカウントの「マイドライブ」の最上層（ルート）に保存される。

### 2. 特定のフォルダに保存する手順（推奨）

1. Googleドライブ側でフォルダを作成
 - ブラウザでGoogleドライブを開き、専用フォルダ（例：ea-ds-data）を作成
 - フォルダの中に入る
 - ブラウザのURLを確認
 - URLの形式：https://drive.google.com/drive/folders/【この部分の英数字文字列】
 - この末尾の英数字が Folder ID（フォルダID）。これをコピー
2. n8nのGoogle Driveノードで設定
 - n8nのワークフローに戻り、Google Driveノードを開いて以下を設定
 - Resource: File
 - Operation: Upload
 - Parent ID (または Parent Folder): * 選択肢から By ID を選ぶ
 - 先ほどコピーした Folder ID を貼り付け

※n8nのUIによっては From list を選択して、マウス操作でフォルダを探して選ぶことも可能
