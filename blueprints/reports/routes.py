from flask import render_template
from flask_login import login_required
from . import bp

@bp.route("/sales-summary")
@login_required
def sales_summary():
    return render_template("reports/sales_summary.html")
