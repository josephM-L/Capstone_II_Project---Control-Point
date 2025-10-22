import csv
from datetime import datetime
from io import TextIOWrapper
from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, Asset, AssetType, AssetStatus, Location, Vendor, Employee

assets_bp = Blueprint("assets", __name__)


@assets_bp.route("/assets", methods=["GET", "POST"])
def assets():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE assets AUTO_INCREMENT = 1;"))
		db.session.commit()

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
					asset_type = (
						AssetType.query.filter_by(name=row.get("asset_type")).first()
						if row.get("asset_type") else None
					)
					status = (
						AssetStatus.query.filter_by(status_name=row.get("status")).first()
						if row.get("status") else None
					)
					location = (
						Location.query.filter_by(name=row.get("location")).first()
						if row.get("location") else None
					)
					vendor = (
						Vendor.query.filter_by(name=row.get("vendor")).first()
						if row.get("vendor") else None
					)
					employee = (
						Employee.query.filter_by(email=row.get("assigned_to")).first()
						if row.get("assigned_to") else None
					)

					# Parse dates and numbers
					purchase_date = (
						datetime.strptime(row.get("purchase_date"), "%Y-%m-%d").date()
						if row.get("purchase_date") else None
					)
					warranty_expiry = (
						datetime.strptime(row.get("warranty_expiry"), "%Y-%m-%d").date()
						if row.get("warranty_expiry") else None
					)
					purchase_cost = (
						float(row.get("purchase_cost")) if row.get("purchase_cost") else None
					)

					# Build asset DB entry and queue for commit
					asset = Asset(
						asset_tag=row.get("asset_tag", "").strip(),
						name=row.get("name", "").strip(),
						description=row.get("description"),
						purchase_date=purchase_date,
						purchase_cost=purchase_cost,
						serial_number=row.get("serial_number"),
						warranty_expiry=warranty_expiry,
						asset_type_id=asset_type.asset_type_id if asset_type else None,
						status_id=status.status_id if status else None,
						location_id=location.location_id if location else None,
						vendor_id=vendor.vendor_id if vendor else None,
						assigned_to=employee.employee_id if employee else None,
					)
					db.session.add(asset)
					count += 1

				# Commit additions to DB
				db.session.commit()
				flash(f"Successfully imported {count} assets from CSV!", "success")

			# Handle errors and exceptions
			except Exception as e:
				db.session.rollback()
				flash(f"Error importing CSV: {e}", "danger")

			return redirect("/assets")

		# For manual form submission
		asset_tag = request.form.get("asset_tag", "").strip()
		name = request.form.get("name", "").strip()
		description = request.form.get("description")
		purchase_date = request.form.get("purchase_date")
		purchase_cost = request.form.get("purchase_cost")
		serial_number = request.form.get("serial_number")
		warranty_expiry = request.form.get("warranty_expiry")

		# Foreign key references
		asset_type_id = request.form.get("asset_type_id")
		status_id = request.form.get("status_id")
		location_id = request.form.get("location_id")
		vendor_id = request.form.get("vendor_id")
		assigned_to = request.form.get("assigned_to")

		# Alert user if required fields are not filled out
		if not asset_tag or not name:
			flash("Asset tag and name are required!", "danger")
			return redirect("/assets")

		try:
			purchase_date_parsed = (
				datetime.strptime(purchase_date, "%Y-%m-%d").date()
				if purchase_date else None
			)
			warranty_expiry_parsed = (
				datetime.strptime(warranty_expiry, "%Y-%m-%d").date()
				if warranty_expiry else None
			)
			purchase_cost_val = (
				float(purchase_cost) if purchase_cost else None
			)

			new_asset = Asset(
				asset_tag=asset_tag,
				name=name,
				description=description,
				purchase_date=purchase_date_parsed,
				purchase_cost=purchase_cost_val,
				serial_number=serial_number,
				warranty_expiry=warranty_expiry_parsed,
				asset_type_id=int(asset_type_id) if asset_type_id else None,
				status_id=int(status_id) if status_id else None,
				location_id=int(location_id) if location_id else None,
				vendor_id=int(vendor_id) if vendor_id else None,
				assigned_to=int(assigned_to) if assigned_to else None,
			)

			db.session.add(new_asset)
			db.session.commit()
			flash("Asset added successfully!", "success")
			return redirect("/assets")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/assets")

	# DISPLAY TABLE ------------------------------------------------------------------------

	# Query related tables for dropdowns
	asset_types = AssetType.query.order_by(AssetType.name).all()
	statuses = AssetStatus.query.order_by(AssetStatus.status_name).all()
	locations = Location.query.order_by(Location.name).all()
	vendors = Vendor.query.order_by(Vendor.name).all()
	employees = Employee.query.order_by(Employee.last_name, Employee.first_name).all()

	# Get arguments for sorting & searching
	sort = request.args.get("sort", "asset_id")  # Default sort column
	direction = request.args.get("direction", "asc")  # Default sort direction
	search = request.args.get("search", None)

	# Define valid columns to avoid SQL injection attacks
	valid_columns = {
		"asset_id": Asset.asset_id,
		"asset_tag": Asset.asset_tag,
		"name": Asset.name,
		"description": Asset.description,
		"asset_type_id": Asset.asset_type_id,
		"status_id": Asset.status_id,
		"location_id": Asset.location_id,
		"assigned_to": Asset.assigned_to,
		"purchase_date": Asset.purchase_date,
		"purchase_cost": Asset.purchase_cost,
		"vendor_id": Asset.vendor_id,
		"warranty_expiry": Asset.warranty_expiry,
		"serial_number": Asset.serial_number,
		"created_at": Asset.created_at,  # TODO Maybe add to sort and table?
		"updated_at": Asset.updated_at,  # TODO Maybe add to sort and table?
	}

	sort_column = valid_columns.get(sort, Asset.asset_id)

	# Apply search if necessary
	assets = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		assets = assets.order_by(sort_column.desc())
	else:
		assets = assets.order_by(sort_column.asc())

	#assets = assets.all()

	# Display table of all assets and data entry forms
	return render_template(
		"assets.html",
		assets=assets,
		asset_types=asset_types,
		statuses=statuses,
		locations=locations,
		vendors=vendors,
		employees=employees,
		sort=sort,
		direction=direction
	)


@assets_bp.route("/assets/delete/<int:asset_id>", methods=["GET", "POST"])
def delete_asset(asset_id):
	asset = Asset.query.get(asset_id)
	if asset:
		db.session.delete(asset)
		db.session.commit()
	return redirect("/assets")



# Search function
def search_for(search):
	query = Asset.query
	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(Asset.asset_id.ilike(search_pattern)) |
			(Asset.name.ilike(search_pattern)) |
			(Asset.description.ilike(search_pattern)) |
			(Asset.asset_type_id.ilike(search_pattern)) |
			(Asset.status_id.ilike(search_pattern)) |
			(Asset.location_id.ilike(search_pattern)) |
			(Asset.assigned_to.ilike(search_pattern)) |
			(Asset.purchase_date.ilike(search_pattern)) |
			(Asset.purchase_cost.ilike(search_pattern)) |
			(Asset.vendor_id.ilike(search_pattern)) |
			(Asset.warranty_expiry.ilike(search_pattern)) |
			(Asset.serial_number.ilike(search_pattern))
		)

	return query