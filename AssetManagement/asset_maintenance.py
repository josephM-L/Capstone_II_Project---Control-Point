import csv
from io import TextIOWrapper
from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, AssetMaintenance, Asset


asset_maintenance_bp = Blueprint("asset_maintenance", __name__)


@asset_maintenance_bp.route("/asset_maintenance", methods=["GET", "POST"])
def asset_maintenance():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE asset_maintenance AUTO_INCREMENT = 1;"))
		db.session.commit()

		# Handle CSV upload
		if "csv_file" in request.files and request.files["csv_file"].filename:
			file = request.files["csv_file"]
			try:
				stream = TextIOWrapper(file.stream, encoding="utf-8")
				csv_reader = csv.DictReader(stream)
				count = 0

				for row in csv_reader:
					# Find asset by ID or tag
					asset = (
						Asset.query.filter_by(asset_id=row.get("asset_id")).first()
						if row.get("asset_id") else None
					)

					if not asset:
						continue

					record = AssetMaintenance(
						asset_id=asset.asset_id,
						maintenance_date=row.get("maintenance_date"),
						description=row.get("description"),
						performed_by=row.get("performed_by"),
						cost=row.get("cost") or None,
						next_due_date=row.get("next_due_date") or None,
					)

					db.session.add(record)
					count += 1

				db.session.commit()
				flash(f"Successfully imported {count} maintenance records from CSV!", "success")

			except Exception as e:
				db.session.rollback()
				flash(f"Error importing CSV: {e}", "danger")

			return redirect("/asset_maintenance")

		# Manual form entry
		asset_id = request.form.get("asset_id")
		maintenance_date = request.form.get("maintenance_date")
		description = request.form.get("description")
		performed_by = request.form.get("performed_by")
		cost = request.form.get("cost") or None
		next_due_date = request.form.get("next_due_date") or None

		if not asset_id or not maintenance_date:
			flash("Asset and maintenance date are required!", "danger")
			return redirect("/asset_maintenance")

		try:
			new_record = AssetMaintenance(
				asset_id=int(asset_id),
				maintenance_date=maintenance_date,
				description=description,
				performed_by=performed_by,
				cost=cost,
				next_due_date=next_due_date
			)

			db.session.add(new_record)
			db.session.commit()
			flash("Maintenance record added successfully!", "success")
			return redirect("/asset_maintenance")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/asset_maintenance")

	# DISPLAY TABLE ------------------------------------------------------------------------

	assets = Asset.query.order_by(Asset.name).all()

	# Handle sorting
	sort = request.args.get("sort", "maintenance_id")
	direction = request.args.get("direction", "asc")
	search = request.args.get("search", None)

	valid_columns = {
		"maintenance_id": AssetMaintenance.maintenance_id,
		"asset_id": AssetMaintenance.asset_id,
		"maintenance_date": AssetMaintenance.maintenance_date,
		"description": AssetMaintenance.description,
		"performed_by": AssetMaintenance.performed_by,
		"cost": AssetMaintenance.cost,
		"next_due_date": AssetMaintenance.next_due_date,
	}

	sort_column = valid_columns.get(sort, AssetMaintenance.maintenance_id)

	# Apply search if necessary
	maintenances = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		maintenances = maintenances.order_by(sort_column.desc())
	else:
		maintenances = maintenances.order_by(sort_column.asc())

	return render_template(
		"asset_maintenance.html",
		maintenances=maintenances,
		assets=assets,
		sort=sort,
		direction=direction
	)


@asset_maintenance_bp.route("/asset_maintenance/delete/<int:maintenance_id>", methods=["GET", "POST"])
def delete_asset_maintenance(maintenance_id):
	record = AssetMaintenance.query.get(maintenance_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/asset_maintenance")

# Search function
def search_for(search):
	query = AssetMaintenance.query.join(Asset, AssetMaintenance.asset_id == Asset.asset_id)

	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(AssetMaintenance.maintenance_id.cast(db.String).ilike(search_pattern)) |
			(Asset.asset_tag.ilike(search_pattern)) |
			(Asset.name.ilike(search_pattern)) |
			(AssetMaintenance.description.ilike(search_pattern)) |
			(AssetMaintenance.performed_by.ilike(search_pattern)) |
			(AssetMaintenance.cost.cast(db.String).ilike(search_pattern)) |
			(AssetMaintenance.maintenance_date.cast(db.String).ilike(search_pattern)) |
			(AssetMaintenance.next_due_date.cast(db.String).ilike(search_pattern))
		)

	return query