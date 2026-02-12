# ==============================================================================
# Outputs
# ==============================================================================
# Values needed for GitHub Secrets, n8n configuration, and operational reference.

# --- GitHub Secrets ---

output "wif_provider_path" {
  description = "WIF Provider full path (GitHub Secrets: EO_GCP_WIF_PROVIDER_PATH)"
  value       = "projects/${var.gcp_project_number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.github_oidc.workload_identity_pool_provider_id}"
}

output "deploy_sa_email" {
  description = "Deployer SA email (GitHub Secrets: EO_GCP_RUN_ANE1_DEPLOY_SA_EMAIL)"
  value       = google_service_account.deployer.email
}

output "runtime_sa_email" {
  description = "Runtime SA email (GitHub Secrets: EO_GCP_RUN_ANE1_RUNTIME_SA_EMAIL)"
  value       = google_service_account.runtime.email
}

output "gcp_project_id" {
  description = "GCP Project ID (GitHub Secrets: EO_GCP_PROJECT_ID)"
  value       = var.gcp_project_id
}

# --- Cloud Run ---

output "cloud_run_service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_v2_service.request_engine.name
}

output "cloud_run_service_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_v2_service.request_engine.uri
}

# --- Service Accounts ---

output "oauth2_invoker_sa_email" {
  description = "OAuth2 Invoker SA email (for n8n Credentials JSON key)"
  value       = google_service_account.oauth2_invoker.email
}

# --- Secret Manager ---

output "secret_name" {
  description = "Secret Manager secret name"
  value       = google_secret_manager_secret.request_secret.secret_id
}

# --- Artifact Registry ---

output "artifact_registry_repository" {
  description = "Artifact Registry repository name"
  value       = google_artifact_registry_repository.cloud_run_source_deploy.name
}
