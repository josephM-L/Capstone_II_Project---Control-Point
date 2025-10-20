from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, Department, Employee

department_bp = Blueprint("department", __name__)


@department_bp.route("/departments", methods=["GET", "POST"])
def departments():
	# ADD / UPDATE ------------------------------------------------------------------------
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE departments AUTO_INCREMENT = 1;"))
		db.session.commit()

		# Manual form entry
		name = request.form.get("name", "").strip()
		manager_id = request.form.get("manager_id")

		if not name:
			flash("Department name is required!", "danger")
			return redirect("/departments")

		try:
			manager_id_value = int(manager_id) if manager_id else None
			new_department = Department(
				name=name,
				manager_id=manager_id_value
			)

			db.session.add(new_department)
			db.session.commit()
			flash("Department added successfully!", "success")
			return redirect("/departments")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/departments")

	# DISPLAY TABLE ------------------------------------------------------------------------

	# Handle sorting
	sort = request.args.get("sort", "department_id")
	direction = request.args.get("direction", "asc")

	valid_columns = {
		"department_id": Department.department_id,
		"name": Department.name,
		"manager_id": Department.manager_id,
	}

	sort_column = valid_columns.get(sort, Department.department_id)

	if direction == "desc":
		departments = Department.query.order_by(sort_column.desc()).all()
	else:
		departments = Department.query.order_by(sort_column.asc()).all()

	# Preload employees for dropdowns and manager display
	employees = Employee.query.order_by(Employee.first_name, Employee.last_name).all()

	return render_template(
		"departments.html",
		departments=departments,
		employees=employees,
		sort=sort,
		direction=direction
	)


@department_bp.route("/departments/delete/<int:department_id>", methods=["GET", "POST"])
def delete_department(department_id):
	record = Department.query.get(department_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/departments")
