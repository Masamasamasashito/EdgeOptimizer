/**
 * ----------------------------------------------------------
 * Edge Optimizer
 * Request Engine Core - Shared Code Module for Cloudflare Workers
 *
 * Crafted by Nishi Labo | https://4649-24.com
 * ----------------------------------------------------------
 *
 * This module contains shared code used by all CF Workers Request Engine implementations.
 * TypeScript port of RequestEngine/common/request_engine_core.py
 *
 * Note: This file is bundled with platform-specific handlers by esbuild during build.
 * Do NOT add platform-specific imports or code here.
 */

import type {
  JsonRecord,
  StringRecord,
  ResourceInfo,
  ExecutionResultParams,
  ExtensionContext,
  ExtensionBuildFunc,
  ExtensionConfig,
} from "../global/funcfiles/src/_01_types";

// ======================================================================
// Constants
// ======================================================================

export const CONSTANTS = {
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

// Workers fetch API does not expose outgoing connection protocol/TLS information.
// request.cf.httpProtocol / request.cf.tlsVersion only provide incoming (client -> Worker) info.
// See: https://developers.cloudflare.com/workers/runtime-apis/request/#incomingrequestcfproperties
// See: https://developers.cloudflare.com/workers/runtime-apis/response/
// See: https://developers.cloudflare.com/workers/runtime-apis/fetch/
export const PROTOCOL_UNAVAILABLE_MESSAGE =
  "unavailable: Workers fetch API does not expose outgoing connection info (https://developers.cloudflare.com/workers/runtime-apis/request/#incomingrequestcfproperties)";

// ======================================================================
// CDN Detection Configuration
// ======================================================================
// Each entry: [detection_header, cache_status_header]
// Matches RequestEngine/common/request_engine_core.py _CDN_DETECTION_CONFIG
const CDN_DETECTION_CONFIG: ReadonlyArray<readonly [string, string]> = [
  // Cloudflare
  ["cf-ray", "cf-cache-status"],
  // AWS CloudFront
  ["x-amz-cf-id", "x-cache"],
  // NitroCDN (NitroPack)
  ["x-nitro-cache", "x-nitro-cache"],
  ["x-nitro-cache-from", "x-nitro-cache"],
  ["x-nitro-rev", "x-nitro-cache"],
  // RabbitLoader
  ["x-rl-cache", "x-rl-cache"],
  ["x-rl-mode", "x-rl-cache"],
  ["x-rl-modified", "x-rl-cache"],
  ["x-rl-rule", "x-rl-cache"],
  // Azure Front Door
  ["x-azure-ref", "x-cache"],
  ["x-azure-fdid", "x-cache"],
  ["x-azure-clientip", "x-cache"],
  ["x-azure-socketip", "x-cache"],
  ["x-azure-requestchain", "x-cache"],
  // Akamai
  ["x-akamai-request-id", "x-cache"],
  ["x-cache-remote", "x-cache"],
  ["x-true-cache-key", "x-cache"],
  ["x-cache-key", "x-cache"],
  ["x-serial", "x-cache"],
  ["x-akamai-edgescape", "x-cache"],
  ["x-check-cacheable", "x-cache"],
  // Vercel
  ["x-vercel-cache", "x-vercel-cache"],
  ["x-vercel-id", "x-vercel-cache"],
  // Sakura Internet Web Accelerator (さくらウェブアクセラレータ)
  ["x-webaccel-origin-status", "x-cache"],
  // Bunny CDN
  ["cdn-pullzone", "cdn-cache"],
  ["cdn-uid", "cdn-cache"],
  ["cdn-requestid", "cdn-cache"],
  // Alibaba Cloud CDN
  ["eagleid", "x-cache"],
  ["x-swift-savetime", "x-cache"],
  ["x-swift-cachetime", "x-cache"],
  // CDNetworks
  ["x-cnc-request-id", "x-cache"],
  // KeyCDN
  ["x-pull", "x-cache"],
  ["x-edge-location", "x-cache"],
  // General / Fastly
  ["x-cache", "x-cache"],
  ["x-served-by", "x-cache"],
  ["x-fastly-request-id", "x-cache"],
];

// ======================================================================
// Extension Registry (拡張機能レジストリ)
// ======================================================================
// Matches RequestEngine/common/request_engine_core.py _EXTENSION_REGISTRY
//
// 拡張機能の追加方法:
// 1. RequestEngine/cloudflare_workers/common/extensions/_ext_<name>.ts を作成
// 2. ファイル内で registerExtension() を呼び出す
// 3. deploy-to-cf-worker-global.yml の _02_extensions.ts 生成ステップに import を追加
//    (_02_extensions.ts はワークフローで動的生成。Python版のcat条件結合と同等)

const _EXTENSION_REGISTRY: Map<string, ExtensionConfig> = new Map();

/**
 * Register an extension module
 *
 * Matches RequestEngine/common/request_engine_core.py register_extension()
 *
 * @param name - Extension name (e.g. "security")
 * @param prefix - Output key prefix (e.g. "eo.security.")
 * @param buildFunc - Function that builds extension output
 * @param defaultEnabled - Whether enabled by default
 */
export function registerExtension(
  name: string,
  prefix: string,
  buildFunc: ExtensionBuildFunc,
  defaultEnabled: boolean = true,
): void {
  _EXTENSION_REGISTRY.set(name, { prefix, buildFunc, defaultEnabled });
}

/**
 * Get registered extensions (for debugging/logging)
 */
export function getRegisteredExtensions(): Map<string, ExtensionConfig> {
  return new Map(_EXTENSION_REGISTRY);
}

// ======================================================================
// Token Calculation (SHA-256)
// ======================================================================

/**
 * Calculate request token (SHA-256 hash)
 *
 * Used to verify against token generated by n8n workflow.
 * Formula: SHA-256(url + request_secret)
 *
 * Matches RequestEngine/common/request_engine_core.py _calc_token()
 *
 * @param url - Target URL
 * @param secret - Request secret (from Cloudflare Workers Secrets)
 * @returns 64-character hexadecimal hash value (lowercase)
 */
export async function calcToken(url: string, secret: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(url + secret);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

// ======================================================================
// URL Extension Determination
// ======================================================================

/**
 * Get extension from URL (removing query parameters and anchors)
 *
 * Matches RequestEngine/common/request_engine_core.py _get_url_extension()
 *
 * @param url - Target URL
 * @returns Extension string (lowercase) or null
 */
export function getUrlExtension(url: string): string | null {
  try {
    const parsed = new URL(url);
    const path = parsed.pathname;
    if (!path) return null;
    if (path.includes(".")) {
      const ext = path.split(".").pop()?.toLowerCase() ?? null;
      // Check if extension is valid string (alphanumeric only)
      if (ext && /^[a-z0-9]+$/.test(ext)) {
        return ext;
      }
    }
    return null;
  } catch {
    return null;
  }
}

// ======================================================================
// Determine Resource Type Based on URL Type and Extension
// ======================================================================

/**
 * Determine resource type from urltype and URL extension
 *
 * Maintains consistency with n8n workflow
 * (160 node: Asset / MainDoc / Exception Classification)
 *
 * Matches RequestEngine/common/request_engine_core.py _determine_resource_type()
 *
 * Asset extensions:
 * - Images: jpg, jpeg, gif, png, webp, avif, svg, ico
 * - CSS: css
 * - JS: js
 * - Fonts: woff, woff2, ttf, otf, eot
 * - Videos: mp4, webm, ogg, mov
 *
 * resource_category:
 * - "html", "image", "css", "js", "font", "video", "other"
 *
 * @param urltype - URL type from n8n ("main_document", "asset", "exception", or null)
 * @param url - Target URL
 * @returns Resource information object
 */
export function determineResourceType(
  urltype: string | null,
  url: string,
): ResourceInfo {
  const resourceInfo: ResourceInfo = {
    urltype,
    url_extension: null,
    resource_category: null,
  };

  const ext = getUrlExtension(url);
  resourceInfo.url_extension = ext;

  if (urltype === "main_document") {
    resourceInfo.resource_category = "html";
  } else if (urltype === "asset") {
    const imageExts = ["jpg", "jpeg", "gif", "png", "webp", "avif", "svg", "ico"];
    const cssExts = ["css"];
    const jsExts = ["js"];
    const fontExts = ["woff", "woff2", "ttf", "otf", "eot"];
    const videoExts = ["mp4", "webm", "ogg", "mov"];

    if (ext && imageExts.includes(ext)) {
      resourceInfo.resource_category = "image";
    } else if (ext && cssExts.includes(ext)) {
      resourceInfo.resource_category = "css";
    } else if (ext && jsExts.includes(ext)) {
      resourceInfo.resource_category = "js";
    } else if (ext && fontExts.includes(ext)) {
      resourceInfo.resource_category = "font";
    } else if (ext && videoExts.includes(ext)) {
      resourceInfo.resource_category = "video";
    } else {
      resourceInfo.resource_category = "other";
    }
  } else if (urltype === "exception") {
    resourceInfo.resource_category = "exception";
  }

  return resourceInfo;
}

// ======================================================================
// Prepare Request Headers
// ======================================================================

/**
 * Normalize request headers
 * - Exclude specific headers (Host, httpRequestNumber)
 * - Attach WAF bypass header (x-eo-re)
 *
 * @param inputHeaders - Raw headers from request
 * @returns Normalized headers
 */
export function prepareRequestHeaders(inputHeaders: unknown): StringRecord {
  const headers: StringRecord = {};

  if (typeof inputHeaders === "object" && inputHeaders !== null) {
    for (const [key, value] of Object.entries(inputHeaders)) {
      if (typeof value !== "string") continue;

      const lowerKey = key.toLowerCase();
      if (CONSTANTS.EO_IGNORED_HEADERS.includes(lowerKey)) continue;

      headers[key] = value;
    }
  }

  // Attach WAF bypass header
  headers[CONSTANTS.EO_HEADER_NAME] = CONSTANTS.EO_HEADER_VALUE;

  return headers;
}

// ======================================================================
// Headers to Record (Helper)
// ======================================================================

/**
 * Convert Headers object or StringRecord to StringRecord
 *
 * @param headers - Headers object, StringRecord, or null
 * @returns StringRecord
 */
function headersToRecord(
  headers: Headers | StringRecord | null | undefined,
): StringRecord {
  if (!headers) return {};
  if (headers instanceof Headers) {
    const record: StringRecord = {};
    headers.forEach((value, key) => {
      record[key] = value;
    });
    return record;
  }
  return headers;
}

// ======================================================================
// CDN Detection (Core capability)
// ======================================================================

/**
 * Detect CDN and cache status from response headers.
 *
 * Uses CDN_DETECTION_CONFIG to identify the CDN serving the response,
 * then looks up the corresponding cache status header.
 *
 * Matches RequestEngine/common/request_engine_core.py _detect_cdn()
 *
 * @param resHeaders - Response headers (StringRecord)
 * @returns CDN detection result
 */
function detectCdn(resHeaders: StringRecord): {
  "cdn-header-name": string | null;
  "cdn-header-value": string | null;
  "cdn-cache-status": string | null;
} {
  const headersLower: StringRecord = {};
  for (const [k, v] of Object.entries(resHeaders)) {
    headersLower[k.toLowerCase()] = v;
  }

  const result: {
    "cdn-header-name": string | null;
    "cdn-header-value": string | null;
    "cdn-cache-status": string | null;
  } = {
    "cdn-header-name": null,
    "cdn-header-value": null,
    "cdn-cache-status": null,
  };

  // Primary detection from CDN_DETECTION_CONFIG
  for (const [detectionHeader, cacheStatusHeader] of CDN_DETECTION_CONFIG) {
    if (detectionHeader in headersLower) {
      result["cdn-header-name"] = detectionHeader;
      result["cdn-header-value"] = headersLower[detectionHeader];
      if (cacheStatusHeader in headersLower) {
        result["cdn-cache-status"] = headersLower[cacheStatusHeader];
      }
      break;
    }
  }

  // Secondary: Server header checks (may override primary detection)
  const serverHeader = headersLower["server"] ?? "";

  // GCP CDN (Cloud CDN / Media CDN) detection
  if (serverHeader.toLowerCase().includes("google-edge-cache")) {
    result["cdn-header-name"] = "server";
    result["cdn-header-value"] = serverHeader;
    const cacheStatus =
      headersLower["cdn-cache-status"] ?? headersLower["cdn_cache_status"];
    if (cacheStatus) {
      result["cdn-cache-status"] = cacheStatus;
    }
  }

  // GCP CDN custom header
  if ("cdn_cache_status" in headersLower) {
    result["cdn-header-name"] = "cdn_cache_status";
    result["cdn-header-value"] = headersLower["cdn_cache_status"];
    result["cdn-cache-status"] = headersLower["cdn_cache_status"];
  }

  // Vercel Server header detection
  if (serverHeader.toLowerCase().includes("vercel")) {
    result["cdn-header-name"] = "server";
    result["cdn-header-value"] = serverHeader;
    if ("x-vercel-cache" in headersLower) {
      result["cdn-cache-status"] = headersLower["x-vercel-cache"];
    }
  }

  // Bunny CDN Server header detection
  if (serverHeader.toLowerCase().includes("bunnycdn")) {
    result["cdn-header-name"] = "server";
    result["cdn-header-value"] = serverHeader;
    if ("cdn-cache" in headersLower) {
      result["cdn-cache-status"] = headersLower["cdn-cache"];
    }
  }

  // Alibaba Cloud CDN (Tengine) Server header detection
  if (serverHeader.toLowerCase().includes("tengine")) {
    result["cdn-header-name"] = "server";
    result["cdn-header-value"] = serverHeader;
    if ("x-cache" in headersLower) {
      result["cdn-cache-status"] = headersLower["x-cache"];
    }
  }

  // Azure Front Door Via header detection
  const viaHeader = headersLower["via"] ?? "";
  if (viaHeader.toLowerCase().includes("azure")) {
    result["cdn-header-name"] = "via";
    result["cdn-header-value"] = viaHeader;
    if ("x-cache" in headersLower) {
      result["cdn-cache-status"] = headersLower["x-cache"];
    }
  }

  return result;
}

// ======================================================================
// Build Flat Result
// ======================================================================

/**
 * Build response in flat JSON structure
 * All keys are normalized to lowercase.
 *
 * Output key order matches RequestEngine/common/request_engine_core.py _build_flat_result()
 *
 * @param params - Execution result parameters
 * @returns Flat JSON object
 */
export function buildFlatResult(params: ExecutionResultParams): JsonRecord {
  const {
    statusCode,
    statusMessage,
    duration_ms,
    ttfb_ms,
    content_length_bytes,
    targetUrl,
    httpRequestNumber,
    httpRequestUUID,
    httpRequestRoundID,
    reqHeaders,
    respHeaders,
    extraError,
    area,
    executionId,
    requestStartTimestamp,
    requestEndTimestamp,
    redirectCount,
    resourceInfo,
  } = params;

  if (!area) {
    throw new Error("area parameter is required - must be passed from platform handler");
  }

  // Convert response headers to StringRecord for CDN detection and security analysis
  const respHeadersRecord = headersToRecord(respHeaders);

  const result: JsonRecord = {};

  // ==================================================================
  // 1. Basic HTTP Information
  // ==================================================================
  result["headers.general.status-code"] = statusCode;
  result["headers.general.status-message"] = statusMessage;
  result["headers.general.request-url"] = targetUrl;
  result["headers.general.http-request-method"] = "GET";

  // ==================================================================
  // 2. Request Identification Information
  // ==================================================================
  if (httpRequestNumber !== undefined && httpRequestNumber !== null) {
    result["eo.meta.http-request-number"] = httpRequestNumber;
  }
  if (httpRequestUUID !== undefined && httpRequestUUID !== null) {
    result["eo.meta.http-request-uuid"] = httpRequestUUID;
  }
  if (httpRequestRoundID !== undefined && httpRequestRoundID !== null) {
    result["eo.meta.http-request-round-id"] = httpRequestRoundID;
  }
  if (resourceInfo?.urltype !== undefined && resourceInfo.urltype !== null) {
    result["eo.meta.urltype"] = resourceInfo.urltype;
  }

  // ==================================================================
  // 3. Execution Environment / Timestamp Information
  // ==================================================================
  result["eo.meta.re-area"] = area;
  if (executionId !== undefined && executionId !== null) {
    result["eo.meta.execution-id"] = executionId;
  }
  if (requestStartTimestamp !== undefined && requestStartTimestamp !== null) {
    result["eo.meta.request-start-timestamp"] = requestStartTimestamp;
  }
  if (requestEndTimestamp !== undefined && requestEndTimestamp !== null) {
    result["eo.meta.request-end-timestamp"] = requestEndTimestamp;
  }

  // ==================================================================
  // 4. Protocol Information
  // ==================================================================
  result["eo.meta.http-protocol-version"] = PROTOCOL_UNAVAILABLE_MESSAGE;
  result["eo.meta.tls-version"] = PROTOCOL_UNAVAILABLE_MESSAGE;

  // ==================================================================
  // 5. CDN Detection (Core capability)
  //    Matches RequestEngine/common/request_engine_core.py _detect_cdn()
  // ==================================================================
  const cdnInfo = detectCdn(respHeadersRecord);
  if (cdnInfo["cdn-header-name"] !== null) {
    result["eo.meta.cdn-header-name"] = cdnInfo["cdn-header-name"];
    result["eo.meta.cdn-header-value"] = cdnInfo["cdn-header-value"];
  }
  if (cdnInfo["cdn-cache-status"] !== null) {
    result["eo.meta.cdn-cache-status"] = cdnInfo["cdn-cache-status"];
  }

  // ==================================================================
  // 6. Measurements
  //    Matches RequestEngine/common/request_engine_core.py _build_flat_result()
  // ==================================================================
  if (duration_ms !== undefined) {
    result["eo.meta.duration-ms"] = Math.round(duration_ms * 100) / 100;
  }
  if (ttfb_ms !== undefined) {
    result["eo.meta.ttfb-ms"] = Math.round(ttfb_ms * 100) / 100;
  }
  if (content_length_bytes !== undefined) {
    result["eo.meta.actual-content-length"] = content_length_bytes;
  }
  result["eo.meta.redirect-count"] = redirectCount ?? 0;

  // ==================================================================
  // 7. Extensions (eo.security.* etc.)
  //    Matches RequestEngine/common/request_engine_core.py build_extension_output()
  // ==================================================================
  const extensionContext: ExtensionContext = {
    targetUrl,
    resHeaders: respHeadersRecord,
  };

  for (const [, ext] of _EXTENSION_REGISTRY) {
    try {
      const rawOutput = ext.buildFunc(extensionContext);
      const sortedKeys = Object.keys(rawOutput).sort();
      for (const key of sortedKeys) {
        result[`${ext.prefix}${key}`] = rawOutput[key];
      }
    } catch (e) {
      result[`${ext.prefix}error`] = String(e);
    }
  }

  // ==================================================================
  // 8. Request Headers (sorted by key)
  // ==================================================================
  for (const key of Object.keys(reqHeaders).sort()) {
    result[`headers.request-headers.${key.toLowerCase()}`] = reqHeaders[key];
  }

  // ==================================================================
  // 9. Response Headers (sorted by key)
  // ==================================================================
  const respEntries = Object.entries(respHeadersRecord);
  respEntries.sort((a, b) => a[0].localeCompare(b[0]));
  for (const [key, value] of respEntries) {
    if (typeof value === "string") {
      result[`headers.response-headers.${key.toLowerCase()}`] = value;
    }
  }

  // ==================================================================
  // 10. Complement content-length header
  // ==================================================================
  if (content_length_bytes !== undefined) {
    const clKey = "headers.response-headers.content-length";
    if (!(clKey in result) || !result[clKey]) {
      result[clKey] = String(content_length_bytes);
    }
  }

  // ==================================================================
  // Error information (appended at the end if present)
  // ==================================================================
  if (extraError) {
    Object.assign(result, extraError);
  }

  return result;
}
