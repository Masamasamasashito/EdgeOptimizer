# Add LLM: ディレクトリ再編成計画

## 目的

- 単一リポジトリ（GitHub の `EdgeOptimizer`）を維持し、**ドメイン・被リンク・Issues の集中**を分散させない。
- 用途別に資産を束ねる：**Web（CDN ウォームアップ等）** / **Local LLM** / **Cloud LLM（GEO 分散プローブ）**。
- **`RequestEngine/`** は **用途別に完全分離**する（下記「結論: RequestEngine/Web と RequestEngine/LLM」）。**コア共通化**（Web と LLM で共有する不変ライブラリ）は、**`RequestEngine/LLM` 側のコアが一定程度できあがってから**着手する。

## 命名規則（ディレクトリ名）

- ディレクトリ名は短く、英小文字とハイフン可：`Web` / `llm/local` / `llm/cloud`。
- 「Edge Optimizer for Web」等の**製品名は README 見出しやドキュメント本文**で補う（パスは長くしすぎない）。

## ディレクトリ案（例）

リポジトリルートからの想定ツリー。既存ファイルの**即時移行は必須としない**（新規は新パス、既存は段階的移行で可）。

```

.github\workflows\deploy-py-to-aws-lambda.yml
⇢rename
  .github\workflows\deploy-py-to-aws-lambda-web.yml
  　azureも、gcpも、cfも同様

EA_Documents/
  Web/EdgeAnalyzer_BusinessVision.md
  Web/LookerStudio_DashboardDesign.md
  Web/n8n_GoogleDrive_connect.md
  llm/              # 開発開始時に追加する
    local/          # 開発開始時に追加する
    cloud/          # 開発開始時に追加する

EO_n8nWorkflow_Json/
  Web/              # 既存 eo-n8n-workflow-jp.json をここへ移す
  llm/              # 開発開始時に追加する
    local/          # 開発開始時に追加する
    cloud/          # 開発開始時に追加する

EO_Terraform_Docker/
⇢Archives/　配下に移動。

MCNE_Documents/
⇢Archives/　配下に移動。

EO_Documents/
  Manuals/
    Web/            # Web 向け手順の整理先（既存 EO_Architectureの中身を全部ここに移行）
    llm/            # 開発開始時に追加する
      local/        # 開発開始時に追加する
      cloud/        # 開発開始時に追加する

EO_Architecture/
  Web/Architecture.md           # 既存 ARCHITECTURE.md の内容を移行
  llm/local/Architecture.md     # 開発開始時に追加する
  llm/cloud/Architecture.md     # 開発開始時に追加する

EA_Documents/                   # Edge Analyzer 系ドキュメントも用途別に束ねる
  Web/                          # Web / CDN 系の分析・連携メモの整理先（新規・段階移行）
  llm/                          # 開発開始時に追加する
    local/                      # 開発開始時に追加する
    cloud/                      # 開発開始時に追加する
  # 既存ファイル（ルート直下）は段階的に上記へ寄せるか、README で索引のみ残す方針を決める

RequestEngine/                  # 下記ツリーへ移行（現状のルート直下 aws/ 等は RequestEngine/Web/ へ移す想定）
  Web/                          # 順次実行版・CDN/Web 向け。既存 RequestEngine の正規配置
    funcfiles/
      common/
        py/
        extensions/
    aws/
    azure/
    gcp/
    cf/
  llm/                          # 開発開始時に追加する
    local/                      # 開発開始時に追加する
    cloud/                      # 開発開始時に追加する
```

## 結論: `RequestEngine/Web` と `RequestEngine/LLM` の完全分離

**RequestEngine のコアは Web 用と LLM 用で分離する。** 以前メモした「用途別ディレクトリ三分割は未推奨」は、**この方針に置き換える**。

| ツリー | 役割 |
|--------|------|
| **`RequestEngine/Web`** | **順次実行・GET 中心の Web 版**を正とする。大規模なコア変更の必要性は**相対的に下がってきている**。 |
| **`RequestEngine/LLM/Cloud`** | GEO 分散・クラウド上の推論 API 向け。 |
| **`RequestEngine/LLM/Local`** | ローカル推論（同一マシン／LAN のエンドポイント）向け。 |

**コア共通化**（Web と LLM で共有する不変ライブラリの抽出）は、**`RequestEngine/LLM` 側で不変的なコアロジックの開発がある程度進んでから**行う。先に **LLM 版を独立ツリーで育てる**。

## LLM 版の着手手順（計画）

1. 現行の `RequestEngine/`（ルート直下の `funcfiles/`・`aws/` 等）を、**`RequestEngine/Web/` 配下に正規化**する（移動・パス修正は別タスク）。
2. **`RequestEngine/Web` を丸ごと複製**し、`RequestEngine/LLM/Cloud` と `RequestEngine/LLM/Local` に**リネーム**（または複製後に 2 本用意）。
3. 各 LLM 側で **流用できる部分は残し、流用すべきでない部分は徹底的に削除**する。
4. その後、**LLM 版の本格開発**（ストリーム・検証値の設計・並列など）に入る。

**注意**: 上記は **IaC・マージスクリプト・GitHub Actions のパス**をすべて `RequestEngine/Web/...` へ追従させる作業を伴う。別タスクで**一覧化してから**変更する。

## 旧メモ（参考）: 分離を一度「未推奨」とした理由

