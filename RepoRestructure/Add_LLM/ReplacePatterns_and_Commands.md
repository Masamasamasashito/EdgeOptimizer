# 手順 1（Cursor）: 置換パターン洗い出し・置換コマンド作成・漏れチェック（再版）

`RepoRestructure/Add_LLM/Plan.md` の「命名規則」「ディレクトリ案」「作業の手分け」に対応する。

- **命名**: Web 系ディレクトリは **`Web/`**（先頭大文字）。LLM 系は **`llm/local/`** と **`llm/cloud/`**（`Plan.md` ツリーどおり）。
- **GitHub Actions のファイル名**: `Plan.md` のツリーでは **`deploy-py-to-aws-lambda-web.yml`** のように **`-web` は小文字**（`.yml`）。`Plan.md` の「関連ディレクトリ」に **`-Web`** とある場合は**表記揺れ**であり、実ファイル名は **小文字 `-web.yml`** で統一する想定。

- **手順 1（本ファイル）**: パターン洗い出し・**置換コマンド作成**（下記 PowerShell。手順 3 はこれを実行）・漏れチェック。**手順 1 ではファイルのリネームや置換を実行しない。**
- **手順 2（人間）**: `.github/workflows` の yml **ファイル名**リネーム、**`Web/`** および **`llm/local/`**・**`llm/cloud/`** の作成・既存移動、`Archives` 移動。
- **手順 3（人間）**: 本ファイルの**置換コマンド**を実行し、結果を確認する。
- **手順 4（Cursor）**: 手順 3 の diff レビュー。

## A. GitHub Actions ファイル名（`-web.yml`）と参照の洗い出し

### A.1 リネーム対応表（手順 2 で人間が `git mv`）

| 現ファイル名 | リネーム後 |
|--------------|------------|
| `deploy-py-to-aws-lambda.yml` | `deploy-py-to-aws-lambda-web.yml` |
| `deploy-py-to-az-function.yml` | `deploy-py-to-az-function-web.yml` |
| `deploy-py-to-gcp-cloudrun.yml` | `deploy-py-to-gcp-cloudrun-web.yml` |
| `deploy-ts-to-cf-worker.yml` | `deploy-ts-to-cf-worker-web.yml` |

**ワークフロー内のコメント**で旧ファイル名を自己参照している箇所は、**手順 3** の **A.4 スクリプト**で文字列を更新する。

### A.2 旧ファイル名を含む参照一覧（手順 3 の置換対象ファイルの目安）

**`deploy-py-to-aws-lambda.yml`**: `CLAUDE.md`, `EO_Documents/Manuals/py/LAMBDA_CFN_README.md`, `EO_Documents/Manuals/py/LAMBDA_README.md`, `EO_Documents/Manuals/py/old/LAMBDA_CFN_MCNE_Naming_Procedure.md`, `EO_Documents/Manuals/SchemaDesign_DbNormalization.md`, `RequestEngine/aws/lambda/py/instances_conf/env.example`, `RequestEngine/aws/lambda/py/instances_conf/lambda001.env`

**`deploy-py-to-az-function.yml`**: `CLAUDE.md`, `EO_Documents/Manuals/SchemaDesign_DbNormalization.md`, `EO_Documents/Manuals/py/AZFUNC_README.md`, `RequestEngine/azure/functions/py/instances_conf/env.example`, `RequestEngine/azure/functions/py/instances_conf/funcapp001.env`

**`deploy-py-to-gcp-cloudrun.yml`**: `CLAUDE.md`, `EO_Documents/Manuals/py/CloudRun_README.md`, `EO_Documents/Manuals/SchemaDesign_DbNormalization.md`, `RequestEngine/gcp/cloudrun/py/terraform/cloud_run.tf`, `RequestEngine/gcp/cloudrun/py/instances_conf/env.example`, `RequestEngine/gcp/cloudrun/py/instances_conf/cloudrun001.env`

**`deploy-ts-to-cf-worker.yml`**: `CLAUDE.md`, `EO_Documents/Manuals/ts/CFWORKER_README.md`, `EO_Documents/Manuals/ts/CFWorker_Overview_README.md`, `EO_Documents/Manuals/SchemaDesign_DbNormalization.md`, `RequestEngine/cf/workers/ts/instances_conf/env.example`, `RequestEngine/cf/workers/ts/instances_conf/cfworker001.env`, `RequestEngine/funcfiles/common/ts/request_engine_core.ts`, **リネーム後の** `.github/workflows/deploy-ts-to-cf-worker-web.yml` 本体

### A.3 プレビュー用（検索のみ）

```powershell
Set-Location "c:\Users\nishi\Documents\Docker\work\EdgeOptimizer"
rg -n "deploy-py-to-aws-lambda\.yml|deploy-py-to-az-function\.yml|deploy-py-to-gcp-cloudrun\.yml|deploy-ts-to-cf-worker\.yml" --glob "!**/.git/**"
```

