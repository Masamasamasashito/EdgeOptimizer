# MultiCloudNamingEngine（MCNE）

- マルチクラウド（AWS / Azure / GCP ）・マルチリージョンにおけるリソース命名を一元化するための設計ドキュメントです。
- ID圧縮命名エンジンです。
- 特定の1社の企業内としてシングルテナントを想定しています。
- B to BのSaaSとして拡張する場合、既にtenantは本ドキュメントの設計に組み込まれているため、この点においては拡張性があります。
  - 各種省略形の_slugは衝突する可能性がある。別途、テナント分離を優先したRLS (Row-Level Security)が必要。
- Cloudflareは未対応。

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

## リソース命名ポリシー

1. リソース名の1文字目は必ず英小文字で始まる。
2. リソース名の最後の1文字は必ず英小文字または数字で終わる。
3. Nano ID 生成時、使用するカスタムアルファベットを `abcdefghijklmnopqrstuvwxyz0123456789` に限定する。

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
　- リソース名に記載。MCNE 設計リミット（1社内 21 文字 / BtoB 22 文字）以内で表現する。
    - Tenant
    - Project
    - Environment
    - Region
    - ResourceType
    - Nano ID
- リソース名のハイフォン有無は、Strict LengthグループとFlexible Lengthグループで異なる。
  - Strict Lengthグループ：ハイフォン無し
    - Azure Storage
    - Azure Key Vault
    - GCP Cloud Storage
    - GCP Service Account
  - Flexible Lengthグループ：ハイフォン有り
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

## 1社内利用前提における推奨例（実機リミット 24 文字、MCNE 設計リミット 21 文字）

バッファ：3文字

| セグメント | DBカラム名 | max_length | 例  | max_length累計 |
| --- | --- | --- | --- | --- |
| Tenant        | tenant_slug | 3 | `nsh`  | 3 |
| Project       | project_slug | 3 | `edo`   | 6 |
| Environment   | environment_slug | 2 | `d1` | 8 |
| Region        | region_short_slug | 4 | `an01`| 12 |
| ResourceType  | resource_type_slug | 3 | `lam`  | 15 |
| NanoID          | issued_name_nanoid_slug | 6 | `5g4h7b` | 21 |

- Strict Lengthグループ：ハイフォン無（最大 21 文字）  
  - `{tenant_slug(3)}{project_slug(3)}{environment_slug(2)}{region_short_slug(4)}{resource_type_slug(3)}{issued_name_nanoid_slug(6)}`  
  - `nshedod1an01lam5g4h7b` (21文字)
- Flexible Lengthグループ：ハイフォン有（最大 26 文字）
  - `{tenant_slug(3)}-{project_slug(3)}-{environment_slug(2)}-{region_short_slug(4)}-{resource_type_slug(3)}-{issued_name_nanoid_slug(6)}`
  - `nsh-edo-d1-an01-lam-5g4h7b` (26文字)

## リージョン短縮名4桁のバリエーション

[地理(2文字：英語)][ゾーン(2文字：数字0から9の10進数)]でクラウドは含めない。

理由：
- MCNEはクラウド抽象化エンジン
- リージョンは地理概念として統一
- 後付拡張が可能

後付拡張の例：
- [地理2文字：英語][ゾーン2文字：英数字0から9 + AからZの36進数]

**Asia Pacific North East**

同一地理圏を同一 prefix に集約。

| クラウド | 実リージョン | 短縮コード  |
| --------- | ------------ | ------ |
| AWS | ap-northeast-1  | `an01` |
| AWS | ap-northeast-2  | `an02` |
| AWS | ap-northeast-3  | `an03` |
| GCP | asia-northeast1 | `an04` |
| GCP | asia-northeast2 | `an05` |
| Azure | japaneast     | `an06` |

**US East**

同一地理圏を同一 prefix に集約。

| クラウド | 実リージョン | 短縮コード  |
| --------- | ------------ | ------ |
| AWS | us-east-1 | `ue01` |
| AWS | us-east-2 | `ue02` |
| GCP | us-east1 | `ue03` |
| Azure | eastus | `ue04` |

## BtoBでSaaSにおける多テナント利用前提における推奨例（実機リミット 24 文字、MCNE 設計リミット 22 文字）

バッファ：2文字

