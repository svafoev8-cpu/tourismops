from flask import Blueprint

bp = Blueprint("auth", __name__)

from . import routes  # подтягиваем маршруты, чтобы они зарегистрировались
