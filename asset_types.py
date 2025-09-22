from flask import Blueprint, render_template, redirect, request, flash
from models import db, AssetType

asset_type_bp = Blueprint("asset_type", __name__)

@asset_type_bp.route("/asset_type", methods=["GET", "POST"])
def create_asset():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description")

        if not name:
            flash("Asset type name is required!", "danger")
            return redirect("/asset_type")

        try:

            new_asset = AssetType(
                name=name,
                category=category,
                description=description
            )

            db.session.add(new_asset)
            db.session.commit()
            flash("Asset type added successfully!", "success")
            return redirect("/asset_type")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect("/asset_type")

    asset_type_query = AssetType.query.order_by(AssetType.asset_type_id).all()
    return render_template("asset_type.html", asset_types=asset_type_query)

@asset_type_bp.route("/asset_type/delete/<int:asset_type_id>", methods=["GET", "POST"])
def delete_asset(asset_type_id):
    asset_type = AssetType.query.get(asset_type_id)
    if asset_type:
        db.session.delete(asset_type)
        db.session.commit()
    return redirect("/asset_type")