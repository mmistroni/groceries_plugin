import os

class Settings:
    PROJECT_NAME: str = "Expense Provisioning App"
    # In-memory SQLite for testing/local by default unless DATABASE_URL is set
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///expenses.db")
    
    # Flags for testing or seeding
    IS_CODESPACE: bool = os.getenv("CODESPACE_NAME") is not None or os.getenv("CODESPACES") == "true"
    ENV: str = os.getenv("ENV", "development")

settings = Settings()
