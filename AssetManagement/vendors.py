from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, Vendor
from route_decorators import role_required

# Create Blueprint
vendor_bp = Blueprint("vendor", __name__)

# Define main page
@vendor_bp.route("/vendors", methods=["GET", "POST"])
@role_required("admin", "manager")
def vendors():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE vendors AUTO_INCREMENT = 1;"))
		db.session.commit()

		# ADD / UPDATE ------------------------------------------------------------------------

		# Manual form entry
		name = request.form.get("name", "").strip()
		contact_name = request.form.get("contact_name", "").strip()
		phone = request.form.get("phone", "").strip()
		email = request.form.get("email", "").strip()
		address = request.form.get("address", "").strip()

		# Alert user if required fields are not filled out
		if not name:
			flash("Vendor name is required!", "danger")
			return redirect("/vendors")

		# Create new data entry
		try:
			new_vendor = Vendor(
				name=name,
				contact_name=contact_name,
				phone=phone,
				email=email,
				address=address
			)

			db.session.add(new_vendor)

			# commit entry and alert user
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

	# Display table
	return render_template(
		"vendors.html",
		vendors=vendors,
		sort=sort,
		direction=direction
	)

# Define deletion page
@vendor_bp.route("/vendors/delete/<int:vendor_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_vendor(vendor_id):
	record = Vendor.query.get(vendor_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/vendors")

# Define edit page
@vendor_bp.route("/vendors/edit/<int:vendor_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def edit_vendor(vendor_id):
	record = Vendor.query.get_or_404(vendor_id)

	# Collect form data
	new_name = request.form.get("name", "").strip()
	new_contact_name = request.form.get("contact_name", "").strip()
	new_phone = request.form.get("phone", "").strip()
	new_email = request.form.get("email", "").strip()
	new_address = request.form.get("address", "").strip()

	# Basic validation
	if not new_name:
		flash("Vendor name cannot be empty.", "danger")
		return redirect("/vendors")

	try:
		record.name = new_name
		record.contact_name = new_contact_name
		record.phone = new_phone
		record.email = new_email
		record.address = new_address

		# Update table
		db.session.commit()
		flash("Vendor updated successfully!", "success")

	except Exception as e:
		db.session.rollback()
		flash(f"Error updating vendor: {e}", "danger")

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
