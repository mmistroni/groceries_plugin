#!/bin/bash
# deploy-job.sh - Deploy the daily automated provisioning task as an Azure Container Apps Job
set -e

RESOURCE_GROUP="rg-groceries-provision-v2"
ACA_ENV="aca-env-provision"
ACR_NAME="acrprovision72014"
APP_NAME="expense-provision-app"
JOB_NAME="expense-provisioning-job"
CRON_SCHEDULE="0 5 * * *"  # Runs once a day at 5:00 AM UTC

DATABASE_URL="${DATABASE_URL:-postgresql://user:password@host:5432/dbname}"

echo "=========================================================="
echo " Deploying Azure Container Apps Cron Job"
echo "=========================================================="

echo "==> Fetching ACR credentials..."
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

echo "==> Creating Azure Container Apps Job with Schedule trigger..."
az containerapp job create \
    --name "$JOB_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ACA_ENV" \
    --image "$ACR_NAME.azurecr.io/$APP_NAME:latest" \
    --trigger-type Schedule \
    --cron-expression "$CRON_SCHEDULE" \
    --replica-timeout 1800 \
    --replica-retry-limit 1 \
    --cpu "0.5" \
    --memory "1.0Gi" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --env-vars "DATABASE_URL=$DATABASE_URL" "ENV=production" \
    --command "python" \
    --args "-m app.run_scheduler_job"

echo "=========================================================="
echo " Container Apps Job deployed successfully!"
echo " Name: $JOB_NAME"
echo " Schedule: $CRON_SCHEDULE (runs daily)"
echo "=========================================================="