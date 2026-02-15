# ----------------------------------------------------
# Edge Optimizer
# Request Engine Core - Shared Code Module
# Crafted by Nishi Labo | https://4649-24.com
# ----------------------------------------------------
#
# This module contains shared code used by all Request Engine implementations:
# - AWS Lambda
# - Azure Functions
# - GCP Cloud Run
#
# Note: This file is merged with platform-specific handlers during deployment.
# Do NOT add platform-specific imports or code here.

# ======================================================================
# Configuration Constants
# ======================================================================

HTTP_REQUEST_TIMEOUT = 10  # HTTP request timeout (seconds)
# 10 seconds is sufficient for warmup purposes (reduced from 30 seconds for cost optimization)

# ======================================================================
# Retry Configuration
# ======================================================================
MAX_RETRY_ATTEMPTS = 2  # Maximum retry count (total 3 attempts including initial)
# Example: Initial + 2 retries = 3 total attempts

RETRY_INITIAL_DELAY = 0.5  # Initial retry delay (seconds)
# 1st retry: 0.5s wait

RETRY_BACKOFF_MULTIPLIER = 2.0  # Exponential backoff multiplier
# Retry interval calculation: delay = RETRY_INITIAL_DELAY * (RETRY_BACKOFF_MULTIPLIER ** attempt)
# Example: 1st: 0.5s, 2nd: 1.0s, 3rd: 2.0s

RETRYABLE_STATUS_CODES = {500, 502, 503, 504}  # HTTP status codes eligible for retry
# 5xx server errors are likely temporary issues, so they are retry targets
# 4xx client errors are not retry targets (retrying won't resolve them)


# ======================================================================
# CDN Detection Configuration
# ======================================================================
# Each entry: (detection_header, cache_status_header)
# detection_header: Header that identifies the CDN
# cache_status_header: Header that indicates cache HIT/MISS for that CDN
_CDN_DETECTION_CONFIG = [
    # Cloudflare
    ("cf-ray", "cf-cache-status"),
    # AWS CloudFront
    ("x-amz-cf-id", "x-cache"),
    # NitroCDN (NitroPack)
    ("x-nitro-cache", "x-nitro-cache"),
    ("x-nitro-cache-from", "x-nitro-cache"),
    ("x-nitro-rev", "x-nitro-cache"),
    # RabbitLoader
    ("x-rl-cache", "x-rl-cache"),
    ("x-rl-mode", "x-rl-cache"),
    ("x-rl-modified", "x-rl-cache"),
    ("x-rl-rule", "x-rl-cache"),
    # Azure Front Door
    ("x-azure-ref", "x-cache"),
    ("x-azure-fdid", "x-cache"),
    ("x-azure-clientip", "x-cache"),
    ("x-azure-socketip", "x-cache"),
    ("x-azure-requestchain", "x-cache"),
    # Akamai
    ("x-akamai-request-id", "x-cache"),
    ("x-cache-remote", "x-cache"),
    ("x-true-cache-key", "x-cache"),
    ("x-cache-key", "x-cache"),
    ("x-serial", "x-cache"),
    ("x-akamai-edgescape", "x-cache"),
    ("x-check-cacheable", "x-cache"),
    # Vercel
    ("x-vercel-cache", "x-vercel-cache"),
    ("x-vercel-id", "x-vercel-cache"),
    # Sakura Internet Web Accelerator (さくらウェブアクセラレータ)
    ("x-webaccel-origin-status", "x-cache"),
    # Bunny CDN
    ("cdn-pullzone", "cdn-cache"),
    ("cdn-uid", "cdn-cache"),
    ("cdn-requestid", "cdn-cache"),
    # Alibaba Cloud CDN
    ("eagleid", "x-cache"),
    ("x-swift-savetime", "x-cache"),
    ("x-swift-cachetime", "x-cache"),
    # CDNetworks
    ("x-cnc-request-id", "x-cache"),
    # KeyCDN
    ("x-pull", "x-cache"),
    ("x-edge-location", "x-cache"),
    # General / Fastly
    ("x-cache", "x-cache"),
    ("x-served-by", "x-cache"),
    ("x-fastly-request-id", "x-cache"),
]


