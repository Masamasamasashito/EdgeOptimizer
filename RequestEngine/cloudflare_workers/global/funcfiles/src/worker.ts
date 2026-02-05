/**
 * ---------------------------------------------------------- 
 * Edge Optimizer
 * Request Engine for Cloudflare Workers
 * 
 * Crafted by Nishi Labo | https://4649-24.com
 * ----------------------------------------------------------
 * 
 * EO Request Engine for Cloudflare Workers (Refactored)
 * * Overview:
 * Executes HTTP requests to specified URLs to warm up the Cloudflare Edge PoP cache.
 * Returns results in a flat JSON structure (supporting TTFB/BodySize measurements).
 * 
 * * Input:
# - JSON Body: { data: { targetUrl, tokenCalculatedByN8n, headers, ... } }
# - GET Query: ?targetUrl=...&tokenCalculatedByN8n=...
 * 
 * * Dependencies:
 * - Header pass-through from n8n No.280 nodes (Host header excluded)
 * - Cloudflare Worker Secrets (env.CFWORKER_REQUEST_SECRET)
 * 
 * * Note on Secret Caching:
 * - Cloudflare Workers environment variables (Secrets) are loaded into memory
 *   when the Worker starts and remain available for all requests.
 * - Unlike Azure Functions, AWS Lambda, and GCP Cloud Run, which fetch secrets
 *   from external services (Key Vault, Secrets Manager, Secret Manager) and
 *   cache them in global variables, Cloudflare Workers Secrets are already
 *   in-memory and require no API calls or explicit caching mechanism.
 * - Each request directly accesses env.CFWORKER_REQUEST_SECRET without
 *   any external API calls, making it the most efficient approach.
 */

// ==========================================
// 1. Types & Interfaces
// ==========================================

// Generic object type used throughout the application
type JsonRecord = Record<string, unknown>;
type StringRecord = Record<string, string>;

interface Env {
  CFWORKER_REQUEST_SECRET: string;
}

// Normalized request data structure
interface WarmupRequest {
  targetUrl: string;
  tokenCalculatedByN8n: string;
  headers: StringRecord;
  httpRequestNumber: string | number;
}

// Final response structure (for flat JSON output)
interface ExecutionResultParams {
  statusCode: number;
  statusMessage: string;
  duration_ms: number;
  ttfb_ms?: number;
  content_length_bytes?: number;
  targetUrl: string;
  httpRequestNumber: string | number;
  reqHeaders: StringRecord;
  respHeaders?: Headers | StringRecord | null;
  extraError?: JsonRecord | null;
  area: string;
  incomingCf?: Record<string, unknown>; // Added for protocol info
}

// Error Context (Information preserved when an error occurs during processing)
interface ExecutionContextState extends Partial<ExecutionResultParams> {
  area: string;
  duration_ms: number;
}

// Error reason definitions
type ErrorReason =
  | "empty_event_list"
  | "invalid_event_type"
  | "missing_url"
  | "missing_secret"
  | "missing_token"
  | "invalid_token"
  | "request_exception";

// ==========================================
// 2. Constants
// ==========================================

const CONSTANTS = {
  EO_HEADER_NAME: "x-eo-re",
  EO_HEADER_VALUE: "cloudflare",
  EO_DEFAULT_AREA: "Cloudflare_global",
  // Header keys to exclude from forwarding/logging (lowercase)
  EO_IGNORED_HEADERS: ["host", "httprequestnumber"],
  EO_COMMON_RESP_HEADERS: {
    "content-type": "application/json;charset=utf-8",
    "Cache-Control": "no-store",
  } as const,
};

// ==========================================
// 3. Utility Functions
// ==========================================

/**
 * Generate hash for token validation
 * SHA-256(url + secret) -> hex string
 */