| セグメント | DBカラム名 | max_length | 例  | max_length累計 |
| --- | --- | --- | --- | --- |
| Tenant        | tenant_slug | 4 | `nshi`  | 4 |
| Project       | project_slug | 3 | `edo`   | 7 |
| Environment   | environment_slug | 2 | `d1` | 9 |
| Region        | region_short_slug | 4 | `an01`| 13 |
| ResourceType  | resource_type_slug | 2 | `lm`  | 15 |
| NanoID          | issued_name_nanoid_slug | 7 | `5g4h78b` | 22 |

- Strict Lengthグループ：ハイフォン無（最大 22 文字）  
  - `{tenant_slug(4)}{project_slug(3)}{environment_slug(2)}{region_short_slug(4)}{resource_type_slug(2)}{issued_name_nanoid_slug(7)}`  
  - `nshiedod1an01lm5g4h78b` (22文字)
- Flexible Lengthグループ：ハイフォン有（最大 27 文字）
  - `{tenant_slug(4)}-{project_slug(3)}-{environment_slug(2)}-{region_short_slug(4)}-{resource_type_slug(2)}-{issued_name_nanoid_slug(7)}`
  - `nshi-edo-d1-an01-lm-5g4h78b` (27文字)

# Muclti Cloud Naming Engineの内部処理フロー

MCNEは、以下のロジックで各リソースの「物理名」を生成

1. 入力: tenant_id, project_id, resource_type_id, environment_id, region_id, 発行済みissued_name_id
2. 変換: 内部マッピングテーブルを参照し、リージョンを4文字（例: an01）、リソースを3文字（例: lam）に変換。
3. Nano ID生成: issued_name_id から 6 or 7文字のNano IDを生成。衝突の場合は試行回数上限を設けてリトライロジック実装必須。
4. 形式選択(推奨の場合):
    - Strict Lengthグループ（Azure Storage等）: ハイフォンなしで連結 → nshiedod1an01lm5g4h78b (22文字)
    - Flexible Lengthグループ（AWS S3等）: ハイフォンありで連結 → nshi-edo-d1-an01-lm-5g4h78b (27文字)
5. 確定: 生成した名前をPostgreSQL(Neon DB)の issued_names に保存。

# 1社内利用前提におけるデータベース・マスタ構成（PostgreSQL）

個々のリソースのUUIDv7を主軸としたマスタ設計

**マスタテーブル群**
| テーブル名 | カラム名 | 説明 | 例 | 文字数 | 備考|
| --- | --- | --- | --- | --- | --- |
| tenants | tenant_id | 主キー | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | UUIDv7 |
| tenants | tenant_slug | テナント名 | nsh | 3文字 | |
| tenants | tenant_display_name | 表示名 | Nishilabo Inc. | | |
| projects | project_id | 主キー | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | UUIDv7 |
| projects | tenant_id | テナントID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| projects | project_slug | プロジェクト名 | edo | 3文字 | |
| projects | project_display_name | 表示名 | Edge Optimizer | | |
| environments | environment_id | 主キー | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | UUIDv7 |
| environments | environment_slug | 環境名 | d1 | 2文字 | |
| environments | environment_display_name | 表示名 | Development1 | | |
| regions | region_id | 主キー | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | UUIDv7 |
| regions | region_short_slug | リージョン名 | an01 | 4文字 | |
| regions | region_display_name | 表示名 | Asia Pacific (Osaka) | | |
| resource_types | resource_type_id | 主キー | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | UUIDv7 |
| resource_types | resource_type_slug | リソースタイプ名 | lam | 3文字 | |
| resource_types | resource_type_display_name | 表示名 | AWS Lambda | | 
| resource_types | naming_length_type | 命名長さ種別 | strict/flexible | - | -（制約詳細は resource_type_constraints を参照） |

**resource_type_constraints（リソース種別×クラウドごとの命名制約）**

同一リソース種別でもクラウドで制約が異なるため、命名制約を `resource_types` から分離し、リソース種別とクラウドの組み合わせごとに保持する。

| テーブル名 | カラム名 | 説明 | 例 | 文字数 | 備考 |
| --- | --- | --- | --- | --- | --- |
| resource_type_constraints | resource_type_constraint_id | 主キー | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | UUIDv7 |
| resource_type_constraints | resource_type_id | リソース種別ID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | 外部キー → resource_types |
| resource_type_constraints | cloud_provider_id | クラウドプロバイダID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | 外部キー → cloud_providers |
| resource_type_constraints | strict_max_length | Strict 時の最大文字数 | 21 or 22 | - | ハイフン無しで連結した場合の上限。実機リミット以下 |
| resource_type_constraints | hyphen_allowed | ハイフン許可 | true / false | - | false = Strict、true = Flexible として扱う |
| resource_type_constraints | global_unique_required | グローバル一意必須 | true / false | - | S3/Storage Account/Key Vault 等は true |

