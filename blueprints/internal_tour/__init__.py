from flask import Blueprint
bp = Blueprint("internal_tour", __name__)
from . import routes  # noqa
