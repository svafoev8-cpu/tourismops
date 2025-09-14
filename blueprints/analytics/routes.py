from flask import render_template
from flask_login import login_required
from . import bp


@bp.route("/ar-aging")
@login_required
def ar_aging():
    return render_template("analytics/ar_aging.html")
