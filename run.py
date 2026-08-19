from __future__ import annotations

import config

from app import create_app
from app.extensions import db
from app.models import Servicio

app = create_app()


def _auto_seed_if_empty() -> None:
    with app.app_context():
        db.create_all()
        exists = db.session.execute(db.select(Servicio)).scalars().first()
        if exists is None:
            from seed import seed

            seed()
            print("Base de datos vacía: se ejecutó el seed automático (python seed.py).")
        else:
            print("Base de datos ya contiene datos.")


_auto_seed_if_empty()

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=config.APP_ENV == "development",
        use_reloader=False,
    )