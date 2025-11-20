from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, Department, Employee
from route_decorators import role_required

# Create Blueprint
department_bp = Blueprint("department", __name__)

# Define main page
@department_bp.route("/departments", methods=["GET", "POST"])
@role_required("admin", "manager")
def departments():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE departments AUTO_INCREMENT = 1;"))
		db.session.commit()

		# ADD / UPDATE ------------------------------------------------------------------------

		# Manual form entry
		name = request.form.get("name", "").strip()
		manager_id = request.form.get("manager_id")

		# Alert user if required fields are not filled out
		if not name:
			flash("Department name is required!", "danger")
			return redirect("/departments")

		# Create new data entry
		try:
			manager_id_value = int(manager_id) if manager_id else None
			new_department = Department(
				name=name,
				manager_id=manager_id_value
			)

			db.session.add(new_department)

			# commit entry and alert user
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
	search = request.args.get("search", None)

	valid_columns = {
		"department_id": Department.department_id,
		"name": Department.name,
		"manager_id": Department.manager_id,
	}

	sort_column = valid_columns.get(sort, Department.department_id)

	# Apply search if necessary
	departments = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		departments = departments.order_by(sort_column.desc())
	else:
		departments = departments.order_by(sort_column.asc())

	# Preload employees for dropdowns and manager display
	employees = Employee.query.order_by(Employee.first_name, Employee.last_name).all()

	# Display table
	return render_template(
		"departments.html",
		departments=departments,
		employees=employees,
		sort=sort,
		direction=direction
	)

# Define deletion page
@department_bp.route("/departments/delete/<int:department_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_department(department_id):
	record = Department.query.get(department_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/departments")

# Define edit page
@department_bp.route("/departments/edit/<int:department_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def edit_department(department_id):
	record = Department.query.get_or_404(department_id)

	# Collect form data
	new_name = request.form.get("department_name", "").strip()
	new_manager_id = request.form.get("manager_id")

	# Basic validation
	if not new_name:
		flash("Department name cannot be empty.", "danger")
		return redirect("/departments")

	try:
		record.name = new_name
		# Allow setting manager to None if the field is blank
		record.manager_id = int(new_manager_id) if new_manager_id else None

		# Update table
		db.session.commit()
		flash("Department updated successfully!", "success")
	except Exception as e:
		db.session.rollback()
		flash(f"Error updating department: {e}", "danger")

	return redirect("/departments")



# Search function
def search_for(search):
	# Create a join to query Department and Employee tables
	query = Department.query.join(Employee, Department.manager_id == Employee.employee_id, isouter=True)

	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(Department.department_id.cast(db.String).ilike(search_pattern)) |
			(Department.name.ilike(search_pattern)) |
			(Department.manager_id.cast(db.String).ilike(search_pattern)) |
			(Employee.first_name.ilike(search_pattern)) |
			(Employee.last_name.ilike(search_pattern))
		)

	return query

