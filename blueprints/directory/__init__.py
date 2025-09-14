from flask import Blueprint
bp = Blueprint("directory", __name__)
from . import routes  # noqa
