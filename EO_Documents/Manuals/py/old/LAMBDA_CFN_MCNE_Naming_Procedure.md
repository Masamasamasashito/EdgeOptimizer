# Lambda / CFn を pyIaC_MCNE_Naming の新命名（PascalCase）に寄せる手順

[pyIaC_MCNE_Naming.md](./pyIaC_MCNE_Naming.md) の §2 セグメント対応に従い、Lambda 関連のパラメータ名・ドキュメント・ワークフローを一括で変更する手順。**リソース名の文字列（例: `tnp-re-d1-lambda-apne1`）は変更しない。** パラメータ名のみ EoTenant / EoProject / EoEnvironment / EoAreaShort / EoServiceServerless / EoServiceSecret に揃える。

**対応前後のパラメータ対応**

| 現行（CFn） | 新命名（PascalCase） | デフォルト値 |
|-------------|----------------------|--------------|
| EoProject | **EoTenant** | tnp |
| EoComponent | **EoProject** | re |
| EoEnv | **EoEnvironment** | d1 |
| EoRegionShort | **EoAreaShort** | apne1 |
| EoServerlessService | **EoServiceServerless** | lambda |
| EoSecretService | **EoServiceSecret** | secretsmng |

※ EoRegion（AWS リージョン識別子）、EoReLambdaLayerName 等の Lambda 固有パラメータはそのまま。EoRePythonRuntimeVer → EoReRuntimeVer に変更。

※ **テナント名の記載:** `tnp` はテナントプレフィックスの例であり、従来の Edge Optimizer の `eo` とは別の値である。ドキュメント等では例のままtnpと記載している旨を宣言したほうが良さそう。

## 手順 1: CloudFormation テンプレートのパラメータ名変更

**対象ファイル:** `RequestEngine/aws/lambda/py/CFn/re-aws-cfnstack.yml`

1. **Parameters セクション**
   - `EoProject` → `EoTenant`（Default: tnp, Description・AllowedPattern は意味に合わせて「Tenant prefix」等に修正）
   - `EoComponent` → `EoProject`（Default: re, Description を「Project identifier」等に）
   - `EoEnv` → `EoEnvironment`（Default: d1）
   - `EoRegionShort` → `EoAreaShort`（Default: apne1, AllowedValues はそのまま）
   - `EoServerlessService` → `EoServiceServerless`（Default: lambda, AllowedValues はそのまま）
   - `EoSecretService` → `EoServiceSecret`（Default: secretsmng, AllowedValues はそのまま）
   - `EoLambdaRequestSecretName` → `EoRequestSecretName`（Default: LAMBDA_REQUEST_SECRET, AllowedValues はそのまま）
   - `EoRegion` → `EoArea`（Default: ap-northeast-1, AllowedValues はそのまま）
   - `EoRePythonRuntimeVer` → `EoReRuntimeVer`（Default: python3.14, AllowedValues はそのまま）
   - `EoReLambdaTimeout` → `EoReTimeout`（Default: 30, AllowedValues はそのまま）
   - `EoReLambdaMemorySize` → `EoReMemorySize`（Default: 128, AllowedValues はそのまま）

2. **Metadata（ParameterGroups / ParameterLabels）**
   - 上記 6 パラメータのラベルを新名に合わせて表示名を修正（例: EoProject → "Tenant Prefix (e.g., tnp)"、EoComponent → "Project Identifier (e.g., re)"）。

3. **Resources および Conditions 内の参照を一括置換（必ず次の順で実施）**
   - 先に `EoProject` を置換すると後で `EoComponent` → `EoProject` が別の EoTenant を EoProject に変えてしまうため、**逆順**で行う。
   - `EoSecretService` → `EoServiceSecret`
   - `EoServerlessService` → `EoServiceServerless`
   - `EoRegionShort` → `EoAreaShort`
   - `EoProject` → `EoTenant`
   - `EoComponent` → `EoProject`
   - `EoEnv` → `EoEnvironment`
   - `EoRePythonRuntimeVer` → `EoReRuntimeVer` 

4. **コメント・POST-DEPLOYMENT 等**
   - 先頭コメントの `{EoProject}-{EoComponent}-...` 等を `{EoTenant}-{EoProject}-...` に変更。
   - Layer ARN 例・IAM ユーザー名のプレースホルダーも同様に新名に合わせる。

5. **Tags の Key 名**
   - `Key: Project` のまま（値は `!Ref EoTenant` または `!Ref EoProject` のどちらか設計に合わせる。通常は Project = EoProject の値）。
   - `Key: EoEnv` → `Key: EoEnvironment`、`Value: !Ref EoEnvironment` に統一。

