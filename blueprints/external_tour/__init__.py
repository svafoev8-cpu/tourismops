from flask import Blueprint

bp = Blueprint("external_tour", __name__)
from . import routes  # noqa
