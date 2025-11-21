import csv
from io import TextIOWrapper

from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, AssetType
from route_decorators import role_required

# Create Blueprint
asset_type_bp = Blueprint("asset_type", __name__)

# Define main page
@asset_type_bp.route("/asset_type", methods=["GET", "POST"])
@role_required("admin", "manager")
def asset_types():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE asset_types AUTO_INCREMENT = 1;"))
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
					# Check for existing asset type by name to avoid duplicates
					# THESE ITEMS WILL ONLY BE ADDED IF THEY DO NOT ALREADY EXIST
					asset_type = (
						AssetType.query.filter_by(name=row.get("name").strip()).first()
						if row.get("name") else None
					)

					# Only add asset type if it does not already exist
					if not asset_type:
						asset_type = AssetType(
							name=row.get("name").strip(),
							category=row.get("category")
							if row.get("category") in ["Tangible", "Intangible"] else None,
							description=row.get("description"),
						)
						db.session.add(asset_type)
						count += 1

				# Commit additions to DB
				db.session.commit()
				flash(f"Successfully imported {count} asset types from CSV!", "success")

			# Handle errors and exceptions
			except Exception as e:
				db.session.rollback()
				flash(f"Error importing CSV: {e}", "danger")

			return redirect("/asset_type")

		# Manual form entry
		name = request.form.get("name", "").strip()
		category = request.form.get("category", "").strip()
		description = request.form.get("description")

		if not name:
			flash("Asset type name is required!", "danger")
			return redirect("/asset_type")

		try:
			new_asset = AssetType(
				name=name,
				category=category,
				description=description
			)

			db.session.add(new_asset)
			db.session.commit()
			flash("Asset type added successfully!", "success")
			return redirect("/asset_type")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/asset_type")

	# DISPLAY TABLE ------------------------------------------------------------------------

	# Handle sorting
	sort = request.args.get("sort", "asset_type_id")
	direction = request.args.get("direction", "asc")
	search = request.args.get("search", None)

	valid_columns = {
		"asset_type_id": AssetType.asset_type_id,
		"name": AssetType.name,
		"category": AssetType.category,
		"description": AssetType.description,
	}

	sort_column = valid_columns.get(sort, AssetType.asset_type_id)

	# Apply search if necessary
	asset_types = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		asset_types = asset_types.order_by(sort_column.desc())
	else:
		asset_types = asset_types.order_by(sort_column.asc())

	return render_template(
		"asset_type.html",
		asset_types=asset_types,
		sort=sort,
		direction=direction
	)

# Define deletion page
@asset_type_bp.route("/asset_type/delete/<int:asset_type_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_asset_type(asset_type_id):
	record = AssetType.query.get(asset_type_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/asset_type")

# Define edit page
@asset_type_bp.route("/asset_type/edit/<int:asset_type_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def edit_asset_type(asset_type_id):
	record = AssetType.query.get_or_404(asset_type_id)

	# Collect form data
	new_name = request.form.get("name", "").strip()
	new_category = request.form.get("category", "").strip()
	new_description = request.form.get("description", "").strip()

	# Basic validation
	if not new_name:
		flash("Type name cannot be empty.", "danger")
		return redirect("/asset_type")

	try:
		record.name = new_name
		record.category = new_category
		record.description = new_description

		# Update table
		db.session.commit()
		flash("Asset type updated successfully!", "success")
	except Exception as e:
		db.session.rollback()
		flash(f"Error updating asset type: {e}", "danger")

	return redirect("/asset_type")


# Search function
def search_for(search):
	query = AssetType.query
	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(AssetType.asset_type_id.ilike(search_pattern)) |
			(AssetType.name.ilike(search_pattern)) |
			(AssetType.category.ilike(search_pattern)) |
			(AssetType.description.ilike(search_pattern))
		)
	return query


