# ----------------------------------------------------
# Edge Optimizer
# Request Engine for GCP Cloud Run - Platform-Specific Handler
# Crafted by Nishi Labo | https://4649-24.com
# ----------------------------------------------------
#
# EO Request Engine for GCP Cloud Run asia-northeast1 region
# * Overview:
# Executes HTTP requests to specified URLs to warm up the GCP Cloud Run cache.
# Returns results in a flat JSON structure (supporting TTFB/BodySize measurements).
#
# * Input:
# - HTTP Method: POST (GET is not implemented)
# - JSON Body: { targetUrl, tokenCalculatedByN8n, headersForTargetUrl, httpRequestNumber, httpRequestUUID, httpRequestRoundID }
#   * targetUrl: Target URL to warm up (required)
#   * tokenCalculatedByN8n: SHA-256(url + request secret) calculated in n8n using EO_Infra_Docker/.env N8N_EO_REQUEST_SECRET (required)
#   * headersForTargetUrl: Optional custom headers for target URL request (object)
#   * httpRequestNumber: Optional request sequence number
#   * httpRequestUUID: Optional UUID for each request (created by n8n)
#   * httpRequestRoundID: Optional UNIX timestamp when the first request of a round reaches 215 Add httpRequestRoundID (created by n8n)
# - Actual usage: n8n workflow (EOn8nWorkflowJson/eo-n8n-workflow-jp.json) sends POST with JSON body
#
# * Dependencies:
# - GCP Secret Manager (env.EO_GCP_PROJECT_ID) - GCP Project ID
# - GCP Secret Manager Secret Name: eo-re-d01-secretmng (CLOUDRUN_REQUEST_SECRET_NAME)
# - GCP Secret Manager Secret Key: CLOUDRUN_REQUEST_SECRET (CLOUDRUN_REQUEST_SECRET_KEY_NAME)
#
# * Note:
# GCP Cloud Run uses OAuth2 Bearer authentication, so n8n workflow uses
# 230 data Keeper for GCP, 235 Get IDtoken From GCP Service Account Access Token,
# 240 IDtoken to json, 245 data and GCP IDtoken Merger nodes before reaching
# 280 GCP-ane1 RequestEngine Oauth2 Bearer node.

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================================================
# Flask Application
# ======================================================================
app = Flask(__name__)

# ======================================================================
# GCP Secret Manager Configuration
# ======================================================================
CLOUDRUN_REQUEST_SECRET_NAME = os.environ.get("CLOUDRUN_REQUEST_SECRET_NAME", "eo-re-d01-secretmng")
CLOUDRUN_REQUEST_SECRET_KEY_NAME = os.environ.get("CLOUDRUN_REQUEST_SECRET_KEY_NAME", "CLOUDRUN_REQUEST_SECRET")

# ======================================================================
# EO Identification Header
# ======================================================================
EO_HEADER_NAME = "x-eo-re"
EO_HEADER_VALUE = "gcp"

# ======================================================================
# Endpoint Configuration
# ======================================================================
CLOUDRUN_ENDPOINT_PATH = "/requestengine_tail"

# ======================================================================
# Global Variables
# ======================================================================
_cached_secretmng_requestsecret_value: Optional[str] = None
# Cache for GCP Secret Manager secret (CLOUDRUN_REQUEST_SECRET) value
# Retrieved on first request, subsequent requests use cached value


