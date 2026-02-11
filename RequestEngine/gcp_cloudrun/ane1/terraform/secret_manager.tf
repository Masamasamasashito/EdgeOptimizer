# ==============================================================================
# Secret Manager - Request Secret for Token Verification
# ==============================================================================
# Creates a secret with placeholder value.
# POST-DEPLOYMENT: Update the secret value with N8N_EO_REQUEST_SECRET from EO_Infra_Docker/.env
#
# Secret name must match code constant: CLOUDRUN_REQUEST_SECRET_NAME = "eo-re-d01-secretmng"
# Reference: RUN_README.md "Secret Manager による照合用リクエストシークレットの管理"

resource "google_secret_manager_secret" "request_secret" {
  project   = var.gcp_project_id
  secret_id = var.secret_name

  labels = local.common_labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.secret_manager]
}

# Secret version with placeholder value (JSON format)
# POST-DEPLOYMENT: Replace with actual N8N_EO_REQUEST_SECRET value
resource "google_secret_manager_secret_version" "request_secret_initial" {
  secret      = google_secret_manager_secret.request_secret.id
  secret_data = jsonencode({ (var.secret_key_name) = "REPLACE_WITH_N8N_EO_REQUEST_SECRET" })
}
