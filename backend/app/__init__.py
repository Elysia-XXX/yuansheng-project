"""应用工厂。"""
from flask import Flask
from flask_cors import CORS

from .config import Config
from .db import db


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)  # 开发期放开跨域；生产可收紧为具体前端域名
    db.init_app(app)

    # 注册蓝图
    from .routes.health import bp as health_bp

    app.register_blueprint(health_bp, url_prefix="/api")

    return app
