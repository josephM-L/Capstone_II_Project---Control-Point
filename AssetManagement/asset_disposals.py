import csv
from datetime import datetime
from io import TextIOWrapper
from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, AssetDisposal, Asset
from route_decorators import role_required

# Create Blueprint
asset_disposal_bp = Blueprint("asset_disposal", __name__)

# Define main page
@asset_disposal_bp.route("/asset_disposals", methods=["GET", "POST"])
@role_required("admin", "manager")
def asset_disposals():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE asset_disposals AUTO_INCREMENT = 1;"))
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

					# Parse dates and numbers
					disposal_date = (
						datetime.strptime(row.get("disposal_date"), "%Y-%m-%d").date()
						if row.get("disposal_date") else None
					)
					sale_value = (
						float(row.get("sale_value")) if row.get("sale_value") else None
					)

					# Only add disposal records if the asset exists and disposal_date is valid
					if asset and disposal_date:
						disposal = AssetDisposal(
							asset_id=asset.asset_id,
							disposal_date=disposal_date,
							method=row.get("method"),
							sale_value=sale_value,
							notes=row.get("notes"),
						)
						db.session.add(disposal)
						count += 1

				# Commit additions to DB
				db.session.commit()
				flash(f"Successfully imported {count} asset disposals from CSV!", "success")

			# Handle errors and exceptions
			except Exception as e:
				db.session.rollback()
				flash(f"Error importing CSV: {e}", "danger")

			return redirect("/asset_disposals")

		# Manual form entry
		asset_id = request.form.get("asset_id")
		disposal_date = request.form.get("disposal_date")
		method = request.form.get("method")
		sale_value = request.form.get("sale_value") or None
		notes = request.form.get("notes") or None

		if not asset_id or not disposal_date or not method:
			flash("Asset, disposal date, and method are required!", "danger")
			return redirect("/asset_disposals")

		try:
			new_disposal = AssetDisposal(
				asset_id=int(asset_id),
				disposal_date=disposal_date,
				method=method,
				sale_value=float(sale_value) if sale_value else None,
				notes=notes
			)

			db.session.add(new_disposal)
			db.session.commit()
			flash("Asset disposal recorded successfully!", "success")
			return redirect("/asset_disposals")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/asset_disposals")

	# DISPLAY TABLE ------------------------------------------------------------------------

	assets = Asset.query.order_by(Asset.name).all()

	# Handle sorting
	sort = request.args.get("sort", "disposal_id")
	direction = request.args.get("direction", "asc")
	search = request.args.get("search", None)

	valid_columns = {
		"disposal_id": AssetDisposal.disposal_id,
		"asset_id": AssetDisposal.asset_id,
		"disposal_date": AssetDisposal.disposal_date,
		"method": AssetDisposal.method,
		"sale_value": AssetDisposal.sale_value,
		"notes": AssetDisposal.notes,
	}

	sort_column = valid_columns.get(sort, AssetDisposal.disposal_id)

	# Apply search if necessary
	disposals = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		disposals = disposals.order_by(sort_column.desc())
	else:
		disposals = disposals.order_by(sort_column.asc())

	return render_template(
		"asset_disposals.html",
		disposals=disposals,
		assets=assets,
		sort=sort,
		direction=direction
	)

# Define deletion page
@asset_disposal_bp.route("/asset_disposals/delete/<int:disposal_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_asset_disposal(disposal_id):
	record = AssetDisposal.query.get(disposal_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/asset_disposals")

# Define edit page
@asset_disposal_bp.route("/asset_disposals/edit/<int:disposal_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def edit_asset_disposal(disposal_id):
	record = AssetDisposal.query.get_or_404(disposal_id)

	# Collect form data
	disposal_date = request.form.get("disposal_date")
	method = request.form.get("method")
	sale_value = request.form.get("sale_value")
	notes = request.form.get("notes", "").strip()

	# Basic validation
	if not disposal_date or not method:
		flash("Disposal date and method cannot be empty.", "danger")
		return redirect("/asset_disposals")

	try:
		record.disposal_date = disposal_date
		record.method = method
		record.sale_value = sale_value or None
		record.notes = notes or None

		# Update table
		db.session.commit()
		flash("Asset disposal record updated successfully!", "success")
	except Exception as e:
		db.session.rollback()
		flash(f"Error updating disposal record: {e}", "danger")

	return redirect("/asset_disposals")


# Search function
def search_for(search):
	# Create a join to query AssetDisposal and Asset tables
	query = AssetDisposal.query.join(Asset, AssetDisposal.asset_id == Asset.asset_id)

	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(AssetDisposal.disposal_id.cast(db.String).ilike(search_pattern)) |
			(Asset.asset_tag.ilike(search_pattern)) |
			(Asset.name.ilike(search_pattern)) |
			(AssetDisposal.method.ilike(search_pattern)) |
			(AssetDisposal.sale_value.cast(db.String).ilike(search_pattern)) |
			(AssetDisposal.notes.ilike(search_pattern)) |
			(AssetDisposal.disposal_date.cast(db.String).ilike(search_pattern))
		)

	return query
