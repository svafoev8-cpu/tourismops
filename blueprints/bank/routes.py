from flask import render_template
from flask_login import login_required
from models import BankOperation
from . import bp
from security import roles_required, ROLE

@bp.route("/")
@login_required
@roles_required(ROLE["FINANCIER"], ROLE["ACCOUNTANT"], ROLE["EXEC"], ROLE["ADMIN"])
def list_ops():
    items = BankOperation.query.order_by(BankOperation.timestamp.desc()).limit(200).all()
    return render_template("bank/list.html", items=items)
