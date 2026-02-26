# MultiCloudNamingEngine（MCNE）

- マルチクラウド（AWS / Azure / GCP ）・マルチエリアにおけるリソース命名を一元化するための設計ドキュメントです。
- ID圧縮命名エンジンです。
- 特定の1社の企業内としてシングルテナントを想定しています。
- B to BのSaaSとして拡張する場合、既にtenantは本ドキュメントの設計に組み込まれているため、この点においては拡張性があります。
  - 各種省略形の_slugは衝突する可能性がある。別途、テナント分離を優先したRLS (Row-Level Security)が必要。
- Cloudflareは未対応。

# 背景

Edge Optimizerの BtoB SaaS化を前提とした場合にマルチクラウドマルチエリアの命名がうまくいかない。失敗するとIaCによるリソース作成失敗などのクリティカルな問題に繋がる。そのため、命名ロジックを専用ライブラリ機能として独立させ、Request Engine や IaC（CFn / Bicep / Terraform / Wrangler）から呼び出して利用する方針とする。

# 階層構造の基本

ユーザー権限ツリー: Tenant ＞ Project ＞ User
リソース実体ツリー: Tenant ＞ Project ＞ Environment ＞ Area ＞ Resource

# マルチクラウド(AWS / Azure / GCP )リソース命名制約

各クラウドの命名規約をすべてそのまま満たすことは現実的ではないため、**MCNE としては「安全サブセット」を一つ決めてそこに合わせる**方針とする。  
2026/02/26 時点では、Azure Storage の制約を安全サブセットとして採用し、MCNE が生成する名前はこの制約を必ず満たすものとする。

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

グローバル一意必須を加味すると、issued_resource_name_nanoidを「論理的なリソースリソースグループ2文字」+「採番4文字」という命名は不可。

# マルチクラウド(AWS / Azure / GCP )リソース命名視認性確保

リソース名の文字数に余裕がある場合、セグメント間にハイフォンを入れる。

# 考え方（特定の1社の企業内としてシングルテナントを想定）

- 特定の1社の企業内としてシングルテナントを想定。
  - S3バケットやAzure Key Vault のようなグローバル一意リソース命名のユニーク確保が重要。
- issued_resource_namesテーブルは個々のリソースのGlobal Unique KeyとしてTenant、Project、Environment、Region、ResourceTypeなどのUUIDをUUIDv7で保持する。
- 「Environment」について、AWSはアカウントIDで環境を区分、AzureはサブスクリプションID(管理リソースグループ)で環境を区分、GCPはプロジェクトで環境を区分。
  - 「Environment」はリソース名にも含み、なおかつタグラベルにも含むのがベストプラクティス。
    - 理由：同一サブスクリプション(Azure)/プロジェクト(GCP)内で prd と dev のストレージアカウントを作る際、名前が重複すると作成できないため。
- 開発運用のコストを考慮し、各クラウドGUI画面におけるリソース命名の視認フィーリングによる理解の確保は必須
- Environment、Cloudプロバイダ種別、(短縮名を含む)エリア種別、リソースタイプは世界共通の命名でOK。
  - TerraformやPulmiなどのメジャーなIaCツールも参考にする
- 各セグメントを「リソース名」or「タグラベル」のどちらに記載するか、双方に記載するか、記載しないか基準が必要
  - タグラベルに記載。
    - Environment
　- リソース名に記載。MCNE 設計リミット（1社内 21 文字 / BtoB 22 文字）以内で表現する。
    - Tenant
    - Project
    - Environment
    - Area
    - ResourceType
    - Nano ID
- リソース名のハイフォン有無は、hyphen_allowed : falseリソースグループとhyphen_allowed : trueリソースグループで異なる。
  - hyphen_allowed : falseリソースグループ：ハイフォン無し
    - Azure Storage
    - Azure Key Vault
    - GCP Cloud Storage
    - GCP Service Account
  - hyphen_allowed : trueリソースグループ：ハイフォン有り
    - AWS S3
    - AWS Lambda
    - AWS Secrets Manager
    - AWS IAM Role
    - AWS IAM Policy

※CloudWatchのログ管理のログリソースグループは、スラッシュが一般的だがハイフォンを採用する。