# ======================================================================
# Extension Registry (拡張機能レジストリ)
# ======================================================================
# 拡張機能を登録・管理するためのレジストリ
# 各拡張機能は _ext_*.py ファイルで定義され、デプロイ時にマージされる
#
# 拡張機能の追加方法:
# 1. RequestEngine/common/extensions/_ext_<name>.py を作成
# 2. ファイル内で EXTENSION_NAME, EXTENSION_PREFIX, build_output() を定義
# 3. ファイル末尾で register_extension() を呼び出す
# 4. GitHub Actions のマージスクリプトに新しいファイルを追加

# 2階層の辞書形式で拡張機能を管理
_EXTENSION_REGISTRY: Dict[str, Dict[str, Any]] = {}

# EX

"""
_EXTENSION_REGISTRY = {
    # 1階層目: キーは「拡張機能の名前」(str)
    "security": {
        # 2階層目: キーは「属性名」(str)
        "prefix": "eo.security.",   # 出力時の接頭辞
        "build_func": _analyze_func, # 実行する関数
        "default_enabled": True      # フラグ
    }
}
"""


def register_extension(
    name: str,
    prefix: str,
    build_func: callable,
    default_enabled: bool = True,
) -> None:
    """
    拡張機能を登録する

    Args:
        name: 拡張機能名 (例: "security")
        prefix: 出力キーのプレフィックス (例: "eo.security.")
        build_func: 出力を生成する関数 (context: dict) -> dict
        default_enabled: デフォルトで有効かどうか
    """
    _EXTENSION_REGISTRY[name] = {
        "prefix": prefix,
        "build_func": build_func,
        "default_enabled": default_enabled,
    }


def get_registered_extensions() -> Dict[str, Dict[str, Any]]:
    """登録済み拡張機能の一覧を取得"""
    return _EXTENSION_REGISTRY.copy()