# ======================================================================
# Get Secret from GCP Secret Manager (retrieved once, cached thereafter)
# ======================================================================
def _get_secretmng_requestsecret_value() -> str:
    """
    Get secret key (CLOUDRUN_REQUEST_SECRET) value from GCP Secret Manager

    Retrieved from GCP Secret Manager on first call, uses cache thereafter.
    This reduces Secret Manager access count, optimizing performance and cost.

    Returns:
        str: Secret key value (value of CLOUDRUN_REQUEST_SECRET)

    Raises:
        RuntimeError: In following cases:
            - EO_GCP_PROJECT_ID environment variable is not set
            - Secret Manager access failed (insufficient permissions, non-existent secret, etc.)
            - SecretString is empty
            - SecretString is not valid JSON
            - Secret key does not exist
            - Secret key value is empty or not a string
    """
    global _cached_secretmng_requestsecret_value
    if _cached_secretmng_requestsecret_value is not None:
        return _cached_secretmng_requestsecret_value

    project_id = os.environ.get("EO_GCP_PROJECT_ID")
    if not project_id:
        raise RuntimeError("Environment variable 'EO_GCP_PROJECT_ID' is not set.")

    try:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{project_id}/secrets/{CLOUDRUN_REQUEST_SECRET_NAME}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        secret_string = response.payload.data.decode("UTF-8")
    except Exception as e:
        raise RuntimeError(f"Failed to get secret value: {e}") from e

    if not secret_string:
        raise RuntimeError(f"SecretString is empty for secret: {CLOUDRUN_REQUEST_SECRET_NAME}")

    # Parse JSON format if applicable (same logic as AWS Lambda)
    try:
        secret_json = json.loads(secret_string)
        if isinstance(secret_json, dict) and CLOUDRUN_REQUEST_SECRET_KEY_NAME in secret_json:
            secret_string = secret_json[CLOUDRUN_REQUEST_SECRET_KEY_NAME]
            if not isinstance(secret_string, str) or not secret_string:
                raise RuntimeError(
                    f"Secret '{CLOUDRUN_REQUEST_SECRET_NAME}' field '{CLOUDRUN_REQUEST_SECRET_KEY_NAME}' is empty or not a string"
                )
    except json.JSONDecodeError:
        # If not JSON, use as plain text
        pass

    _cached_secretmng_requestsecret_value = secret_string
    return secret_string


# ======================================================================
# Get GCP Region
# ======================================================================
def _get_gcp_region() -> str:
    """
    Get GCP region from metadata server or environment variable

    Returns:
        str: GCP region (e.g., "asia-northeast1") or "gcp-unknown" if not available
    """
    region = None

    # Try to get from metadata server
    try:
        url = "http://metadata.google.internal/computeMetadata/v1/instance/region"
        resp = requests.get(url, headers={"Metadata-Flavor": "Google"}, timeout=2)
        if resp.status_code == 200:
            # Format: projects/12345/regions/asia-northeast1
            region = resp.text.split('/')[-1]
    except Exception:
        pass

    # Fallback to environment variable
    if not region:
        region = os.environ.get("GCP_REGION") or "gcp-unknown"

    return region


