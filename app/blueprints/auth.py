from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from ..extensions import db, limiter
from ..forms import LoginForm, RegisterForm
from ..models import User

bp = Blueprint("auth", __name__)


@bp.route("/", methods=["GET", "POST"])
@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(request.args.get("next") or url_for("main.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists.", "danger")
        else:
            user = User(username=form.username.data, role=form.role.data, mobile=form.mobile.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please sign in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("auth.login"))
