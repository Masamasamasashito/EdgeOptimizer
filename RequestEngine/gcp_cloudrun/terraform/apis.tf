# ==============================================================================
# GCP API Enablement
# ==============================================================================
# Enable required GCP APIs for Cloud Run Request Engine.
# Reference: RUN_README.md "必要なAPIの有効化" section

resource "google_project_service" "cloud_functions" {
  project            = var.gcp_project_id
  service            = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_build" {
  project            = var.gcp_project_id
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  project            = var.gcp_project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_run" {
  project            = var.gcp_project_id
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secret_manager" {
  project            = var.gcp_project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iam" {
  project            = var.gcp_project_id
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iam_credentials" {
  project            = var.gcp_project_id
  service            = "iamcredentials.googleapis.com"
  disable_on_destroy = false
}
