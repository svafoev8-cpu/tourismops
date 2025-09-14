from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from models import User

from . import bp


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("core.dashboard"))
        else:
            flash("Неверный логин или пароль", "danger")
    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
