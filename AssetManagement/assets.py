from datetime import datetime
from flask import Blueprint, render_template, redirect, request, flash
from models import db, Asset, AssetType, AssetStatus, Location, Vendor, Employee

assets_bp = Blueprint("assets", __name__)

@assets_bp.route("/assets", methods=["GET", "POST"])
def assets():
    if request.method == "POST":
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

        if not asset_tag or not name:
            flash("Asset tag and name are required!", "danger")
            return redirect("/assets")

        try:
            purchase_date_parsed = datetime.strptime(purchase_date, "%Y-%m-%d").date() if purchase_date else None
            warranty_expiry_parsed = datetime.strptime(warranty_expiry, "%Y-%m-%d").date() if warranty_expiry else None
            purchase_cost_val = float(purchase_cost) if purchase_cost else None

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

    # Query all assets
    asset_query = Asset.query.order_by(Asset.asset_id).all()

    # Query related tables for dropdowns
    asset_types = AssetType.query.order_by(AssetType.name).all()
    statuses = AssetStatus.query.order_by(AssetStatus.status_name).all()
    locations = Location.query.order_by(Location.name).all()
    vendors = Vendor.query.order_by(Vendor.name).all()
    employees = Employee.query.order_by(Employee.last_name, Employee.first_name).all()

    return render_template(
        "assets.html",
        assets=asset_query,
        asset_types=asset_types,
        statuses=statuses,
        locations=locations,
        vendors=vendors,
        employees=employees
    )


@assets_bp.route("/assets/delete/<int:asset_id>", methods=["GET", "POST"])
def delete_asset(asset_id):
    asset = Asset.query.get(asset_id)
    if asset:
        db.session.delete(asset)
        db.session.commit()
    return redirect("/assets")
