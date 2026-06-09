import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GLM_API_KEY: str = os.getenv("GLM_API_KEY", "")
    GLM_MODEL: str = os.getenv("GLM_MODEL", "glm-4-flash")
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

settings = Settings()