※ 置換時は **EoReLambdaLayerSuffix / EoReLambdaLayerVer** は変更しないこと（EoRegion → EoArea は手順どおり実施）。また、`EoProject` → `EoTenant` を先に、`EoComponent` → `EoProject` を後に実施すること。二重に変わらないよう順序どおりに実施する。

6. **eo-aws-cfnstack.yml を re-aws-cfnstack.yml にリネーム**
   - `eo`があるままだと、ファイル名まで変更しないといけないので、EoTenantはリネームしておく。

7. **eo-re-d1-lambda-python-slim-layer を tnp-re-d1-lambda-python-slim-layer にリネーム**
- `RequestEngine\aws\lambda\py\CFn\re-aws-cfnstack.yml`にて。

8. **各種.bicep を プレフィックス無しにリネーム**
   - `EO_Documents\Manuals\SchemaDesign_DbNormalization.md`にて。
     - RequestEngine\azure\functions\py\bicep\eo-re-d1-azure-funcapp.bicep　を RequestEngine\azure\functions\py\bicep\az-funcapp.bicepにリネーム
     - RequestEngine\azure\functions\py\bicep\eo-re-d1-az-child-mgmt-grp.bicep　を RequestEngine\azure\functions\py\bicep\az-child-mgmt-grp.bicepにリネーム
     - RequestEngine\azure\functions\py\bicep\eo-re-d1-az-child-mgmt-grp-policies.bicep　を RequestEngine\azure\functions\py\bicep\az-child-mgmt-grp-policies.bicepにリネーム

9. **eo- を tnp- にリネーム**
- `EO_Documents\Manuals\RE_README.md`にて。

10. EO_Documents\Manuals\SchemaDesign_DbNormalization.md の 2.3 クラウド4種の実際の .env 定義を修正
- 変わってきているので、修正する。

## 手順 1a: Lambda リソース名パターンを `{EoProject}-{EoEnvironment}-{EoAreaShort}-{EoServiceServerless}` に変更

**対象:** リクエストエンジンの AWS Lambda のみ（他クラウドは既存方針どおり）。

1. **CFn（re-aws-cfnstack.yml）のリソース名パターン**
   - `LambdaFunction` の `FunctionName` を  
     旧: `${EoTenant}-${EoProject}-${EoEnvironment}-${EoServiceServerless}-${EoAreaShort}`  
     新: `${EoProject}-${EoEnvironment}-${EoAreaShort}-${EoServiceServerless}`  
     となるように修正する。
   - `LambdaLogGroup` の `LogGroupName` / `Tags.Name` も同じ順番に揃える。
   - IAM Role / Policy / User 名（`-role` / `-basic-exec-iamp` / `-role-iamp` / `-iamu` / `-access-key-iamp` / `-ghactions-deploy-iamr` / `-ghactions-deploy-iamr-iamp`）など、Lambda 関連で `{...}-lambda-{EoAreaShort}` になっている箇所を `{...}-{EoAreaShort}-lambda` に変更する。
   - コメントの例示（Layer ARN など）で Lambda 関連名を記載している場合も、`{EoAreaShort}-{EoServiceServerless}` の順になるよう更新する。

2. **ワークフロー（deploy-py-to-aws-lambda.yml）の `function-name`**
   - `aws-lambda-deploy` ステップの `function-name` を  
     旧: `${{ env.EoTenant }}-${{ env.EoProject }}-${{ env.EoEnvironment }}-${{ env.EoServiceServerless }}-${{ env.EoAreaShort }}`  
     新: `${{ env.EoProject }}-${{ env.EoEnvironment }}-${{ env.EoAreaShort }}-${{ env.EoServiceServerless }}`  
     に変更する。
   - コメントの「Resource name pattern」も `{EoProject}-{EoEnvironment}-{EoAreaShort}-{EoServiceServerless}` に合わせておく。

3. **ドキュメントの命名例**
   - LAMBDA_CFN_README / NODE180_REQUESTENGINE_README / RE_README / SchemaDesign_DbNormalization で、Lambda 関数名パターンや具体例を説明している箇所は、  
     `{プロジェクト}-{環境}-{エリア}-{サービス種別}` の順になるよう表・本文を更新する。
   - 他クラウド（Azure Functions / Cloud Run / CF Workers）はそれぞれの MCNE 設計に従う。ここでは Lambda のみ、MCNE のセグメント順（tenant → project → environment → area → service_type）に合わせることが目的。

## 手順 2: GitHub Actions ワークフロー

**対象ファイル:** `.github/workflows/deploy-py-to-aws-lambda.yml`

1. コメントのパターン表記を新命名に合わせる。
   - 例: `# Resource name pattern: re-d1-apne1-lambda` → `# Resource name pattern: {EoProject}-{EoEnvironment}-{EoAreaShort}-{EoServiceServerless}` など。

