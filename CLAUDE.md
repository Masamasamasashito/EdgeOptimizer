# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Edge Optimizer (EO) is a multi-cloud serverless infrastructure for cache warmup, performance measurement, data cleaning for ai training , and security validation. It uses n8n as the orchestration layer to dispatch requests to serverless functions across AWS Lambda, Azure Functions, GCP Cloud Run, and Cloudflare Workers.

## Architecture

```
n8n (Orchestration) → Request Engines (Serverless)
├── AWS Lambda (ap-northeast-1)      - Python 3.14
├── Azure Functions (Japan East)     - Python 3.13
├── GCP Cloud Run (asia-northeast1)  - Python (Flask)
└── Cloudflare Workers (global edge) - TypeScript
```

**Security Model**: 2-layer authentication
1. Platform authentication (IAM keys, Function App keys, OAuth2 tokens, CF Access tokens)
2. Token verification: `SHA-256(url + N8N_EO_REQUEST_SECRET)` validated in each Request Engine
3. DNS TXT records for domain ownership verification (where applicable)

## Development Commands

### Local Environment (Docker) for n8n

```bash
cd EO_Infra_Docker
cp env.example .env
# Generate secrets (see README.md for OS-specific commands)
docker compose up -d                    # Start services
docker compose --profile prod up -d     # Start with Caddy (production)
docker compose down                     # Stop services
docker compose logs -f n8n              # View n8n logs
```

Access n8n at http://localhost:5678

### Terraform (Infrastructure)

To Be Determined

```bash
cd EO_Terraform_Docker
docker compose run --rm terraform init
docker compose run --rm terraform plan
docker compose run --rm terraform apply
```

### Request Engine Deployment

Deployments are triggered via GitHub Actions (manual `workflow_dispatch`):
- `.github/workflows/deploy-to-aws-lambda-apne1.yml`
- `.github/workflows/deploy-to-az-function-jpeast.yml`
- `.github/workflows/deploy-to-gcp-cloudrun-ane1.yml`
- `.github/workflows/deploy-to-cf-worker-global.yml`

For Cloudflare Workers local development:
```bash
cd RequestEngine/cloudflare_workers/global/funcfiles
npm install
npx wrangler dev                        # Local dev server
npx wrangler secret put CFWORKER_REQUEST_SECRET  # Set secret
```

## Key Directories

- `EO_Infra_Docker/` - Docker Compose for local n8n, PostgreSQL, Redis, Playwright, SearXNG
- `RequestEngine/` - Serverless function implementations per platform
  - `*/funcfiles/` - Actual function code
- `terraform/` - Infrastructure as Code modules
- `EOn8nWorkflowJson/` - n8n workflow definitions for import
- `test/` - **OSS公開を避けるファイルの置き場。このディレクトリ内のファイルを他のディレクトリへ移動禁止。**

## Docs

- `RequestEngine\RE_README.md` - n8n Credentals and HTTP Request Node setup
    - `RequestEngine\aws_lambda\apne1\funcfiles\lambda_function.py.bak` - Documentation for the original monolithic structure is currently postponed
- `RequestEngine\aws_lambda\apne1\LAMBDA_README.md` - AWS Lambda specific setup
- `RequestEngine\azure_functions\jpeast\AZFUNC_README.md` - Azure Functions specific setup
- `RequestEngine\gcp_cloudrun\ane1\RUN_README.md` - GCP Cloud Run specific setup
- `RequestEngine\cloudflare_workers\global\CFWORKER_README.md` - Cloudflare Workers specific setup

### Refactoring Strategy: Common Parts Extraction

EX) AWS Lambda

- RequestEngine\aws_lambda\apne1\funcfiles\lambda_function.py
    - Before: Monolithic code with all logic in a single file
    - After: `RequestEngine\aws_lambda\apne1\funcfiles\_03_aws_lambda_handler.py` for AWS Lambda specific handler , Verify n8n secret and cloudsecret
    - After: `RequestEngine\aws_lambda\apne1\funcfiles\_01_imports.py` for imports
    - After: `RequestEngine\common\request_engine_core.py` for shared core logic
    - After: `RequestEngine\common\extensions` directory for shared utilities (`_ext_mesure.py`, `_ext_peformance.py`, `_ext_security.py`)
    - After: `RequestEngine\aws_lambda\apne1\funcfiles\lambda_function.py.bak` - Documentation for the original monolithic structure is currently postponed

