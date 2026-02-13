# ----------------------------------------------------
# Edge Optimizer
# Request Engine for Azure Functions - Platform-Specific Handler
# Crafted by Nishi Labo | https://4649-24.com
# ----------------------------------------------------
#
# EO Request Engine for Azure Functions Japan East region
# * Overview:
# Executes HTTP requests to specified URLs to warm up the Azure Functions cache.
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
# - Azure Key Vault (env.EO_AZ_RE_KEYVAULT_URL) - Key Vault URI
# - Azure Key Vault Secret Name: AZFUNC-REQUEST-SECRET (AZFUNC_REQUEST_SECRET_NAME)

# ======================================================================
# Azure Key Vault Configuration
# ======================================================================
AZFUNC_REQUEST_SECRET_NAME = "AZFUNC-REQUEST-SECRET"  # Azure Key Vault secret name (not Key Vault name)

# ======================================================================
# EO Identification Header
# ======================================================================
# Custom header used to identify Request Engine
EO_HEADER_NAME = "x-eo-re"
EO_HEADER_VALUE = "azure"

# ======================================================================
# Global Variables
# ======================================================================
_cached_kv_request_secret: Optional[str] = None
# Cache for Azure Key Vault secret (AZFUNC-REQUEST-SECRET) value
# Retrieved on first request, subsequent requests use cached value
# Note: Different from n8n's N8N_EO_REQUEST_SECRET (values must be the same)

app = func.FunctionApp()


# ======================================================================
# Get Azure Functions Execution ID
# ======================================================================
def _get_execution_id() -> Optional[str]:
    """
    Get Azure Functions execution ID
    Attempts to get from environment variables (returns None if not available)
    """
    execution_id = os.environ.get("_X_MS_EXECUTION_ID") or os.environ.get("WEBSITE_INSTANCE_ID")
    return execution_id if execution_id else None


# ======================================================================
# Get Secret from Azure Key Vault (retrieved once, cached thereafter)
# ======================================================================
def _get_kv_request_secret() -> str:
    """
    Get secret (AZFUNC-REQUEST-SECRET) value from Azure Key Vault

    Retrieved from Azure Key Vault on first call, uses cache thereafter.
    This reduces Key Vault access count, optimizing performance and cost.

    Returns:
        str: Secret value (value of AZFUNC-REQUEST-SECRET)

    Raises:
        RuntimeError: In following cases:
            - EO_AZ_RE_KEYVAULT_URL environment variable is not set
            - Key Vault access failed (insufficient permissions, non-existent secret, etc.)
    """
    global _cached_kv_request_secret
    if _cached_kv_request_secret is not None:
        return _cached_kv_request_secret

    # EO_AZ_RE_KEYVAULT_URL from Function App application settings
    keyvault_url = os.environ.get("EO_AZ_RE_KEYVAULT_URL")
    if not keyvault_url:
        raise RuntimeError("EO_AZ_RE_KEYVAULT_URL environment variable is not set")

    try:
        azure_credential = DefaultAzureCredential()
        azure_kv_secret_client = SecretClient(vault_url=keyvault_url, credential=azure_credential)
        azure_kv_secret = azure_kv_secret_client.get_secret(AZFUNC_REQUEST_SECRET_NAME)
        _cached_kv_request_secret = azure_kv_secret.value
        return _cached_kv_request_secret
    except Exception as e:
        raise RuntimeError(f"Failed to get secret from Azure Key Vault: {str(e)}")


