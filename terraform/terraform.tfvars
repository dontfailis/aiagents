## Variables for this project

project_id            = "qwiklabs-asl-02-12036ac6afd2"
location              = "us-central1"
lb-backend-1_name     = "my-lb-backend"
memorystore-1_name    = "my-redis"
firestore-1_database_id = "(default)"
apphub_application_id = "chronex-apphub"

# Agent service URLs - populate these after the first deploy
# agent_createworld_url     = "https://agent-createworld-xxxx-uc.a.run.app"
# agent_createcharacter_url = "https://agent-createcharacter-xxxx-uc.a.run.app"
# agent_narrative_url       = "https://agent-narrative-xxxx-uc.a.run.app"
# agent_optiongen_url       = "https://agent-optiongeneration-xxxx-uc.a.run.app"

# Cloud Build / GitHub connection
github_owner           = "dontfailis"
github_repo            = "aiagents"
artifact_registry_repo = "cloud-run-source-deploy"

# 2nd-gen Cloud Build GitHub connection credentials.
# 1. Install the Cloud Build GitHub App on your repo and find the
#    installation ID in: https://github.com/settings/installations
# 2. Store a GitHub personal-access-token in Secret Manager and put
#    the full version resource name below.
github_app_installation_id        = 0        # replace with real installation ID
github_oauth_token_secret_version = "projects/qwiklabs-asl-02-12036ac6afd2/secrets/github-cloudbuild-token/versions/latest"