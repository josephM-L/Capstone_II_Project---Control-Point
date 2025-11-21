import csv
from datetime import datetime
from io import TextIOWrapper, StringIO
from flask import Blueprint, render_template, redirect, request, flash, Response
from sqlalchemy import text
from models import db, Asset, AssetType, AssetStatus, Location, Vendor, Employee, AssetAssignment
from route_decorators import role_required

# Create Blueprint
assets_bp = Blueprint("assets", __name__)

# Define main page
@assets_bp.route("/assets", methods=["GET", "POST"])
@role_required("admin", "manager", "user")
def assets():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE assets AUTO_INCREMENT = 1;"))
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
						asset_type_id=int(row.get("asset_type_id")) if row.get("asset_type_id") else None,
						status_id=int(row.get("status_id")) if row.get("status_id") else None,
						location_id=int(row.get("location_id")) if row.get("location_id") else None,
						vendor_id=int(row.get("vendor_id")) if row.get("vendor_id") else None,
						assigned_to=int(row.get("assigned_to")) if row.get("assigned_to") else None,
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

		# Create new data entry
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

			# Update table
			db.session.add(new_asset)

			# commit entry and alert user
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

# Define deletion page
@assets_bp.route("/assets/delete/<int:asset_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_asset(asset_id):
	asset = Asset.query.get(asset_id)
	if asset:
		db.session.delete(asset)
		db.session.commit()
	return redirect("/assets")

# Define edit page
@assets_bp.route("/assets/edit/<int:asset_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def edit_asset(asset_id):
	record = Asset.query.get_or_404(asset_id)

	# Collect form data
	asset_tag = request.form.get("asset_tag", "").strip()
	name = request.form.get("name", "").strip()
	description = request.form.get("description", "").strip()
	asset_type_id = request.form.get("asset_type_id")
	status_id = request.form.get("status_id")
	location_id = request.form.get("location_id")
	assigned_to = request.form.get("assigned_to")
	purchase_date = request.form.get("purchase_date")
	purchase_cost = request.form.get("purchase_cost")
	vendor_id = request.form.get("vendor_id")
	warranty_expiry = request.form.get("warranty_expiry")
	serial_number = request.form.get("serial_number", "").strip()

	# Basic validation
	if not asset_tag or not name:
		flash("Asset tag and name cannot be empty.", "danger")
		return redirect("/assets")

	try:
		record.asset_tag = asset_tag
		record.name = name
		record.description = description or None
		record.asset_type_id = asset_type_id or None
		record.status_id = status_id or None
		record.location_id = location_id or None
		record.assigned_to = assigned_to or None
		record.purchase_date = purchase_date or None
		record.purchase_cost = purchase_cost or None
		record.vendor_id = vendor_id or None
		record.warranty_expiry = warranty_expiry or None
		record.serial_number = serial_number or None

		# Update table
		db.session.commit()
		flash("Asset updated successfully!", "success")
	except Exception as e:
		db.session.rollback()
		flash(f"Error updating asset: {e}", "danger")

	return redirect("/assets")




# Export CSV
@assets_bp.route("/assets/export", methods=["GET", "POST"])
@role_required("admin")
def export_assets():
	assets = Asset.query.all()
	output = StringIO()
	# Create writer and define field names for output file
	writer = csv.DictWriter(output, fieldnames=[
		"asset_tag", "name", "description", "asset_type", "status",
		"location", "assigned_to", "purchase_date", "purchase_cost",
		"vendor", "warranty_expiry", "serial_number"
	])
	writer.writeheader()

	# Loop through all entries and add them to the output file
	for a in assets:
		writer.writerow({
			"asset_tag": a.asset_tag,
			"name": a.name,
			"description": a.description or "",
			"asset_type": a.asset_type.name if a.asset_type else "",
			"status": a.status.status_name if a.status else "",
			"location": a.location.name if a.location else "",
			"assigned_to": a.assigned_to if a.assigned_to else "",
			"purchase_date": a.purchase_date.strftime("%Y-%m-%d") if a.purchase_date else "",
			"purchase_cost": str(a.purchase_cost) if a.purchase_cost else "",
			"vendor": a.vendor.name if a.vendor else "",
			"warranty_expiry": a.warranty_expiry.strftime("%Y-%m-%d") if a.warranty_expiry else "",
			"serial_number": a.serial_number or "",
		})

	# Reset output pointer to read whole output
	output.seek(0)
	return Response(
		output.getvalue(),
		mimetype="text/csv",
		headers={"Content-Disposition": "attachment;filename=assets.csv"}
	)


# Search function
def search_for(search):
	# Create a join to query Assets, Vendor, Location, AssetType, and AssetStatus tables
	query = Asset.query.join(Vendor, isouter=True).join(Location, isouter=True).join(AssetType, isouter=True).join(AssetStatus, isouter=True)
	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(Asset.asset_tag.ilike(search_pattern)) |
			(Asset.name.ilike(search_pattern)) |
			(Asset.description.ilike(search_pattern)) |
			(Asset.serial_number.ilike(search_pattern)) |
			(Asset.purchase_date.ilike(search_pattern)) |
			(Asset.purchase_cost.ilike(search_pattern)) |
			(Asset.warranty_expiry.ilike(search_pattern)) |
			(AssetStatus.status_name.ilike(search_pattern)) |
			(Vendor.name.ilike(search_pattern)) |
			(Location.name.ilike(search_pattern)) |
			(AssetType.name.ilike(search_pattern))

		)
	return query