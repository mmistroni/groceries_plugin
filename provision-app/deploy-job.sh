#!/bin/bash
# deploy-job.sh - Script to deploy the daily automated provisioning task as an Azure Container Apps Job
set -e

# Load settings from primary deployment if available
if [ -f .env-deploy ]; then
    source .env-deploy
else
    echo "ERROR: .env-deploy file not found. Please run ./deploy.sh first to set up the infrastructure."
    exit 1
fi

JOB_NAME="expense-provisioning-job"
CRON_SCHEDULE="0 5 * * *"  # Runs once a day at 5:00 AM UTC

echo "=========================================================="
echo " Deploying Azure Container Apps Cron Job"
echo "=========================================================="

# Fetch ACR password dynamically using corrected command syntax
echo "==> Fetching ACR credentials..."
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

echo "==> Creating Azure Container Apps Job with Cron trigger..."
# This Job starts up a single replica, runs the scheduler job module, and terminates
az containerapp job create \
    --name "$JOB_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ACA_ENV" \
    --image "$ACR_NAME.azurecr.io/$APP_NAME:latest" \
    --trigger-type Cron \
    --cron-expression "$CRON_SCHEDULE" \
    --replica-timeout 1800 \
    --replica-retry-limit 1 \
    --cpu "0.5" \
    --memory "1.0Gi" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --env-vars DATABASE_URL="$DATABASE_URL" ENV="production" \
    --command "python" \
    --args "-m" "app.run_scheduler_job"

echo "=========================================================="
echo " Container Apps Job deployed successfully!"
echo " Name: $JOB_NAME"
echo " Schedule: $CRON_SCHEDULE (runs daily)"
echo " The job will spin up briefly, run scheduler insertions, and shut down."
echo "=========================================================="