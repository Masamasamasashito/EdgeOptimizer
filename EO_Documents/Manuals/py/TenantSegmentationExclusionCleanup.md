# IaC対象AWS,Azure,GCPのテナントセグメント除外と整理

# 前提

**マルチクラウド・マルチリージョン・マルチテナント・・サーバレス・B to B・Saasの場合、以下の制約から全部1本のリソース命名でやろうとすると構造的に矛盾する。**

- ハイフォン不可（Azure Storageなど）
- 先頭英字必須
- 24文字制限（Azure Storageなど）
- グローバル一意必須（Azure Storageなど）
- 15文字制限（Windowsホスト名）

**文字長が短いという制約により、リソース名1本で以下の課題を「全解決する」のが物理的に無理。全部1本の名前でやろうとするのが構造的に矛盾。**

- 命名セグメントの抽象化
- 可読性
- 一意性
- 変更耐性
- 全クラウド互換

## 発覚した事実

- 意味を持つ物理セグメント組み合わせ命名 → 構造的に苦しいが、ほどほどの可読性は確保できる
- 無機質な物理命名 → 構造問題は解消するが、可読性は皆無

## 事実から見えてきた無難なセグメント境界

1. **MMM**マルチクラウド・マルチリージョン・マルチテナント・B to B・Saas（MMM）
  - リソース名の環境変数セグメントは一意の世界グローバルユニークIDのみ(もしくはprefix(+resource)くらいの識別子+一意の世界グローバルユニークID)
  - タグラベルで以下の環境変数セグメントを管理
    - テナント
    - プロジェクト
    - 環境
    - エリア
    - サービス
    - リソース
    - 世界グローバル一意(Azure StorageやAzure Key Vault のような世界共通一意リソースの場合)
    - オーナー/オーナーグループ
2. **MMS**マルチクラウド・マルチリージョン・シングルテナント（1社内利用）・サーバレス
  - リソース名で以下の環境変数セグメントを管理
    - プロジェクト
    - 環境
    - エリア
    - サービス(リソース)
    - 世界グローバル一意(Azure StorageやAzure Key Vault のような場合)
  - タグラベルで以下の環境変数セグメントを管理
    - オーナー/オーナーグループ
  - 拡張性確保：命名生成ロジック共通化

※2.のMMSではテナント環境変数セグメントが無いことに注目。環境変数セグメントが1つ増えるだけで命名の文字長が危機的になるため。

以下、環境変数セグメント=セグメント とする。

## 1. 現状

- **追記のみでMMMに寄せる:** 考え方が根本的に間違っている。シングルテナントからマルチテナントへの追記だけによる対応は不可能。大幅なリソース命名セグメントの設計変更が必要
- **設計を寄せる:** MMSをMMMに寄せるには、セグメントをタグラベルに移管し、なおかつテナントセグメントをタグラベルに追加、リソース名は世界グローバルユニークIDを主体としたパターン式に変更する必要がある。
- **名前の付け替え:** 
  - AWS
    - MMSからMMMへの柔軟性があると思い込んだまま、MMM寄せ試行錯誤してしまった残骸あり。テナントも組み込んでしまっている。
    -作業は主に`EO_Documents\Manuals\py\old`中のファイルに書かれている。
  - Azure
    - MMSからMMMへの柔軟性があると思い込んだまま、MMM寄せ試行錯誤してしまった残骸あり。
    -作業は主に`EO_Documents\Manuals\py\old`中のファイルに書かれている。
  - GCP
    - MMSのまま。殆どいじってない。

## 2. リソース命名セグメント方針

1. RequestEngine関連は、リソース名のセグメントをMMSですべて統一。
2. 各クラウドのIaCもMMSですべて統一。テナントセグメントは完全排除。必要ならテナントは EoProject 側で吸収する。
3. MMMとMMSで互換性を考慮する設計を辞める。
4. MCNEに寄せるというよりもセグメントの不変化を目指し、セグメント内の文字数リバランスの自由度を確保する。
5. RequestEngine全体でリソース命名セグメントの記法はPascalCaseに統一。
6. リソース命名セグメントの接頭辞は、スコープ別でEo(Edge Optimizer)もしくはEoRe(Edge Optimizer の RequestEngine)に統一。
7. CFnにおけるEoTenantは削除。
8. EoTenant、EoProject、EoComponentの整理整頓は、順序が複雑だったがシンプルに考える。
  1. EoProjectはそのまま。EoProjectのValue例は`re`とする(マルチクラウドはRequestEngineが使う為。eoだとn8nが含まれてしまう)。現在は `eo`、`nis`、`tnp`などが考えられる。
  2. EoComponentは廃止。用途/役割向けでEoComponentを作ると、セグメントが増えて文字長が危機的になるため。
9. EoResourceではなく、EoServiceに命名変更。クラウド側のサービスやリソースを表現する。
10. AWS,Azure,GCPでTerraform統一に向けて、個別クラウドの独自セグメントは最小限に抑える。
11. `.yml(CFn)`、`.yml(docker)`、`.yml(github actions)`、`.bicep` や `.tf`などのファイル名はを動的に変更するコストを抑えるため、動的なセグメントをファイル名に含むことを禁止する。
12. RequestEngine全体の`各種IaCのREADME.ｍd`、`.yml(CFn)`、`.yml(docker)`、`.yml(github actions)`、`.bicep` や `.tf`のファイルで、共通セグメントをPascalCaseで使用する。
13. セグメントを組み合わせたリソース名の文字長の制約は、Azure Storageの24文字以内、ハイフォン無し、バッファ3文字で、21文字以内を基準とする。
14. Nano ID採用できない場合に限り、ソルトによるハッシュ化を採用する。
15. 基本セグメント順 : EoProject → EoEnvironment → EoAreaShort → EoService → EoNanoid/EoSaltHash
16. EoCloudは、EoAreaで確定するため不採用。
17. EoService と EoAreaShort の順序について、EoAreaShort → EoService の順序を採用する。改善作業の影響範囲が広いため、影響範囲の計画をしてから変更する。
18. リソース名の主要なセグメントは以下の通り。