## Request Engine Data Flow

n8n sends POST with:
```json
{
  "data": {
    "targetUrl": "...",
    "token": "SHA-256(url + secret)",
    "headers": {"User-Agent": "...", "Accept-Language": "..."},
    "httpRequestNumber": "...",
    "httpRequestUUID": "...",
    "httpRequestRoundID": "..."
  }
}
```

Request Engines return flat JSON with 3 namespaces: `headers.*` (general/request-headers/response-headers), `eo.meta.*`, `eo.security.*`, `error.*`

## Request Engine Design Principles

Request Engine は生データの取得と計測に専念する。導出・分析・分類は消費側（オーケストレーター等）の責務とする。

**Core（必須出力）**: RE の実行時にしか得られないデータ
- `headers.general.*` — HTTPステータス、リクエストURL、メソッド
- `eo.meta.*` — 実行環境（re-area, execution-id, timestamps, protocol, tls）、リクエスト識別情報（パススルー）、計測値（duration-ms, ttfb-ms, actual-content-length, redirect-count, retry情報）、CDN検出（cdn-header-name, cdn-header-value, cdn-cache-status）
- `headers.request-headers.*` / `headers.response-headers.*` — 生ヘッダー

**Extension（暫定出力）**: レスポンスヘッダーやURLから導出可能なデータ。将来的に消費側へ移動する前提。
- `eo.security.*` — セキュリティヘッダー分析

**新しいキーを追加する際の判断基準**:
1. RE の実行時にしか取得できないか？ → Core (`eo.meta.*`)
2. `headers.response-headers.*` やURLから導出できるか？ → Extension（暫定、`eo.security.*` 等）

## Important Conventions

- **Secret management**: All Request Engines share the same `N8N_EO_REQUEST_SECRET` value stored in their respective cloud secret services
- **Token verification**: Each Request Engine validates incoming tokens against `SHA-256(url + secret)` before processing
- **Naming convention**: Resources follow `eo-re-d01-{service}-{region}` pattern

## Git Operation Policy

1. Execute all `git add`, `git commit`, and `git push` operations through human operators unless explicit instructions direct the AI to perform them.
The AI refrains from executing these commands.
2. Provide commit preparation information in the following form:
    - List all resources that require staging with `git add`.
    - Provide the commit message to be used.
    - Output only the required information, without including any git commands.

## Environment Variables

Critical variables in `EO_Infra_Docker/.env`:
- `N8N_ENCRYPTION_KEY` - n8n credential encryption
- `N8N_EO_REQUEST_SECRET` - Shared secret for token generation/verification
- `POSTGRES_PASSWORD`, `REDIS_PASSWORD` - Service credentials

## Reliability Features (Request Engines)

- Max 3 retries with exponential backoff (0.5s, 1s, 2s)
- 10-second timeout per request
- 5MB content limit for memory protection
- Retryable status codes: 500, 502, 503, 504

## CRITICAL STANDARDS
1. **Name Persistence:** Maintain all existing variable and function names. Explicit instruction is required for any renaming.
   - 既存の名称を厳格に保持し、変更が必要な場合は必ずユーザーの承諾を得ること。
2. **Language Policy:** Communicate exclusively in Japanese.
   - 指定がない限り、思考プロセスおよび出力のすべてを日本語で行うこと。
3. **Change Control Protocol:** Prioritize architectural integrity. Request formal approval before executing any structural, design, or logic modifications.
   - 構造・デザイン・コードの変更前には、変更案を提示し承認を得るプロセスを必須とする。
4. **Markdown Style:** Do not use `---` (horizontal rule) in markdown files.
   - マークダウンファイルで水平線（`---`）を使用しないこと。
5. **Naming Readability:** When proposing names for variables, functions, files, or any identifiers, prioritize "first-glance comprehension" over technical precision alone. A name must be understandable to someone seeing it for the first time without reading the source code.
   - 命名提案時は「初見で意味が通るか」を最優先基準とする。技術的正確さだけでは不十分。コードを読まずとも名前だけで意図が伝わること。
6. **File Path References:** When referencing files in code comments, documentation, or any text, always use the full path from the repository root directory. Never use bare filenames.
   - コメント・ドキュメント等でファイルを参照する際は、リポジトリルートからのフルパスで記載すること。ファイル名単体での記載は禁止。

