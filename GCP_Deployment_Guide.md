# AI RPG Architecture Deployment Guide

This guide explains the provided code structure and provides instructions on how to install and run the core architectural components on Google Cloud Platform (GCP).

## Architecture Components Implemented

1. **API / Orchestration Layer:**
   - Location: `/backend`
   - Built with **Python** and **FastAPI**.
   - Handles the routing between the frontend and the Vertex AI Agent Engine.
   - Contains placeholder endpoints mapping exactly to the ones specified in the PRD (Section 9.1).
   - Containerized securely using a standard `Dockerfile`.

2. **Async Task Layer:**
   - Powered by **Google Cloud Pub/Sub**.
   - Facilitates decoupling of the `State Keeper Agent` and long-running state updates.

3. **Data Layer:**
   - Powered by **Google Cloud Firestore**.

---

## How to Install and Use on GCP

### Prerequisites
1. Install the [Google Cloud SDK (gcloud CLI)](https://cloud.google.com/sdk/docs/install).
2. Authenticate locally by running:
   ```bash
   gcloud auth login
   ```
3. Create a Google Cloud Project (or have an existing one). Ensure billing is enabled.

### Deployment Method

You can deploy the infrastructure directly using the provided bash script:

1. **Edit the deployment script:**
   Open `deploy_gcp.sh` and update the `PROJECT_ID` variable with your actual Google Cloud Project ID.
   ```bash
   PROJECT_ID="my-google-cloud-project-id" 
   ```

2. **Run the Script:**
   In your terminal, standing in the `aiagents` directory, execute:
   ```bash
   bash deploy_gcp.sh
   ```

### What the script does:
- **Enables APIs:** Turns on Cloud Run, Firestore, Pub/Sub, and Vertex AI.
- **Initializes Firestore:** Creates a NoSQL database for World States and Event logs.
- **Creates Pub/Sub Topics:** Sets up asynchronous queues for the State Keeper.
- **Deploys to Cloud Run:** Takes the Python FastAPI app in `/backend`, containerizes it via Cloud Build, and hosts it serverlessly on Cloud Run.

### Post-Deployment
Once the `deploy_gcp.sh` script completes, it will output a **Service URL** (e.g., `https://ai-rpg-orchestrator-xxxxx-uc.a.run.app`).

You can verify the backend is running by visiting:
`[YOUR_SERVICE_URL]/docs` 
This will open the automatically generated Swagger API documentation where you can test the Orchestration endpoints directly.

### Vertex AI Agent engine (ADK) Setup
To plug in the Agents (generated in the previous steps):
1. Navigate to the [Vertex AI Agent Builder](https://console.cloud.google.com/gen-app-builder/engines) in the GCP Console.
2. Create new Agents using the Markdown prompts provided (`Agent_WorldBuilder.md`, etc.).
3. Note their Agent IDs and use the `google-cloud-aiplatform` Python SDK in `backend/main.py` to invoke them from the API endpoints.