| 改善前CFn | 改善前Bicep | 改善前GCP Terraform | 改善後共通リソース命名セグメントPascalCase(CFn,Bicep,Terraform) | 備考 |
|------------------|-----------------|----------------------|------------------|------------------|
| EoTenant | 無し | 無し | 廃止 | テナントはEoProject側で吸収する。 |
| EoProject | EO_PROJECT | project_prefix | EoProject | - |
| EoComponent | EO_COMPONENT | component | EoComponent | 廃止 |
| EoEnv | environment_slug | environment | EoEnvironment |
| EoRegion | region_slug | region | EoArea | 各クラウドを横断して扱うためAreaとした |
| EoRegionShort | area_short_slug | region_short | EoAreaShort | 文字数の変動を許容するか、要検討 |
| EoGlobalPrjEnvId | — | — | EoNanoId or EoSaltHash | EoNanoId |
| EoServerlessService（CFn）等 | service_type_slug | service_type | EoServiceServerless（値例: lambda, fnc） |
| EoSecretService（CFn）等 | service_type_slug | service_type | EoServiceSecret（値例: secretsmng, kv） |
| EoServiceStorage（CFn）等 | service_type_slug | service_type | EoServiceStorage（値例: st） |
| EoLambdaRequestSecretName | request_secret_name | request_secret_name | EoRequestSecretName（値例: LAMBDA_REQUEST_SECRET） |
|EoRePythonRuntimeVer | python_runtime_version | python_runtime_version | EoReRuntimeVer（値例: python3.14） |
|EoReLambdaTimeout | lambda_timeout | lambda_timeout | EoReTimeout（値例: 30） |
|EoReLambdaMemorySize | lambda_memory_size | lambda_memory_size | EoReMemorySize（値例: 128） |
| EoReInstanceId | issued_resource_name_nanoid_slug | issued_resource_name_nanoid | 廃止。採番管理しない世界グローバルユニークIDのNanoIdに依存する |

- .envファイルが有るため、envという単語を避けてEoEnvではなくEoEnvironmentにした。
- オーナー/オーナーグループはタグラベルで管理

**サービスの 1 パラメータ（EoService）統合する/しない検討** 同一 CFn スタックで Lambda 名（lambda）と Secrets Manager 名（secretsmng）の両方が必要になるため、1 パラメータでは両方の値を表現できず矛盾する。このため **EoServiceServerless / EoServiceSecret / EoServiceStorage** の分割などを検討する。

## 2. 改善前と改善後でロジックが異なるセグメント

おそらく無いが、出てきた場合のためにフォーマットだけ置いておく。

| 項目 | 現況（CFn/Bicep/Terraform） | MCNE に寄せる場合 |
|------|-----------------------------|-------------------|


## 3. hyphen_allowed 2 グループ (Azure Storageの場合)

| グループ | リソース | パターン | 例 |
|----------|----------|----------|-----|
| hyphen_allowed : false | Storage | `{EoProject}{EoEnvironment}{EoArea}{EoService***}{EoNanoidSlug}` | `eored1an06st5g4h7b` |
| hyphen_allowed : true | Key Vault | `{EoProject}-{EoEnvironment}-{EoArea}-{EoService***}-{EoNanoidSlug}` | `eo-re-d1-an06-kv-5g4h7b` |
| hyphen_allowed : true | Function App 等 | `{EoProject}-{EoEnvironment}-{EoArea}-{EoService***}-{EoNanoidSlug}` | `eo-re-d1-an06-fnc-5g4h7b` |

Key Vault は Azure 上ハイフン可だが、MCNE の安全サブセットに合わせて hyphen_allowed : false で統一する。

## 4. 移行・実装の要点

- **注意:** (1) EoTenant / EoProject の 2 本をセットで変更 (2) ワークフロー・`./AZFUNC_BICEP_README.md`・`../SchemaDesign_DbNormalization.md`・他 IaC の参照を一括更新 (3) 既存環境がある場合は移行手順を用意。
- **チェックリスト:** Bicep のパラメータ・変数式を新セグメント対応に変更 → リソース名を §5 のパターンに変更 → ワークフロー・`./AZFUNC_BICEP_README.md`・`../SchemaDesign_DbNormalization.md` を更新。

## 5. README に追記するだけの場合（設計は変えない）

設計を変えず拡張性だけ確保する場合、AZFUNC_BICEP_README の「リソース名パターン」付近に次の 1 ブロックを追記する。

> 本手順のリソース名は [SchemaDesign_DbNormalization.md](../SchemaDesign_DbNormalization.md) に準拠しています。マルチクラウド命名の一元化方針は [MCNE_Documents/README.md](../../../MCNE_Documents/README.md) を参照してください。将来 MCNE を導入する場合は、MCNE が発行するリソース名を Bicep のパラメータに渡して利用する想定です。現行の EO_PROJECT / EO_REGION_SHORT / EO_GLOBAL_PRJ_ENV_ID / EO_RE_INSTANCE_ID は、MCNE の tenant_slug・project_slug / area_short_slug / 一意部分（Nano ID）等に対応します。

実際に Bicep を MCNE に合わせる場合は、本ドキュメントの §2〜§6 に沿って修正する。
