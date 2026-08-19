from flask import Blueprint

cliente = Blueprint("cliente", __name__, url_prefix="/")

from app.cliente import routes  # noqa: E402, F401