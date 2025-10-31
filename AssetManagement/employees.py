import csv
from io import TextIOWrapper
from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, Employee, Department
from route_decorators import role_required

employee_bp = Blueprint("employee", __name__)


@employee_bp.route("/employees", methods=["GET", "POST"])
@role_required("admin", "manager", "user")
def employees():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE employees AUTO_INCREMENT = 1;"))
		db.session.commit()

		# Handle CSV upload
		if "csv_file" in request.files and request.files["csv_file"].filename:
			file = request.files["csv_file"]
			try:
				stream = TextIOWrapper(file.stream, encoding="utf-8")
				csv_reader = csv.DictReader(stream)
				count = 0

				for row in csv_reader:
					# Look up department by name if provided
					department = (
						Department.query.filter_by(name=row.get("department")).first()
						if row.get("department") else None
					)

					# Build employee record
					employee = Employee(
						first_name=row.get("first_name", "").strip(),
						last_name=row.get("last_name", "").strip(),
						email=row.get("email", "").strip(),
						phone=row.get("phone", "").strip(),
						department_id=department.department_id if department else None,
						role=row.get("role", "").strip(),
						status=row.get("status", "Active").strip(),
					)

					db.session.add(employee)
					count += 1

				db.session.commit()
				flash(f"Successfully imported {count} employees from CSV!", "success")

			except Exception as e:
				db.session.rollback()
				flash(f"Error importing CSV: {e}", "danger")

			return redirect("/employees")

		# Manual form entry
		first_name = request.form.get("first_name", "").strip()
		last_name = request.form.get("last_name", "").strip()
		email = request.form.get("email", "").strip()
		phone = request.form.get("phone", "").strip()
		department_id = request.form.get("department_id")
		role = request.form.get("role", "").strip()
		status = request.form.get("status", "Active").strip()

		# Validation
		if not first_name or not last_name or not email:
			flash("First name, last name, and email are required!", "danger")
			return redirect("/employees")

		try:
			department_id_val = int(department_id) if department_id else None

			new_employee = Employee(
				first_name=first_name,
				last_name=last_name,
				email=email,
				phone=phone,
				department_id=department_id_val,
				role=role,
				status=status
			)

			db.session.add(new_employee)
			db.session.commit()
			flash("Employee added successfully!", "success")
			return redirect("/employees")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/employees")

	# DISPLAY TABLE ------------------------------------------------------------------------

	# Query related tables for dropdowns
	departments = Department.query.order_by(Department.name).all()

	# Handle sorting
	sort = request.args.get("sort", "employee_id")  # Default sort column
	direction = request.args.get("direction", "asc")  # Default sort direction
	search = request.args.get("search", None)

	# Define valid columns to avoid SQL injection attacks
	valid_columns = {
		"employee_id": Employee.employee_id,
		"first_name": Employee.first_name,
		"last_name": Employee.last_name,
		"email": Employee.email,
		"phone": Employee.phone,
		"role": Employee.role,
		"status": Employee.status,
		"department_id": Employee.department_id,
	}

	sort_column = valid_columns.get(sort, Employee.employee_id)

	# Apply search if necessary
	employees = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		employees = employees.order_by(sort_column.desc())
	else:
		employees = employees.order_by(sort_column.asc())

	# Render table and forms
	return render_template(
		"employees.html",
		employees=employees,
		departments=departments,
		sort=sort,
		direction=direction
	)


@employee_bp.route("/employees/delete/<int:employee_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_employee(employee_id):
	employee = Employee.query.get(employee_id)
	if employee:
		db.session.delete(employee)
		db.session.commit()
	return redirect("/employees")

@employee_bp.route("/employees/edit/<int:employee_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def edit_employee(employee_id):
	record = Employee.query.get_or_404(employee_id)

	first_name = request.form.get("first_name", "").strip()
	last_name = request.form.get("last_name", "").strip()
	email = request.form.get("email", "").strip()
	phone = request.form.get("phone", "").strip()
	department_id = request.form.get("department_id")
	role = request.form.get("role", "").strip()
	status = request.form.get("status", "Active")

	if not first_name or not last_name or not email:
		flash("First name, last name, and email are required.", "danger")
		return redirect("/employees")

	try:
		record.first_name = first_name
		record.last_name = last_name
		record.email = email
		record.phone = phone
		record.department_id = department_id if department_id else None
		record.role = role
		record.status = status

		db.session.commit()
		flash("Employee updated successfully!", "success")
	except Exception as e:
		db.session.rollback()
		flash(f"Error updating employee: {e}", "danger")

	return redirect("/employees")



# Search function
def search_for(search):
	query = Employee.query
	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(Employee.employee_id.ilike(search_pattern)) |
			(Employee.first_name.ilike(search_pattern)) |
			(Employee.last_name.ilike(search_pattern)) |
			(Employee.email.ilike(search_pattern)) |
			(Employee.phone.ilike(search_pattern)) |
			(Employee.role.ilike(search_pattern)) |
			(Employee.status.ilike(search_pattern)) |
			(Employee.department_id.ilike(search_pattern))
		)

	return query