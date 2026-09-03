set -e

# 1. Fresh Resource Group name to bypass the deletion wait
RESOURCE_GROUP="rg-groceries-provision-v2"
LOCATION="uksouth"

# 2. Truly dynamic random number generation (prevents duplicate server name errors)
RANDOM_ID="72014"
#$(shuf -i 10000-99999 -n 1 2>/dev/null || echo $((10000 + $$ % 89999)))

ACR_NAME="acrprovision${RANDOM_ID}"
ACA_ENV="aca-env-provision"
APP_NAME="expense-provision-app"
PG_SERVER_NAME="pg-provision-db-${RANDOM_ID}"
PG_DB_NAME="zkbudget"
PG_USER="dbadmin"
PG_PASSWORD="${GROCERIES_DB_PASSWORD}"


if [ -z "$PG_PASSWORD" ]; then
    printf "Enter PostgreSQL Admin Password: "
    stty -echo
    read PG_PASSWORD
    stty echo
    echo ""
fi


echo "=========================================================="
echo " Starting Azure Deployment for Expense Provisioning App"
echo "=========================================================="

# 1. Fetch Developer's Public IP to secure database access
echo "==> Fetching developer's public IP address..."
DEV_IP=$(curl -s https://api.ipify.org)
if [ -z "$DEV_IP" ]; then
    echo "WARNING: Could not determine public IP. Database firewall might need manual adjustment."
else
    echo "Detected public IP: $DEV_IP"
fi

# 2. Create Resource Group
echo "==> Creating Azure Resource Group ($RESOURCE_GROUP) in $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

# 3. Provision PostgreSQL Server & Database (if not already present)
echo "==> Checking if PostgreSQL server ($PG_SERVER_NAME) exists..."
if ! az postgres flexible-server show --resource-group "$RESOURCE_GROUP" --name "$PG_SERVER_NAME" >/dev/null 2>&1; then
    echo "==> Provisioning cost-optimized Azure Database for PostgreSQL (Burstable B1ms tier)..."
    az postgres flexible-server create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$PG_SERVER_NAME" \
        --location "$LOCATION" \
        --admin-user "$PG_USER" \
        --admin-password "$PG_PASSWORD" \
        --sku-name Standard_B1ms \
        --tier Burstable \
        --yes

    echo "==> Creating database ($PG_DB_NAME) inside PostgreSQL Flexible Server..."
    az postgres flexible-server db create \
        --resource-group "$RESOURCE_GROUP" \
        --server-name "$PG_SERVER_NAME" \
        --name "$PG_DB_NAME"
else
    echo "==> PostgreSQL server ($PG_SERVER_NAME) already exists. Skipping creation."
fi

# 4. Set up firewall rules
if [ ! -z "$DEV_IP" ]; then
    echo "==> Configuring firewall rule for developer IP ($DEV_IP)..."
    az postgres flexible-server firewall-rule create \
        --resource-group "$RESOURCE_GROUP" \
        --server-name "$PG_SERVER_NAME" \
        --name AllowDeveloperIP \
        --start-ip-address "$DEV_IP" \
        --end-ip-address "$DEV_IP" \
        >/dev/null 2>&1 || true
fi

echo "==> Configuring firewall rule to allow internal connections from Azure Container Apps..."
az postgres flexible-server firewall-rule create \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$PG_SERVER_NAME" \
    --name AllowAllAzureIPs \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0 \
    >/dev/null 2>&1 || true



# 5. Create Azure Container Registry (ACR) and build image
echo "==> Provisioning Azure Container Registry ($ACR_NAME)..."
az acr create --resource-group "$RESOURCE_GROUP" --name "$ACR_NAME" --sku Basic --admin-enabled true

echo "==> Building and pushing container image to ACR..."
az acr build --registry "$ACR_NAME" --image "$APP_NAME:latest" .

# 6. Deploy Azure Container App Environment
echo "==> Setting up Container App Environment..."
az containerapp env create --name "$ACA_ENV" --resource-group "$RESOURCE_GROUP" --location "$LOCATION"

# Get ACR credentials
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

# Create JDBC/SQLAlchemy style Connection string
DATABASE_URL="postgresql://$PG_USER:$PG_PASSWORD@$PG_SERVER_NAME.postgres.database.azure.com:5432/$PG_DB_NAME?sslmode=require"

# 7. Create Web Container App with scale-to-zero settings (0 replicas minimum)
echo "==> Deploying the Web Container App with Scale-to-Zero settings (0-1 replicas)..."
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
    --env-vars DATABASE_URL="$DATABASE_URL" ENV="production" \
    --query "properties.configuration.ingress.fqdn" \
    -o tsv)

echo "=========================================================="
echo " Web app deployed successfully!"
echo " Application URL: http://$FQDN"
echo " Note: App will spin down to 0 instances when idle, incurring £0 cost."
echo " Saved connection details for the Job deployment."
echo "=========================================================="

# Export variables for Job script
echo "export RESOURCE_GROUP=\"$RESOURCE_GROUP\"" > .env-deploy
echo "export ACA_ENV=\"$ACA_ENV\"" >> .env-deploy
echo "export ACR_NAME=\"$ACR_NAME\"" >> .env-deploy
echo "export APP_NAME=\"$APP_NAME\"" >> .env-deploy
echo "export DATABASE_URL=\"$DATABASE_URL\"" >> .env-deploy
echo "export ACR_PASSWORD=\"$ACR_PASSWORD\"" >> .env-deploy
