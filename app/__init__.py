from __future__ import annotations

import os
from typing import Dict, Optional

from flask import Flask

from app.extensions import csrf, db


def create_app(config: Optional[Dict] = None) -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(app.instance_path, "reservafacil.db"),
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TIMEZONE"] = "America/Lima"

    if config:
        app.config.update(config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    from app.admin import admin as admin_bp
    from app.api import api as api_bp
    from app.cliente import cliente as cliente_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(cliente_bp)

    tables_created: Dict[str, bool] = {"done": False}

    @app.before_request
    def _create_tables_on_first_request() -> None:
        if not tables_created["done"]:
            db.create_all()
            tables_created["done"] = True

    return app