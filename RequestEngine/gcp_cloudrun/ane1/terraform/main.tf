# ==============================================================================
# Edge Optimizer - GCP Cloud Run Request Engine Infrastructure
# ==============================================================================
# Terraform configuration for provisioning GCP Cloud Run Request Engine resources.
# Creates: APIs, Service Accounts, Secret Manager, WIF, Artifact Registry, Cloud Run
#
# PREREQUISITES:
# 1. GCP Project created with billing enabled
# 2. gcloud CLI authenticated: gcloud auth application-default login
# 3. Terraform >= 1.5.0 installed
#
# POST-DEPLOYMENT STEPS:
# 1. Update Secret Manager value with N8N_EO_REQUEST_SECRET from EO_Infra_Docker/.env
# 2. Create OAuth2 Invoker SA JSON key manually (IAM > Service Accounts)
# 3. Set GitHub Secrets (see outputs)
# 4. Deploy application code via GitHub Actions
#
# See: RUN_TF_README.md for detailed step-by-step instructions
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ==============================================================================
# Local Variables - Naming Convention
# ==============================================================================
# Pattern: {project_prefix}-{component}-{environment}-{resource}-{region_short}
# Example: eo-re-d01-cloudrun-ane1

locals {
  name_prefix  = "${var.project_prefix}-${var.component}-${var.environment}"
  region_short = var.region_short

  common_labels = {
    project     = var.project_prefix
    component   = var.component
    environment = var.environment
    managed-by  = "terraform"
  }
}
