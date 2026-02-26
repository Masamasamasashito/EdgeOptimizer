# Azure Functions Bicepを軸にしたpyIaCのMCNE 命名寄せ計画

**参照:**
1. [MCNE_Documents/README.md](../../../MCNE_Documents/README.md)
2. [pyIaC_MCNE_plan.md](./pyIaC_MCNE_plan.md)
3. [AZFUNC_BICEP_MCNE_plan.md](./AZFUNC_BICEP_MCNE_plan.md)
4. [LAMBDA_CFN_README.md](./LAMBDA_CFN_README.md)
5. [CloudRun_TF_README.md](./CloudRun_TF_README.md)
6. [SchemaDesign_DbNormalization.md](../SchemaDesign_DbNormalization.md) 

## 1. 結論と方針

- **追記のみ:** README に「MCNE 参照・将来は MCNE 発行名を Bicep に渡す」と書くだけなら追記で足りる。
- **設計を寄せる:** セグメント対応・パターン式・一意部分（Nano ID）・hyphen 2 グループの修正がセットで必要。以下はその採用案（BtoB 前段として妥当・整合性の高い改善案）。
- **名前の付け替え:** 旧 EO_PROJECT → EoTenant、旧 EO_COMPONENT → EoProject は **2 本セット**で変更。EoRegion は Azure 配置用に維持。
- セグメント命名に用途/役割（EO_COMPONENT）を持たせると制約を守れない、破綻する。

## 2. セグメント対応（採用案）

| 現行（Bicep 等） | MCNE セグメント | 新命名/PascalCase(CFn,Bicep,Terraform) |
|------------------|-----------------|----------------------|
| EO_PROJECT | tenant_slug | **EoTenant** |
| EO_COMPONENT | project_slug | **EoProject** |
| EO_ENV※ | environment_slug | **EoEnvironment** |
| EO_REGION_SHORT | area_short_slug | **EoAreaShort** |
| EO_GLOBAL_PRJ_ENV_ID | — | **廃止** |
| EoServerlessService（CFn）等 | service_type_slug | **EoServiceServerless**（値例: lambda, fnc） |
| EoSecretService（CFn）等 | service_type_slug | **EoServiceSecret**（値例: secretsmng, kv） |
| — | service_type_slug | **EoServiceStorage**（値例: st） |
| EO_RE_INSTANCE_ID | issued_resource_name_nanoid_slug | **EoNanoidSlug**（6 or 7 文字の Nano ID） |

**サービス種別を 1 パラメータ（EoService）に統合しない理由:** 同一 CFn スタックで Lambda 名（lambda）と Secrets Manager 名（secretsmng）の両方が必要になるため、1 パラメータでは両方の値を表現できず矛盾する。このため **EoServiceServerless / EoServiceSecret / EoServiceStorage** に分けてリネームする。MCNE では service_type_slug を用いる（[MCNE_Documents/README.md](../../../MCNE_Documents/README.md) 参照）。

※.envファイルがあるため、envという単語を避けてEoEnvではなくEoEnvironmentにした。

## 3. 現況と MCNE でロジックが異なる項目

| 項目 | 現況（CFn/Bicep/Terraform） | MCNE に寄せる場合 |
|------|-----------------------------|-------------------|
| **EoAreaShort** | クラウドごとのリージョン短縮（apne1, jpe, asne1）。値の体系がクラウドごとに異なる。 | クラウド非依存の area_short_slug（4 文字。an01, an06 等）。area マスタで実リージョンを解決。 |
| **EoServiceServerless / EoServiceSecret / EoServiceStorage** | パラメータや名前埋め込みで個別に表現（EoServerlessService, EoSecretService、funcapp/kv/st 等）。 | service_type_slug をマスタで一元管理。サービス種別×クラウドで hyphen_allowed や文字数制約を参照。 |

