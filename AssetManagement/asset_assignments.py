import csv
from datetime import datetime
from io import TextIOWrapper
from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, AssetAssignment, Asset, Employee
from route_decorators import role_required

# Create Blueprint
asset_assignment_bp = Blueprint("asset_assignment", __name__)

# Define main page
@asset_assignment_bp.route("/asset_assignments", methods=["GET", "POST"])
@role_required("admin", "manager", "user")
def asset_assignments():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE asset_assignments AUTO_INCREMENT = 1;"))
		db.session.commit()

		# ADD / UPDATE ------------------------------------------------------------------------

		# For uploading CSV
		if "csv_file" in request.files and request.files["csv_file"].filename:
			file = request.files["csv_file"]
			try:
				stream = TextIOWrapper(file.stream, encoding="utf-8")
				csv_reader = csv.DictReader(stream)
				count = 0

				for row in csv_reader:
					# Look up related foreign keys by name if given
					# THESE ITEMS WILL ONLY BE ADDED IF THEY EXIST IN THEIR RESPECTIVE TABLES
					asset = (
						Asset.query.filter_by(asset_id=row.get("asset_id")).first()
						if row.get("asset_id") else None
					)
					employee = (
						Employee.query.filter_by(employee_id=row.get("employee_id")).first()
						if row.get("employee_id") else None
					)

					# Parse dates
					assigned_date = (
						datetime.strptime(row.get("assigned_date"), "%Y-%m-%d").date()
						if row.get("assigned_date") else None
					)
					returned_date = (
						datetime.strptime(row.get("returned_date"), "%Y-%m-%d").date()
						if row.get("returned_date") else None
					)

					# Only add assignment records if the referenced items exist
					if asset and employee and assigned_date:
						assignment = AssetAssignment(
							asset_id=asset.asset_id,
							employee_id=employee.employee_id,
							assigned_date=assigned_date,
							returned_date=returned_date,
						)
						db.session.add(assignment)
						count += 1

				# Commit additions to DB
				db.session.commit()
				flash(f"Successfully imported {count} asset assignments from CSV!", "success")

			# Handle errors and exceptions
			except Exception as e:
				db.session.rollback()
				flash(f"Error importing CSV: {e}", "danger")

			return redirect("/asset_assignments")

		# Manual form entry
		asset_id = request.form.get("asset_id")
		employee_id = request.form.get("employee_id")
		assigned_date = request.form.get("assigned_date")
		returned_date = request.form.get("returned_date") or None

		# Alert user if required fields are not filled out
		if not asset_id or not employee_id or not assigned_date:
			flash("Asset, employee, and assigned date are required!", "danger")
			return redirect("/asset_assignments")

		# Create new data entry
		try:
			new_assignment = AssetAssignment(
				asset_id=int(asset_id),
				employee_id=int(employee_id),
				assigned_date=assigned_date,
				returned_date=returned_date
			)

			db.session.add(new_assignment)

			# Update asset table
			asset = Asset.query.get(asset_id)
			if asset:
				asset.assigned_to = employee_id

			# commit entry and alert user
			db.session.commit()
			flash("Asset assignment added successfully!", "success")
			return redirect("/asset_assignments")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/asset_assignments")

	# DISPLAY TABLE ------------------------------------------------------------------------

	assets = Asset.query.order_by(Asset.name).all()
	employees = Employee.query.order_by(Employee.last_name, Employee.first_name).all()

	# Handle sorting
	sort = request.args.get("sort", "assignment_id")
	direction = request.args.get("direction", "asc")
	search = request.args.get("search", None)

	valid_columns = {
		"assignment_id": AssetAssignment.assignment_id,
		"asset_id": AssetAssignment.asset_id,
		"employee_id": AssetAssignment.employee_id,
		"assigned_date": AssetAssignment.assigned_date,
		"returned_date": AssetAssignment.returned_date,
	}

	sort_column = valid_columns.get(sort, AssetAssignment.assignment_id)

	# Apply search if necessary
	assignments = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		assignments = assignments.order_by(sort_column.desc())
	else:
		assignments = assignments.order_by(sort_column.asc())

	# Display table
	return render_template(
		"asset_assignments.html",
		assignments=assignments,
		assets=assets,
		employees=employees,
		sort=sort,
		direction=direction
	)

# Define deletion page
@asset_assignment_bp.route("/asset_assignments/delete/<int:assignment_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_asset_assignment(assignment_id):
	assignment = AssetAssignment.query.get(assignment_id)
	if assignment:
		db.session.delete(assignment)
		db.session.commit()
	return redirect("/asset_assignments")

# Define edit page
@asset_assignment_bp.route("/asset_assignments/edit/<int:assignment_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def edit_asset_assignment(assignment_id):
	record = AssetAssignment.query.get_or_404(assignment_id)

	# Collect form data
	asset_id = request.form.get("asset_id")
	employee_id = request.form.get("employee_id")
	assigned_date = request.form.get("assigned_date")
	returned_date = request.form.get("returned_date")

	# Basic validation
	if not asset_id or not employee_id or not assigned_date:
		flash("Asset, employee, and assigned date cannot be empty.", "danger")
		return redirect("/asset_assignments")

	try:
		record.asset_id = asset_id
		record.employee_id = employee_id
		record.assigned_date = assigned_date
		record.returned_date = returned_date or None

		# Update table
		asset = Asset.query.get(asset_id)
		if asset:
			asset.assigned_to = employee_id

		db.session.commit()
		flash("Assignment updated successfully!", "success")
	except Exception as e:
		db.session.rollback()
		flash(f"Error updating assignment: {e}", "danger")

	return redirect("/asset_assignments")


# Search function
def search_for(search):
	# Create a join to query asset_assignment, asset, and employee tables
	query = AssetAssignment.query \
		.join(Asset, AssetAssignment.asset_id == Asset.asset_id) \
		.join(Employee, AssetAssignment.employee_id == Employee.employee_id)
	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(AssetAssignment.assignment_id.ilike(search_pattern)) |
			(Asset.asset_tag.ilike(search_pattern)) |
			(Employee.first_name.ilike(search_pattern)) |
			(Employee.last_name.ilike(search_pattern)) |
			(AssetAssignment.assigned_date.ilike(search_pattern)) |
			(AssetAssignment.returned_date.ilike(search_pattern))
		)

	return query
