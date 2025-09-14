from flask import render_template
from flask_login import login_required
from . import bp


@bp.route("/")
@login_required
def index():
    return render_template("core/dashboard.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("core/dashboard.html")