2. 環境変数を新命名に合わせ、マルチクラウド共通項目のみ Github Actions Secret化する。
   - `EoProject` マルチクラウド共通項目
   - `EoEnvironment` マルチクラウド共通項目
   - `EoAreaShort` マルチクラウド共通項目
   - `EoArea` マルチクラウド共通項目
   - `EoServiceServerless`
   - `EoReRuntimeVer`

3. `instances_conf` への参照コメントはそのままで可。`.env` の変数名（EO_REGION_SHORT 等）は現状のまま（instances_conf は別手順で MCNE に寄せる場合に変更）。

## 手順 3: LAMBDA_CFN_README.md

**対象ファイル:** `EO_Documents/Manuals/py/LAMBDA_CFN_README.md`

1. **パラメータ一覧表（§ パラメータ一覧）**
   - | EoProject | `eo` | プロジェクトプレフィックス | → | EoTenant | `tnp` | テナントプレフィックス(廃止) |
   - | EoComponent | `re` | コンポーネント識別子（Request Engine） | → | EoProject | `re` | プロジェクト識別子（Request Engine） |
   - | EoEnv | `d1` | 環境識別子（dev01 等） | → | EoEnvironment | `d1` | 環境識別子（dev01 等） |
   - | EoRegionShort | `apne1` | リージョン短縮名 | → | EoAreaShort | `apne1` | エリア短縮名 |

2. **手順中のパラメータ名**
   - `ParameterKey=EoProject` 等の例を `ParameterKey=EoProject`, `ParameterKey=EoEnvironment`, `ParameterKey=EoAreaShort` に変更。
   - `EoReLambdaLayerName` はどうするか要確認。

3. **注意・トラブルシューティング**
   - 「EoEnv パラメータを変更」→「EoEnvironment パラメータを変更」に読み替え。

4. **リソース名の具体例（tnp-re-d1-lambda-apne1 等）**
   - 変更しない。説明で「EoTenant-EoProject-EoEnvironment-EoServiceServerless-EoAreaShort の並び」と補足する場合は可。

5. **参照ドキュメント**
   - [pyIaC_MCNE_Naming.md](./pyIaC_MCNE_Naming.md) および [SchemaDesign_DbNormalization.md](../SchemaDesign_DbNormalization.md) への参照を明記しておく。

## 手順 4: LAMBDA_README.md

**対象ファイル:** `EO_Documents/Manuals/py/LAMBDA_README.md`

1. リソース名の**具体例**（`tnp-re-d1-lambda-apne1` 等）は**eoからtnpに変更**。
2. CFn パラメータ名に言及している箇所があれば、EoTenant / EoProject / EoEnvironment / EoAreaShort / EoServiceServerless / EoServiceSecret に合わせて文言を修正。
3. 「命名は LAMBDA_CFN_README および pyIaC_MCNE_Naming に準拠」のような一文を追加してもよい。

## 手順 5: instances_conf（.env）

**対象ファイル:**
- `RequestEngine/aws/lambda/py/instances_conf/lambda001.env`
- `RequestEngine/aws/lambda/py/instances_conf/env.example`

1. **現状のキー名は維持**
   - `EO_RE_INSTANCE_TYPE`, `EO_RE_INSTANCE_ID`, `EO_REGION`, `EO_REGION_SHORT` は SchemaDesign_DbNormalization およびワークフローから参照されているため、**この手順では変更しない**。
2. コメントで「CFn のパラメータ（EoTenant, EoProject, EoEnvironment, EoAreaShort, EoServiceServerless）と組み合わせてリソース名が決まる」旨を追記する程度にとどめるか、追記しなくてもよい。

## 手順 6: その他参照箇所の確認・修正

1. **EO_Documents/Manuals/n8n/NODE180_REQUESTENGINE_README.md**
   - Lambda 関数名の例（`tnp-re-d1-lambda-apne1`, `tnp-re-d1-lambda-apse1`）は**eoからtnpに変更**。パラメータ名の説明があれば EoTenant / EoProject 等に合わせる。

2. **EO_Documents/Manuals/RE_README.md**
   - 関数名 `tnp-re-d1-lambda-apne1` は**eoからtnpに変更**。CFn パラメータ名の記載があれば新名に修正。

3. **EO_Documents/Manuals/SchemaDesign_DbNormalization.md**
   - §5.2 AWS リソースの表で「ProjectPrefix / Component / Environment / RegionShort」等の表現を、「EoTenant / EoProject / EoEnvironment / EoAreaShort に対応」と注記するか、表の列見出しを新命名に合わせて更新する。このファイルは全リクエストエンジンの作業後に一括で変更する。