デプロイ・マージの二重管理リスクを避けるため、当初は **単一 `RequestEngine/` ツリー**を推奨していた。のち **Web と LLM で主力・実行モデルが根本的に異なる**こと、**検証値・ストリーム・並列**の設計を無理に一枚岩にしない判断を優先し、**物理分離に切り替えた**。

## 用語（混同禁止）

文書・会話では次を区別する。**「トークン」単独**は使わない（LLM のトークンと誤解されるため）。

| 呼び方 | 意味 |
|--------|------|
| **リクエストシークレット** | EO の共有秘密（例: `N8N_EO_REQUEST_SECRET`、各クラウドのシークレットストアに格納される値）。 |
| **検証値**（既存 JSON では n8n 計算結果を指すフィールド名のまま） | n8n が算出し、Request Engine が **リクエストシークレット**と組み合わせて照合する値。既存実装は `SHA-256(targetUrl + リクエストシークレット)` 相当の比較。 |
| **検証値の照合** | 上記の一致確認。**「トークン照合」**のような曖昧語は使わない。 |
| **LLM のトークン** | モデル入出力の単位（TPM 等）。EO 認証とは無関係。 |

**既存の変数名・JSON キー名は変更しない**（プロジェクト方針）。説明文だけ上表に寄せる。

## Web 版と LLM 版で求められる主力（前提の違い）

| 観点 | Web 版（CDN 等） | LLM 版（推論 API） |
|------|------------------|---------------------|
| **入力の主役** | **ターゲット URL の列**の獲得・重複排除・フィルタ精度 | **同一 `targetUrl` に対するリクエストボディ**が実行ごとに大きく変わる前提になりやすい |
| **HTTP** | GET 中心 | POST + JSON、**ストリーミング**が主戦場になりうる |
| **認証の論点** | URL 単位の検証値で説明しやすい | 同一 URL・別ボディのとき、**検証値を何に紐づけるか**は別設計が要る（現状の URL のみハッシュと矛盾しうる） |
| **並列** | n8n ループ + 地域分散で十分なことが多い | **ファンアウト**・長時間接続は **RE／別プロセス側**の設計が主 |

## コア共通化（将来タスク）

- **タイミング**: `RequestEngine/LLM` の**不変的なコア**（ストリーム・検証・計測の方針が固まったあと）。
- **候補**: リトライ、TLS／HTTP メタ取得、時刻、フラット JSON の枠組みなど、**両系統が同じ契約で使える**ものだけを抽出する。
- **現時点では**、Web と LLM の**巨大な `funcfiles/common` 共有**を前提にした設計は行わない（上記「完全分離」）。

## 運用・IaC のメモ（2026 年時点の認識）

- **約 2026 年 2 月末以降**: IaC を含む保守を **Lambda 中心に絞っている**経緯がある。
- **GKE・マルチリージョン推論（例: Cloud 側 LLM プローブ）**を本気で載せるなら、**GCP Cloud Run の RE**（および正規化後の `RequestEngine/Web/gcp/cloudrun/` または `RequestEngine/LLM/Cloud/gcp/cloudrun/` の Terraform）の **再開・更新**が必要になる可能性が高い。本項は「将来の決定事項」としてメモし、実際の再開タイミングは別途決定する。

## 置かないもの（参考）

- **`test/`**（リポジトリ規約どおり）: 他ディレクトリへの移動・複製は禁止。
- 新規用途のワークフロー JSON は **`EO_n8nWorkflow_Json/llm/local/` または `llm/cloud/`** に置く。

## 移行の原則

1. **一括リネームより段階的**：まず `llm/local/` と `llm/cloud/` を空で作成し、短い README のみ置く、でもよい。
2. **README 内リンク・手順書・n8n のファイルパス**は一括置換の影響が大きいため、**検索で確認してから**パス更新する。
3. 既存の **JSON キー名・エンドポイント名・変数名**はプロジェクト方針どおり変更しない（変更時は別途承認）。

## 関連ディレクトリ（本リポジトリ内）

- `RepoRestructure/Add_LLM/Plan.md` … 本計画メモ
- `RepoRestructure/Add_LLM/ReplacePatterns_and_Commands.md` … 手順 1 の成果物（**ワークフロー `*-web.yml` リネームと参照一覧**、`RequestEngine/Web/` 正規化、**手順 3 用の置換コマンド（PowerShell）**、手順 2〜4 との対応、漏れチェックリスト）
- `EO_Infra_Docker/` … n8n 等の共通インフラ（用途別に分けずに共用）

# その他

Archives/ 配下に移動するファイルは、以下の通り。

- EO_Terraform_Docker/
- MCNE_Documents/

# 作業の手分け

## 1
- CursorAI
  - 置換パターン洗い出し
  - ファイル内の置換コマンド作成
  - 置換コマンドのパターン漏れチェック
  - 成果物: `RepoRestructure/Add_LLM/ReplacePatterns_and_Commands.md`

## 2
- 人間
  - .github\workflowsのymlファイルをリネーム
  - /Web/ディレクトリを足す。既存を移動する。
  - /llm/local/ディレクトリを足す
  - /llm/cloud/ディレクトリを足す
  - /Archives/ディレクトリ対象の移動

## 3

- 人間
  - 置換コマンドの実行
  - 置換コマンドの結果確認

## 4

- CursorAI
  - 人間が実行した置換コマンドの結果チェック