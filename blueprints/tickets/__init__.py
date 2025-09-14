from flask import Blueprint

bp = Blueprint("tickets", __name__)
from . import routes  # noqa
