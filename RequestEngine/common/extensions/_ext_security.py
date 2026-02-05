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