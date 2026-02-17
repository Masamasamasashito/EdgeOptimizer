/**
 * ----------------------------------------------------------
 * Edge Optimizer
 * Extension: Security (eo.security.*)
 *
 * Crafted by Nishi Labo | https://4649-24.com
 * ----------------------------------------------------------
 *
 * This extension provides security header analysis:
 * - HTTPS detection
 * - HSTS (HTTP Strict Transport Security)
 * - CSP (Content Security Policy)
 * - X-Content-Type-Options
 * - X-Frame-Options
 * - X-XSS-Protection
 * - Referrer-Policy
 * - Permissions-Policy
 *
 * Matches RequestEngine/common/extensions/_ext_security.py
 */

import { registerExtension } from "../request_engine_core";
import type {
  JsonRecord,
  StringRecord,
  ExtensionContext,
} from "../../../cf/workers/ts/funcfiles/src/_01_types";

const EXTENSION_NAME = "security";
const EXTENSION_PREFIX = "eo.security.";

// Security header definitions (header name -> key name mapping)
const SECURITY_HEADERS: ReadonlyArray<readonly [string, string]> = [
  ["strict-transport-security", "hsts"],
  ["content-security-policy", "csp"],
  ["x-content-type-options", "x_content_type_options"],
  ["x-frame-options", "x_frame_options"],
  ["x-xss-protection", "x_xss_protection"],
  ["referrer-policy", "referrer_policy"],
];

// ======================================================================
// Analyze Security Headers
// ======================================================================

function analyzeSecurityHeaders(
  resHeaders: StringRecord,
  targetUrl: string,
): JsonRecord {
  const headersLower: StringRecord = {};
  for (const [k, v] of Object.entries(resHeaders)) {
    headersLower[k.toLowerCase()] = v;
  }

  const security: JsonRecord = {};
  security["is_https"] = targetUrl.startsWith("https://");

  // Check each security header
  for (const [headerName, keyPrefix] of SECURITY_HEADERS) {
    const headerValue = headersLower[headerName];
    security[`${keyPrefix}_present`] = headerValue !== undefined;
    if (headerValue) {
      security[`${keyPrefix}_value`] = headerValue;
    }
  }

  // Permissions-Policy (formerly Feature-Policy) - Special handling
  const permissionsPolicy =
    headersLower["permissions-policy"] ?? headersLower["feature-policy"];
  security["permissions_policy_present"] = permissionsPolicy !== undefined;
  if (permissionsPolicy) {
    security["permissions_policy_value"] = permissionsPolicy;
  }

  return security;
}

// ======================================================================
// Build Output (Extension interface)
// ======================================================================

function buildOutput(context: ExtensionContext): JsonRecord {
  const securityMetrics = analyzeSecurityHeaders(
    context.resHeaders,
    context.targetUrl,
  );
  // Return sorted output (matches Python: {k: v for k in sorted(...)})
  const sorted: JsonRecord = {};
  for (const key of Object.keys(securityMetrics).sort()) {
    sorted[key] = securityMetrics[key];
  }
  return sorted;
}

// Register this extension
registerExtension(EXTENSION_NAME, EXTENSION_PREFIX, buildOutput, true);