# セグメント配置方針（タグ vs リソース名）

各セグメントをどこに載せるかは、MCNE では次のように整理する。

- **タグラベルに必ず載せる**: Environment（必要に応じて Tenant / Project / Area / ResourceType も載せる）
- **リソース名に必ず載せる（ハイフォン無し 用パックの対象）**: Tenant / Project / Environment / Area / ResourceType / Nano ID  
  - これらを連結した長さは **MCNE 設計リミット**以内に収める（実機リミット 24 文字のまま使う例では 4+3+2+5+4+6 = 24。バッファを取る場合は MCNE 設計リミットを 22 文字等にし、セグメント長を再配分する）。

# 個別リソース命名シュミレーション

## 1社内利用前提における推奨例（実機リミット 24 文字、MCNE 設計リミット 21 文字）

バッファ：3文字

| セグメント | DBカラム名 | max_length | 例  | max_length累計 |
| --- | --- | --- | --- | --- |
| Tenant        | tenant_slug | 3 | `nsh`  | 3 |
| Project       | project_slug | 3 | `edo`   | 6 |
| Environment   | environment_slug | 2 | `d1` | 8 |
| Area        | area_short_slug | 4 | `an01`| 12 |
| ResourceType  | resource_type_slug | 3 | `lam`  | 15 |
| NanoID          | issued_resource_name_nanoid_slug | 6 | `5g4h7b` | 21 |

- hyphen_allowed : falseリソースグループ：ハイフォン無（最大 21 文字）  
  - `{tenant_slug(3)}{project_slug(3)}{environment_slug(2)}{area_short_slug(4)}{resource_type_slug(3)}{issued_resource_name_nanoid_slug(6)}`  
  - `nshedod1an01lam5g4h7b` (21文字)
- hyphen_allowed : trueリソースグループ：ハイフォン有（最大 26 文字）
  - `{tenant_slug(3)}-{project_slug(3)}-{environment_slug(2)}-{area_short_slug(4)}-{resource_type_slug(3)}-{issued_resource_name_nanoid_slug(6)}`
  - `nsh-edo-d1-an01-lam-5g4h7b` (26文字)

## エリア短縮名4桁のバリエーション

[地理(2文字：英語)][ゾーン(2文字：数字0から9の10進数)]でクラウドは含めない。

理由：
- MCNEはクラウド抽象化エンジン
- エリアは地理概念として統一
- 後付拡張が可能

後付拡張の例：
- [地理2文字：英語][ゾーン2文字：英数字0から9 + AからZの36進数]

**Asia Pacific North East 短縮コード紐づけリスト**

同一地理圏を同一 prefix に集約。

| クラウド | 実エリア | 短縮コード  |
| --------- | ------------ | ------ |
| AWS | ap-northeast-1  | `an01` |
| AWS | ap-northeast-2  | `an02` |
| AWS | ap-northeast-3  | `an03` |
| GCP | asia-northeast1 | `an04` |
| GCP | asia-northeast2 | `an05` |
| Azure | japaneast     | `an06` |

**US East 短縮コード紐づけリスト**

同一地理圏を同一 prefix に集約。

| クラウド | 実エリア | 短縮コード  |
| --------- | ------------ | ------ |
| AWS | us-east-1 | `ue01` |
| AWS | us-east-2 | `ue02` |
| GCP | us-east1 | `ue03` |
| Azure | eastus | `ue04` |

※これだけでは全然足りないので、開発開始時点で実エリアと短縮コード紐づけリスト作成が必要。

## BtoBでSaaSにおける多テナント利用前提における推奨例（実機リミット 24 文字、MCNE 設計リミット 22 文字）

バッファ：2文字

| セグメント | DBカラム名 | max_length | 例  | max_length累計 |
| --- | --- | --- | --- | --- |
| Tenant        | tenant_slug | 4 | `nshi`  | 4 |
| Project       | project_slug | 3 | `edo`   | 7 |
| Environment   | environment_slug | 2 | `d1` | 9 |
| Area        | area_short_slug | 4 | `an01`| 13 |
| ResourceType  | resource_type_slug | 2 | `lm`  | 15 |
| NanoID          | issued_resource_name_nanoid_slug | 7 | `5g4h78b` | 22 |

