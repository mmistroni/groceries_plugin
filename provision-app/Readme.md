This is a provision-app built entirely by antigravity and deployed on azure based on this prompt

Role: You are a senior Python software engineer and cloud infrastructure expert.

Goal: Build a lightweight expense provisioning CRUD application that runs locally in a development Codespace using an in-memory database for testing, and connects to a cost-optimized, persistent database when deployed to Microsoft Azure.

Database Environment Configuration:
- Local/Testing: Configure the application to use an in-memory SQLite database (`sqlite3` or `aiosqlite`) when running local integration tests or inside the Codespace environment. Include a seed/pre-population routine containing mock expense data, standard direct debits, and monthly upload values for testing purposes.
- Production/Azure: Configure the application to dynamically switch to a persistent relational database using environment variables. Target the absolute cheapest persistent option on Azure—specifically Azure SQL Database (Serverless tier with auto-pause enabled) or Azure Database for PostgreSQL (Flexible Server, Burstable tier with auto-stop).
- Database Access: Ensure the Azure provisioning scripts configure a secure firewall rule allowing the developer's specific IP address to connect directly. Provide instructions in the README.md on how to connect via standard database management tools (like DBeaver) to manually inspect data when needed.

Application Architecture & Features:
1. Web Framework: Implement the server using a lightweight Python framework (FastAPI or Flask).
2. UI Layout: Keep maintenance simple by utilizing server-side rendering with standard HTML, CSS (e.g., Tailwind CSS via CDN), and HTMX for clean, asynchronous dynamic UI interactions.
3. CRUD Operations: Provide clean UI views to view, create, update, and delete individual expense entries, as well as a dedicated view to manage bulk expense uploads (handling multiple direct debits and modifying monthly lump-sum figures).
4. Task Scheduling & GUI Configuration: 
   - Define a modular task or endpoint specifically designed to process automated expense insertions at a designated day of the month.
   - Build a dedicated GUI/Admin settings page in the UI where the user can easily view, configure, and amend these scheduled rules (such as changing the specific day of the month the automated insertions occur or tweaking default monthly amounts).

Azure Deployment & Cost Optimization (Scale-to-Zero):
- The application will not be used 24/7. Provide a multi-stage `Dockerfile` targeting a lightweight base image.
- Generate the infrastructure-as-code or Azure CLI script to deploy this container to Azure Container Apps (ACA). Configure the container setting to scale to 0 instances when idle to maintain near-zero costs.
- Provide a secondary Azure configuration file/CLI script defining an "Azure Container Apps Job" tied to a cron trigger (e.g., executing once a day) to handle the automated scheduling execution by briefly starting up, checking the database configuration rules, running the required tasks, and terminating.

Testing Framework:
- Include a comprehensive suite of unit and integration tests using `pytest` that utilize the SQLite in-memory configuration.
- Write automated UI functional tests using Selenium to validate crucial frontend pathways (such as modifying an expense amount, triggering bulk edits, and saving the scheduled task configurations). 
- Provide an explicit setup step in a `README.md` file instructing how to configure the headless browser drivers for the Selenium tests inside the container environment.



## deployment on 20/8
https://expense-provision-app.mangoocean-45fee3d8.uksouth.azurecontainerapps.io/