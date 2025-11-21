from flask import Blueprint, render_template, redirect, request, flash, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

login_bp = Blueprint("login", __name__)

@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.user_id
            session["username"] = user.username
            session["role"] = user.role
            flash("Login successful!", "success")
            return redirect("/")
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login.login"))

    return render_template("login.html")


@login_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect("/")
