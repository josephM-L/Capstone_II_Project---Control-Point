from flask import Blueprint, render_template, redirect, request, flash
from models import db, AssetMaintenance, Asset

asset_maintenance_bp = Blueprint("asset_maintenance", __name__)

@asset_maintenance_bp.route("/asset_maintenance", methods=["GET", "POST"])
def asset_maintenance():
    if request.method == "POST":
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

    # Query all maintenance records and all assets for dropdown
    maintenances = AssetMaintenance.query.order_by(AssetMaintenance.maintenance_id).all()
    assets = Asset.query.order_by(Asset.asset_id).all()

    return render_template(
        "asset_maintenance.html",
        maintenances=maintenances,
        assets=assets
    )

@asset_maintenance_bp.route("/asset_maintenance/delete/<int:maintenance_id>", methods=["GET", "POST"])
def delete_asset_maintenance(maintenance_id):
    record = AssetMaintenance.query.get(maintenance_id)
    if record:
        db.session.delete(record)
        db.session.commit()
    return redirect("/asset_maintenance")