# ======================================================================
# Main Function (Azure Functions Handler)
# ======================================================================
@app.route(route="requestengine_func", auth_level=func.AuthLevel.FUNCTION, methods=["GET", "POST"])
def requestengine_func(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Functions main handler

    Process HTTP requests sent from n8n workflow, execute HTTP requests to target URLs,
    measure/analyze performance metrics, and return results in flat JSON structure.

    Args:
        req: Azure Functions HTTP request object
            - JSON Body: {targetUrl, tokenCalculatedByN8n, ...}
            - targetUrl: Target URL (required)
            - tokenCalculatedByN8n: Authentication token (required, SHA-256(url + secret))
            - headersForTargetUrl: Request headers for target URL (optional)
            - httpRequestNumber: Request number (optional)
            - httpRequestUUID: Request UUID (optional)
            - httpRequestRoundID: Request round ID (optional)
            - urltype: URL type (optional, "main_document", "asset", "exception")

    Returns:
        func.HttpResponse: JSON response
            - On success: HTTP status code 200, includes performance metrics
            - On error: Appropriate HTTP status code, includes error message

    Note:
        - Authentication: Verify token parameter against Azure Key Vault secret
        - Retry: Automatic retry for temporary errors (up to 3 times)
        - Memory protection: Skip analysis for content exceeding 5MB
    """
    start_time = time.time()

    # Get Azure region for passing to _build_flat_result
    azure_region = os.environ.get("REGION_NAME")

    try:
        # ==================================================================
        # Receive request from n8n HttpRequest node (Request Engine node)
        # ==================================================================
        # JSON parse and data extraction
        try:
            body_json = req.get_json() or {}
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
                execution_id = _get_execution_id()
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
                    execution_id=execution_id,
                    area=azure_region,
                )
                return func.HttpResponse(
                    json.dumps(result),
                    status_code=400,
                    mimetype="application/json",
                )
            body_json = body_json[0]

        # Return error if body_json is not dictionary format
        if not isinstance(body_json, dict):
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            execution_id = _get_execution_id()
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
                execution_id=execution_id,
                area=azure_region,
            )
            return func.HttpResponse(
                json.dumps(result),
                status_code=400,
                mimetype="application/json",
            )

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
            execution_id = _get_execution_id()
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
                execution_id=execution_id,
                urltype=urltype,
                area=azure_region,
            )
            return func.HttpResponse(
                json.dumps(result),
                status_code=400,
                mimetype="application/json",
            )

        # ==================================================================
        # Verify n8n-generated token against token generated from Azure Key Vault secret
        # ==================================================================
        try:
            kv_request_secret = _get_kv_request_secret()
            tokenCalculatedByCloudSecret = _calc_token(target_url, kv_request_secret)
            if n8n_requestsecret_token == tokenCalculatedByCloudSecret:
                # Token verification successful: continue processing
                pass
            else:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                execution_id = _get_execution_id()
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
                    execution_id=execution_id,
                    urltype=urltype,
                    area=azure_region,
                )
                return func.HttpResponse(
                    json.dumps(result),
                    status_code=401,
                    mimetype="application/json",
                )
        except Exception as e:
            logging.error(f"Request Secret validation failed: {str(e)}")
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            execution_id = _get_execution_id()
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
                execution_id=execution_id,
                urltype=urltype,
                area=azure_region,
            )
            return func.HttpResponse(
                json.dumps(result),
                status_code=500,
                mimetype="application/json",
            )

        # ==================================================================
        # Prepare request headers
        # ==================================================================
        req_headers: Dict[str, str] = dict(input_headers)
        # Set User-Agent if specified (always included from n8n workflow node 175)
        if ua_from_request_headers:
            req_headers.setdefault("User-Agent", ua_from_request_headers)
        # Add EO identification header (for Request Engine identification)
        req_headers[EO_HEADER_NAME] = EO_HEADER_VALUE

        # ==================================================================
        # Execute HTTP request (with retry)
        # ==================================================================
        # Initial_Response_ms (TTFB) measurement
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
                execution_id = _get_execution_id()

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
                    execution_id=execution_id,
                    redirect_count=redirect_count,
                    urltype=urltype,
                    retry_info=retry_info,
                    area=azure_region,
                )
                return func.HttpResponse(
                    json.dumps(result),
                    status_code=200,
                    mimetype="application/json",
                )

        # ==================================================================
        # Error Handling
        # ==================================================================
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            execution_id = _get_execution_id()
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
                execution_id=execution_id,
                redirect_count=0,
                urltype=urltype if "urltype" in locals() else None,
                retry_info=retry_info if "retry_info" in locals() else None,
                area=azure_region,
            )
            return func.HttpResponse(
                json.dumps(result),
                status_code=500,
                mimetype="application/json",
            )

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        execution_id = _get_execution_id()
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
            execution_id=execution_id,
            redirect_count=0,
            urltype=urltype if "urltype" in locals() else None,
            retry_info=None,
            area=azure_region,
        )
        return func.HttpResponse(
            json.dumps(result),
            status_code=500,
            mimetype="application/json",
        )
