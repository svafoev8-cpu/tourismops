from flask import render_template
from flask_login import login_required
from models import InternalTour
from . import bp
from security import roles_required, ROLE

@bp.route("/")
@login_required
@roles_required(ROLE["MANAGER_INT"], ROLE["ACCOUNTANT"], ROLE["EXEC"], ROLE["ADMIN"])
def list_tours():
    items = InternalTour.query.order_by(InternalTour.start_date.desc()).limit(200).all()
    return render_template("internal_tour/list.html", items=items)
