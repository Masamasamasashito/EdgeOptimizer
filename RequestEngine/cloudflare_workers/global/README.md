# EO Request Engine for Cloudflare Workers

A high-performance, lightweight Request Engine for the Edge Optimizer (EO) by n8n, built on Cloudflare Workers. This engine handles warmup requests to Edge PoPs with precise timing measurements (TTFB, Duration).

## Prerequisites

- [Node.js](https://nodejs.org/) (Latest LTS recommended)
- [npm](https://www.npmjs.com/)
- [Cloudflare Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/) (`npm install -g wrangler`)

## Setup & Configuration

1. **Clone the repository** and navigate to the directory:
   ```bash
   cd RequestEngine/cloudflare_workers/global/funcfiles
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure `wrangler.toml`**:

- RequestEngine\cloudflare_workers\global\CFWORKER_README.md

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

## Usage API

The worker accepts JSON payloads compatible with the EO ecosystem.

### Request Format(n8n → Cloudflare Worker)
```json
{
  "data": {
    "targeturl": "https://sample.com/page1",
    "urltype": "main_document",
    "token": "generated-sha256-hash", // SHA256(url + N8N_EO_REQUEST_SECRET)
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
    - `eo.meta.*`: Metadata and context (Conditions, IDs, Regions).
    - `eo.measure.*`: All measurement values (Performance, Security, etc.).

```jsonc
{
  // --- Request General Info ---
  "headers.general.request-url": "https://target-site.com/page1",
  "headers.general.http-request-method": "GET",
  "headers.general.status-code": "200 OK",
  "headers.general.connection-protocol": "HTTP/2", // Protocol (n8n -> Worker)
  "headers.general.connection-tls-version": "TLSv1.3", // TLS Version (n8n -> Worker)

  // --- Response Headers (From Origin) ---
  "headers.response-headers.content-type": "text/html; charset=utf-8",
  "headers.response-headers.date": "Tue, 24 Dec 2024 04:54:10 GMT",
  "headers.response-headers.cache-control": "max-age=3600",
  "headers.response-headers.content-length": "1024",

  // --- Request Headers (Sent to Origin) ---
  "headers.request-headers.user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
  "headers.request-headers.accept-encoding": "gzip",
  "headers.request-headers.x-eo-client": "eo-cloudflare-worker",

  // --- EO Metadata & Context ---
  "eo.meta.http-request-number": 1,           // ID passed from input (pass-through)
  "eo.meta.area": "NRT",                      // Execution Region (Cloudflare Colo Code)
  
  // --- EO Measurements (Performance & Security) ---
  "eo.measure.duration-ms": 125,              // Total duration of the fetch request
  "eo.measure.ttfb-ms": 45,                   // Time To First Byte (latency)
  "eo.measure.actual-content-length": 1024,   // Actual size of the downloaded body
}
```

## CI/CD Deployment

This repository works with GitHub Actions for automated deployment.

### 1. Prerequisites
Ensure the `.github/workflows/deploy.yml` exists.

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
Push changes to the `funcfiles/src/` directory, `funcfiles/package.json`, or `funcfiles/tsconfig.json` on the `main` branch to trigger the deployment.

