from flask import Blueprint
bp = Blueprint("analytics", __name__)
from . import routes  # noqa
