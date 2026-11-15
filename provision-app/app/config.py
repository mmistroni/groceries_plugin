import os

class Settings:
    PROJECT_NAME: str = "Expense Provisioning App"
    # Defaults to local relative path if no environment variable is set
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./expenses.db")
    
    # Flags
    IS_CODESPACE: bool = os.getenv("CODESPACE_NAME") is not None or os.getenv("CODESPACES") == "true"
    ENV: str = os.getenv("ENV", "development")

settings = Settings()