※(resource_type_id, cloud_provider_id) に Unique 制約を設ける。命名時は issued_names の resource_type_id と cloud_provider_id で本テーブルを参照し、strict_max_length / hyphen_allowed に従って物理名を生成する。

※短縮リージョン名、リソースタイプ名は、短縮リージョン名、リソースタイプ名の変数マスタが別途必要、各クラウドのリージョン名と短縮リージョン名、リソースタイプ名とリソースタイプ名のマッピングを保持する。

**トランザクションテーブル（発行済台帳）**
| テーブル名 | カラム名 | 説明 | 例 | 文字数 | 備考|
| --- | --- | --- | --- | --- | --- |
| issued_names | issued_name_id | 主キー (InstanceUUID) | 01H... | 36 | UUIDv7 (Nano IDの生成元) |
| issued_names | issued_name_nanoid_slug | Nano ID | 5g4h78 | 6 or 7文字 | |
| issued_names | tenant_id | テナントID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| issued_names | project_id | プロジェクトID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| issued_names | environment_id | 環境ID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| issued_names | region_id | リージョンID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| issued_names | resource_type_id | リソースタイプID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| issued_names | cloud_provider_id | クラウドプロバイダID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | 外部キー参照テーブル: cloud_providers |
| issued_names | created_by_id | 作成者ID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | 外部キー参照テーブル: users |
| issued_names | naming_length_type | 命名長さ種別 | strict/flexible | - | - |
| issued_names | issued_resource_strict_length_id | 発行済リソースID(Strict Lengthグループ) | nshedod1... | 21 or 22文字 | **全レコードUnique Index必須** |
| issued_names | issued_resource_flexible_length_id | 発行済リソースID(Flexible Lengthグループ) | nsh-edo-d1-... | 26 or 27文字 | **全レコードUnique Index必須** |
| issued_names | issued_name_deleted_at | 論理削除 | timestamp | - | - |

※issued_resource_strict_length_id と issued_resource_flexible_length_id は、各クラウドの「名称使用可能チェックAPI」を叩くバリデーションが必要。
※users テーブルは、ユーザー管理テーブルであり、ユーザーID、ユーザー名、ユーザー表示名、ユーザーメールアドレス、ユーザー権限などを保持する。

# 改善すべき重要ポイント

## ① naming_length_type の設計はまだ弱い

**現状**
- `resource_types.naming_length_type`
- `issued_names.naming_length_type`

**問題**
- 同じ ResourceType でもクラウドで制約が違う。
  - 例: S3 → Flexible、Azure Storage → Strict
- 将来、別クラウドで同種が Strict になる可能性がある。

**推奨構造**
- 命名制約を `resource_types` から分離し、**resource_type_constraints** テーブルを導入する（本 README の「1社内利用前提におけるデータベース・マスタ構成」内にテーブル定義を記載済み）。
  - `resource_type_id`、`cloud_provider_id`、`strict_max_length`、`hyphen_allowed`、`global_unique_required`
  - 主キーは `resource_type_constraint_id`（UUIDv7）。(resource_type_id, cloud_provider_id) に Unique 制約。

## ② issued_resource_strict と flexible 両方を永続化している

**問題**
- Strict と Flexible の両カラムを永続化しており冗長である。
- 理論上、Strict があれば Flexible は再生成可能。
- 現構造では 2 カラム Unique Index の整合性維持が複雑になる。

**推奨**
- **naming_schema_version** を導入し、将来のスキーマ変更に備える。
  - `naming_schema_version smallint not null`
- Strict のみ永続化し、Flexible は必要時に Strict から導出する設計を検討する。

## ③ Nano ID 衝突戦略が弱い

**現状の桁数と空間**
- 6文字（36進）: 36^6 ≒ 2.1B
- 7文字: 36^7 ≒ 78B
- 単一企業なら十分だが、論理削除あり・グローバル一意必須リソースありのため、衝突リスクを明示的に扱う必要がある。

**推奨（仕様書に明文化すべき）**
- **tenant + project + environment 単位で衝突チェック**を行う。
- **5回リトライ上限**を設ける。
- リトライ上限を越えて失敗した場合は**桁増加モード**（例: 6文字→7文字）に切り替える。