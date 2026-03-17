#!/usr/bin/env bash
# build-and-push.sh
#
# Builds all service Docker images and pushes them to Artifact Registry.
# After running this script, re-run `terraform apply` to point each
# Cloud Run service at the new image.
#
# Usage:
#   ./build-and-push.sh                        # uses defaults below
#   PROJECT=my-project REGION=europe-west1 ./build-and-push.sh

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT="${PROJECT:-qwiklabs-asl-02-12036ac6afd2}"
REGION="${REGION:-us-central1}"
REPO="${REPO:-cloud-run-source-deploy}"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}"

# folder → Cloud Run service name
declare -A SERVICES=(
  ["agent-createworld"]="agent-createworld"
  ["agent-createcharacter"]="agent-createcharacter"
  ["agent-narrative"]="agent-narrative"
  ["agent-optiongeneration"]="agent-optiongeneration"
  ["mcp-server"]="agent-mcp"
  ["frontend-web"]="frontend-web"
)

# ── Helpers ───────────────────────────────────────────────────────────────────
log()  { echo -e "\n\033[1;34m▶ $*\033[0m"; }
ok()   { echo -e "\033[1;32m✔ $*\033[0m"; }
err()  { echo -e "\033[1;31m✖ $*\033[0m" >&2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Pre-flight ─────────────────────────────────────────────────────────────────
log "Configuring Docker auth for Artifact Registry (${REGION})"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

log "Ensuring Artifact Registry repository '${REPO}' exists"
gcloud artifacts repositories describe "${REPO}" \
  --project="${PROJECT}" \
  --location="${REGION}" &>/dev/null \
|| gcloud artifacts repositories create "${REPO}" \
  --project="${PROJECT}" \
  --location="${REGION}" \
  --repository-format=docker \
  --description="Docker images for AI agent services"

# ── Build & push each service ──────────────────────────────────────────────────
FAILED=()

for FOLDER in "${!SERVICES[@]}"; do
  SERVICE="${SERVICES[$FOLDER]}"
  IMAGE="${REGISTRY}/${SERVICE}:latest"
  SRC="${SCRIPT_DIR}/${FOLDER}"

  log "Building ${FOLDER} → ${IMAGE}"

  if [[ ! -f "${SRC}/Dockerfile" ]]; then
    err "No Dockerfile found in ${SRC}, skipping."
    FAILED+=("${FOLDER}")
    continue
  fi

  # frontend-web needs the project root as build context (imports tools/)
  if [[ "${FOLDER}" == "frontend-web" ]]; then
    BUILD_CONTEXT="${SCRIPT_DIR}"
    DOCKERFILE_FLAG=("-f" "${SRC}/Dockerfile")
  else
    BUILD_CONTEXT="${SRC}"
    DOCKERFILE_FLAG=()
  fi

  if docker build \
      --platform linux/amd64 \
      -t "${IMAGE}" \
      "${DOCKERFILE_FLAG[@]}" \
      "${BUILD_CONTEXT}"; then
    ok "Built ${FOLDER}"
  else
    err "Build failed for ${FOLDER}"
    FAILED+=("${FOLDER}")
    continue
  fi

  if docker push "${IMAGE}"; then
    ok "Pushed ${IMAGE}"
  else
    err "Push failed for ${FOLDER}"
    FAILED+=("${FOLDER}")
  fi
done

# ── Summary ────────────────────────────────────────────────────────────────────
echo ""
if [[ ${#FAILED[@]} -eq 0 ]]; then
  ok "All images built and pushed successfully."
else
  err "The following services failed: ${FAILED[*]}"
  exit 1
fi

echo ""
echo "Images available at:"
for FOLDER in "${!SERVICES[@]}"; do
  SERVICE="${SERVICES[$FOLDER]}"
  echo "  ${REGISTRY}/${SERVICE}:latest"
done

echo ""
echo "Next step — update Cloud Run services to use the new images:"
echo "  cd terraform && terraform apply"
