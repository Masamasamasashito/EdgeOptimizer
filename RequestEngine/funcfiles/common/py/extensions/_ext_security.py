# ----------------------------------------------------
# Edge Optimizer
# Extension: Security (eo.security.*)
# Crafted by Nishi Labo | https://4649-24.com
# ----------------------------------------------------
#
# This extension provides security header analysis:
# - HTTPS detection
# - HSTS (HTTP Strict Transport Security)
# - CSP (Content Security Policy)
# - X-Content-Type-Options
# - X-Frame-Options
# - X-XSS-Protection
# - Referrer-Policy
# - Permissions-Policy

EXTENSION_NAME = "security"
EXTENSION_PREFIX = "eo.security."


# ======================================================================
# Analyze Security Headers
# ======================================================================
def _analyze_security_headers(res_headers: Dict[str, str], target_url: str) -> Dict[str, Any]:
    """
    Analyze security headers and return metrics
    Included in Core Web Vitals / PageSpeed Insights / Security metrics
    """
    security = {}
    security["is_https"] = target_url.startswith("https://")

    headers_lower = {k.lower(): v for k, v in res_headers.items()}

    # Security header definitions (header name -> key name mapping)
    security_headers = {
        "strict-transport-security": "hsts",
        "content-security-policy": "csp",
        "x-content-type-options": "x_content_type_options",
        "x-frame-options": "x_frame_options",
        "x-xss-protection": "x_xss_protection",
        "referrer-policy": "referrer_policy",
    }

    # Check each security header
    for header_name, key_prefix in security_headers.items():
        header_value = headers_lower.get(header_name)
        security[f"{key_prefix}_present"] = header_value is not None
        if header_value:
            security[f"{key_prefix}_value"] = header_value

    # Permissions-Policy (formerly Feature-Policy) - Special handling
    permissions_policy = headers_lower.get("permissions-policy") or headers_lower.get("feature-policy")
    security["permissions_policy_present"] = permissions_policy is not None
    if permissions_policy:
        security["permissions_policy_value"] = permissions_policy

    return security


def build_output(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build security extension output

    Args:
        context: Dictionary containing:
            - res_headers: Response headers
            - target_url: Target URL

    Returns:
        Dict[str, Any]: Security metrics (without prefix)
    """
    res_headers = context.get("res_headers", {})
    target_url = context.get("target_url", "")

    # Use _analyze_security_headers function
    security_metrics = _analyze_security_headers(res_headers, target_url)

    # Return sorted output
    return {k: security_metrics[k] for k in sorted(security_metrics.keys())}


# Register this extension
register_extension(
    name=EXTENSION_NAME,
    prefix=EXTENSION_PREFIX,
    build_func=build_output,
    default_enabled=True,
)
