# MultiCloudNamingEngine（MCNE）

- マルチクラウド（AWS / Azure / GCP / Cloudflare）・マルチリージョンにおけるリソース命名を一元化するための専用ライブラリドキュメントです。
- 特定の1社の企業内としてシングルテナントを想定しています。
- B to BのSaaSとして拡張する場合、既にtenantは本ドキュメントの設計に組み込まれているため、この点においては拡張性があります。UUIDv7をグローバルな識別子として使用しない。
  - 各種省略形の_slugは衝突する可能性がある。別途、テナント分離を優先したRLS (Row-Level Security)が必要。

# 背景

Edge Optimizerの BtoB SaaS化を前提とした場合にマルチクラウドマルチリージョンの命名がうまくいかない。失敗するとIaCによるリソース作成失敗などのクリティカルな問題に繋がる。そのため、命名ロジックを専用ライブラリ機能として独立させ、Request Engine や IaC（CFn / Bicep / Terraform / Wrangler）から呼び出して利用する方針とする。世界的に同じ課題があり、ニーズもあると考えられる

# 階層構造の基本

ユーザー権限ツリー: Tenant ＞ Project ＞ User
リソース実体ツリー: Tenant ＞ Project ＞ Environment ＞ Region ＞ Resource

# マルチクラウド(AWS / Azure / GCP )リソース命名制約

各クラウドの命名規約をすべてそのまま満たすことは現実的ではないため、**MCNE としては「安全サブセット」を一つ決めてそこに合わせる**方針とする。  
2026/02/25 時点では、Azure Storage の制約を安全サブセットとして採用し、MCNE が生成する名前はこの制約を必ず満たすものとする。

## 実機リミットと MCNE 設計リミット

- **実機リミット**: 各クラウドプロバイダが定めるリソース名の**ハード上限**（文字数・文字種）。例: Azure Storage は「小文字英数字のみ、3〜24文字」。仕様変更等で変動しうる。
- **MCNE 設計リミット**: MCNE が名前を生成する際に**実際に使う上限**。実機リミットより短く（または狭く）取り、**バッファ**を残す。例: 実機リミットが 24 文字なら、MCNE 設計リミットを 22 文字にし、2 文字分は将来の仕様変更・プレフィックス追加・セグメント拡張に備える。MCNE が出力する名前は常に MCNE 設計リミット以内に収める。

実機リミットいっぱいまで使うと、仕様変更や設計見直し時に命名スキーム全体の変更が必要になり、既存リソースの再発行や IaC の一斉更新が発生するリスクが大きい。そのため MCNE 設計リミットで余裕を持たせる。

- Azure Storage の「小文字英数字のみ（ハイフォン不可）、3~24文字」を**実機リミット**の代表として採用し、MCNE が扱う全リソース共通の「安全な文字種」とする。**MCNE 設計リミット**は文字数について実機より短く取り、バッファを確保する（具体値はセグメント設計で決定）
  - UUIDv4 や UUIDv7 は桁数が多すぎてこの制約を満たせないため、**リソース名そのものには UUID を直接使わず、短い slug + Nano IDに変換する**
  - グローバル一意が必要なリソース（S3 バケット/Storage アカウント/Key Vault 等）も、この安全サブセットの範囲内で一意名を生成する

※Nano ID 生成時、使用するカスタムアルファベットを `abcdefghijklmnopqrstuvwxyz0123456789` に限定する。

## リソース名の文字数制約が厳しいクラウドサービス

- Azure Storage（**グローバル一意必須**）
  - 小文字英数字のみ（ハイフォン不可）、3~24文字
- Azure Key Vault（**グローバル一意必須**）
  - 小文字英数字のみ（ハイフォン不可）、3~24文字
- GCP Cloud Storage（**グローバル一意必須**）
  - 小文字英数字のみ（ハイフォン不可）、3~63文字
- GCP Service Account（**プロジェクト内一意**）
  - 小文字英数字のみ（ハイフォン不可）、3~30文字

グローバル一意必須を加味すると、issued_name_nanoidを「論理的なリソースグループ2文字」+「採番4文字」という命名は不可。

# マルチクラウド(AWS / Azure / GCP )リソース命名視認性確保

リソース名の文字数に余裕がある場合、セグメント間にハイフォンを入れる。

# 考え方（特定の1社の企業内としてシングルテナントを想定）

- 特定の1社の企業内としてシングルテナントを想定。
  - S3バケットやAzure Key Vault のようなグローバル一意リソース命名のユニーク確保が重要。