async function generateSecurityToken(url: string, secret: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(url + secret);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

/**
 * Normalize request headers
 * - Exclude specific headers like Host
 * - Attach WAF bypass headers
 */
function prepareRequestHeaders(inputHeaders: unknown): StringRecord {
  const headers: StringRecord = {};

  if (typeof inputHeaders === 'object' && inputHeaders !== null) {
    for (const [key, value] of Object.entries(inputHeaders)) {
      if (typeof value !== 'string') continue;

      const lowerKey = key.toLowerCase();
      if (CONSTANTS.EO_IGNORED_HEADERS.includes(lowerKey)) continue;

      headers[key] = value;
    }
  }

  // Attach WAF bypass header
  headers[CONSTANTS.EO_HEADER_NAME] = CONSTANTS.EO_HEADER_VALUE;

  return headers;
}

/**
 * Convert result object to a flat JSON format.
 */
function formatFlatResult(params: ExecutionResultParams): JsonRecord {
  const {
    statusCode,
    statusMessage,
    duration_ms,
    ttfb_ms,
    content_length_bytes,
    targetUrl,
    httpRequestNumber,
    reqHeaders,
    respHeaders,
    extraError,
    area,
  } = params;

  // 1. headers.general
  // parameters to be added to headers.general (Connection info from n8n to Worker)
  // Note: Standard Workers fetch API does not expose the outgoing protocol version.
  const protocol = (params.incomingCf?.httpProtocol as string) || "unknown";
  const tlsVersion = (params.incomingCf?.tlsVersion as string) || "unknown";

  const result: JsonRecord = {
    "headers.general.request-url": targetUrl,
    "headers.general.http-request-method": targetUrl ? "GET" : "",
    "headers.general.status-code": `${statusCode} ${statusMessage}`.trim(),
    "headers.general.connection-protocol": protocol,
    "headers.general.connection-tls-version": tlsVersion,
  };

  // 2. headers.response-headers
  if (respHeaders) {
    const entries = respHeaders instanceof Headers
      ? Array.from(respHeaders.entries())
      : Object.entries(respHeaders);

    for (const [key, value] of entries) {
      if (typeof value === 'string') {
        result[`headers.response-headers.${key.toLowerCase()}`] = value;
      }
    }
    // Content-length polyfill logic
    if (content_length_bytes !== undefined) {
      const clKey = "headers.response-headers.content-length";
      if (!(clKey in result) || !result[clKey]) {
        result[clKey] = String(content_length_bytes);
      }
    }
  }

  // 3. headers.request-headers
  for (const [key, value] of Object.entries(reqHeaders)) {
    result[`headers.request-headers.${key.toLowerCase()}`] = value;
  }

  // 4. eo.meta (Metadata & Context)
  result["eo.meta.http-request-number"] = httpRequestNumber;
  result["eo.meta.area"] = area;

  // 5. eo.measure (Measurements: Performance, Security, etc.)
  result["eo.measure.duration-ms"] = Number(duration_ms);

  if (ttfb_ms !== undefined) {
    result["eo.measure.ttfb-ms"] = Number(ttfb_ms);
  }

  if (content_length_bytes !== undefined) {
    result["eo.measure.actual-content-length"] = Number(content_length_bytes);
  }

  // Integrate error information (Added at the end)
  if (extraError) {
    Object.assign(result, extraError);
  }

  return result;
}

/**
 * Helper function to generate custom error responses
 */
function createErrorResponse(
  status: number,
  reason: ErrorReason,
  message: string,
  context: ExecutionContextState,
  detail?: string
): Response {
  const errorData = {
    "error.reason": reason,
    "error.message": message,
    ...(detail ? { "error.detail": detail } : {}),
  };

  const payload = formatFlatResult({
    statusCode: status,
    statusMessage: reason.toUpperCase(),
    // Fix: Unified to duration_ms as context.totalMs was referenced but undefined
    duration_ms: context.duration_ms || 0,
    targetUrl: context.targetUrl || "",
    httpRequestNumber: context.httpRequestNumber || "None",
    reqHeaders: context.reqHeaders || {},
    respHeaders: {},
    extraError: errorData,
    area: context.area,
    incomingCf: {},
  });

  return new Response(JSON.stringify(payload), {
    status,
    headers: CONSTANTS.EO_COMMON_RESP_HEADERS,
  });
}

// ==========================================
// 4. Input Parser
// ==========================================

/**
 * Helper to extract parameters from Body or Query
 */
function extractRawData(body: unknown): unknown {
  // Normalize Event format (Handle array head, presence of 'data' property)
  let target = body;

  // If array, extract the first element (Standard behavior for n8n)
  if (Array.isArray(body)) {
    if (body.length === 0) throw new Error("EMPTY_EVENT_LIST");
    target = body[0];
  }

  // If structure is { "data": { ... } }, extract contents of 'data'
  if (target && typeof target === 'object' && 'data' in target) {
    return (target as { data: unknown }).data;
  }

  return target;
}

/**
 * Parses the request (JSON Body or Query String) and returns it in a unified format
 */
async function parseRequestInput(request: Request): Promise<WarmupRequest> {
  let rawData: unknown = null;

  // 1. Attempt to parse JSON Body
  // Checking Content-Type header is best practice, but using try-catch to match existing logic
  try {
    const clone = request.clone();
    const body = await clone.json();
    if (body) {
      rawData = extractRawData(body);
    }
  } catch {
    // Ignore JSON parse failures (Fallback to GET query)
  }

  // 2. Parse GET Query (Only if JSON is empty)
  if (!rawData && request.method === "GET") {
    const urlObj = new URL(request.url);
    const headers: StringRecord = {};
    request.headers.forEach((v, k) => { headers[k] = v; });

    rawData = {
      targetUrl: urlObj.searchParams.get("targetUrl"),
      tokenCalculatedByN8n: urlObj.searchParams.get("tokenCalculatedByN8n"),
      httpRequestNumber: urlObj.searchParams.get("httpRequestNumber"),
      headers: headers
    };
  }

  // If valid data could not be obtained
  if (!rawData || typeof rawData !== 'object') {
    throw new Error("INVALID_EVENT_TYPE");
  }

  // Temporary variable for type assertion
  const input = rawData as Record<string, unknown>;

  return {
    targetUrl: typeof input.targetUrl === 'string' ? input.targetUrl : "",
    tokenCalculatedByN8n: typeof input.tokenCalculatedByN8n === 'string' ? input.tokenCalculatedByN8n : "",
    // Extract httpRequestNumber as metadata
    httpRequestNumber: (typeof input.httpRequestNumber === 'string' || typeof input.httpRequestNumber === 'number')
      ? input.httpRequestNumber
      : "None",
    // httprequestnumber contained in headers is excluded by prepareRequestHeaders
    headers: prepareRequestHeaders(input.headers),
  };
}

// ==========================================
// 5. Main Logic
// ==========================================

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    const start_time = performance.now();

    // Get Area Information (Cloudflare proprietary property)
    const cf = (request as unknown as { cf: { colo: string } }).cf;
    const area = (cf && typeof cf.colo === "string") ? cf.colo : CONSTANTS.EO_DEFAULT_AREA;

    // Initialize Context (For preserving info on error)
    const context: ExecutionContextState = {
      area,
      duration_ms: 0
    };

    try {
      // ==================================================================
      // n8nのHttpRequestノード(リクエストエンジンノード)からリクエスト受信
      // (Receive from n8n HttpRequest node (Request Engine node))
      // ==================================================================
      // ------------------------------------------------
      // Step 1: Input Parsing
      // ------------------------------------------------
      let warmupReq: WarmupRequest;
      try {
        warmupReq = await parseRequestInput(request);
      } catch (e: unknown) {
        const err = e instanceof Error ? e : new Error(String(e));
        const reason: ErrorReason = err.message === "EMPTY_EVENT_LIST" ? "empty_event_list" : "invalid_event_type";
        return createErrorResponse(400, reason, err.message, context);
      }

      // Update Context (For error handling)
      context.targetUrl = warmupReq.targetUrl;
      context.httpRequestNumber = warmupReq.httpRequestNumber;
      context.reqHeaders = warmupReq.headers;

      // ------------------------------------------------
      // Step 2: Validation
      // ------------------------------------------------
      // Check URL
      if (!warmupReq.targetUrl) {
        context.duration_ms = performance.now() - start_time;
        return createErrorResponse(400, "missing_url", "Target URL is missing.", context);
      }

      // Check Environment Variable
      // Note: env.CFWORKER_REQUEST_SECRET is already in-memory (loaded at Worker startup),
      // so no API calls or caching mechanism is needed (unlike other platforms).
      if (!env.CFWORKER_REQUEST_SECRET) {
        context.duration_ms = performance.now() - start_time;
        return createErrorResponse(500, "missing_secret", "Environment variable CFWORKER_REQUEST_SECRET is not configured.", context);
      }

      // Check Token Existence
      if (!warmupReq.tokenCalculatedByN8n) {
        context.duration_ms = performance.now() - start_time;
        return createErrorResponse(401, "missing_token", "Security token is missing.", context);
      }

      // ------------------------------------------------
      // Step 3: Token Validation
      // ------------------------------------------------
      const tokenCalculatedByCloudSecret = await generateSecurityToken(warmupReq.targetUrl, env.CFWORKER_REQUEST_SECRET);
      if (warmupReq.tokenCalculatedByN8n !== tokenCalculatedByCloudSecret) {
        context.duration_ms = performance.now() - start_time;
        return createErrorResponse(401, "invalid_token", "Token validation failed.", context);
      }

      // ------------------------------------------------
      // Step 4: Execute Warmup Request (GET)
      // ------------------------------------------------
      // ==================================================================
      // WarmupターゲットURLにHTTPリクエスト送信
      // (Send to Request for Warmup Target URL)
      // ==================================================================
      const resp = await fetch(warmupReq.targetUrl, {
        method: "GET",
        headers: warmupReq.headers,
        redirect: "follow",
      });

      // ==================================================================
      // WarmupResultData受信
      // (Recieve WarmupResultData from Target URL)
      // ==================================================================
      // 1. Measure TTFB (When await fetch completes)
      const ttfb_end = performance.now();
      const measured_ttfb = ttfb_end - start_time;

      // 2. Download Body & Measure Size
      const bodyBuffer = await resp.arrayBuffer();
      const measured_body_size = bodyBuffer.byteLength;

      // 3. Measure Duration (Download complete)
      const end_time = performance.now();
      const measured_duration = end_time - start_time;

      // ------------------------------------------------
      // Step 5: Generate Success Response
      // ------------------------------------------------
      const result = formatFlatResult({
        statusCode: resp.status,
        statusMessage: resp.statusText,

        // Pass measurements
        duration_ms: measured_duration,
        ttfb_ms: measured_ttfb,
        content_length_bytes: measured_body_size,

        targetUrl: warmupReq.targetUrl,
        httpRequestNumber: warmupReq.httpRequestNumber,
        reqHeaders: warmupReq.headers,
        respHeaders: resp.headers,
        extraError: null,
        area,
        incomingCf: cf as unknown as Record<string, unknown>,
      });

      // ==================================================================
      // n8nのHttpRequestノード(リクエストエンジンノード)にWarmup結果データを返す
      // (Reply to n8n HttpRequest node (Request Engine node) with WarmupResultData)
      // ==================================================================
      return new Response(JSON.stringify(result), {
        status: 200, // The fetch result is inside the JSON, Worker itself returns 200
        headers: CONSTANTS.EO_COMMON_RESP_HEADERS,
      });

    } catch (e: unknown) {
      // Fetch Execution Error (DNS error, timeout, etc.)
      context.duration_ms = performance.now() - start_time;
      const errorText = String(e);

      return createErrorResponse(599, "request_exception", "HTTP request to origin failed.", context, errorText);
    }
  },
};