4. **CLAUDE.md**
   - Lambda 関連の Docs 記載に LAMBDA_CFN_README や pyIaC_MCNE_Naming を並べている場合は、そのままで可。

## 手順 7: 変更後の確認チェックリスト

以下を実施後、**eo / eo-aws-cfnstack / 旧パラメータ名の残り**がないかまとめて確認する。

**CFn・ワークフロー**
- [ ] `re-aws-cfnstack.yml` で `EoProject` / `EoComponent` / `EoEnv` / `EoRegionShort` / `EoServerlessService` / `EoSecretService` が存在しない（すべて EoTenant / EoProject / EoEnvironment / EoAreaShort / EoServiceServerless / EoServiceSecret に置換されている）
- [ ] 同じ YAML 内で EoReLambdaLayerSuffix / EoReLambdaLayerVer はそのまま。EoRegion → EoArea、EoRePythonRuntimeVer → EoReRuntimeVer 等は手順どおり変更済み
- [ ] `.github/workflows/deploy-py-to-aws-lambda.yml` の `LAMBDA_FUNCTION_NAME` がテナント名付きの想定値になっている（リソース名を変える場合は別手順）
- [ ] `re-aws-cfnstack.yml` 先頭コメントの Layer ARN 例が、使用するテナント名（または <テナント名> の説明）に合っている

**README・ドキュメント**
- [ ] LAMBDA_CFN_README.md: パラメータ一覧・手順・コマンド例が新パラメータ名になっている。リソース名例は eo → テナント名（または <テナント名> 表記）に揃え、EoReLambdaLayerName は CFn に合わせ EoReLambdaLayerSuffix / EoReLambdaLayerVer に修正。「EoEnv パラメータ」→「EoEnvironment パラメータ」
- [ ] LAMBDA_README.md: パラメータ名の言及を新名に。リソース名例をテナント名（または <テナント名>）に。ワークフロー名は `deploy-py-to-aws-lambda.yml`
- [ ] NODE180_REQUESTENGINE_README.md / RE_README.md: 関数名例がテナント名付き（または <テナント名> 表記）になっている
- [ ] SchemaDesign_DbNormalization.md: 全 RE 一括変更時は `eo-aws-cfnstack.yml` → `re-aws-cfnstack.yml`、リソース名例をテナント名またはプレースホルダに

**運用・スタック**
- [ ] 既存スタックがある場合: パラメータ名変更は **スタックの更新では互換性がなくなる** ため、新スタック作成またはインポートで対応する必要があることを README に注意書きした

## 補足: リソース名（tnp-re-d1-lambda-apne1）を変える場合

MCNE の EoNanoidSlug を導入し、Lambda 関数名を `{EoTenant}-{EoProject}-{EoEnvironment}-{EoServiceServerless}-{EoAreaShort}-{EoNanoidSlug}` にする場合は、本手順とは別に以下が必要である。

- CFn に EoNanoidSlug パラメータを追加し、`FunctionName` 等の `!Sub` に組み込む。
- Github workflowの `LAMBDA_FUNCTION_NAME` を新パターンに変更。
- 既存 Lambda は名前変更不可のため「新名で新規作成 → 切り替え → 旧削除」の移行手順を別途用意する。

本手順では**パラメータ名の PascalCase 統一とドキュメント・ワークフローコメントの更新**までとする。

## 影響ファイル一覧

| ファイル | 変更内容 |
|----------|----------|
| `RequestEngine/aws/lambda/py/CFn/re-aws-cfnstack.yml` | パラメータ名 6 個のリネーム、全参照・Metadata・Tags の Key を新名に統一 |
| `.github/workflows/deploy-py-to-aws-lambda.yml` | コメントのパターン表記を新命名に合わせる（env の値はそのまま） |
| `EO_Documents/Manuals/py/LAMBDA_CFN_README.md` | パラメータ一覧・手順・コマンド例・注意文のパラメータ名を新名に |
| `EO_Documents/Manuals/py/LAMBDA_README.md` | CFn パラメータ名の言及があれば新名に。リソース名例は変更しない |
| `RequestEngine/aws/lambda/py/instances_conf/lambda001.env` | 変更不要（必要ならコメントのみ） |
| `RequestEngine/aws/lambda/py/instances_conf/env.example` | 同上 |
| `EO_Documents/Manuals/n8n/NODE180_REQUESTENGINE_README.md` | パラメータ名の説明があれば新名に。関数名例はそのまま |
| `EO_Documents/Manuals/RE_README.md` | パラメータ名の記載があれば新名に。関数名はそのまま |
| `EO_Documents/Manuals/SchemaDesign_DbNormalization.md` | §5.2 の表・注記を EoTenant/EoProject/EoEnvironment/EoAreaShort に対応させてよい |