- issued_namesテーブルは個々のリソースのGlobal Unique KeyとしてTenant、Project、Environment、Region、ResourceTypeなどのUUIDをUUIDv7で保持する。
- 「Environment」について、AWSはアカウントIDで環境を区分、AzureはサブスクリプションID(管理グループ)で環境を区分、GCPはプロジェクトで環境を区分。
  - 「Environment」はリソース名にも含み、なおかつタグラベルにも含むのがベストプラクティス。
    - 理由：同一サブスクリプション(Azure)/プロジェクト(GCP)内で prd と dev のストレージアカウントを作る際、名前が重複すると作成できないため。
- 開発運用のコストを考慮し、各クラウドGUI画面におけるリソース命名の視認フィーリングによる理解の確保は必須
- Environment、Cloudプロバイダ種別、(短縮名を含む)リージョン種別、リソースタイプは世界共通の命名でOK。
  - TerraformやPulmiなどのメジャーなIaCツールも参考にする
- 各セグメントを「リソース名」or「タグラベル」のどちらに記載するか、双方に記載するか、記載しないか基準が必要
  - タグラベルに記載。
    - Environment
　- リソース名に記載。最短文字数24文字で表現できるようにする必要あり。
    - Tenant
    - Project
    - Environment
    - Region
    - ResourceType
    - Nano ID
- リソース名のハイフォン有無は、Strict LengthリソースグループとFlexible Lengthリソースグループで異なる。
  - Strict Lengthリソースグループ：ハイフォン無し
    - Azure Storage
    - Azure Key Vault
    - GCP Cloud Storage
    - GCP Service Account
  - Flexible Lengthリソースグループ：ハイフォン有り
    - AWS S3
    - AWS Lambda
    - AWS Secrets Manager
    - AWS IAM Role
    - AWS IAM Policy

※CloudWatchのログ管理のロググループは、スラッシュが一般的だがハイフォンを採用する。

# セグメント配置方針（タグ vs リソース名）

各セグメントをどこに載せるかは、MCNE では次のように整理する。

- **タグラベルに必ず載せる**: Environment（必要に応じて Tenant / Project / Region / ResourceType も載せる）
- **リソース名に必ず載せる（Strict 用パックの対象）**: Tenant / Project / Environment / Region / ResourceType / Nano ID  
  - これらを連結した長さは **MCNE 設計リミット**以内に収める（実機リミット 24 文字のまま使う例では 4+3+2+5+4+6 = 24。バッファを取る場合は MCNE 設計リミットを 22 文字等にし、セグメント長を再配分する）。

# 個別リソース命名シュミレーション

## 例（実機リミット 24 文字 = MCNE 設計リミット）

バッファ：0文字

| セグメント | DBカラム名 | max_length | 例 | max_length累計 |
| --- | --- | --- | --- | --- |
| Tenant | tenant_slug | 2 | `ns` | 2 |
| Project | project_slug | 3 | `edo` | 5 |
| Environment | environment_slug | 2 | `d1` | 7 |
| Region | region_slug | 5 | `apne1` | 12 |
| ResourceType | resource_type_slug | 6 | `lambda` | 18 |
| Nano ID | issued_name_nanoid | 6 | `5g4h78` | 24 |

- ハイフォン有
  - `{tenant_slug(2)}-{project_slug(3)}-{environment_slug(2)}-{region_slug(5)}-{resource_type_slug(3)}-{issued_name_nanoid_slug(6)}`
  - `ns-edo-d1-apne1-lambda-5g4h78` (29文字)
- ハイフォン無（Strict 対象用の 24 文字）
  - `{tenant_slug(2)}{project_slug(3)}{environment_slug(2)}{region_slug(5)}{resource_type_slug(6)}{issued_name_nanoid_slug(6)}`
  - `nsedod1apne1lambda5g4h78` (24文字)

## 例（実機リミット 24 文字、MCNE 設計リミット 21 文字）

バッファ：3文字

| セグメント | DBカラム名 | max_length | 例  | max_length累計 |
| --- | --- | --- | --- | --- |
| Tenant        | tenant_slug | 2 | `ns`  | 2  |
| Project       | project_slug | 2 | `eo`   | 4  |
| Environment   | environment_slug | 2 | `d1`   | 6  |
| Region        | region_slug | 5 | `apne1`| 11 |
| ResourceType  | resource_type_slug | 4 | `lamb`  | 15 |
| NanoID          | issued_name_nanoid_slug | 6 | `5g4h7b` | 21 |

