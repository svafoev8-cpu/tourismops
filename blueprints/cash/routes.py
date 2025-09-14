# C:\tourismops\blueprints\cash\routes.py

from datetime import datetime
from decimal import Decimal, InvalidOperation
import csv
import io

from flask import (
    render_template, redirect, url_for, flash, request,
    abort, send_file
)
from flask_login import login_required, current_user

from extensions import db
from models import CashOperation, AuditLog
from . import bp
from .forms import CashForm
from security import roles_required, read_only_for, ROLE


# =========================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================

def _log(action: str, details: str = ""):
    """Запись действия в аудит."""
    try:
        db.session.add(AuditLog(
            user_id=getattr(current_user, "id", None),
            action=action if not details else f"{action} | {details}",
            timestamp=datetime.utcnow()
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()  # не валим основной поток из-за лога


def _parse_decimal(value, default=None):
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return default


def _apply_filters(q):
    """
    Фильтры истории по query-параметрам:
      ?from=YYYY-MM-DD&to=YYYY-MM-DD&type=income|expense&currency=USD|EUR|UZS&mine=1
    """
    fdate = request.args.get("from")
    tdate = request.args.get("to")
    kind = request.args.get("type")
    curr = request.args.get("currency")
    mine = request.args.get("mine")  # если указать mine=1 — только мои записи

    if fdate:
        try:
            dt = datetime.strptime(fdate, "%Y-%m-%d")
            q = q.filter(CashOperation.timestamp >= dt)
        except ValueError:
            pass

    if tdate:
        try:
            # включительно до конца дня
            dt = datetime.strptime(tdate, "%Y-%m-%d")
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            q = q.filter(CashOperation.timestamp <= dt)
        except ValueError:
            pass

    if kind in ("income", "expense"):
        q = q.filter(CashOperation.type == kind)

    if curr in ("USD", "EUR", "UZS"):
        q = q.filter(CashOperation.currency == curr)

    # ограничение видимости по пользователю (для не-руководителей)
    if mine == "1" or getattr(current_user, "role", "") not in ("admin", "executive"):
        q = q.filter(CashOperation.user_id == current_user.id)

    return q


# =========================
# СПИСОК + ДОБАВЛЕНИЕ
# =========================

@bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required(ROLE["CASHIER"], ROLE["ACCOUNTANT"], ROLE["EXEC"], ROLE["ADMIN"])
@read_only_for(ROLE["CURATOR"])
def list_ops():
    form = CashForm()

    if request.method == "POST" and form.validate_on_submit():
        item = CashOperation(
            user_id=current_user.id,
            type=form.type.data,
            currency=form.currency.data,
            amount=_parse_decimal(form.amount.data, Decimal("0.00")),
            description=form.description.data,
            # если позже добавите поля fio/rate в форму — просто раскомментируйте:
            # fio=form.fio.data,
            # rate=_parse_decimal(form.rate.data),
        )
        db.session.add(item)
        db.session.commit()
        _log("cash:create", f"id={item.id} {item.type} {item.amount} {item.currency}")
        flash("Операция сохранена", "success")
        return redirect(url_for("cash.list_ops"))

    q = CashOperation.query
    # не админ/руководство видят только свои
    if getattr(current_user, "role", "") not in ("admin", "executive"):
        q = q.filter_by(user_id=current_user.id)

    items = q.order_by(CashOperation.timestamp.desc()).limit(200).all()
    return render_template("cash/list.html", items=items, form=form)


# =========================
# ИСТОРИЯ С ФИЛЬТРАМИ
# =========================

@bp.route("/history")
@login_required
@roles_required(ROLE["CASHIER"], ROLE["ACCOUNTANT"], ROLE["EXEC"], ROLE["ADMIN"])
def history():
    q = _apply_filters(CashOperation.query)
    items = q.order_by(CashOperation.timestamp.desc()).all()

    # агрегаты (итоги)
    total_income = sum((op.amount for op in items if op.type == "income"), Decimal())
    total_expense = sum((op.amount for op in items if op.type == "expense"), Decimal())
    balance = (total_income or Decimal()) - (total_expense or Decimal())

    return render_template(
        "cash/history.html",
        items=items,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
    )


# =========================
# РЕДАКТИРОВАНИЕ / УДАЛЕНИЕ
# =========================

@bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(ROLE["CASHIER"], ROLE["ACCOUNTANT"], ROLE["ADMIN"])
@read_only_for(ROLE["CURATOR"])
def edit(item_id):
    item = db.session.get(CashOperation, item_id)
    if not item:
        abort(404)

    # ограничение: не админ/руководство могут править только свои записи
    if getattr(current_user, "role", "") not in ("admin", "executive") and item.user_id != current_user.id:
        abort(403)

    form = CashForm(obj=item)
    if form.validate_on_submit():
        item.type = form.type.data
        item.currency = form.currency.data
        item.amount = _parse_decimal(form.amount.data, item.amount)
        item.description = form.description.data
        # item.fio = getattr(form, "fio", None) and form.fio.data
        # item.rate = _parse_decimal(getattr(form, "rate", None) and form.rate.data, item.rate)
        db.session.commit()
        _log("cash:update", f"id={item.id}")
        flash("Операция обновлена", "success")
        return redirect(url_for("cash.history"))

    return render_template("cash/edit.html", form=form, item=item)


@bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
@roles_required(ROLE["CASHIER"], ROLE["ACCOUNTANT"], ROLE["ADMIN"])
@read_only_for(ROLE["CURATOR"])
def delete(item_id):
    item = db.session.get(CashOperation, item_id)
    if not item:
        abort(404)

    if getattr(current_user, "role", "") not in ("admin", "executive") and item.user_id != current_user.id:
        abort(403)

    db.session.delete(item)
    db.session.commit()
    _log("cash:delete", f"id={item_id}")
    flash("Операция удалена", "success")
    return redirect(url_for("cash.history"))


# =========================
# ПЕЧАТЬ ОРДЕРА (HTML)
# =========================

@bp.route("/order/<int:item_id>")
@login_required
@roles_required(ROLE["CASHIER"], ROLE["ACCOUNTANT"], ROLE["EXEC"], ROLE["ADMIN"])
def order(item_id):
    item = db.session.get(CashOperation, item_id)
    if not item:
        abort(404)
    # не-руководство видят только свои
    if getattr(current_user, "role", "") not in ("admin", "executive") and item.user_id != current_user.id:
        abort(403)
    return render_template("cash/order.html", item=item)


# =========================
# KO-1 / KO-2 → DOCX
# =========================

@bp.route("/order-docx/<int:item_id>")
@login_required
@roles_required(ROLE["CASHIER"], ROLE["ACCOUNTANT"], ROLE["EXEC"], ROLE["ADMIN"])
def order_docx(item_id):
    item = db.session.get(CashOperation, item_id)
    if not item:
        abort(404)

    # не-руководство видят только свои
    if getattr(current_user, "role", "") not in ("admin", "executive") and item.user_id != current_user.id:
        abort(403)

    from docxtpl import DocxTemplate
    from decimal import Decimal
    from num2words import num2words
    import os
    from flask import current_app

    # выбираем шаблон
    doc_name = "ko-1.docx" if item.type == "income" else "ko-2.docx"
    tpl_path = os.path.join(current_app.root_path, "static", "docs", doc_name)
    if not os.path.exists(tpl_path):
        abort(404, f"Шаблон не найден: {tpl_path}")

    # сумма цифрами (две цифры после запятой)
    try:
        amount_rub = f"{Decimal(item.amount or 0):.2f}"
    except Exception:
        amount_rub = f"{item.amount}"

    # сумма прописью (ru)
    try:
        amount_words_base = num2words(Decimal(item.amount or 0), lang="ru").capitalize()
    except Exception:
        amount_words_base = ""

    # контекст под твои плейсхолдеры (doc_no, date, from, basis, amount_rub, amount_words)
    ctx = {
        "doc_no": str(item.id),
        "date": item.timestamp.strftime("%d.%m.%Y") if item.timestamp else "",
        "from": getattr(item, "fio", "") or "",
        "basis": item.description or "",
        "amount_rub": amount_rub,
        "amount_words": f"{amount_words_base} {item.currency}".strip(),
    }

    doc = DocxTemplate(tpl_path)
    doc.render(ctx)

    mem = io.BytesIO()
    doc.save(mem)
    mem.seek(0)
    fname = f"{'KO-1' if item.type=='income' else 'KO-2'}_{item.id}.docx"
    _log("cash:order_docx", f"id={item.id}")
    return send_file(mem, as_attachment=True, download_name=fname,
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# =========================
# ЭКСПОРТ CSV
# =========================

@bp.route("/export.csv")
@login_required
@roles_required(ROLE["CASHIER"], ROLE["ACCOUNTANT"], ROLE["EXEC"], ROLE["ADMIN"])
def export_csv():
    q = _apply_filters(CashOperation.query)
    items = q.order_by(CashOperation.timestamp.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Дата", "Тип", "Сумма", "Валюта", "Пользователь", "Описание"])

    for i in items:
        writer.writerow([
            i.timestamp.strftime("%Y-%m-%d %H:%M") if i.timestamp else "",
            i.type,
            f"{i.amount}",
            i.currency,
            i.user_id,
            (i.description or "").replace("\n", " ").strip()
        ])

    mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))  # с BOM для Excel
    filename = f"cash_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    _log("cash:export", f"rows={len(items)}")
    return send_file(
        mem, mimetype="text/csv", as_attachment=True, download_name=filename
    )
