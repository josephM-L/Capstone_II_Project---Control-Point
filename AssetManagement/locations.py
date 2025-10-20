from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, Location

location_bp = Blueprint("location", __name__)


@location_bp.route("/locations", methods=["GET", "POST"])
def locations():
	# ADD / UPDATE ------------------------------------------------------------------------
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE locations AUTO_INCREMENT = 1;"))
		db.session.commit()

		# Manual form entry
		name = request.form.get("name", "").strip()
		address = request.form.get("address", "").strip()
		city = request.form.get("city", "").strip()
		country = request.form.get("country", "").strip()

		if not name:
			flash("Location name is required!", "danger")
			return redirect("/locations")

		try:
			new_location = Location(
				name=name,
				address=address,
				city=city,
				country=country
			)

			db.session.add(new_location)
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

	valid_columns = {
		"location_id": Location.location_id,
		"name": Location.name,
		"address": Location.address,
		"city": Location.city,
		"country": Location.country,
	}

	sort_column = valid_columns.get(sort, Location.location_id)

	if direction == "desc":
		locations = Location.query.order_by(sort_column.desc()).all()
	else:
		locations = Location.query.order_by(sort_column.asc()).all()

	return render_template(
		"locations.html",
		locations=locations,
		sort=sort,
		direction=direction
	)


@location_bp.route("/locations/delete/<int:location_id>", methods=["GET", "POST"])
def delete_location(location_id):
	record = Location.query.get(location_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/locations")