### A.4 置換コマンド作成（ワークフロー名 4 本・手順 3 で実行）

**前提**: 手順 2 で **yml ファイルを `git mv` 済み**。ドキュメント・コメント内の**文字列だけ**が旧名のまま残っている状態で実行する。

**リポジトリルートで実行**。まず **DryRun** で変更予定ファイルを表示し、問題なければ **`$DryRun = $false`** にして再実行。

```powershell
Set-Location "c:\Users\nishi\Documents\Docker\work\EdgeOptimizer"
$DryRun = $true

$pairs = @(
  @{ Old = "deploy-py-to-aws-lambda.yml"; New = "deploy-py-to-aws-lambda-web.yml" }
  @{ Old = "deploy-py-to-az-function.yml"; New = "deploy-py-to-az-function-web.yml" }
  @{ Old = "deploy-py-to-gcp-cloudrun.yml"; New = "deploy-py-to-gcp-cloudrun-web.yml" }
  @{ Old = "deploy-ts-to-cf-worker.yml"; New = "deploy-ts-to-cf-worker-web.yml" }
)

$files = Get-ChildItem -Path . -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' -and $_.FullName -notmatch '[\\/]node_modules[\\/]' } |
  Where-Object { $_.Extension -in @(".md", ".yml", ".yaml", ".tf", ".env", ".example", ".ts", ".py", ".toml") -or $_.Name -in @("env.example", "lambda001.env", "funcapp001.env", "cloudrun001.env", "cfworker001.env") }

foreach ($f in $files) {
  $raw = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
  if ($null -eq $raw) { continue }
  $new = $raw
  foreach ($p in $pairs) {
    $new = $new.Replace($p.Old, $p.New)
  }
  if ($new -ne $raw) {
    if ($DryRun) {
      Write-Host "[DRYRUN] WOULD UPDATE: $($f.FullName)"
    } else {
      Set-Content -LiteralPath $f.FullName -Value $new -Encoding UTF8 -NoNewline
      Write-Host "UPDATED: $($f.FullName)"
    }
  }
}
```

**注意**: `Set-Content -NoNewline` は環境によって末尾改行が変わる可能性がある。**差分は必ず `git diff` で確認**。**バイナリや巨大ファイル**は上記 `$files` から除外されているが、`EO_n8nWorkflow_Json` を触る場合は **UI 文言の方針**（勝手に変えない）を別途確認すること。

## B. `RequestEngine/` → `RequestEngine/Web/`（パス正規化）

`Plan.md` のツリーでは **`RequestEngine/Web/`**（`Web` は先頭大文字）。置換後の文字列もこれに合わせる。

### B.1 前提

- **`RequestEngine/aws` 等を `git mv` で `RequestEngine/Web/aws` へ移した後**に、リポジトリ内の**テキスト**を置換する。
- **`RequestEngine/llm` や `RequestEngine/LLM` が存在する**と、単純な前置換は誤爆しうる。下は **サブパス固定**の置換のみ。

### B.2 置換が必要になりうる場所（カテゴリ）

| 優先度 | 種別 | 内容 |
|--------|------|------|
| 高 | workflows | `SRC_DIR` / `COMMON_DIR` / `EXT_DIR` / `working-directory` |
| 高 | Dependabot | `.github/dependabot.yml` の `directory:` |
| 中 | ルートドキュメント | `README.md`, `CLAUDE.md`, `AppRequirements.md`, `QUICK_START.md` |
| 中 | EO_Documents | `Manuals/**/*.md` 等 |
| 低 | コメント | `RequestEngine/funcfiles/common/**/*.{py,ts}` |

### B.3 サブパス単位の対応（文字列）

```
RequestEngine/funcfiles/   → RequestEngine/Web/funcfiles/
RequestEngine/aws/         → RequestEngine/Web/aws/
RequestEngine/azure/       → RequestEngine/Web/azure/
RequestEngine/gcp/         → RequestEngine/Web/gcp/
RequestEngine/cf/          → RequestEngine/Web/cf/
```

`RequestEngine\` を使うパスも同様に **バックスラッシュ版**の置換を別ループで行う（`...\Web\...`）。

### B.4 置換コマンド作成（RequestEngine パス・手順 3 で実行）

**前提**: 手順 2 で **ディレクトリの `git mv` 済み**。テキストだけ旧パス。

**DryRun → 本実行**の流れは `A.4` と同様。`$DryRun = $true` のままファイル一覧を確認後、`$false` に。

```powershell
Set-Location "c:\Users\nishi\Documents\Docker\work\EdgeOptimizer"
$DryRun = $true

