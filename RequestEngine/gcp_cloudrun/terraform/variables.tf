# ==============================================================================
# Variables
# ==============================================================================

# --- Naming Convention ---

variable "project_prefix" {
  description = "Project prefix for resource naming (e.g., eo)"
  type        = string
  default     = "eo"

  validation {
    condition     = can(regex("^[a-z0-9]+$", var.project_prefix))
    error_message = "project_prefix must be lowercase alphanumeric only."
  }
}

variable "component" {
  description = "Component identifier (re = Request Engine)"
  type        = string
  default     = "re"

  validation {
    condition     = can(regex("^[a-z0-9]+$", var.component))
    error_message = "component must be lowercase alphanumeric only."
  }
}

variable "environment" {
  description = "Environment identifier (d01 = dev01, p01 = prod01)"
  type        = string
  default     = "d01"

  validation {
    condition     = can(regex("^[a-z0-9]+$", var.environment))
    error_message = "environment must be lowercase alphanumeric only."
  }
}

variable "region_short" {
  description = "Short region name for resource naming"
  type        = string
  default     = "ane1"

  validation {
    condition     = contains(["ane1", "ane2", "ane3", "ase1", "use1", "usw2", "euw1"], var.region_short)
    error_message = "region_short must be one of: ane1, ane2, ane3, ase1, use1, usw2, euw1."
  }
}

# --- GCP Settings ---

variable "gcp_project_id" {
  description = "GCP Project ID (e.g., eo-re-d01-pr-ane1)"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.gcp_project_id))
    error_message = "gcp_project_id must be 6-30 characters, lowercase, numbers, and hyphens."
  }
}

variable "gcp_project_number" {
  description = "GCP Project Number (numeric, required for WIF principalSet)"
  type        = string

  validation {
    condition     = can(regex("^[0-9]+$", var.gcp_project_number))
    error_message = "gcp_project_number must be numeric."
  }
}

variable "gcp_region" {
  description = "GCP region for deployment"
  type        = string
  default     = "asia-northeast1"

  validation {
    condition = contains([
      "asia-northeast1", "asia-northeast2", "asia-northeast3",
      "asia-southeast1", "us-east1", "us-west1", "europe-west1"
    ], var.gcp_region)
    error_message = "gcp_region must be a valid GCP region."
  }
}

# --- GitHub Actions OIDC ---

variable "github_org" {
  description = "GitHub organization or username"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

# --- Cloud Run Settings ---

variable "cloud_run_memory" {
  description = "Cloud Run instance memory (e.g., 512Mi, 1Gi) - minimum 512Mi with CPU always allocated"
  type        = string
  default     = "512Mi"
}

variable "cloud_run_cpu" {
  description = "Cloud Run instance CPU (e.g., 1, 2)"
  type        = string
  default     = "1"
}

variable "cloud_run_max_instances" {
  description = "Cloud Run maximum instance count"
  type        = number
  default     = 10

  validation {
    condition     = var.cloud_run_max_instances >= 1 && var.cloud_run_max_instances <= 1000
    error_message = "cloud_run_max_instances must be between 1 and 1000."
  }
}

variable "cloud_run_min_instances" {
  description = "Cloud Run minimum instance count"
  type        = number
  default     = 0

  validation {
    condition     = var.cloud_run_min_instances >= 0
    error_message = "cloud_run_min_instances must be 0 or greater."
  }
}

variable "cloud_run_timeout" {
  description = "Cloud Run request timeout in seconds"
  type        = number
  default     = 300

  validation {
    condition     = var.cloud_run_timeout >= 1 && var.cloud_run_timeout <= 3600
    error_message = "cloud_run_timeout must be between 1 and 3600 seconds."
  }
}

variable "cloud_run_port" {
  description = "Cloud Run container port"
  type        = number
  default     = 8080
}

# --- Secret Manager ---

variable "secret_name" {
  description = "Secret Manager secret name (must match code constant CLOUDRUN_REQUEST_SECRET_NAME)"
  type        = string
  default     = "eo-re-d01-secretmng"
}

variable "secret_key_name" {
  description = "Key name within the secret JSON (must match code constant CLOUDRUN_REQUEST_SECRET_KEY_NAME)"
  type        = string
  default     = "CLOUDRUN_REQUEST_SECRET"
}
