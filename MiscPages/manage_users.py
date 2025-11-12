from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from models import db, User, Employee
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
		employee_id = request.form.get("employee_id", "").strip() or None

		hashed_pw = generate_password_hash(password)

		# Validation
		if not username or not email or not hashed_pw:
			flash("Username, email, and password are required!", "danger")
			return redirect("/users")

		try:
			new_user = User(
				username=username,
				email=email,
				password_hash=hashed_pw,
				full_name=full_name,
				role=role,
				employee_id=employee_id
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

	# Get data from employees table
	employees = Employee.query.all()

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
		direction=direction,
		employees=employees
	)


@users_bp.route("/users/delete/<int:user_id>", methods=["GET", "POST"])
@role_required("admin")
def delete_user(user_id):
	record = User.query.get(user_id)
	if record:
		db.session.delete(record)
		db.session.commit()
		flash("User and related employee and assignments deleted successfully!", "success")
	return redirect("/users")


@users_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_user(user_id):
	user = User.query.get_or_404(user_id)

	new_username = request.form.get("username", "").strip()
	new_email = request.form.get("email", "").strip()
	new_full_name = request.form.get("full_name", "").strip()
	new_role = request.form.get("role", "").strip()
	new_password = request.form.get("password", "").strip()

	if not new_username or not new_email:
		flash("Username and email cannot be empty.", "danger")
		return redirect("/users")

	try:
		user.username = new_username
		user.email = new_email
		user.full_name = new_full_name
		if new_role in ["admin", "manager", "user"]:
			user.role = new_role

		if new_password:
			new_hash = generate_password_hash(new_password)
			user.password_hash = new_hash

		db.session.commit()
		flash("User updated successfully!", "success")
	except Exception as e:
		db.session.rollback()
		flash(f"Error updating user: {e}", "danger")

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
