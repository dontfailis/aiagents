#!/bin/bash
# Deploy AI RPG Architecture on Google Cloud Platform
# Run this script from the root directory of the project.

set -e

# ==========================================
# 1. Configuration Variables
# ==========================================
PROJECT_ID="your-gcp-project-id" # REPLACE THIS
REGION="us-central1"
SERVICE_NAME="ai-rpg-orchestrator"
PUBSUB_TOPIC="session-updates"
DATASET_ID="ai_rpg_analytics"

echo "Deploying AI RPG architecture to $PROJECT_ID in $REGION..."

# ==========================================
# 2. Enable Required GCP APIs
# ==========================================
echo "Enabling necessary GCP Services (Cloud Run, Firestore, Pub/Sub, Vertex AI, Artifact Registry)..."
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    pubsub.googleapis.com \
    aiplatform.googleapis.com \
    artifactregistry.googleapis.com \
    --project=$PROJECT_ID

# ==========================================
# 3. Setup Firestore (Native Mode)
# ==========================================
# Note: Firestore can only be created once per project. 
# If it fails stating it already exists, it will continue.
echo "Setting up Firestore database..."
gcloud firestore databases create --location=$REGION --project=$PROJECT_ID || echo "Firestore already initialized."

# ==========================================
# 4. Setup Pub/Sub for Async Tasks
# ==========================================
echo "Creating Pub/Sub topic for State Keeper updates..."
gcloud pubsub topics create $PUBSUB_TOPIC --project=$PROJECT_ID || echo "Topic already exists."

# ==========================================
# 5. Build and Deploy Orchestration API to Cloud Run
# ==========================================
echo "Deploying API Layer to Cloud Run..."
cd backend

# Use Cloud Build to submit and deploy the service
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --set-env-vars PUBSUB_TOPIC=$PUBSUB_TOPIC \
    --max-instances 10

echo "Deployment complete!"
echo "Your API URL can be found above."
