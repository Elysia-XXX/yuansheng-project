"""应用配置：从 .env 或环境变量读取，默认连接本机无密码 PostgreSQL。"""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    AGENT_DEMO_MODE = os.getenv("AGENT_DEMO_MODE", "false").lower() == "true"
    AGENT_API_KEY = os.getenv("AGENT_API_KEY", os.getenv("MIMO_API_KEY", ""))
    AGENT_BASE_URL = os.getenv("AGENT_BASE_URL", os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1"))
    AGENT_MODEL = os.getenv("AGENT_MODEL", os.getenv("MIMO_MODEL", "mimo-v2.5-pro"))
    # --- 数据库配置 ---
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    CATALOG_DB_NAME = os.getenv("CATALOG_DB_NAME", "product_catalog")

    # 无密码时不拼 :password@，避免空凭据
    if DB_PASSWORD:
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql+psycopg2://{DB_USER}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Xiaomi MiMo（密钥只从本地 .env / 系统环境读取；修改后由 Flask 热重载）---
    MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
    MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
    MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2.5-pro")
