# Cloud Build triggers for each agent service.
# Each trigger fires when code is pushed to the `main` branch under
# the corresponding agent folder, and uses the cloudbuild.yaml file
# inside that folder as the build configuration.

locals {
  agents = {
    "agent-createworld" = {
      service_name = "agent-createworld"
      folder       = "agent-createworld"
      description  = "Build and deploy agent-createworld on push to main"
    }
    "agent-createcharacter" = {
      service_name = "agent-createcharacter"
      folder       = "agent-createcharacter"
      description  = "Build and deploy agent-createcharacter on push to main"
    }
    "agent-narrative" = {
      service_name = "agent-narrative"
      folder       = "agent-narrative"
      description  = "Build and deploy agent-narrative on push to main"
    }
    "agent-optiongeneration" = {
      service_name = "agent-optiongeneration"
      folder       = "agent-optiongeneration"
      description  = "Build and deploy agent-optiongeneration on push to main"
    }
  }
}

# Enable the Cloud Build API
resource "google_project_service" "cloudbuild" {
  project            = var.project_id
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

# Enable the Artifact Registry API (required to push images)
resource "google_project_service" "artifactregistry" {
  project            = var.project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Artifact Registry repository used to store all agent Docker images
resource "google_artifact_registry_repository" "agents" {
  project       = var.project_id
  location      = var.location
  repository_id = var.artifact_registry_repo
  format        = "DOCKER"
  description   = "Docker images for AI agent services"

  depends_on = [google_project_service.artifactregistry]
}

# Cloud Build trigger per agent — fires on push to main for the agent folder
resource "google_cloudbuild_trigger" "agent_triggers" {
  for_each = local.agents

  project     = var.project_id
  location    = var.location
  name        = "trigger-${each.key}"
  description = each.value.description

  # Only watch changes inside the specific agent folder
  included_files = ["${each.value.folder}/**"]

  github {
    owner = var.github_owner
    name  = var.github_repo

    push {
      branch = "^main$"
    }
  }

  # Use the cloudbuild.yaml inside the agent folder as the build config
  filename = "${each.value.folder}/cloudbuild.yaml"

  substitutions = {
    _REGION       = var.location
    _REPO         = var.artifact_registry_repo
    _SERVICE_NAME = each.value.service_name
  }

  depends_on = [google_project_service.cloudbuild]
}
