import csv
from io import TextIOWrapper

from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, AssetStatus
from route_decorators import role_required

# Create Blueprint
asset_status_bp = Blueprint("asset_status", __name__)

# Define main page
@asset_status_bp.route("/asset_status", methods=["GET", "POST"])
@role_required("admin", "manager")
def asset_statuses():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE asset_statuses AUTO_INCREMENT = 1;"))
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
					# THESE ITEMS WILL ONLY BE ADDED IF THEY DO NOT ALREADY EXIST
					existing_status = (
						AssetStatus.query.filter_by(status_name=row.get("status_name")).first()
						if row.get("status_name") else None
					)

					# Only add status if it does not already exist
					if not existing_status and row.get("status_name"):
						status = AssetStatus(
							status_name=row.get("status_name").strip(),
						)
						db.session.add(status)
						count += 1

				# Commit additions to DB
				db.session.commit()
				flash(f"Successfully imported {count} asset statuses from CSV!", "success")

			# Handle errors and exceptions
			except Exception as e:
				db.session.rollback()
				flash(f"Error importing CSV: {e}", "danger")

			return redirect("/asset_status")

		# Manual form entry
		status_name = request.form.get("status_name", "").strip()

		if not status_name:
			flash("Status name is required!", "danger")
			return redirect("/asset_status")

		try:
			new_status = AssetStatus(
				status_name=status_name
			)
			db.session.add(new_status)
			db.session.commit()
			flash("Asset status added successfully!", "success")
			return redirect("/asset_status")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/asset_status")

	# DISPLAY TABLE ------------------------------------------------------------------------

	# Handle sorting
	sort = request.args.get("sort", "status_id")
	direction = request.args.get("direction", "asc")
	search = request.args.get("search", None)

	valid_columns = {
		"status_id": AssetStatus.status_id,
		"status_name": AssetStatus.status_name,
	}

	sort_column = valid_columns.get(sort, AssetStatus.status_id)

	# Apply search if necessary
	statuses = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		statuses = statuses.order_by(sort_column.desc())
	else:
		statuses = statuses.order_by(sort_column.asc())

	return render_template(
		"asset_status.html",
		statuses=statuses,
		sort=sort,
		direction=direction
	)

# Define deletion page
@asset_status_bp.route("/asset_status/delete/<int:status_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_asset_status(status_id):
	record = AssetStatus.query.get(status_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/asset_status")

# Define edit page
@asset_status_bp.route("/asset_status/edit/<int:status_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def edit_asset_status(status_id):
	record = AssetStatus.query.get_or_404(status_id)

	# Collect form data
	new_name = request.form.get("status_name", "").strip()

	# Basic validation
	if not new_name:
		flash("Status name cannot be empty.", "danger")
		return redirect("/asset_status")

	try:
		record.status_name = new_name

		# Update table
		db.session.commit()
		flash("Asset status updated successfully!", "success")
	except Exception as e:
		db.session.rollback()
		flash(f"Error updating status: {e}", "danger")

	return redirect("/asset_status")


# Search function
def search_for(search):
	query = AssetStatus.query
	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(AssetStatus.status_id.ilike(search_pattern)) |
			(AssetStatus.status_name.ilike(search_pattern))
		)
	return query
