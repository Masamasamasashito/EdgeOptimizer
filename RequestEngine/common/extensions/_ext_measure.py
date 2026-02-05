# ----------------------------------------------------
# Edge Optimizer
# Extension: Measure (eo.measure.*)
# Crafted by Nishi Labo | https://4649-24.com
# ----------------------------------------------------
#
# This extension provides basic measurement metrics:
# - duration-ms: Total request execution time
# - ttfb-ms: Time To First Byte
# - actual-content-length: Response body size

EXTENSION_NAME = "measure"
EXTENSION_PREFIX = "eo.measure."


def build_output(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build measure extension output

    Args:
        context: Dictionary containing:
            - duration_ms: Total request execution time (milliseconds)
            - Initial_Response_ms: Time To First Byte (milliseconds)
            - content_length_bytes: Response body size (bytes)

    Returns:
        Dict[str, Any]: Measure metrics (without prefix)
    """
    output = {}

    duration_ms = context.get("duration_ms")
    if duration_ms is not None:
        output["duration-ms"] = round(duration_ms, 2)

    initial_response_ms = context.get("Initial_Response_ms")
    if initial_response_ms is not None:
        output["ttfb-ms"] = round(initial_response_ms, 2)

    content_length_bytes = context.get("content_length_bytes")
    if content_length_bytes is not None:
        output["actual-content-length"] = content_length_bytes

    return output


# Register this extension
register_extension(
    name=EXTENSION_NAME,
    prefix=EXTENSION_PREFIX,
    build_func=build_output,
    default_enabled=True,
)