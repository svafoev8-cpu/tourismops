from flask import render_template
from flask_login import login_required

from models import ExternalTour
from security import ROLE, roles_required

from . import bp


@bp.route("/")
@login_required
@roles_required(ROLE["MANAGER_EXT"], ROLE["ACCOUNTANT"], ROLE["EXEC"], ROLE["ADMIN"])
def list_tours():
    items = ExternalTour.query.order_by(ExternalTour.start_date.desc()).limit(200).all()
    return render_template("external_tour/list.html", items=items)
