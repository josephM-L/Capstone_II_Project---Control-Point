from datetime import datetime
from flask import Blueprint, render_template, redirect, request, flash
from models import db, Asset

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

        if not asset_tag or not name:
            flash("Asset tag and name are required!", "danger")
            return redirect("/assets")

        try:
            purchase_date_parsed = datetime.strptime(purchase_date, "%Y-%m-%d").date() if purchase_date else None
            purchase_cost_val = float(purchase_cost) if purchase_cost else None

            new_asset = Asset(
                asset_tag=asset_tag,
                name=name,
                description=description,
                purchase_date=purchase_date_parsed,
                purchase_cost=purchase_cost_val,
                serial_number=serial_number
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
    return render_template("assets.html", assets=asset_query)

@assets_bp.route("/assets/delete/<int:asset_id>", methods=["GET", "POST"])
def delete_asset(asset_id):
    asset = Asset.query.get(asset_id)
    if asset:
        db.session.delete(asset)
        db.session.commit()
    return redirect("/assets")