- ハイフォン有
  - `{tenant_slug(2)}-{project_slug(2)}-{environment_slug(2)}-{region_slug(5)}-{resource_type_slug(4)}-{issued_name_nanoid_slug(6)}`
  - `ns-eo-d1-apne1-lamb-5g4h7b` (26文字)
- ハイフォン無（Strict 対象用の 21 文字）  
  - `{tenant_slug(2)}{project_slug(2)}{environment_slug(2)}{region_slug(5)}{resource_type_slug(4)}{issued_name_nanoid_slug(6)}`  
  - `nsedod1apne1lamb5g4h7b`（21文字） 

# Muclti Cloud Naming Engineの内部処理フロー

MCNEは、以下のロジックで各リソースの「物理名」を生成

1. 入力: TenantUUIDv7, ProjectUUIDv7, ResourceTypeUUIDv7, Env, Region, 新規発行用InstanceUUIDv7
2. 変換: 内部マッピングテーブルを参照し、リージョンを5文字（例: apne1）、リソースを4文字（例: lamb）に変換。
3. Nano ID生成: InstanceUUIDv7 から 6文字のNano IDを生成。衝突の場合はリトライロジック実装必須。
4. 形式選択: * Strict対象（Azure Storage等）: ハイフォンなしで連結 → nishedod1apne1lamb5g4h78 (24文字)
    - Flexible対象（AWS S3等）: ハイフォンありで連結 → nish-edo-d1-apne1-lamb-5g4h78 (29文字)
5. 確定: 生成した名前をPostgreSQL(Neon DB)の issued_names に保存。

# データベース・マスタ構成（PostgreSQL）

個々のリソースのUUIDv7を主軸としたマスタ設計

**マスタテーブル群**
| テーブル名 | カラム名 | 説明 | 例 | 文字数 | 備考|
| --- | --- | --- | --- | --- | --- |
| tenants | tenant_id | 主キー | 01H... | 36 | UUIDv7 |
| tenants | tenant_slug | テナント名 | nish | 4文字 | UNIQUE制約 |
| tenants | tenant_display_name | 表示名 | Nishilabo Inc. | | |
| projects | project_id | 主キー | 01H... | 36 | UUIDv7 |
| projects | tenant_id | テナントID | 01H... | | 外部キー |
| projects | project_slug | プロジェクト名 | edo | 3文字 | |
| projects | project_   display_name | 表示名 | Edge Optimizer | | |
| environments | environment_id | 主キー | 01H... | 36 | UUIDv7 |
| environments | environment_slug | 環境名 | d1 | 2文字 | UNIQUE制約 |
| environments | environment_display_name | 表示名 | Development1 | | |
| regions | region_id | 主キー | 01H... | 36 | UUIDv7 |
| regions | region_slug | リージョン名 | apne1 | 5文字 | UNIQUE制約 |
| regions | region_display_name | 表示名 | Asia Pacific (Osaka) | | |
| resource_types | resource_type_id | 主キー | 01H... | 36 | UUIDv7 |
| resource_types | resource_type_slug | リソースタイプ名 | lamb | 4文字 | UNIQUE制約 |
| resource_types | resource_type_display_name | 表示名 | AWS Lambda | | |

※短縮リージョン名、リソースタイプ名は、短縮リージョン名、リソースタイプ名の変数マスタが別途必要、各クラウドのリージョン名と短縮リージョン名、リソースタイプ名とリソースタイプ名のマッピングを保持する。

**トランザクションテーブル（発行済台帳）**
| テーブル名 | カラム名 | 説明 | 例 | 文字数 | 備考|
| --- | --- | --- | --- | --- | --- |
| issued_names | issued_name_id | 主キー (InstanceUUID) | 01H... | 36 | UUIDv7 (Nano IDの生成元) |
| issued_names | tenant_id | テナントID | 01H... | | 外部キー |
| issued_names | project_id | プロジェクトID | 01H... | | 外部キー |
| issued_names | environment_id | 環境ID | 01H... | | 外部キー |
| issued_names | region_id | リージョンID | 01H... | | 外部キー |
| issued_names | resource_type_id | リソースタイプID | 01H... | | 外部キー |
| issued_names | issued_name_nanoid | Nano ID | 5g4h78 | 6文字 | |
| issued_names | issued_name_slug | 発行済リソース名 | nish-edo-d1... | 29 | **全レコードUNIQUE制約必須** |