- hyphen_allowed : falseリソースグループ：ハイフォン無（最大 22 文字）  
  - `{tenant_slug(4)}{project_slug(3)}{environment_slug(2)}{area_short_slug(4)}{resource_type_slug(2)}{issued_resource_name_nanoid_slug(7)}`  
  - `nshiedod1an01lm5g4h78b` (22文字)
- hyphen_allowed : trueリソースグループ：ハイフォン有（最大 27 文字）
  - `{tenant_slug(4)}-{project_slug(3)}-{environment_slug(2)}-{area_short_slug(4)}-{resource_type_slug(2)}-{issued_resource_name_nanoid_slug(7)}`
  - `nshi-edo-d1-an01-lm-5g4h78b` (27文字)

# Muclti Cloud Naming Engineの内部処理フロー

MCNEは、以下のロジックで各リソースの「物理名」を生成

1. 入力: tenant_id, project_id, resource_type_id, environment_id, area_id, 発行済みissued_resource_name_id
2. 変換: 内部マッピングテーブルを参照し、エリアを4文字（例: an01）、リソースを3文字（例: lam）に変換。
3. Nano ID生成: issued_resource_name_id から 6 文字のNano IDを生成。衝突する場合はリトライ試行回数上限5回として、上限回数を超えた場合は7文字のNanoIDとする。
4. 形式選択(推奨の場合):
    - hyphen_allowed : falseリソースグループ（Azure Storage等）: ハイフォンなしで連結 → nshiedod1an01lm5g4h78b (22文字)
    - hyphen_allowed : trueリソースグループ（AWS S3等）: ハイフォンありで連結 → nshi-edo-d1-an01-lm-5g4h78b (27文字)
5. 確定: 生成した名前をPostgreSQL(Neon DB)の issued_resource_names に保存。

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
| areas | area_id | 主キー | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | UUIDv7 |
| areas | area_short_slug | エリア名 | an01 | 4文字 | |
| areas | area_display_name | 表示名 | Asia Pacific (Osaka) | | |
| resource_types | resource_type_id | 主キー | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | UUIDv7 |
| resource_types | resource_type_slug | リソースタイプ名 | lam | 3文字 | |
| resource_types | resource_type_display_name | 表示名 | AWS Lambda | | 

**resource_type_constraints（リソース種別×クラウドごとの命名制約）**

クラウド × リソース種別の組み合わせでhyphen_allowed : falseリソースグループとhyphen_allowed : trueリソースグループの制約が異なるため、ハイフォン無しとLengthの命名制約を `resource_types` から分離し、リソース種別とクラウドの組み合わせごとに保持する。

| テーブル名 | カラム名 | 説明 | 例 | 文字数 | 備考 |
| --- | --- | --- | --- | --- | --- |
| resource_type_constraints | resource_type_constraint_id | 主キー | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | UUIDv7 |
| resource_type_constraints | resource_type_id | リソース種別ID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | 外部キー → resource_types |
| resource_type_constraints | cloud_provider_id | クラウドプロバイダID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | 外部キー → cloud_providers |
| resource_type_constraints | hyphen_allowed_false_max_length | ハイフォン無し 時の最大文字数 | 22 | - | ハイフォン無し連結の上限。実機リミット以下 |
| resource_type_constraints | hyphen_allowed_false_min_length | ハイフォン無し 時の最小文字数 | 21 | - | ハイフォン無し連結の下限。実機リミット以下 |
| resource_type_constraints | hyphen_allowed | ハイフォン許可 | true / false | - | false = ハイフォン無し、true = ハイフォン有り として扱う |
| resource_type_constraints | lowercase_required  | 小文字必須 | true / false | - |  |
| resource_type_constraints | global_unique_required | グローバル一意必須 | true / false | - | S3/Storage Account/Key Vault 等は true |

※(resource_type_id, cloud_provider_id) に Unique 制約を設ける。命名時は issued_resource_names の resource_type_id と cloud_provider_id で本テーブルを参照し、hyphen_allowed_false_max_length / hyphen_allowed_false_min_length / lowercase_required / hyphen_allowed に従って物理名を生成する。

