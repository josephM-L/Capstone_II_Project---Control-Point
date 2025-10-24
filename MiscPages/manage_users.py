from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from models import db, User
from route_decorators import role_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET", "POST"])
@role_required("admin")
def users():
	# ADD / UPDATE ------------------------------------------------------------------------
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE users AUTO_INCREMENT = 1;"))
		db.session.commit()

		# Get form data
		username = request.form.get("username", "").strip()
		email = request.form.get("email", "").strip()
		password = request.form.get("password", "").strip()
		full_name = request.form.get("full_name", "").strip()
		role = request.form.get("role", "user").strip()

		hashed_pw = generate_password_hash(password)

		# Validation
		if not username or not email or not hashed_pw:
			flash("Username, email, and password are required!", "danger")
			return redirect("/users")

		try:
			new_user = User(
				username=username,
				email=email,
				password_hash=hashed_pw,  # You can later replace with real hashing
				full_name=full_name,
				role=role
			)
			db.session.add(new_user)
			db.session.commit()
			flash("User added successfully!", "success")
			return redirect("/users")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/users")

	# DISPLAY TABLE ------------------------------------------------------------------------

	# Handle sorting
	sort = request.args.get("sort", "user_id")
	direction = request.args.get("direction", "asc")
	search = request.args.get("search", None)

	valid_columns = {
		"user_id": User.user_id,
		"username": User.username,
		"email": User.email,
		"full_name": User.full_name,
		"role": User.role,
		"created_at": User.created_at,
	}

	sort_column = valid_columns.get(sort, User.user_id)

	# Apply search
	users = search_for(search)

	# Apply sorting and ordering
	if direction == "desc":
		users = users.order_by(sort_column.desc())
	else:
		users = users.order_by(sort_column.asc())

	return render_template(
		"users.html",
		users=users,
		sort=sort,
		direction=direction
	)


@users_bp.route("/users/delete/<int:user_id>", methods=["GET", "POST"])
@role_required("admin")
def delete_user(user_id):
	record = User.query.get(user_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/users")


# Search function
def search_for(search):
	query = User.query
	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(User.user_id.ilike(search_pattern)) |
			(User.username.ilike(search_pattern)) |
			(User.email.ilike(search_pattern)) |
			(User.full_name.ilike(search_pattern)) |
			(User.role.ilike(search_pattern)) |
			(User.created_at.ilike(search_pattern))
		)
	return query
