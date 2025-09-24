from flask import Blueprint, render_template, redirect, request, flash
from models import db, Vendor

vendor_bp = Blueprint("vendor", __name__)

@vendor_bp.route("/vendors", methods=["GET", "POST"])
def vendors():
    if request.method == "POST":
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

    # Query all vendors
    vendor_query = Vendor.query.order_by(Vendor.vendor_id).all()
    return render_template("vendors.html", vendors=vendor_query)

@vendor_bp.route("/vendors/delete/<int:vendor_id>", methods=["GET", "POST"])
def delete_vendor(vendor_id):
    vendor = Vendor.query.get(vendor_id)
    if vendor:
        db.session.delete(vendor)
        db.session.commit()
    return redirect("/vendors")
