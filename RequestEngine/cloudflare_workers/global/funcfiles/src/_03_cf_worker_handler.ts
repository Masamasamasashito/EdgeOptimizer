/**
 * ----------------------------------------------------------
 * Edge Optimizer
 * Request Engine for Cloudflare Workers - Platform-Specific Handler
 *
 * Crafted by Nishi Labo | https://4649-24.com
 * ----------------------------------------------------------
 *
 * EO Request Engine for Cloudflare Workers
 *
 * Overview:
 * Executes HTTP requests to specified URLs to warm up the Cloudflare Edge PoP cache.
 * Returns results in a flat JSON structure (supporting TTFB/BodySize measurements).
 *
 * Input:
 * - JSON Body: { data: { targetUrl, tokenCalculatedByN8n, headers, ... } }
 * - GET Query: ?targetUrl=...&tokenCalculatedByN8n=...
 *
 * Dependencies:
 * - Header pass-through from n8n No.280 nodes (Host header excluded)
 * - Cloudflare Worker Secrets (env.CFWORKER_REQUEST_SECRET)
 *
 * Note on Secret Caching:
 * - Cloudflare Workers environment variables (Secrets) are loaded into memory
 *   when the Worker starts and remain available for all requests.
 * - Unlike Azure Functions, AWS Lambda, and GCP Cloud Run, which fetch secrets
 *   from external services (Key Vault, Secrets Manager, Secret Manager) and
 *   cache them in global variables, Cloudflare Workers Secrets are already
 *   in-memory and require no API calls or explicit caching mechanism.
 * - Each request directly accesses env.CFWORKER_REQUEST_SECRET without
 *   any external API calls, making it the most efficient approach.
 */

import type {
  StringRecord,
  Env,
  WarmupRequest,
  ExecutionContextState,
  ErrorReason,
} from "./_01_types";

import {
  CONSTANTS,
  calcToken,
  prepareRequestHeaders,
  buildFlatResult,
  determineResourceType,
} from "../../../common/request_engine_core";

// Side-effect import: registers extensions into the extension registry
import "./_02_extensions";

// ==========================================
// Input Parser
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
  if (target && typeof target === "object" && "data" in target) {
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
    request.headers.forEach((v, k) => {
      headers[k] = v;
    });

    rawData = {
      targetUrl: urlObj.searchParams.get("targetUrl"),
      tokenCalculatedByN8n: urlObj.searchParams.get("tokenCalculatedByN8n"),
      httpRequestNumber: urlObj.searchParams.get("httpRequestNumber"),
      headers: headers,
    };
  }

  // If valid data could not be obtained
  if (!rawData || typeof rawData !== "object") {
    throw new Error("INVALID_EVENT_TYPE");
  }

  // Temporary variable for type assertion
  const input = rawData as Record<string, unknown>;

  return {
    targetUrl: typeof input.targetUrl === "string" ? input.targetUrl : "",
    tokenCalculatedByN8n:
      typeof input.tokenCalculatedByN8n === "string"
        ? input.tokenCalculatedByN8n
        : "",
    // Extract httpRequestNumber as metadata
    httpRequestNumber:
      typeof input.httpRequestNumber === "string" ||
      typeof input.httpRequestNumber === "number"
        ? input.httpRequestNumber
        : "None",
    // Extract httpRequestUUID (created by n8n)
    httpRequestUUID:
      typeof input.httpRequestUUID === "string" ? input.httpRequestUUID : null,
    // Extract httpRequestRoundID (UNIX timestamp, created by n8n)
    httpRequestRoundID:
      typeof input.httpRequestRoundID === "number"
        ? input.httpRequestRoundID
        : null,
    // Extract urltype for resource type determination
    urltype: typeof input.urltype === "string" ? input.urltype : null,
    // httprequestnumber contained in headers is excluded by prepareRequestHeaders
    headers: prepareRequestHeaders(input.headers),
  };
}

// ==========================================
// Error Response Helper
// ==========================================

/**
 * Helper function to generate custom error responses
 */
function createErrorResponse(
  status: number,
  reason: ErrorReason,
  message: string,
  context: ExecutionContextState,
  detail?: string,
): Response {
  const errorData = {
    "error.reason": reason,
    "error.message": message,
    ...(detail ? { "error.detail": detail } : {}),
  };

  const payload = buildFlatResult({
    statusCode: status,
    statusMessage: reason.toUpperCase(),
    duration_ms: context.duration_ms || 0,
    targetUrl: context.targetUrl || "",
    httpRequestNumber: context.httpRequestNumber || "None",
    httpRequestUUID: context.httpRequestUUID,
    httpRequestRoundID: context.httpRequestRoundID,
    reqHeaders: context.reqHeaders || {},
    respHeaders: {},
    extraError: errorData,
    area: context.area,
    executionId: context.executionId,
    requestStartTimestamp: context.requestStartTimestamp,
    requestEndTimestamp: Date.now() / 1000,
  });

  return new Response(JSON.stringify(payload), {
    status,
    headers: CONSTANTS.EO_COMMON_RESP_HEADERS,
  });
}

