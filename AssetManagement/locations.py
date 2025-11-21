import csv
from io import TextIOWrapper

from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, Location
from route_decorators import role_required

# Create Blueprint
location_bp = Blueprint("location", __name__)

# Define main page
@location_bp.route("/locations", methods=["GET", "POST"])
@role_required("admin", "manager")
def locations():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE locations AUTO_INCREMENT = 1;"))
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
					existing_location = (
						Location.query.filter_by(name=row.get("name")).first()
						if row.get("name") else None
					)

					# Only add locations if they do not already exist
					if not existing_location and row.get("name"):
						location = Location(
							name=row.get("name", "").strip(),
							address=row.get("address"),
							city=row.get("city"),
							country=row.get("country"),
						)
						db.session.add(location)
						count += 1

				# Commit additions to DB
				db.session.commit()
				flash(f"Successfully imported {count} locations from CSV!", "success")

			# Handle errors and exceptions
			except Exception as e:
				db.session.rollback()
				flash(f"Error importing CSV: {e}", "danger")

			return redirect("/locations")


		# Manual form entry
		name = request.form.get("name", "").strip()
		address = request.form.get("address", "").strip()
		city = request.form.get("city", "").strip()
		country = request.form.get("country", "").strip()

		# Alert user if required fields are not filled out
		if not name:
			flash("Location name is required!", "danger")
			return redirect("/locations")

		# Create new data entry
		try:
			new_location = Location(
				name=name,
				address=address,
				city=city,
				country=country
			)

			db.session.add(new_location)

			# commit entry and alert user
			db.session.commit()
			flash("Location added successfully!", "success")
			return redirect("/locations")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/locations")

	# DISPLAY TABLE ------------------------------------------------------------------------

	# Handle sorting
	sort = request.args.get("sort", "location_id")
	direction = request.args.get("direction", "asc")
	search = request.args.get("search", None)

	valid_columns = {
		"location_id": Location.location_id,
		"name": Location.name,
		"address": Location.address,
		"city": Location.city,
		"country": Location.country,
	}

	sort_column = valid_columns.get(sort, Location.location_id)

	# Apply search if necessary
	locations = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		locations = locations.order_by(sort_column.desc())
	else:
		locations = locations.order_by(sort_column.asc())

	# Display table
	return render_template(
		"locations.html",
		locations=locations,
		sort=sort,
		direction=direction
	)

# Define deletion page
@location_bp.route("/locations/delete/<int:location_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_location(location_id):
	record = Location.query.get(location_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/locations")

# Define edit page
@location_bp.route("/locations/edit/<int:location_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def edit_location(location_id):
	record = Location.query.get_or_404(location_id)

	# Collect form data
	new_name = request.form.get("name", "").strip()
	new_address = request.form.get("address", "").strip()
	new_city = request.form.get("city", "").strip()
	new_country = request.form.get("country", "").strip()

	# Basic validation
	if not new_name:
		flash("Location name cannot be empty.", "danger")
		return redirect("/locations")

	try:
		record.name = new_name
		record.address = new_address
		record.city = new_city
		record.country = new_country

		# Update table
		db.session.commit()
		flash("Location updated successfully!", "success")
	except Exception as e:
		db.session.rollback()
		flash(f"Error updating location: {e}", "danger")

	return redirect("/locations")



# Search function
def search_for(search):
	query = Location.query
	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(Location.location_id.ilike(search_pattern)) |
			(Location.name.ilike(search_pattern)) |
			(Location.address.ilike(search_pattern)) |
			(Location.city.ilike(search_pattern)) |
			(Location.country.ilike(search_pattern))
		)
	return query