def build_extension_output(
    name: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    指定した拡張機能の出力を生成する

    Args:
        name: 拡張機能名
        context: 拡張機能に渡すコンテキスト

    Returns:
        Dict[str, Any]: 拡張機能の出力 (プレフィックス付きのキー)
    """
    if name not in _EXTENSION_REGISTRY:
        return {}

    ext = _EXTENSION_REGISTRY[name]
    try:
        raw_output = ext["build_func"](context)
        # プレフィックスを付けて返す
        prefix = ext["prefix"]
        return {f"{prefix}{k}": v for k, v in raw_output.items()}
    except Exception as e:
        logging.warning(f"Extension '{name}' failed: {str(e)}")
        return {f"{ext['prefix']}error": str(e)}


# ======================================================================
# Token Calculation (SHA-256)
# ======================================================================
def _calc_token(url: str, secret: str) -> str:
    """
    Calculate request token (SHA-256 hash)

    Used to verify against token generated by n8n workflow.
    Formula: SHA-256(url + request_secret)

    Args:
        url: Target URL
        secret: Request secret (retrieved from cloud secret manager)

    Returns:
        str: 64-character hexadecimal hash value (lowercase)

    Note:
        - n8n side uses N8N_EO_REQUEST_SECRET
        - Cloud side uses platform-specific secret key
        - Both values must be identical
    """
    return hashlib.sha256(f"{url}{secret}".encode()).hexdigest()


# ======================================================================
# Get HTTP Protocol Version
# ======================================================================
def _get_http_protocol_version(response: requests.Response) -> Optional[str]:
    """
    Get HTTP protocol version (HTTP/1.1, HTTP/2, HTTP/3, etc.)
    Returns error message with reason if determination is difficult
    """
    if not hasattr(response, 'raw') or response.raw is None:
        return "ERROR: Cannot determine HTTP protocol version. The response object does not have a 'raw' attribute or it is None. The 'raw' attribute is required to access the underlying HTTP version information."

    try:
        version = getattr(response.raw, 'version', None)
        if version is None:
            version = getattr(response.raw, '_http_version', None)
        if version:
            if version == 11:
                return "HTTP/1.1"
            elif version == 20:
                return "HTTP/2"
            elif version == 30:
                return "HTTP/3"
            elif isinstance(version, (int, float)):
                return f"HTTP/{version/10}"
            else:
                return str(version)
        else:
            return "ERROR: Cannot determine HTTP protocol version. The response.raw object does not have 'version' or '_http_version' attributes. These attributes are required to determine the HTTP protocol version, but they are not available in this response object."
    except AttributeError as e:
        return f"ERROR: Cannot determine HTTP protocol version due to AttributeError. Accessing the HTTP version attribute failed: {str(e)}. The response object structure may not match the expected format."
    except TypeError as e:
        return f"ERROR: Cannot determine HTTP protocol version due to TypeError. Type mismatch occurred while accessing the HTTP version: {str(e)}."
    except Exception as e:
        return f"ERROR: Cannot determine HTTP protocol version due to unexpected error ({type(e).__name__}): {str(e)}."


# ======================================================================
# Get TLS Version
# ======================================================================
def _get_tls_version(response: requests.Response, target_url: str) -> Optional[str]:
    """
    Get TLS version
    Returns value with reason on failure
    """
    if not target_url.startswith("https://"):
        return "unknown: not_https"
    if not hasattr(response, 'raw') or response.raw is None:
        return "unknown: response_raw_not_available"

    try:
        connection = getattr(response.raw, '_connection', None)
        if connection is None:
            return "unknown: connection_not_found"

        sock = getattr(connection, 'sock', None)
        if sock is None:
            return "unknown: sock_not_found"
        if not isinstance(sock, ssl.SSLSocket):
            return f"unknown: sock_not_ssl (type: {type(sock).__name__})"

        try:
            ssl_version_str = sock.version()
            tls_version_map = {
                'TLSv1': 'TLSv1.0',
                'TLSv1.1': 'TLSv1.1',
                'TLSv1.2': 'TLSv1.2',
                'TLSv1.3': 'TLSv1.3',
            }
            for key, value in tls_version_map.items():
                if key in ssl_version_str:
                    return value
            if ssl_version_str:
                return ssl_version_str
            return "unknown: version_string_empty"
        except AttributeError as e:
            return f"unknown: version_method_failed (AttributeError: {str(e)})"
        except TypeError as e:
            return f"unknown: version_method_failed (TypeError: {str(e)})"
        except Exception as e:
            return f"unknown: version_method_failed (Exception: {type(e).__name__}: {str(e)})"
    except AttributeError as e:
        return f"unknown: connection_access_failed (AttributeError: {str(e)})"
    except TypeError as e:
        return f"unknown: connection_access_failed (TypeError: {str(e)})"
    except Exception as e:
        return f"unknown: connection_access_failed (Exception: {type(e).__name__}: {str(e)})"


# ======================================================================
# CDN Detection (Core capability)
# ======================================================================
def _detect_cdn(res_headers: Dict[str, str]) -> Dict[str, Optional[str]]:
    """
    Detect CDN and cache status from response headers.

    Uses _CDN_DETECTION_CONFIG to identify the CDN serving the response,
    then looks up the corresponding cache status header.

    Args:
        res_headers: Response headers

    Returns:
        Dict with keys:
            - "cdn-header-name": Detected CDN header name (or None)
            - "cdn-header-value": Detected CDN header value (or None)
            - "cdn-cache-status": Cache status value (or None)
    """
    headers_lower = {k.lower(): v for k, v in res_headers.items()}

    result = {
        "cdn-header-name": None,
        "cdn-header-value": None,
        "cdn-cache-status": None,
    }

    # Primary detection from _CDN_DETECTION_CONFIG
    for detection_header, cache_status_header in _CDN_DETECTION_CONFIG:
        if detection_header in headers_lower:
            result["cdn-header-name"] = detection_header
            result["cdn-header-value"] = headers_lower[detection_header]
            if cache_status_header in headers_lower:
                result["cdn-cache-status"] = headers_lower[cache_status_header]
            break

    # Secondary: Server header checks (may override primary detection)
    server_header = headers_lower.get("server", "")

    # GCP CDN (Cloud CDN / Media CDN) detection
    if "google-edge-cache" in server_header.lower():
        result["cdn-header-name"] = "server"
        result["cdn-header-value"] = server_header
        cache_status = headers_lower.get("cdn-cache-status") or headers_lower.get("cdn_cache_status")
        if cache_status:
            result["cdn-cache-status"] = cache_status

    # GCP CDN custom header
    if "cdn_cache_status" in headers_lower:
        result["cdn-header-name"] = "cdn_cache_status"
        result["cdn-header-value"] = headers_lower["cdn_cache_status"]
        result["cdn-cache-status"] = headers_lower["cdn_cache_status"]

    # Vercel Server header detection
    if "vercel" in server_header.lower():
        result["cdn-header-name"] = "server"
        result["cdn-header-value"] = server_header
        if "x-vercel-cache" in headers_lower:
            result["cdn-cache-status"] = headers_lower["x-vercel-cache"]

    # Bunny CDN Server header detection
    if "bunnycdn" in server_header.lower():
        result["cdn-header-name"] = "server"
        result["cdn-header-value"] = server_header
        if "cdn-cache" in headers_lower:
            result["cdn-cache-status"] = headers_lower["cdn-cache"]

    # Alibaba Cloud CDN (Tengine) Server header detection
    if "tengine" in server_header.lower():
        result["cdn-header-name"] = "server"
        result["cdn-header-value"] = server_header
        if "x-cache" in headers_lower:
            result["cdn-cache-status"] = headers_lower["x-cache"]

    # Azure Front Door Via header detection
    via_header = headers_lower.get("via", "")
    if "azure" in via_header.lower():
        result["cdn-header-name"] = "via"
        result["cdn-header-value"] = via_header
        if "x-cache" in headers_lower:
            result["cdn-cache-status"] = headers_lower["x-cache"]

    return result


# ======================================================================
# Retryable Error Determination
# ======================================================================
def _is_retryable_error(exception: Exception, status_code: Optional[int] = None) -> bool:
    """
    Determine if error is retryable
    Temporary errors (network errors, server errors, etc.) are retry targets.
    """
    if isinstance(exception, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True

    if status_code and status_code in RETRYABLE_STATUS_CODES:
        return True

    if isinstance(exception, requests.exceptions.HTTPError):
        if status_code and status_code in RETRYABLE_STATUS_CODES:
            return True

    return False


# ======================================================================
# HTTP Request Execution (with Retry)
# ======================================================================
def _execute_http_request_with_retry(
    target_url: str,
    headers: Dict[str, str],
) -> Tuple[requests.Response, Dict[str, Any]]:
    """
    Execute HTTP request with retry (stream=True)
    Automatically retry for temporary errors.

    Note: stream=True makes requests.get() return when response headers are received
    (before body download). This enables accurate TTFB measurement in the caller.
    The caller MUST consume the body (response.content) and close the response.
    """
    retry_info = {
        "retry_attempts": 0,
        "retry_delays": [],
        "last_error": None,
    }

    last_exception = None
    last_response = None

    for attempt in range(MAX_RETRY_ATTEMPTS + 1):
        try:
            response = requests.get(
                target_url,
                headers=headers,
                timeout=HTTP_REQUEST_TIMEOUT,
                allow_redirects=True,
                stream=True,
            )

            status_code = response.status_code

            if status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRY_ATTEMPTS:
                last_response = response
                response.close()
                delay = RETRY_INITIAL_DELAY * (RETRY_BACKOFF_MULTIPLIER ** attempt)
                retry_info["retry_delays"].append(delay)
                time.sleep(delay)
                retry_info["retry_attempts"] += 1
                logging.warning(f"Retry attempt {retry_info['retry_attempts']} for status {status_code}")
                continue

            retry_info["retry_attempts"] = attempt
            return response, retry_info

        except requests.exceptions.RequestException as e:
            last_exception = e
            retry_info["last_error"] = str(e)

            if _is_retryable_error(e) and attempt < MAX_RETRY_ATTEMPTS:
                delay = RETRY_INITIAL_DELAY * (RETRY_BACKOFF_MULTIPLIER ** attempt)
                retry_info["retry_delays"].append(delay)
                time.sleep(delay)
                retry_info["retry_attempts"] += 1
                continue
            else:
                raise

    if last_response: last_response.close()
    if last_exception: raise last_exception
    raise RuntimeError("Maximum retry attempts reached")


# ======================================================================
# Build Flat Result
# ======================================================================
def _build_flat_result(
    *,
    status_code: int,
    status_message: str,
    duration_ms: float,
    Initial_Response_ms: Optional[float] = None,
    content_length_bytes: Optional[int] = None,
    target_url: str,
    http_request_number: Optional[Any] = None,
    http_request_uuid: Optional[str] = None,
    http_request_round_id: Optional[int] = None,
    req_headers: Dict[str, str],
    res_headers: Dict[str, str],
    tls_version: Optional[str] = None,
    http_protocol_version: Optional[str] = None,
    request_start_timestamp: Optional[float] = None,
    request_end_timestamp: Optional[float] = None,
    execution_id: Optional[str] = None,
    area: Optional[str] = None,
    redirect_count: int = 0,
    urltype: Optional[str] = None,
    retry_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build response in flat JSON structure (Pure HTTP Focus)
    All keys are normalized to lowercase.
    """
    if not area:
        raise RuntimeError("area parameter is required - must be passed from platform handler")

    protocol_value = http_protocol_version or "unknown"
    tls_version_value = tls_version or "unknown"

    ordered_result = {}

    # ==================================================================
    # 1. Basic HTTP Information
    # ==================================================================
    ordered_result["headers.general.status-code"] = status_code
    ordered_result["headers.general.status-message"] = status_message
    ordered_result["headers.general.request-url"] = target_url
    ordered_result["headers.general.http-request-method"] = "GET"

    # ==================================================================
    # 2. Request Identification Information
    # ==================================================================
    if http_request_number is not None:
        ordered_result["eo.meta.http-request-number"] = http_request_number
    if http_request_uuid is not None:
        ordered_result["eo.meta.http-request-uuid"] = http_request_uuid
    if http_request_round_id is not None:
        ordered_result["eo.meta.http-request-round-id"] = http_request_round_id
    if urltype is not None:
        ordered_result["eo.meta.urltype"] = urltype

    # ==================================================================
    # 3. Execution Environment / Timestamp Information
    # ==================================================================
    ordered_result["eo.meta.re-area"] = area
    if execution_id is not None:
        ordered_result["eo.meta.execution-id"] = execution_id
    if request_start_timestamp is not None:
        ordered_result["eo.meta.request-start-timestamp"] = request_start_timestamp
    if request_end_timestamp is not None:
        ordered_result["eo.meta.request-end-timestamp"] = request_end_timestamp

    # ==================================================================
    # 4. Protocol Information
    # ==================================================================
    ordered_result["eo.meta.http-protocol-version"] = protocol_value
    ordered_result["eo.meta.tls-version"] = tls_version_value

    # ==================================================================
    # 5. CDN Detection (Core capability)
    # ==================================================================
    cdn_info = _detect_cdn(res_headers)
    if cdn_info["cdn-header-name"] is not None:
        ordered_result["eo.meta.cdn-header-name"] = cdn_info["cdn-header-name"]
        ordered_result["eo.meta.cdn-header-value"] = cdn_info["cdn-header-value"]
    if cdn_info["cdn-cache-status"] is not None:
        ordered_result["eo.meta.cdn-cache-status"] = cdn_info["cdn-cache-status"]

    # ==================================================================
    # 6. Measurements
    # ==================================================================
    if duration_ms is not None:
        ordered_result["eo.meta.duration-ms"] = round(duration_ms, 2)
    if Initial_Response_ms is not None:
        ordered_result["eo.meta.ttfb-ms"] = round(Initial_Response_ms, 2)
    if content_length_bytes is not None:
        ordered_result["eo.meta.actual-content-length"] = content_length_bytes
    ordered_result["eo.meta.redirect-count"] = redirect_count
    if retry_info:
        ordered_result["eo.meta.retry-attempts"] = retry_info.get("retry_attempts", 0)
        if retry_info.get("retry_delays"):
            ordered_result["eo.meta.retry-delays-ms"] = [round(d * 1000, 2) for d in retry_info.get("retry_delays", [])]
        if retry_info.get("last_error"):
            ordered_result["eo.meta.retry-last-error"] = retry_info.get("last_error")

    # ==================================================================
    # 7. Extensions (eo.security.* etc.)
    # ==================================================================
    extension_context = {
        "target_url": target_url,
        "res_headers": res_headers,
    }

    for ext_name in _EXTENSION_REGISTRY:
        ext_output = build_extension_output(ext_name, extension_context)
        ordered_result.update(ext_output)

    # ==================================================================
    # 8. Request Headers
    # ==================================================================
    for key in sorted(req_headers.keys()):
        ordered_result[f"headers.request-headers.{key.lower()}"] = req_headers[key]

    # ==================================================================
    # 9. Response Headers
    # ==================================================================
    for key in sorted(res_headers.keys()):
        ordered_result[f"headers.response-headers.{key.lower()}"] = res_headers[key]

    return ordered_result
