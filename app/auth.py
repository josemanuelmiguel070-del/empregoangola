from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from .extensions import db
from .models import AdminUser

auth = Blueprint("auth", __name__, url_prefix="/admin")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    next_url = request.values.get("next", "")
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db.session.query(AdminUser).filter_by(email=email).first()
        if user is not None and user.is_active and user.check_password(password):
            login_user(user)
            if next_url.startswith("/admin/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("admin.dashboard"))
        flash("Email ou palavra-passe inválidos.", "error")

    return render_template("admin/login.html", next_url=next_url)


@auth.post("/logout")
def logout():
    logout_user()
    flash("Sessão terminada.", "success")
    return redirect(url_for("auth.login"))
