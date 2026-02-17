/**
 * ----------------------------------------------------------
 * Edge Optimizer
 * Request Engine for Cloudflare Workers - Type Definitions
 *
 * Crafted by Nishi Labo | https://4649-24.com
 * ----------------------------------------------------------
 */

// Generic object types used throughout the application
export type JsonRecord = Record<string, unknown>;
export type StringRecord = Record<string, string>;

// Cloudflare Workers environment bindings
export interface Env {
  CFWORKER_REQUEST_SECRET: string;
}

// Resource information (from URL type and extension analysis)
// Matches RequestEngine/common/py/request_engine_core.py _determine_resource_type() output
export interface ResourceInfo {
  urltype: string | null;
  url_extension: string | null;
  resource_category: string | null;
}

// Normalized request data structure
export interface WarmupRequest {
  targetUrl: string;
  tokenCalculatedByN8n: string;
  headers: StringRecord;
  httpRequestNumber: string | number;
  httpRequestUUID: string | null;
  httpRequestRoundID: number | null;
  urltype: string | null;
}

// Parameters for building flat JSON result
// Matches RequestEngine/common/py/request_engine_core.py _build_flat_result() signature
export interface ExecutionResultParams {
  statusCode: number;
  statusMessage: string;
  duration_ms: number;
  ttfb_ms?: number;
  content_length_bytes?: number;
  targetUrl: string;
  httpRequestNumber: string | number;
  httpRequestUUID?: string | null;
  httpRequestRoundID?: number | null;
  reqHeaders: StringRecord;
  respHeaders?: Headers | StringRecord | null;
  extraError?: JsonRecord | null;
  area: string;
  executionId?: string | null;
  requestStartTimestamp?: number | null;
  requestEndTimestamp?: number | null;
  redirectCount?: number;
  resourceInfo?: ResourceInfo | null;
}

// Extension context passed to extension build functions
// Matches Python: context = {"target_url": ..., "res_headers": ...}
export interface ExtensionContext {
  targetUrl: string;
  resHeaders: StringRecord;
}

// Extension build function signature
export type ExtensionBuildFunc = (context: ExtensionContext) => JsonRecord;

// Extension configuration stored in the registry
export interface ExtensionConfig {
  prefix: string;
  buildFunc: ExtensionBuildFunc;
  defaultEnabled: boolean;
}

// Error context state (information preserved when an error occurs)
export interface ExecutionContextState extends Partial<ExecutionResultParams> {
  area: string;
  duration_ms: number;
}

// Error reason definitions
export type ErrorReason =
  | "empty_event_list"
  | "invalid_event_type"
  | "missing_url"
  | "missing_secret"
  | "missing_token"
  | "invalid_token"
  | "request_exception";