MCNE に寄せる場合は、EoAreaShort は area マスタに合わせた値・解決ロジックに、サービス種別は EoServiceServerless / EoServiceSecret / EoServiceStorage および service_type_slug に合わせた扱いに変更する。

## 4. 3 クラウド相性・記法統一

**相性: 良い。** 同じ階層（Tenant / Project / Environment / Area）で揃えられる。

| 概念 | Bicep | AWS CFn | GCP Terraform |
|------|-------|---------|---------------|
| テナント | EoTenant | EoProject→EoTenant | project_prefix→EoTenant |
| プロジェクト | EoProject | EoComponent→EoProject | component→EoProject |
| 環境 | EoEnvironment | EoEnvironment | environment→EoEnvironment |
| エリア | EoAreaShort | EoRegionShort→EoAreaShort | region_short→EoAreaShort |
| 一意部分 | EoNanoidSlug | 現状未使用（将来追加可） | 現状未使用（将来追加可） |

**記法を PascalCase に統一:** 環境変数・ワークフローで **EoTenant, EoProject, EoEnvironment, EoAreaShort, EoServiceServerless, EoServiceSecret, EoServiceStorage, EoNanoidSlug** を共通にし、CFn/Bicep はそのまま、Terraform は `TF_VAR_EoProject` 等で渡す。**理由:** CFn の論理名は `[A-Za-z][A-Za-z0-9]*` のためアンダースコア不可で PascalCase が事実上必須。3 クラウドで同一名を共有するには CFn の制約に合わせる。Bicep は PascalCase 可、Terraform も文法上 PascalCase 可。

## 5. 命名パターン（hyphen_allowed 2 グループ）

**セグメント順:** tenant → project → environment → area → service_type → nanoid

| グループ | リソース | パターン | 例 |
|----------|----------|----------|-----|
| hyphen_allowed : false | Key Vault, Storage | `{tenant}{project}{env}{area}{service_type_slug}{nanoid}` | `eored1an06kv5g4h7b`, `eored1an06st5g4h7b` |
| hyphen_allowed : true | Function App 等 | `{tenant}-{project}-{env}-{area}-{service_type_slug}-{nanoid}` | `eo-re-d1-an06-fnc-5g4h7b` |

Key Vault は Azure 上ハイフン可だが、MCNE の安全サブセットに合わせて hyphen_allowed : false で統一する。

## 6. 移行・実装の要点

- **移行:** 新パターンでリソース名が変わるため、既存は「新名で新規作成 → 切り替え → 旧削除」等の手順を別途用意。同一名の変更は不可。
- **注意:** (1) EoTenant / EoProject の 2 本をセットで変更 (2) ワークフロー・README・naming_convention・他 IaC の参照を一括更新 (3) 既存環境がある場合は移行手順を用意。
- **チェックリスト:** Bicep のパラメータ・変数式を新セグメント対応に変更 → リソース名を §5 のパターンに変更 → ワークフロー・README・naming_convention を更新。

## 7. README に追記するだけの場合（設計は変えない）

設計を変えず拡張性だけ確保する場合、AZFUNC_BICEP_README の「リソース名パターン」付近に次の 1 ブロックを追記する。

> 本手順のリソース名は [SchemaDesign_DbNormalization.md](../SchemaDesign_DbNormalization.md) に準拠しています。マルチクラウド命名の一元化方針は [MCNE_Documents/README.md](../../../MCNE_Documents/README.md) を参照してください。将来 MCNE を導入する場合は、MCNE が発行するリソース名を Bicep のパラメータに渡して利用する想定です。現行の EO_PROJECT / EO_REGION_SHORT / EO_GLOBAL_PRJ_ENV_ID / EO_RE_INSTANCE_ID は、MCNE の tenant_slug・project_slug / area_short_slug / 一意部分（Nano ID）等に対応します。

実際に Bicep を MCNE に合わせる場合は、本ドキュメントの §2〜§6 に沿って修正する。
