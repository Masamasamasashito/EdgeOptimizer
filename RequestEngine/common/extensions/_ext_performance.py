# ----------------------------------------------------
# Edge Optimizer
# Extension: Performance (eo.performance.*)
# Crafted by Nishi Labo | https://4649-24.com
# ----------------------------------------------------
#
# This extension provides performance metrics:
# - CDN detection
# - Cache information
# - Retry information

EXTENSION_NAME = "performance"
EXTENSION_PREFIX = "eo.performance."


def build_output(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build performance extension output

    Args:
        context: Dictionary containing:
            - Initial_Response_ms: Time To First Byte (milliseconds)
            - content_length_bytes: Response body size (bytes)
            - res_headers: Response headers
            - redirect_count: Number of redirects
            - resource_info: Resource information
            - retry_info: Retry information

    Returns:
        Dict[str, Any]: Performance metrics (without prefix)
    """
    output = {}

    # Get performance metrics from _get_performance_metrics
    performance_metrics = _get_performance_metrics(
        Initial_Response_ms=context.get("Initial_Response_ms"),
        content_length_bytes=context.get("content_length_bytes"),
        res_headers=context.get("res_headers", {}),
        redirect_count=context.get("redirect_count", 0),
        resource_info=context.get("resource_info"),
        retry_info=context.get("retry_info"),
    )

    # Resource information (first)
    resource_keys = ["resource_urltype", "resource_extension", "resource_category"]
    for key in resource_keys:
        if key in performance_metrics:
            output[key] = performance_metrics.pop(key)

    # TTFB (Initial_Response_ms)
    if "Initial_Response_ms" in performance_metrics:
        output["ttfb_ms"] = performance_metrics.pop("Initial_Response_ms")

    # Redirect count
    if "redirect_count" in performance_metrics:
        output["redirect_count"] = performance_metrics.pop("redirect_count")

    # Content information
    content_keys = ["content_size_bytes", "content_length_header", "content_encoding", "html_encoding"]
    for key in content_keys:
        if key in performance_metrics:
            output[key] = performance_metrics.pop(key)

    # Cache information
    cache_keys = [k for k in list(performance_metrics.keys()) if k in ("cache_control", "etag", "last_modified")]
    for key in sorted(cache_keys):
        output[key] = performance_metrics.pop(key)

    # CDN information
    cdn_keys = [k for k in list(performance_metrics.keys()) if k.startswith("cdn_")]
    for key in sorted(cdn_keys):
        output[key] = performance_metrics.pop(key)

    # Retry information
    retry_keys = [k for k in list(performance_metrics.keys()) if k.startswith("retry_")]
    for key in sorted(retry_keys):
        output[key] = performance_metrics.pop(key)

    # Remaining metrics
    for key in sorted(performance_metrics.keys()):
        output[key] = performance_metrics[key]

    return output


# Register this extension
register_extension(
    name=EXTENSION_NAME,
    prefix=EXTENSION_PREFIX,
    build_func=build_output,
    default_enabled=True,
)