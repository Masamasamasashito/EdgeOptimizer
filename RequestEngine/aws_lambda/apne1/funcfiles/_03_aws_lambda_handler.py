# ----------------------------------------------------
# Edge Optimizer
# Request Engine for AWS Lambda - Platform-Specific Handler
# Crafted by Nishi Labo | https://4649-24.com
# ----------------------------------------------------
#
# EO Request Engine for AWS Lambda
# * Overview:
# Executes HTTP requests to specified URLs to warm up the AWS Lambda cache.
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
# - AWS Secrets Manager (env.AWS_REGION) - Region for Secrets Manager
# - AWS Secrets Manager Secret Name: eo-re-d01-secretsmng-apne1 (LAMBDA_REQUEST_SECRET_NAME)
# - AWS Secrets Manager Secret Key: LAMBDA_REQUEST_SECRET (LAMBDA_REQUEST_SECRET_KEY_NAME)

# ======================================================================
# AWS-Specific Imports
# ======================================================================
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# ======================================================================
# AWS Secrets Manager Configuration
# ======================================================================
LAMBDA_REQUEST_SECRET_NAME = "eo-re-d01-secretsmng-apne1"  # AWS Secrets Manager secret name (secret ID)
LAMBDA_REQUEST_SECRET_KEY_NAME = "LAMBDA_REQUEST_SECRET"  # Key name within the secret

# ======================================================================
# EO Identification Header
# ======================================================================
# Custom header used to identify Request Engine
EO_HEADER_NAME = "x-eo-re"
EO_HEADER_VALUE = "aws"

# ======================================================================
# Global Variables
# ======================================================================
_cached_secretsmng_secretkey_value: Optional[str] = None
# Cache for AWS Secrets Manager secret key (LAMBDA_REQUEST_SECRET) value
# Retrieved on first request, subsequent requests use cached value
# Note: Different from n8n's N8N_EO_REQUEST_SECRET (values must be the same)


# ======================================================================
# Get Secret Key Value from AWS Secrets Manager (retrieved once, cached thereafter)
# ======================================================================
def _get_secretsmng_secretkey_value() -> str:
    """
    Get secret key (LAMBDA_REQUEST_SECRET) value from AWS Secrets Manager

    Retrieved from AWS Secrets Manager on first call, uses cache thereafter.
    This reduces AWS Secrets Manager access count, optimizing performance and cost.

    Returns:
        str: Secret key value (value of LAMBDA_REQUEST_SECRET)

    Raises:
        RuntimeError: In following cases:
            - AWS_REGION environment variable is not set
            - Secrets Manager access failed (insufficient permissions, non-existent secret, etc.)
            - SecretString is empty
            - SecretString is not valid JSON
            - Secret key does not exist
            - Secret key value is empty or not a string

    Note:
        - Secret must be stored in JSON format
        - Secret key name: LAMBDA_REQUEST_SECRET_KEY_NAME
        - Cache is valid as long as Lambda execution environment is reused
    """
    # If already retrieved, return cached value without querying Secrets Manager
    # (performance optimization and cost reduction)
    global _cached_secretsmng_secretkey_value
    if _cached_secretsmng_secretkey_value is not None:
        return _cached_secretsmng_secretkey_value

    # Get and validate AWS_REGION environment variable
    # Automatically set in AWS Lambda, but check just in case
    region = os.environ.get("AWS_REGION")
    if not region:
        raise RuntimeError("AWS_REGION environment variable is not set")

    # Create boto3 session and initialize Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region,
    )

    # ==================================================================
    # Get secret from Secrets Manager
    # ==================================================================
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=LAMBDA_REQUEST_SECRET_NAME
        )
    # General AWS errors (insufficient permissions, non-existent secret, etc.)
    except ClientError as e:
        raise RuntimeError(f"Failed to get Secret of Secrets Manager: {e}") from e
    # boto3 internal errors
    except BotoCoreError as e:
        raise RuntimeError(f"Failed to Secret of Secrets Manager (BotoCoreError): {e}") from e

    # ==================================================================
    # Validate SecretString
    # ==================================================================
    secret_string = get_secret_value_response.get("SecretString")
    # Error if empty
    if not secret_string:
        raise RuntimeError(f"SecretString is empty for Secret of Secrets Manager: {LAMBDA_REQUEST_SECRET_NAME}")

    # Check if JSON format
    try:
        secret_json = json.loads(secret_string)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"SecretString for '{LAMBDA_REQUEST_SECRET_NAME}' is not valid JSON: {e}"
        ) from e

    # ==================================================================
    # Verify secret key existence and validate value
    # ==================================================================
    if LAMBDA_REQUEST_SECRET_KEY_NAME not in secret_json:
        raise RuntimeError(
            f"SecretKey '{LAMBDA_REQUEST_SECRET_KEY_NAME}' not found in Secret of Secrets Manager '{LAMBDA_REQUEST_SECRET_NAME}'"
        )

    # Check secret key value type and content
    secretkey_value = secret_json[LAMBDA_REQUEST_SECRET_KEY_NAME]
    if not isinstance(secretkey_value, str) or not secretkey_value:
        raise RuntimeError(
            f"Secret '{LAMBDA_REQUEST_SECRET_NAME}' SecretKey '{LAMBDA_REQUEST_SECRET_KEY_NAME}' is empty or not a string"
        )

    # ==================================================================
    # Cache and return
    # ==================================================================
    # Cache only secret key value (for security reasons, don't cache entire JSON)
    _cached_secretsmng_secretkey_value = secretkey_value
    return secretkey_value


