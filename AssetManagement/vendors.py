from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, Vendor
from route_decorators import role_required

vendor_bp = Blueprint("vendor", __name__)


@vendor_bp.route("/vendors", methods=["GET", "POST"])
@role_required("admin", "manager")
def vendors():
	# ADD / UPDATE ------------------------------------------------------------------------
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE vendors AUTO_INCREMENT = 1;"))
		db.session.commit()

		# Manual form entry
		name = request.form.get("name", "").strip()
		contact_name = request.form.get("contact_name", "").strip()
		phone = request.form.get("phone", "").strip()
		email = request.form.get("email", "").strip()
		address = request.form.get("address", "").strip()

		if not name:
			flash("Vendor name is required!", "danger")
			return redirect("/vendors")

		try:
			new_vendor = Vendor(
				name=name,
				contact_name=contact_name,
				phone=phone,
				email=email,
				address=address
			)

			db.session.add(new_vendor)
			db.session.commit()
			flash("Vendor added successfully!", "success")
			return redirect("/vendors")

		except Exception as e:
			db.session.rollback()
			flash(f"Error: {e}", "danger")
			return redirect("/vendors")

	# DISPLAY TABLE ------------------------------------------------------------------------

	# Handle sorting
	sort = request.args.get("sort", "vendor_id")
	direction = request.args.get("direction", "asc")
	search = request.args.get("search", None)

	valid_columns = {
		"vendor_id": Vendor.vendor_id,
		"name": Vendor.name,
		"contact_name": Vendor.contact_name,
		"phone": Vendor.phone,
		"email": Vendor.email,
		"address": Vendor.address,
	}

	sort_column = valid_columns.get(sort, Vendor.vendor_id)

	# Apply search if necessary
	vendors = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		vendors = vendors.order_by(sort_column.desc())
	else:
		vendors = vendors.order_by(sort_column.asc())

	return render_template(
		"vendors.html",
		vendors=vendors,
		sort=sort,
		direction=direction
	)


@vendor_bp.route("/vendors/delete/<int:vendor_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_vendor(vendor_id):
	record = Vendor.query.get(vendor_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/vendors")


# Search function
def search_for(search):
	query = Vendor.query
	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(Vendor.vendor_id.cast(db.String).ilike(search_pattern)) |
			(Vendor.name.ilike(search_pattern)) |
			(Vendor.email.ilike(search_pattern)) |
			(Vendor.phone.ilike(search_pattern)) |
			(Vendor.address.ilike(search_pattern))
		)
	return query
