"""应用工厂。"""
from flask import Flask
from flask_cors import CORS
from sqlalchemy import text

from .config import Config
from .db import db


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)  # 开发期放开跨域；生产可收紧为具体前端域名
    db.init_app(app)

    # 注册蓝图
    from .routes.health import bp as health_bp
    from .routes.dataset import bp as dataset_bp
    from .routes.analysis import bp as analysis_bp
    from .routes.reviews import bp as reviews_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(dataset_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(reviews_bp)

    # 确保业务表存在（已存在的表不受影响）
    with app.app_context():
        from . import models  # noqa: F401  导入模型以便 create_all 识别

        db.create_all()
        # create_all 不会给已有表补列；这里做幂等的小型迁移。
        db.session.execute(
            text("ALTER TABLE dataset_info ADD COLUMN IF NOT EXISTS source_product_id VARCHAR(50)")
        )
        db.session.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'analysis_result' AND column_name = 'sentiment_polarity'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'analysis_result' AND column_name = 'evaluation_level'
                ) THEN
                    ALTER TABLE analysis_result RENAME COLUMN sentiment_polarity TO evaluation_level;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'analysis_result' AND column_name = 'emotion_dimension'
                ) THEN
                    ALTER TABLE analysis_result ADD COLUMN emotion_dimension VARCHAR(30);
                END IF;
            END $$;
        """))
        db.session.commit()

    return app
