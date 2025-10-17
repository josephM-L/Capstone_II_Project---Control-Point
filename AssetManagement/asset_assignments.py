import csv
from io import TextIOWrapper
from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, AssetAssignment, Asset, Employee

asset_assignment_bp = Blueprint("asset_assignment", __name__)


@asset_assignment_bp.route("/asset_assignments", methods=["GET", "POST"])
def asset_assignments():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE asset_assignments AUTO_INCREMENT = 1;"))
		db.session.commit()

		# Handle CSV upload
		if "csv_file" in request.files and request.files["csv_file"].filename:
			file = request.files["csv_file"]
			try:
				stream = TextIOWrapper(file.stream, encoding="utf-8")
				csv_reader = csv.DictReader(stream)
				count = 0

				for row in csv_reader:
					# Find asset and employee by ID or name if available
					asset = (
						Asset.query.filter_by(asset_id=row.get("asset_id")).first()
						if row.get("asset_id") else None
					)
					employee = (
						Employee.query.filter_by(email=row.get("employee_email")).first()
						if row.get("employee_email") else None
					)

					if not asset or not employee:
						continue

					assignment = AssetAssignment(
						asset_id=asset.asset_id,
						employee_id=employee.employee_id,
						assigned_date=row.get("assigned_date"),
						returned_date=row.get("returned_date") or None,
					)

					db.session.add(assignment)
					count += 1

				db.session.commit()
				flash(f"Successfully imported {count} assignments from CSV!", "success")

			except Exception as e:
				db.session.rollback()
				flash(f"Error importing CSV: {e}", "danger")

			return redirect("/asset_assignments")

		# Manual form entry
		asset_id = request.form.get("asset_id")
		employee_id = request.form.get("employee_id")
		assigned_date = request.form.get("assigned_date")
		returned_date = request.form.get("returned_date") or None

		if not asset_id or not employee_id or not assigned_date:
			flash("Asset, employee, and assigned date are required!", "danger")
			return redirect("/asset_assignments")

		try:
			new_assignment = AssetAssignment(
				asset_id=int(asset_id),
				employee_id=int(employee_id),
				assigned_date=assigned_date,
				returned_date=returned_date
			)

			db.session.add(new_assignment)
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

	valid_columns = {
		"assignment_id": AssetAssignment.assignment_id,
		"asset_id": AssetAssignment.asset_id,
		"employee_id": AssetAssignment.employee_id,
		"assigned_date": AssetAssignment.assigned_date,
		"returned_date": AssetAssignment.returned_date,
	}

	sort_column = valid_columns.get(sort, AssetAssignment.assignment_id)

	if direction == "desc":
		assignments = AssetAssignment.query.order_by(sort_column.desc()).all()
	else:
		assignments = AssetAssignment.query.order_by(sort_column.asc()).all()

	return render_template(
		"asset_assignments.html",
		assignments=assignments,
		assets=assets,
		employees=employees,
		sort=sort,
		direction=direction
	)


@asset_assignment_bp.route("/asset_assignments/delete/<int:assignment_id>", methods=["GET", "POST"])
def delete_asset_assignment(assignment_id):
	assignment = AssetAssignment.query.get(assignment_id)
	if assignment:
		db.session.delete(assignment)
		db.session.commit()
	return redirect("/asset_assignments")
