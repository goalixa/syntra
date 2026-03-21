import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "Syntra AI Orchestrator"

    API_VERSION = "v1"

    # Auth service
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service")

    # Kubernetes
    KUBECTL_PATH = os.getenv("KUBECTL_PATH", "kubectl")

    # AI
    MODEL_NAME = os.getenv("MODEL_NAME", "claude")

settings = Settings()
