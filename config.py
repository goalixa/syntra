import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "Syntra AI Orchestrator"

    API_VERSION = "v1"

    # Auth service (Kubernetes service name)
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:80")

    # Syntra Admin API Key (for creating users via admin API)
    SYNTRA_ADMIN_API_KEY = os.getenv("SYNTRA_ADMIN_API_KEY", "")

    # Kubernetes
    KUBECTL_PATH = os.getenv("KUBECTL_PATH", "kubectl")

    # AI
    MODEL_NAME = os.getenv("MODEL_NAME", "claude")

settings = Settings()
