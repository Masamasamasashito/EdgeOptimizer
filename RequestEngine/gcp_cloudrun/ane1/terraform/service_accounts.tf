# ==============================================================================
# Service Accounts and IAM Role Bindings
# ==============================================================================
# Creates 3 Service Accounts with least-privilege IAM configuration.
# Reference: RUN_README.md "Service Account合計5件の用途と権限" table
#
# SA naming: eo-gcp-sa-{env}-{role}-{region_short}
# Constraint: SA ID must be 6-30 chars, lowercase alphanumeric + hyphens

# ==============================================================================
# 1. Deployer SA - GitHub Actions deploy agent
# ==============================================================================
resource "google_service_account" "deployer" {
  project      = var.gcp_project_id
  account_id   = "${var.project_prefix}-gcp-sa-${var.environment}-deploy-${local.region_short}"
  display_name = "EO GCP Deployer SA (${local.region_short})"
  description  = "GitHub Actions deploy agent for Cloud Run (WIF OIDC)"

  depends_on = [google_project_service.iam]
}

# Deployer SA - Project-level roles
resource "google_project_iam_member" "deployer_run_admin" {
  project = var.gcp_project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

resource "google_project_iam_member" "deployer_cloudbuild_editor" {
  project = var.gcp_project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

resource "google_project_iam_member" "deployer_service_usage" {
  project = var.gcp_project_id
  role    = "roles/serviceusage.serviceUsageConsumer"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

resource "google_project_iam_member" "deployer_storage_admin" {
  project = var.gcp_project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

resource "google_project_iam_member" "deployer_ar_repo_admin" {
  project = var.gcp_project_id
  role    = "roles/artifactregistry.repoAdmin"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# Deployer SA - actAs Compute Engine default SA
resource "google_service_account_iam_member" "deployer_actAs_compute" {
  service_account_id = "projects/${var.gcp_project_id}/serviceAccounts/${var.gcp_project_number}-compute@developer.gserviceaccount.com"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer.email}"
}

# ==============================================================================
# 2. Runtime SA - Cloud Run execution identity + Secret Manager access
# ==============================================================================
resource "google_service_account" "runtime" {
  project      = var.gcp_project_id
  account_id   = "${var.project_prefix}-gcp-sa-${var.environment}-runtime-${local.region_short}"
  display_name = "EO GCP Cloud Run Runtime SA (${local.region_short})"
  description  = "Cloud Run runtime identity with Secret Manager access"

  depends_on = [google_project_service.iam]
}

# Runtime SA - Project-level role (Secret Manager access)
resource "google_project_iam_member" "runtime_secret_accessor" {
  project = var.gcp_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# Runtime SA - Allow Cloud Build SA to actAs Runtime SA (for deploy)
resource "google_service_account_iam_member" "runtime_actAs_cloudbuild" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${var.gcp_project_number}@cloudbuild.gserviceaccount.com"
}

# Runtime SA - Allow Deployer SA to actAs Runtime SA (for deploy)
resource "google_service_account_iam_member" "runtime_actAs_deployer" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer.email}"
}

# ==============================================================================
# 3. OAuth2 Invoker SA - n8n HTTP Request authentication
# ==============================================================================
resource "google_service_account" "oauth2_invoker" {
  project      = var.gcp_project_id
  account_id   = "${var.project_prefix}-gcp-sa-${var.environment}-oa2be-inv-${local.region_short}"
  display_name = "EO GCP OAuth2 Invoker SA (${local.region_short})"
  description  = "OAuth2 Bearer token auth for n8n to invoke Cloud Run"

  depends_on = [google_project_service.iam]
}

# OAuth2 Invoker SA - Self token creator (for ID token generation)
resource "google_service_account_iam_member" "oauth2_invoker_self_token_creator" {
  service_account_id = google_service_account.oauth2_invoker.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.oauth2_invoker.email}"
}

# ==============================================================================
# Compute Engine Default SA - Artifact Registry permission
# ==============================================================================
resource "google_project_iam_member" "compute_default_ar_repo_admin" {
  project = var.gcp_project_id
  role    = "roles/artifactregistry.repoAdmin"
  member  = "serviceAccount:${var.gcp_project_number}-compute@developer.gserviceaccount.com"
}
