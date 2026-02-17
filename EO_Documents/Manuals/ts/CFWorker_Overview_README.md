# EO Request Engine for Cloudflare Workers

A high-performance, lightweight Request Engine for the Edge Optimizer (EO) by n8n, built on Cloudflare Workers. This engine handles warmup requests to Edge PoPs with precise timing measurements (TTFB, Duration).

## Prerequisites

- [Node.js](https://nodejs.org/) (Latest LTS recommended)
- [npm](https://www.npmjs.com/)
- [Cloudflare Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/) (`npm install -g wrangler`)

## Setup & Configuration

1. **Clone the repository** and navigate to the directory:
   ```bash
   cd RequestEngine/cf/workers/ts/funcfiles
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure `wrangler.toml`**:

- EO_Documents\Manuals\ts\CFWORKER_README.md

## Secrets Configuration

This worker requires a `CFWORKER_REQUEST_SECRET` for security token validation.

**Important!**
- The value of `CFWORKER_REQUEST_SECRET` used in this Cloudflare Worker Application must match the value of `N8N_EO_REQUEST_SECRET` in your `.env` ( `env.example` ) file.
- Please read the entire ".env GET READY: First Trial Setup (Quick Start)" section in `env.example`, and verify the value of `N8N_EO_REQUEST_SECRET` in your `.env` file.

### To set the secret for development/production:

```bash
npx wrangler secret put CFWORKER_REQUEST_SECRET
# Enter your N8N_EO_REQUEST_SECRET value with .env
```

## Local Development

Start the local development server:

```bash
npm run dev
```

## Deployment

Deploy the worker to the Cloudflare network:

```bash
npm run deploy
```

## File Structure

Python版 Request Engine の `common/` + プラットフォーム固有ハンドラー構造を TypeScript で再現。

```
RequestEngine/common/ts/                                ← CF Workers共通
├── request_engine_core.ts                              ← 共通コアロジック
└── extensions/
    └── _ext_security.ts                                ← security 拡張

RequestEngine/cf/workers/ts/funcfiles/src/  ← プラットフォーム固有
├── _01_types.ts                                        ← 型定義・インターフェース
├── _02_extensions.ts                                   ← ワークフローで動的生成（.gitignore対象）
├── _03_cf_worker_handler.ts                            ← メインハンドラー
└── worker.ts                                           ← エントリポイント（re-export のみ）
```

esbuild（`RequestEngine/cf/workers/ts/funcfiles/build.mjs`）が `bundle: true` で全 `import` を解決し、`dist/worker.js` に1ファイルにバンドル。

## Usage API

The worker accepts JSON payloads compatible with the EO ecosystem.

### Request Format(n8n → Cloudflare Worker)
```json
{
  "data": {
    "targetUrl": "https://sample.com/page1",
    "urltype": "main_document",
    "tokenCalculatedByN8n": "generated-sha256-hash", // SHA256(url + N8N_EO_REQUEST_SECRET)
    "headers": {
      "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
      "Accept-Language": "ja,ja-JP;q=0.9,en-US;q=0.8,en;q=0.7"
    },
    "userAgentLabel": "ios_safari_17",  
    "cloud_type_area": "GcpCloudFunctions_asia-northeast1",
    "httpRequestNumber": xxx,  
    "httpRequestUUID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "httpRequestRoundID": xxxxxxxxxx
  }
}
```

### Response Format
Returns a flat JSON object with timing metrics (compatible with EO Aggregators).

**Field Naming Convention**

The JSON keys follow a specific convention for clarity and standardization:

- **`headers.*`**: These fields strictly follow the naming convention used in **Chrome DevTools > Network Tab**.
    - `headers.general`: Correspond to the "General" section (Status Code, Request URL, Method).
    - `headers.response-headers`: Correspond to the "Response Headers" section (from the Origin).
    - `headers.request-headers`: Correspond to the "Request Headers" section (sent to the Origin).
    - *Note: This ensures the data structure is instantly familiar to web developers.*

- **`eo.*`**: These are proprietary metrics added by **Nishi Labo** for the **Edge Optimizer**.
    - `eo.meta.*`: Metadata, context, and measurements (IDs, Regions, Timing, CDN detection).
    - `eo.security.*`: Security header analysis (HSTS, CSP, etc.).

```jsonc
{
  // --- Request General Info ---
  "headers.general.status-code": 200,
  "headers.general.status-message": "OK",
  "headers.general.request-url": "https://target-site.com/page1",
  "headers.general.http-request-method": "GET",

  // --- EO Metadata & Identification ---
  "eo.meta.http-request-number": 1,
  "eo.meta.http-request-uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "eo.meta.http-request-round-id": 1739000000,
  "eo.meta.urltype": "main_document",

  // --- EO Execution Environment ---
  "eo.meta.re-area": "NRT",                   // Cloudflare Colo Code
  "eo.meta.execution-id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "eo.meta.request-start-timestamp": 1739000000.123,
  "eo.meta.request-end-timestamp": 1739000000.456,

  // --- EO Protocol (Workers API limitation: fixed values) ---
  "eo.meta.http-protocol-version": "unavailable: Workers fetch API does not expose outgoing connection info (...)",
  "eo.meta.tls-version": "unavailable: Workers fetch API does not expose outgoing connection info (...)",

  // --- EO CDN Detection ---
  "eo.meta.cdn-header-name": "cf-ray",
  "eo.meta.cdn-header-value": "xxxxxxxx-NRT",
  "eo.meta.cdn-cache-status": "HIT",

  // --- EO Measurements ---
  "eo.meta.duration-ms": 125.45,
  "eo.meta.ttfb-ms": 45.12,
  "eo.meta.actual-content-length": 1024,
  "eo.meta.redirect-count": 0,

  // --- EO Security ---
  "eo.security.is_https": true,
  "eo.security.hsts_present": true,
  "eo.security.hsts_value": "max-age=31536000; includeSubDomains",
  // ... (csp, x_content_type_options, x_frame_options, etc.)

  // --- Response Headers (From Origin) ---
  "headers.response-headers.content-type": "text/html; charset=utf-8",
  "headers.response-headers.date": "Tue, 24 Dec 2024 04:54:10 GMT",
  "headers.response-headers.cache-control": "max-age=3600",
  "headers.response-headers.content-length": "1024",

  // --- Request Headers (Sent to Origin) ---
  "headers.request-headers.user-agent": "Mozilla/5.0 ...",
  "headers.request-headers.accept-encoding": "gzip",
  "headers.request-headers.x-eo-re": "cloudflare"
}
```

## CI/CD Deployment

This repository works with GitHub Actions for automated deployment.

### 1. Prerequisites
Ensure `.github/workflows/deploy-ts-to-cf-worker.yml` exists.

### 2. GitHub Secrets Configuration
Set the following secrets in your GitHub Repository settings (Settings > Secrets and variables > Actions):

| Github Secrets Name | Description |
|---|---|
| `EO_CF_WORKER_USER_API_TOKEN_FOR_GITHUB` | Cloudflare API Token with Workers permissions. |
| `EO_CF_ACCOUNT_ID` | Your Cloudflare Account ID. |

**Note:**
Please make sure to register CFWORKER_REQUEST_SECRET (N8N_EO_REQUEST_SECRET) as a secret in your Cloudflare Worker's Secrets.
Likewise, register any GitHub secrets in GitHub Secrets.

### 3. Trigger
GitHub Actions > Run workflow から手動実行（`workflow_dispatch`）。

| 入力名 | 型 | デフォルト | 説明 |
|--------|------|-----------|------|
| `ext_security` | boolean | `true` | Security Extension（`eo.security.*`）の有効/無効 |

