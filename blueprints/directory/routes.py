from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensions import db
from models import Subagent, Supplier
from security import ROLE, roles_required

from . import bp


@bp.route("/suppliers")
@login_required
@roles_required(ROLE["ACCOUNTANT"], ROLE["ADMIN"])
def suppliers_list():
    q = request.args.get("q")
    qry = Supplier.query
    if q:
        like = f"%{q}%"
        qry = qry.filter((Supplier.code.ilike(like)) | (Supplier.name.ilike(like)))
    items = qry.order_by(Supplier.name.asc()).all()
    return render_template("directory/suppliers_list.html", items=items, q=q)


@bp.route("/suppliers/new", methods=["GET", "POST"])
@login_required
@roles_required(ROLE["ACCOUNTANT"], ROLE["ADMIN"])
def suppliers_new():
    if request.method == "POST":
        db.session.add(
            Supplier(
                code=request.form.get("code"),
                name=request.form.get("name"),
                phone=request.form.get("phone"),
            )
        )
        db.session.commit()
        flash("Поставщик добавлен", "success")
        return redirect(url_for("directory.suppliers_list"))
    return render_template("directory/suppliers_form.html", item=None)


@bp.route("/suppliers/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(ROLE["ACCOUNTANT"], ROLE["ADMIN"])
def suppliers_edit(item_id):
    item = db.session.get(Supplier, item_id)
    if request.method == "POST":
        item.code = request.form.get("code")
        item.name = request.form.get("name")
        item.phone = request.form.get("phone")
        db.session.commit()
        flash("Поставщик обновлён", "success")
        return redirect(url_for("directory.suppliers_list"))
    return render_template("directory/suppliers_form.html", item=item)


@bp.route("/subagents")
@login_required
@roles_required(ROLE["ACCOUNTANT"], ROLE["ADMIN"])
def subagents_list():
    q = request.args.get("q")
    qry = Subagent.query
    if q:
        like = f"%{q}%"
        qry = qry.filter((Subagent.code.ilike(like)) | (Subagent.name.ilike(like)))
    items = qry.order_by(Subagent.name.asc()).all()
    return render_template("directory/subagents_list.html", items=items, q=q)


@bp.route("/subagents/new", methods=["GET", "POST"])
@login_required
@roles_required(ROLE["ACCOUNTANT"], ROLE["ADMIN"])
def subagents_new():
    if request.method == "POST":
        db.session.add(
            Subagent(
                code=request.form.get("code"),
                name=request.form.get("name"),
            )
        )
        db.session.commit()
        flash("Субагент добавлен", "success")
        return redirect(url_for("directory.subagents_list"))
    return render_template("directory/subagents_form.html", item=None)


@bp.route("/subagents/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(ROLE["ACCOUNTANT"], ROLE["ADMIN"])
def subagents_edit(item_id):
    item = db.session.get(Subagent, item_id)
    if request.method == "POST":
        item.code = request.form.get("code")
        item.name = request.form.get("name")
        db.session.commit()
        flash("Субагент обновлён", "success")
        return redirect(url_for("directory.subagents_list"))
    return render_template("directory/subagents_form.html", item=item)
