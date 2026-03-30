# ==============================================================================
# Artifact Registry - Docker Repository for Cloud Run Source Deploy
# ==============================================================================
# GitHub Actions `gcloud run deploy --source` uses Cloud Build to build container images.
# The built images are stored in this Artifact Registry repository.
# Reference: EO_Documents/Manuals/py/CloudRun_README.md "Github Actionsからデプロイする際の保存先となるリポジトリを先に作成する"

resource "google_artifact_registry_repository" "cloud_run_source_deploy" {
  project       = var.gcp_project_id
  location      = var.gcp_region
  repository_id = "cloud-run-source-deploy"
  format        = "DOCKER"
  description   = "Cloud Run Source Deployments"

  labels = local.eo_gcp_resource_labels

  depends_on = [google_project_service.artifact_registry]
}
