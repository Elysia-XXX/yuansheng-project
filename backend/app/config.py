"""应用配置：从 .env 或环境变量读取，默认连接本机无密码 PostgreSQL。"""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- 数据库配置 ---
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "postgres")

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