# ======================================================================
# Main Function (Flask Handler)
# ======================================================================
@app.route(CLOUDRUN_ENDPOINT_PATH, methods=["GET", "POST"])
def requestengine_tail():
    """
    GCP Cloud Run main handler (Flask endpoint)

    Process HTTP requests sent from n8n workflow, execute HTTP requests to target URLs,
    measure/analyze performance metrics, and return results in flat JSON structure.

    Returns:
        Flask Response: JSON response
            - On success: HTTP status code 200, includes performance metrics
            - On error: Appropriate HTTP status code, includes error message

    Note:
        - Authentication: Verify token parameter against GCP Secret Manager secret
        - Retry: Automatic retry for temporary errors (up to 3 times)
        - Memory protection: Skip analysis for content exceeding 5MB
    """
    start_time = time.time()

    # Get GCP region and convert to short name
    gcp_region = _get_gcp_region()
    gcp_region_display = gcp_region

    try:
        # ==================================================================
        # Receive request from n8n HttpRequest node (Request Engine node)
        # ==================================================================
        # JSON parse and data extraction
        try:
            body_json = request.get_json() or {}
        except Exception:
            body_json = {}

        # ==================================================================
        # Normalize event format
        # ==================================================================
        # Note: Event normalization (array handling, type validation) is NOT in common/
        # because error response format differs per platform:
        # - AWS Lambda: return dict
        # - Azure Functions: return func.HttpResponse(...)
        # - GCP Cloud Run: return jsonify(...), status_code

        # If body_json is array format, extract first element
        if isinstance(body_json, list):
            if len(body_json) == 0:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                result = _build_flat_result(
                    status_code=400,
                    status_message="EMPTY_EVENT_LIST",
                    duration_ms=duration_ms,
                    target_url="",
                    http_request_number=None,
                    req_headers={},
                    res_headers={},
                    request_start_timestamp=start_time,
                    request_end_timestamp=end_time,
                    execution_id=None,
                    area=gcp_region_display,
                )
                return jsonify(result), 400
            body_json = body_json[0]

        # Return error if body_json is not dictionary format
        if not isinstance(body_json, dict):
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            result = _build_flat_result(
                status_code=400,
                status_message="INVALID_EVENT_TYPE",
                duration_ms=duration_ms,
                target_url="",
                http_request_number=None,
                req_headers={},
                res_headers={},
                request_start_timestamp=start_time,
                request_end_timestamp=end_time,
                execution_id=None,
                area=gcp_region_display,
            )
            return jsonify(result), 400

        data = body_json

        # ==================================================================
        # Extract request data
        # ==================================================================
        target_url = data.get("targetUrl") or ""
        n8n_requestsecret_token = data.get("tokenCalculatedByN8n")
        http_request_number = data.get("httpRequestNumber")
        http_request_uuid = data.get("httpRequestUUID")
        http_request_round_id = data.get("httpRequestRoundID")
        urltype = data.get("urltype")
        input_headers = data.get("headersForTargetUrl") if isinstance(data.get("headersForTargetUrl"), dict) else {}

        # Get User-Agent header
        ua_from_request_headers = input_headers.get("User-Agent") or ""

        # ==================================================================
        # URL Validation
        # ==================================================================
        if not target_url:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            result = _build_flat_result(
                status_code=400,
                status_message="MISSING_URL",
                duration_ms=duration_ms,
                target_url="",
                http_request_number=http_request_number,
                http_request_uuid=http_request_uuid,
                http_request_round_id=http_request_round_id,
                req_headers={},
                res_headers={},
                request_start_timestamp=start_time,
                request_end_timestamp=end_time,
                execution_id=None,
                urltype=urltype,
                area=gcp_region_display,
            )
            return jsonify(result), 400

        # ==================================================================
        # Verify n8n-generated token against token generated from GCP Secret Manager secret
        # ==================================================================
        try:
            secretmng_requestsecret_value = _get_secretmng_requestsecret_value()
            tokenCalculatedByCloudSecret = _calc_token(target_url, secretmng_requestsecret_value)
            if n8n_requestsecret_token == tokenCalculatedByCloudSecret:
                # Token verification successful: continue processing
                pass
            else:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                result = _build_flat_result(
                    status_code=401,
                    status_message="INVALID_TOKEN",
                    duration_ms=duration_ms,
                    target_url=target_url,
                    http_request_number=http_request_number,
                    http_request_uuid=http_request_uuid,
                    http_request_round_id=http_request_round_id,
                    req_headers={},
                    res_headers={},
                    request_start_timestamp=start_time,
                    request_end_timestamp=end_time,
                    execution_id=None,
                    urltype=urltype,
                    area=gcp_region_display,
                )
                return jsonify(result), 401
        except Exception as e:
            logger.error(f"Request Secret validation failed: {str(e)}")
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            result = _build_flat_result(
                status_code=500,
                status_message="SECRET_FETCH_FAILED",
                duration_ms=duration_ms,
                target_url=target_url,
                http_request_number=http_request_number,
                http_request_uuid=http_request_uuid,
                http_request_round_id=http_request_round_id,
                req_headers={},
                res_headers={},
                request_start_timestamp=start_time,
                request_end_timestamp=end_time,
                execution_id=None,
                urltype=urltype,
                area=gcp_region_display,
            )
            return jsonify(result), 500

        # ==================================================================
        # Prepare request headers
        # ==================================================================
        req_headers: Dict[str, str] = dict(input_headers)
        # Set User-Agent if specified
        if ua_from_request_headers:
            req_headers.setdefault("User-Agent", ua_from_request_headers)
        # Add EO identification header
        req_headers[EO_HEADER_NAME] = EO_HEADER_VALUE

        # ==================================================================
        # Execute HTTP request (with retry)
        # ==================================================================
        # stream=True makes requests.get() return at headers-received (before body download)
        http_request_start_time = time.time()
        try:
            # ==================================================================
            # Send HTTP request to Warmup Target URL
            # ==================================================================
            response, retry_info = _execute_http_request_with_retry(
                target_url,
                req_headers,
            )

            with response:
                # ==================================================================
                # TTFB measurement (stream=True: headers already received, body not yet downloaded)
                # ==================================================================
                ttfb_end = time.time()
                Initial_Response_ms = (ttfb_end - http_request_start_time) * 1000

                # ==================================================================
                # Get HTTP protocol version (connection still open with stream=True)
                # ==================================================================
                http_protocol_version = _get_http_protocol_version(response)

                # ==================================================================
                # Get TLS version (connection still open with stream=True)
                # ==================================================================
                tls_version = _get_tls_version(response, target_url)

                # ==================================================================
                # Get response headers
                # ==================================================================
                res_headers = dict(response.headers)

                # ==================================================================
                # Get redirect count
                # ==================================================================
                redirect_count = len(response.history) if hasattr(response, 'history') else 0

                # ==================================================================
                # Download body (cache warmup) and measure actual content length
                # ==================================================================
                body_content = response.content
                content_length = len(body_content)

                # ==================================================================
                # Build result
                # ==================================================================
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                # ==================================================================
                # Return warmup result data to n8n HttpRequest node
                # ==================================================================
                result = _build_flat_result(
                    status_code=response.status_code,
                    status_message=response.reason or "OK",
                    duration_ms=duration_ms,
                    Initial_Response_ms=Initial_Response_ms,
                    content_length_bytes=content_length,
                    target_url=target_url,
                    http_request_number=http_request_number,
                    http_request_uuid=http_request_uuid,
                    http_request_round_id=http_request_round_id,
                    req_headers=req_headers,
                    res_headers=res_headers,
                    tls_version=tls_version,
                    http_protocol_version=http_protocol_version,
                    request_start_timestamp=http_request_start_time,
                    request_end_timestamp=end_time,
                    execution_id=None,
                    redirect_count=redirect_count,
                    urltype=urltype,
                    retry_info=retry_info,
                    area=gcp_region_display,
                )
                return jsonify(result), 200

        # ==================================================================
        # Error Handling
        # ==================================================================
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            result = _build_flat_result(
                status_code=500,
                status_message=f"Request failed: {str(e)}",
                duration_ms=duration_ms,
                target_url=target_url,
                http_request_number=http_request_number,
                http_request_uuid=http_request_uuid,
                http_request_round_id=http_request_round_id,
                req_headers=req_headers,
                res_headers={},
                request_start_timestamp=http_request_start_time if "http_request_start_time" in locals() else None,
                request_end_timestamp=end_time,
                execution_id=None,
                redirect_count=0,
                urltype=urltype if "urltype" in locals() else None,
                retry_info=retry_info if "retry_info" in locals() else None,
                area=gcp_region_display,
            )
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        error_target_url = target_url if "target_url" in locals() else ""
        result = _build_flat_result(
            status_code=500,
            status_message=f"Internal error: {str(e)}",
            duration_ms=duration_ms,
            target_url=error_target_url,
            http_request_number=http_request_number if "http_request_number" in locals() else None,
            http_request_uuid=http_request_uuid if "http_request_uuid" in locals() else None,
            http_request_round_id=http_request_round_id if "http_request_round_id" in locals() else None,
            req_headers=input_headers if "input_headers" in locals() else {},
            res_headers={},
            request_start_timestamp=start_time if "start_time" in locals() else None,
            request_end_timestamp=end_time,
            execution_id=None,
            redirect_count=0,
            urltype=urltype if "urltype" in locals() else None,
            retry_info=None,
            area=gcp_region_display,
        )
        return jsonify(result), 500


# ======================================================================
# Entry Point
# ======================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