# ======================================================================
# Main Function (Lambda Handler)
# ======================================================================
def lambda_handler(event: Any, context: Any) -> Dict[str, Any]:
    """
    AWS Lambda main handler

    Process HTTP requests sent from n8n workflow, execute HTTP requests to target URLs,
    measure/analyze performance metrics, and return results in flat JSON structure.

    Args:
        event: Lambda event (JSON Body or Lambda event structure)
            - Array format: [{...}] - uses first element
            - Object format: {targetUrl, tokenCalculatedByN8n, ...}
            - targetUrl: Target URL (required)
            - tokenCalculatedByN8n: Authentication token (required, SHA-256(url + secret))
            - headersForTargetUrl: Request headers for target URL (optional)
            - httpRequestNumber: Request number (optional)
            - httpRequestUUID: Request UUID (optional)
            - httpRequestRoundID: Request round ID (optional)
            - urltype: URL type (optional, "main_document", "asset", "exception")
        context: Lambda context (used to get execution ID, etc.)

    Returns:
        Dict[str, Any]: Flat JSON structure response
            - On success: HTTP status code 200, includes performance metrics
            - On error: Appropriate HTTP status code, includes error message

    Note:
        - Authentication: Verify token parameter against AWS Secrets Manager secret
        - Retry: Automatic retry for temporary errors (up to 3 times)
        - Memory protection: Skip analysis for content exceeding 5MB
    """
    start_time = time.time()

    # Get AWS region for passing to _build_flat_result
    aws_region = os.environ.get("AWS_REGION")

    # ==================================================================
    # Receive request from n8n AWS Lambda node (Request Engine node)
    # ==================================================================
    # ==================================================================
    # Debug: Log event output
    # ==================================================================
    # Used to check event content during development/debugging
    print("### RAW EVENT START ###")
    try:
        print(json.dumps(event, ensure_ascii=False))
    except Exception:
        print(str(event))
    print("### RAW EVENT END ###")

    # ==================================================================
    # Normalize event format
    # ==================================================================
    # If event is array format, extract first element
    # (Some Lambda integrations send in array format)
    if isinstance(event, list):
        if len(event) == 0:
            # Return error for empty array
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            return _build_flat_result(
                status_code=400,
                status_message="EMPTY_EVENT_LIST",
                duration_ms=duration_ms,
                target_url="",
                http_request_number=None,
                req_headers={},
                res_headers={},
                request_start_timestamp=start_time,
                request_end_timestamp=end_time,
                execution_id=context.aws_request_id if context else None,
                area=aws_region,
            )
        event = event[0]  # Use first element

    # Return error if event is not dictionary format
    if not isinstance(event, dict):
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        return _build_flat_result(
            status_code=400,
            status_message="INVALID_EVENT_TYPE",
            duration_ms=duration_ms,
            target_url="",
            http_request_number=None,
            req_headers={},
            res_headers={},
            request_start_timestamp=start_time,
            request_end_timestamp=end_time,
            execution_id=context.aws_request_id if context else None,
            area=aws_region,
        )

    data = event

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
    ua_from_request_headers = (
        input_headers.get("User-Agent") or ""
    )

    # ==================================================================
    # URL Validation
    # ==================================================================
    if not target_url:
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        return _build_flat_result(
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
            execution_id=context.aws_request_id if context else None,
            urltype=urltype,
            area=aws_region,
        )

    # ==================================================================
    # Verify n8n-generated token against token generated from AWS Secrets Manager secret key
    # ==================================================================
    # Get secret from AWS Secrets Manager
    # Note: Secret is retrieved once, subsequent calls use cached value
    try:
        secretsmng_secretkey_value = _get_secretsmng_secretkey_value()
        tokenCalculatedByCloudSecret = _calc_token(target_url, secretsmng_secretkey_value)  # SHA-256(url + request secret)
        if n8n_requestsecret_token == tokenCalculatedByCloudSecret:
            # Token verification successful: continue processing
            pass
        else:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            return _build_flat_result(
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
                execution_id=context.aws_request_id if context else None,
                urltype=urltype,
                area=aws_region,
            )
    except Exception as e:
        logging.error(f"Request Secret validation failed: {str(e)}")
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        return _build_flat_result(
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
            execution_id=context.aws_request_id if context else None,
            urltype=urltype,
            area=aws_region,
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
    # Initial_Response_ms (Time To First Byte) measurement
    # Definition: Time from sending HTTP request to receiving response headers from server
    # Includes: DNS lookup, TCP connection, TLS handshake, server processing, network latency
    # Measurement: stream=True makes requests.get() return at headers-received (before body download)
    http_request_start_time = time.time()
    try:
        # ==================================================================
        # Send HTTP request to Warmup Target URL
        # ==================================================================
        # HTTP request execution with retry support
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
            # Return warmup result data to n8n AWS Lambda node (Request Engine node)
            # ==================================================================
            # Build result in flat JSON structure
            return _build_flat_result(
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
                execution_id=context.aws_request_id if context else None,
                redirect_count=redirect_count,
                urltype=urltype,
                retry_info=retry_info,
                area=aws_region,
            )

    # ==================================================================
    # Error Handling
    # ==================================================================
    except requests.exceptions.RequestException as e:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            return _build_flat_result(
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
                execution_id=context.aws_request_id if context else None,
                redirect_count=0,
                urltype=urltype if "urltype" in locals() else None,
                retry_info=retry_info if "retry_info" in locals() else None,
                area=aws_region,
            )

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        error_target_url = target_url if "target_url" in locals() else ""
        return _build_flat_result(
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
            execution_id=context.aws_request_id if context else None,
            redirect_count=0,
            urltype=urltype if "urltype" in locals() else None,
            retry_info=None,  # No retry info for unexpected errors
            area=aws_region,
        )