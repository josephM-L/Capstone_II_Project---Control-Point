from flask import Blueprint, render_template, redirect, request, flash
from models import db, Location

location_bp = Blueprint("location", __name__)

@location_bp.route("/locations", methods=["GET", "POST"])
def locations():
    if request.method == "POST":
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

    # Query all locations
    location_query = Location.query.order_by(Location.location_id).all()
    return render_template("locations.html", locations=location_query)

@location_bp.route("/locations/delete/<int:location_id>", methods=["GET", "POST"])
def delete_location(location_id):
    location = Location.query.get(location_id)
    if location:
        db.session.delete(location)
        db.session.commit()
    return redirect("/locations")
