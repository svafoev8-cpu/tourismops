from flask import Blueprint
bp = Blueprint("reports", __name__)
from . import routes  # noqa