※短縮エリア名、リソースタイプ名は、短縮エリア名、リソースタイプ名の変数マスタが別途必要、各クラウドのエリア名と短縮エリア名、リソースタイプ名とリソースタイプ名のマッピングを保持する。

**トランザクションテーブル（発行済リソース名台帳）**
| テーブル名 | カラム名 | 説明 | 例 | 文字数 | 備考|
| --- | --- | --- | --- | --- | --- |
| issued_resource_names | issued_resource_name_id | 主キー (InstanceUUID) | 01H... | 36 | UUIDv7 (Nano IDの生成元) |
| issued_resource_names | issued_resource_name_nanoid_slug | Nano ID | 5g4h78 | 6 or 7文字 | |
| issued_resource_names | issued_resource_name_nanoid_slug_length | Nano ID 桁数 | 6 or 7 | - | - |
| issued_resource_names | tenant_id | テナントID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| issued_resource_names | project_id | プロジェクトID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| issued_resource_names | environment_id | 環境ID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| issued_resource_names | area_id | エリアID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| issued_resource_names | resource_type_id | リソースタイプID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | | 外部キー |
| issued_resource_names | cloud_provider_id | クラウドプロバイダID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | 外部キー参照テーブル: cloud_providers |
| issued_resource_names | created_by_id | 作成者ID | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | 36 | 外部キー参照テーブル: users |
| issued_resource_names | issued_resource_name_slug | 発行済リソース名 | nshedod1an01lm5g4h78b | 22文字 | **全レコードUnique Index必須** |
| issued_resource_names | issued_resource_name_length | 発行済リソース名の長さ | 21 or 22文字 | - | **全レコードUnique Index必須** |
| issued_resource_names | issued_resource_name_deleted_at | 論理削除 | timestamp | - | - |

※issued_resource_names_strict_length_id と issued_resource_flexible_length_id は、各クラウドの「名称使用可能チェックAPI」を叩くバリデーションが必要。
※users テーブルは、ユーザー管理テーブルであり、ユーザーID、ユーザー名、ユーザー表示名、ユーザーメールアドレス、ユーザー権限などを保持する。

# Nano ID 衝突回避戦略

**現状の桁数と空間**
- 6文字（36進）: 36^6 ≒ 2.1B
- 7文字: 36^7 ≒ 78B
- 単一企業なら十分だが、論理削除あり・グローバル一意必須リソースありのため、衝突リスクを明示的に扱う必要がある。

**推奨（仕様書に明文化すべき）**
- **tenant + project + environment 単位で衝突チェック**を行う。
- **5回リトライ上限**を設ける。
- リトライ上限を越えて失敗した場合は**桁増加モード**（例: 6文字→7文字）に切り替える。

# hyphen_allowed の設計

- 同じ ResourceType でもクラウドで制約が違う。
  - 例: S3 → ハイフォン有り、Azure Storage → ハイフォン無し
- 将来、別クラウドで同種のリソースが ハイフォン無し になる可能性など、大げさとも言われるくらい想定外の事態を考慮しておくべき。

# 課題

抽象化を突き詰めると、ユニーク確保対策の衝突問題を避けやすくなるが、GUI上における人間の運用負荷が高くなる。

抽象化 と 運用負荷 のバランスを見極める必要がある。

1. 衝突チェックのスコープ設計
- global_unique_required = true の場合
  - 全 issued_resource_name_slug で衝突チェック
- global_unique_required = false の場合
  - (tenant_id + project_id + environment_id) 単位で衝突チェック
2. physical_name のユニーク保証範囲
3. resource_type 2文字は将来苦しくないか？
  - 2文字だと、36^2 = 1296通り。
  - 抽象化を丁寧に行えば、1296通りで足りる。
    - 例: AWS Lambda, Azure Functions, GCP Cloud Run は (抽象化)name:fncでid:25 として扱う。
  - マスタ管理なら問題ない。
4. 名前に意味を詰め込みすぎ
- 以下が発生した場合
  1. tenant名変更
  2. project統合
  3. env再設計
  4. area抽象化変更

→ 名前変更＝物理リソース再作成が必要になる