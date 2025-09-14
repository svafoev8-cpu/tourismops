from flask import Blueprint

bp = Blueprint("bank", __name__)
from . import routes  # noqa
