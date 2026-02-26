# ==============================================================================
# Cloud Run Service - Request Engine Shell
# ==============================================================================
# Creates the Cloud Run service with placeholder image.
# Actual application code is deployed via GitHub Actions (gcloud run deploy --source).
#
# Request Engine Instance config: ../instances_conf/cloudrun001.env
# Service name: eo-re-d1-cloudrun-asne1
# Authentication: OAuth2 Bearer (no allUsers IAM binding - requires valid ID token)
# Reference: ../../../../../.github/workflows/deploy-py-to-gcp-cloudrun.yml for deployment configuration

resource "google_cloud_run_v2_service" "request_engine" {
  project  = var.gcp_project_id
  name     = "${local.name_prefix}-cloudrun-${local.region_short}"
  location = var.gcp_region

  labels = local.eo_gcp_resource_labels

  template {
    service_account = google_service_account.runtime.email

    scaling {
      max_instance_count = var.cloud_run_max_instances
      min_instance_count = var.cloud_run_min_instances
    }

    timeout = "${var.cloud_run_timeout}s"

    containers {
      # Placeholder image - will be replaced by GitHub Actions deployment
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      ports {
        container_port = var.cloud_run_port
      }

      resources {
        limits = {
          memory = var.cloud_run_memory
          cpu    = var.cloud_run_cpu
        }
      }

      env {
        name  = "EO_GCP_PROJECT_ID"
        value = var.gcp_project_id
      }

      env {
        name  = "CLOUDRUN_REQUEST_SECRET_NAME"
        value = var.secret_name
      }
    }
  }

  # Ignore changes to image/template that GitHub Actions deployment will update
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].revision,
      client,
      client_version,
    ]
  }

  depends_on = [
    google_project_service.cloud_run,
    google_service_account.runtime,
    google_secret_manager_secret.request_secret,
  ]
}

# ==============================================================================
# OAuth2 Invoker SA - Cloud Run Invoker role (service-level)
# ==============================================================================
# Allow OAuth2 Invoker SA to invoke this Cloud Run service.
# Without this binding, n8n requests will receive 401 Unauthorized.
# Reference: EO_Documents/Manuals/py/CloudRun_README.md "Cloud Run サービス起動元ロールを付与"
resource "google_cloud_run_v2_service_iam_member" "oauth2_invoker" {
  project  = google_cloud_run_v2_service.request_engine.project
  location = google_cloud_run_v2_service.request_engine.location
  name     = google_cloud_run_v2_service.request_engine.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.oauth2_invoker.email}"
}

# NOTE: No google_cloud_run_v2_service_iam_member for allUsers.
# Cloud Run requires OAuth2 Bearer token (ID token) for authentication.
# n8n uses OAuth2 Invoker SA to obtain ID token and invoke the service.
