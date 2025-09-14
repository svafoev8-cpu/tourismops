# C:\tourismops\blueprints\refs\__init__.py
from flask import Blueprint
bp = Blueprint("refs", __name__, url_prefix="/refs")
from . import routes  # noqa
