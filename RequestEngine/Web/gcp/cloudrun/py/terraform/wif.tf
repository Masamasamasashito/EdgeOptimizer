# ==============================================================================
# Workload Identity Federation - GitHub Actions OIDC Authentication
# ==============================================================================
# Enables GitHub Actions to authenticate to GCP without static service account keys.
# Reference: EO_Documents/Manuals/py/CloudRun_README.md "Workload Identity 連携による GitHub Actions の認証設定"
#
# ※ ここでの "Provider" は WIF ID プロバイダ (IdP) であり、
#   main.tf の Terraform プロバイダ (hashicorp/google) とは別概念です。
#
# Pool naming: eo-gcp-pool-wif-d1 (4-32 chars, lowercase + digits + hyphens)
# IdP naming:  eo-gcp-idp-gh-oidc-wif-d1

# ==============================================================================
# Workload Identity Pool
# ==============================================================================
resource "google_iam_workload_identity_pool" "github" {
  project                   = var.gcp_project_id
  workload_identity_pool_id = "${var.project_prefix}-gcp-pool-wif-${var.environment}"
  display_name              = "EO GCP Pool WIF ${upper(var.environment)}"
  description               = "Workload Identity Pool for GitHub Actions OIDC"

  depends_on = [google_project_service.iam]
}

# ==============================================================================
# WIF ID プロバイダ / IdP (GitHub Actions OIDC)
# ※ Terraform プロバイダ (main.tf) とは別概念
# ==============================================================================
resource "google_iam_workload_identity_pool_provider" "github_oidc" {
  project                            = var.gcp_project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "${var.project_prefix}-gcp-idp-gh-oidc-wif-${var.environment}"
  display_name                       = "EO GCP IDP GitHub OIDC ${upper(var.environment)}"
  description                        = "GitHub Actions OIDC provider for Cloud Run deployment"

  # Restrict to specific repository
  attribute_condition = "assertion.repository == '${var.github_org}/${var.github_repo}'"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
    allowed_audiences = [
      "projects/${var.gcp_project_number}/locations/global/workloadIdentityPools/${var.project_prefix}-gcp-pool-wif-${var.environment}/providers/${var.project_prefix}-gcp-idp-gh-oidc-wif-${var.environment}"
    ]
  }
}

# ==============================================================================
# Deployer SA - Workload Identity User binding (GitHub Actions → Deployer SA)
# ==============================================================================
resource "google_service_account_iam_member" "deployer_wif_binding" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/projects/${var.gcp_project_number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/attribute.repository/${var.github_org}/${var.github_repo}"
}
