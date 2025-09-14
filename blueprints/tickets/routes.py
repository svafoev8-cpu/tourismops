from flask import render_template
from flask_login import login_required
from models import TicketSale
from . import bp
from security import roles_required, ROLE


@bp.route("/")
@login_required
@roles_required(ROLE["FINANCIER"], ROLE["ACCOUNTANT"], ROLE["EXEC"], ROLE["ADMIN"])
def list_sales():
    items = TicketSale.query.order_by(TicketSale.sale_date.desc()).limit(200).all()
    return render_template("tickets/list.html", items=items)
