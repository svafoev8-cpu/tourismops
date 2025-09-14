# C:\tourismops\blueprints\refs\routes.py
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import Client
from . import bp
from .forms import ClientForm, ACCOUNT_TYPE_CHOICES, ACCOUNT_STATUS_CHOICES

@bp.route("/clients", methods=["GET", "POST"])
@login_required
def clients():
    form = ClientForm()

    # Если пришёл запрос на редактирование через query (?edit=<id>) — подставим данные в форму
    edit_id = request.args.get("edit", type=int)
    if edit_id and request.method == "GET":
        item = Client.query.get_or_404(edit_id)
        form.item_id.data = str(item.id)
        form.code.data = item.code
        form.name.data = item.name
        form.account_type.data = item.account_type
        form.account_status.data = item.account_status

    if form.validate_on_submit():
        # Режим: создать или обновить?
        if form.item_id.data:
            # Обновление
            item = Client.query.get_or_404(int(form.item_id.data))
            item.code = form.code.data.strip()
            item.name = form.name.data.strip()
            item.account_type = form.account_type.data
            item.account_status = form.account_status.data
            try:
                db.session.commit()
                flash("Клиент обновлён", "success")
                return redirect(url_for("refs.clients"))
            except IntegrityError:
                db.session.rollback()
                flash("Код клиента уже существует", "danger")
        else:
            # Создание
            c = Client(
                code=form.code.data.strip(),
                name=form.name.data.strip(),
                account_type=form.account_type.data,
                account_status=form.account_status.data,
            )
            db.session.add(c)
            try:
                db.session.commit()
                flash("Клиент добавлен", "success")
                return redirect(url_for("refs.clients"))
            except IntegrityError:
                db.session.rollback()
                flash("Код клиента уже существует", "danger")

    # Фильтры и поиск
    q = Client.query
    status = request.args.get("status")          # open|closed|None
    acc_type = request.args.get("type")          # одно из ACCOUNT_TYPE_CHOICES
    term = request.args.get("q", "").strip()     # поисковая строка

    if status in ("open", "closed"):
        q = q.filter(Client.account_status == status)
    if acc_type and acc_type in dict(ACCOUNT_TYPE_CHOICES):
        q = q.filter(Client.account_type == acc_type)
    if term:
        like = f"%{term}%"
        q = q.filter((Client.code.ilike(like)) | (Client.name.ilike(like)))

    items = q.order_by(Client.name.asc()).all()
    return render_template(
        "refs/clients.html",
        form=form,
        items=items,
        status=status,
        acc_type=acc_type,
        term=term,
        ACCOUNT_TYPE_CHOICES=ACCOUNT_TYPE_CHOICES,
        ACCOUNT_STATUS_CHOICES=ACCOUNT_STATUS_CHOICES,
    )

@bp.route("/clients/<int:pk>/delete", methods=["POST"])
@login_required
def clients_delete(pk):
    item = Client.query.get_or_404(pk)
    db.session.delete(item)
    db.session.commit()
    flash("Клиент удалён", "warning")
    return redirect(url_for("refs.clients"))
