# Expense Provisioning Application

A lightweight, server-side rendered expense provisioning CRUD application built with **FastAPI**, **HTMX**, and **Tailwind CSS**. It is designed to run locally in a Codespace using a seeded, in-memory/file SQLite database for development/testing, and dynamically switch to a cost-optimized, persistent Azure Database for PostgreSQL instance in production. 

Costs are kept at near-zero by deploying the web container to **Azure Container Apps (ACA)** configured with scale-to-zero, and utilizing an **Azure Container Apps Job** on a daily cron trigger to process automated direct-debit insertions.

---

## 🏗️ Architecture & Stack

- **Backend**: FastAPI (Python 3.11) with SQLAlchemy ORM.
- **Frontend**: Server-Side Rendered (Jinja2 Templates) styled with Tailwind CSS via CDN.
- **Interactions**: HTMX for smooth, asynchronous inline CRUD swaps and search filtering without full page reloads.
- **Database**:
  - **Local/Test**: SQLite (`expenses.db` or isolated temporary DBs for tests).
  - **Production/Azure**: Azure Database for PostgreSQL (Flexible Server, Burstable B1ms tier - the absolute cheapest persistent DB tier on Azure which supports auto-stop/start).
- **Automation / Serverless**:
  - **Azure Container Apps**: Hosting the web app. Configured with `min-replicas = 0` to scale down to zero when idle (incurring £0 compute cost).
  - **Azure Container Apps Job**: Daily cron job running the database scheduler utility (`app/run_scheduler_job.py`) and terminating immediately.

---

## 🚀 Getting Started (Local Development)

### 1. Pre-requisites
Ensure Python 3.11+ is installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the development server with:
```bash
uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

- **Auto-Seeding**: Upon the first start, if the database is empty, it automatically pre-populates with mock expenses, active direct debits, and monthly upload lump-sum values for instant preview.

---

## 🧪 Testing & Selenium Driver Setup

The project includes a comprehensive suite of unit, integration, and UI functional tests.

### 1. Headless Browser Driver Setup
To run the automated UI functional tests using Selenium, a headless web browser must be installed in the environment.

We provide a script to automatically download and install Google Chrome inside Ubuntu/Debian environments (like GitHub Codespaces):
```bash
chmod +x setup_test_env.sh
./setup_test_env.sh
```
*Note: The Python tests use `webdriver-manager` which automatically detects the installed Google Chrome version, downloads the matching `chromedriver` executable, and handles environment pathways at runtime.*

### 2. Run the Test Suite
Execute the entire test suite (unit + integration + Selenium UI tests):
```bash
PYTHONPATH=. pytest -v tests/
```
- **Fallback Behavior**: If Chrome is not installed, the Selenium UI tests in `tests/test_ui.py` are automatically skipped with a descriptive message, preventing build failures, while the backend unit/integration tests continue to run and pass.

---

## 🖥️ Database Access via DBeaver (Direct Connection)

When deployed to Azure, the provisioning script automatically retrieves your machine's current public IP address and creates a secure firewall rule allowing direct database connections.

To connect manually via a database client like **DBeaver** or **pgAdmin**:

1. **Locate Connection Parameters** (found in the Azure Portal or printouts of `deploy.sh`):
   - **Host**: `pg-provision-db-<id>.postgres.database.azure.com`
   - **Database**: `zkbudget`
   - **Username**: `dbadmin`
   - **Password**: `SecurePassword123!`
   - **Port**: `5432`

2. **DBeaver Setup**:
   - Click **New Database Connection** and select **PostgreSQL**.
   - Fill in **Host**, **Database**, **Username**, and **Password** fields.
   - Go to the **SSL** tab:
     - Check **Use SSL**.
     - Set **SSL Mode** to `require`.
   - Click **Test Connection** to verify connection, and click **Finish**.
   - You can now directly query or modify the `EXPENSE_ENTRY` and `SCHEDULED_RULE` tables.

---

## ☁️ Azure Deployment & Cost Optimization

Both deployment scripts are located in the root directory. To run them, make sure you are authenticated with the Azure CLI (`az login`).

### 1. Deploy the Web App (Scale-to-Zero)
```bash
chmod +x deploy.sh
./deploy.sh
```
This script does the following:
- Fetches your public IP via `ipify` and adds it to the PostgreSQL firewall.
- Provisions the cheapest **Burstable B1ms** flexible PostgreSQL server.
- Compiles the multi-stage Docker image and pushes it to Azure Container Registry (ACR).
- Deploys the container to Azure Container Apps (ACA) with **scale-to-zero** enabled (`--min-replicas 0 --max-replicas 1`), meaning it shuts down when idle and costs zero when not in use.

### 2. Deploy the Daily Scheduler Job (Cron Trigger)
```bash
chmod +x deploy-job.sh
./deploy-job.sh
```
This script provisions an **Azure Container Apps Job** bound to the same PostgreSQL database:
- **Trigger**: Cron schedule (`0 5 * * *` - once a day at 5:00 AM UTC).
- **Execution**: Spins up the container, overrides the entrypoint to execute the Python job (`python -m app.run_scheduler_job`), inserts scheduled direct debits/lump-sums due for the day, updates the rules' `last_run` timestamp, and immediately terminates, preserving resource consumption and keeping costs near zero.
