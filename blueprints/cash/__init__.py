from flask import Blueprint
bp = Blueprint("cash", __name__)
from . import routes  # noqa
