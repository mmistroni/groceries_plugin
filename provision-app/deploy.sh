#!/bin/bash
set -e

# 1. Resource Group and Naming
RESOURCE_GROUP="rg-groceries-provision-v2"
LOCATION="uksouth"
RANDOM_ID="72014"

ACR_NAME="acrprovision${RANDOM_ID}"
ACA_ENV="aca-env-provision"
APP_NAME="expense-provision-app"
STORAGE_ACCOUNT="expensestorage${RANDOM_ID}"
BLOB_CONTAINER="dbcontainer"

echo "=========================================================="
echo " Starting Azure Deployment (Local SQLite + Blob Sync)"
echo "=========================================================="

# 1. Create Resource Group
echo "==> Creating Azure Resource Group ($RESOURCE_GROUP) in $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

# 2. Create Storage Account & Blob Container for Persistence
echo "==> Checking storage account ($STORAGE_ACCOUNT)..."
if ! az storage account show --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
    echo "==> Provisioning storage account..."
    az storage account create \
        --name "$STORAGE_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku Standard_LRS \
        --output none
fi

echo "==> Waiting for storage account to be ready and retrieving key..."
STORAGE_KEY=""
for i in {1..12}; do
    STORAGE_KEY=$(az storage account keys list \
        --account-name "$STORAGE_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --query "[0].value" -o tsv 2>/dev/null || true)
    
    if [ -n "$STORAGE_KEY" ]; then
        break
    fi
    echo "Attempt $i: Storage keys not ready yet, retrying in 5 seconds..."
    sleep 5
done

if [ -z "$STORAGE_KEY" ]; then
    echo "ERROR: Failed to retrieve storage account keys after 60 seconds."
    exit 1
fi

echo "==> Ensuring blob container ($BLOB_CONTAINER) exists..."
az storage container create \
    --name "$BLOB_CONTAINER" \
    --account-name "$STORAGE_ACCOUNT" \
    --account-key "$STORAGE_KEY" \
    --output none

STORAGE_CONN="DefaultEndpointsProtocol=https;AccountName=${STORAGE_ACCOUNT};AccountKey=${STORAGE_KEY};EndpointSuffix=core.windows.net"

# 3. Create Azure Container Registry (ACR) and build image
echo "==> Provisioning Azure Container Registry ($ACR_NAME)..."
az acr create --resource-group "$RESOURCE_GROUP" --name "$ACR_NAME" --sku Basic --admin-enabled true --output none

echo "==> Building and pushing container image to ACR..."
az acr build --registry "$ACR_NAME" --image "$APP_NAME:latest" . --output none

# 4. Deploy Azure Container App Environment
echo "==> Setting up Container App Environment ($ACA_ENV)..."
if ! az containerapp env show --name "$ACA_ENV" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
    az containerapp env create --name "$ACA_ENV" --resource-group "$RESOURCE_GROUP" --location "$LOCATION" --output none
fi

# Get ACR credentials
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

# SQLite Connection string pointing to the container's local SSD
SQLITE_URL="sqlite:///./expenses.db"

# 5. Deploy Web Container App (Self-contained, no volume mounts)
echo "==> Deploying the Web Container App..."
FQDN=$(az containerapp create \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ACA_ENV" \
    --image "$ACR_NAME.azurecr.io/$APP_NAME:latest" \
    --target-port 8000 \
    --ingress external \
    --registry-server "$ACR_NAME.azurecr.io" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --min-replicas 0 \
    --max-replicas 1 \
    --env-vars DATABASE_URL="$SQLITE_URL" AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONN" ENV="production" \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv)

echo "=========================================================="
echo " Web app deployed successfully with Local SQLite + Blob Sync!"
echo " Application URL: http://$FQDN"
echo " Note: App will spin down to 0 instances when idle (£0 compute cost)."
echo "=========================================================="