// ==========================================
// Main Logic
// ==========================================

export default {
  async fetch(
    request: Request,
    env: Env,
    _ctx: ExecutionContext,
  ): Promise<Response> {
    const start_time = performance.now();
    const requestStartTimestamp = Date.now() / 1000;

    // Generate execution ID
    const executionId = crypto.randomUUID();

    // Get Area Information (Cloudflare proprietary property)
    const cf = (request as unknown as { cf: { colo: string } }).cf;
    const area =
      cf && typeof cf.colo === "string" ? cf.colo : CONSTANTS.EO_DEFAULT_AREA;

    // Initialize Context (For preserving info on error)
    const context: ExecutionContextState = {
      area,
      duration_ms: 0,
      executionId,
      requestStartTimestamp,
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
        const reason: ErrorReason =
          err.message === "EMPTY_EVENT_LIST"
            ? "empty_event_list"
            : "invalid_event_type";
        return createErrorResponse(400, reason, err.message, context);
      }

      // Update Context (For error handling)
      context.targetUrl = warmupReq.targetUrl;
      context.httpRequestNumber = warmupReq.httpRequestNumber;
      context.httpRequestUUID = warmupReq.httpRequestUUID;
      context.httpRequestRoundID = warmupReq.httpRequestRoundID;
      context.reqHeaders = warmupReq.headers;

      // ------------------------------------------------
      // Step 2: Validation
      // ------------------------------------------------
      // Check URL
      if (!warmupReq.targetUrl) {
        context.duration_ms = performance.now() - start_time;
        return createErrorResponse(
          400,
          "missing_url",
          "Target URL is missing.",
          context,
        );
      }

      // Check Environment Variable
      // Note: env.CFWORKER_REQUEST_SECRET is already in-memory (loaded at Worker startup),
      // so no API calls or caching mechanism is needed (unlike other platforms).
      if (!env.CFWORKER_REQUEST_SECRET) {
        context.duration_ms = performance.now() - start_time;
        return createErrorResponse(
          500,
          "missing_secret",
          "Environment variable CFWORKER_REQUEST_SECRET is not configured.",
          context,
        );
      }

      // Check Token Existence
      if (!warmupReq.tokenCalculatedByN8n) {
        context.duration_ms = performance.now() - start_time;
        return createErrorResponse(
          401,
          "missing_token",
          "Security token is missing.",
          context,
        );
      }

      // ------------------------------------------------
      // Step 3: Token Validation
      // ------------------------------------------------
      const tokenCalculatedByCloudSecret = await calcToken(
        warmupReq.targetUrl,
        env.CFWORKER_REQUEST_SECRET,
      );
      if (warmupReq.tokenCalculatedByN8n !== tokenCalculatedByCloudSecret) {
        context.duration_ms = performance.now() - start_time;
        return createErrorResponse(
          401,
          "invalid_token",
          "Token validation failed.",
          context,
        );
      }

      // ------------------------------------------------
      // Step 4: Determine Resource Type
      // ------------------------------------------------
      const resourceInfo = determineResourceType(
        warmupReq.urltype,
        warmupReq.targetUrl,
      );

      // ------------------------------------------------
      // Step 5: Execute Warmup Request (GET)
      // ------------------------------------------------
      // ==================================================================
      // WarmupターゲットURLにHTTPリクエスト送信
      // (Send HTTP request to Warmup Target URL)
      // ==================================================================
      const resp = await fetch(warmupReq.targetUrl, {
        method: "GET",
        headers: warmupReq.headers,
        redirect: "follow",
      });

      // ==================================================================
      // WarmupResultData受信
      // (Receive WarmupResultData from Target URL)
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

      // 4. Redirect count (Workers API only exposes boolean)
      const redirectCount = resp.redirected ? 1 : 0;

      // 5. Request End Timestamp
      const requestEndTimestamp = Date.now() / 1000;

      // ------------------------------------------------
      // Step 6: Generate Success Response
      // ------------------------------------------------
      const result = buildFlatResult({
        statusCode: resp.status,
        statusMessage: resp.statusText,

        // Pass measurements
        duration_ms: measured_duration,
        ttfb_ms: measured_ttfb,
        content_length_bytes: measured_body_size,

        targetUrl: warmupReq.targetUrl,
        httpRequestNumber: warmupReq.httpRequestNumber,
        httpRequestUUID: warmupReq.httpRequestUUID,
        httpRequestRoundID: warmupReq.httpRequestRoundID,
        reqHeaders: warmupReq.headers,
        respHeaders: resp.headers,
        extraError: null,
        area,
        executionId,
        requestStartTimestamp,
        requestEndTimestamp,
        redirectCount,
        resourceInfo,
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

      return createErrorResponse(
        599,
        "request_exception",
        "HTTP request to origin failed.",
        context,
        errorText,
      );
    }
  },
};