$pairsSlash = @(
  @{ Old = "RequestEngine/funcfiles/"; New = "RequestEngine/Web/funcfiles/" }
  @{ Old = "RequestEngine/aws/"; New = "RequestEngine/Web/aws/" }
  @{ Old = "RequestEngine/azure/"; New = "RequestEngine/Web/azure/" }
  @{ Old = "RequestEngine/gcp/"; New = "RequestEngine/Web/gcp/" }
  @{ Old = "RequestEngine/cf/"; New = "RequestEngine/Web/cf/" }
)
$pairsBackslash = @(
  @{ Old = "RequestEngine\funcfiles\"; New = "RequestEngine\Web\funcfiles\" }
  @{ Old = "RequestEngine\aws\"; New = "RequestEngine\Web\aws\" }
  @{ Old = "RequestEngine\azure\"; New = "RequestEngine\Web\azure\" }
  @{ Old = "RequestEngine\gcp\"; New = "RequestEngine\Web\gcp\" }
  @{ Old = "RequestEngine\cf\"; New = "RequestEngine\Web\cf\" }
)

$files = Get-ChildItem -Path . -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' -and $_.FullName -notmatch '[\\/]node_modules[\\/]' }

foreach ($f in $files) {
  $raw = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
  if ($null -eq $raw) { continue }
  $new = $raw
  foreach ($p in $pairsSlash) { $new = $new.Replace($p.Old, $p.New) }
  foreach ($p in $pairsBackslash) { $new = $new.Replace($p.Old, $p.New) }
  if ($new -ne $raw) {
    if ($DryRun) {
      Write-Host "[DRYRUN] WOULD UPDATE: $($f.FullName)"
    } else {
      Set-Content -LiteralPath $f.FullName -Value $new -Encoding UTF8 -NoNewline
      Write-Host "UPDATED: $($f.FullName)"
    }
  }
}
```

**注意**: `dependabot.yml` の先頭スラッシュ付きパスは、上記で **`/RequestEngine/aws` → `/RequestEngine/Web/aws`** のように **先頭に `Web` が入る**。**マッピングは長い順**（`funcfiles` を先）。**`RequestEngine/llm` や LLM 用ツリー**ができたあとで誤置換がないか **手順 4 で再確認**すること。

## C. Plan.md ツリーで「移動が主」なもの（本ファイルの A.4 / B.4 の外）

次は **手順 2（人間）**でディレクトリ作成・`git mv` が主。**一括テキスト置換スクリプトでは代替できない**（移動後に `README` や相互リンクを個別に直す想定）。

| 対象 | `Plan.md` 上の行き先（例） |
|------|---------------------------|
| `EO_Terraform_Docker/` | `Archives/` 配下 |
| `MCNE_Documents/` | `Archives/` 配下 |
| `EA_Documents/` 直下のファイル | `EA_Documents/Web/` 等へ段階移行 |
| `EO_n8nWorkflow_Json/` | `EO_n8nWorkflow_Json/Web/`（例: `eo-n8n-workflow-jp.json`） |
| `EO_Documents/Manuals/` | `EO_Documents/Manuals/Web/` および将来 `llm/local` / `llm/cloud` |
| `EO_Architecture/` | `EO_Architecture/Web/` 等 |
| `RequestEngine/` | `RequestEngine/Web/` 以下へ正規化後、`llm/local`・`llm/cloud` は開発開始時に追加 |

**新規用途のワークフロー JSON** の置き場所は `Plan.md` の「置かないもの」:**`EO_n8nWorkflow_Json/llm/local/` または `llm/cloud/`**。

## D. 手順 1 の漏れチェックリスト（統合）

- [ ] ワークフロー名: **A.2** 一覧と `rg` で旧名が残っていないか（**小文字 `-web.yml`**）
- [ ] ワークフロー **YAML 本体**内のコメント・`Auto-generated by` 行
- [ ] `RequestEngine/llm` や `RequestEngine/LLM` を誤って `RequestEngine/Web/llm` にしていないか
- [ ] `EO_RequestEngine` のような表記の残り
- [ ] `dependabot.yml` の `directory:` が実ディレクトリと一致しているか
- [ ] n8n・手順書の **ボタン名・ノードラベル**を勝手に変えていないか
- [ ] ディレクトリ名 **`Web/`**（大文字）と **ワークフロー `-web.yml`**（小文字）の混同がないか

## E. 手順 3 向け・作業順の推奨

1. 手順 2: ワークフロー **4 ファイル**を `git mv` で **`*-web.yml`** へ。
2. 手順 3: **A.4** を実行（DryRun → 本実行）→ `git diff`。
3. 手順 2: `RequestEngine` を **`RequestEngine/Web`** 配下へ物理移動（`Plan.md` ツリーどおり）。
4. 手順 3: **B.4** を実行（DryRun → 本実行）→ `git diff`。
5. 手順 2（継続）: **`Web/`**・**`llm/local/`**・**`llm/cloud/`** の追加と、`Archives` 等の移動（**セクション C**）。
6. 手順 4: Cursor でレビュー。

## F. 旧版メモ

初版の「参照した検索の要点」は **A・B** に統合した。以後は `rg` で再スキャンし、本ファイルの **A.2** を更新する。
