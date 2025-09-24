from flask import Blueprint, render_template, redirect, request, flash
from models import db, AssetDisposal, Asset

asset_disposal_bp = Blueprint("asset_disposal", __name__)

@asset_disposal_bp.route("/asset_disposals", methods=["GET", "POST"])
def asset_disposals():
    if request.method == "POST":
        asset_id = request.form.get("asset_id")
        disposal_date = request.form.get("disposal_date")
        method = request.form.get("method")
        sale_value = request.form.get("sale_value") or None
        notes = request.form.get("notes") or None

        if not asset_id or not disposal_date or not method:
            flash("Asset, disposal date, and method are required!", "danger")
            return redirect("/asset_disposals")

        try:
            new_disposal = AssetDisposal(
                asset_id=int(asset_id),
                disposal_date=disposal_date,
                method=method,
                sale_value=float(sale_value) if sale_value else None,
                notes=notes
            )
            db.session.add(new_disposal)
            db.session.commit()
            flash("Asset disposal recorded successfully!", "success")
            return redirect("/asset_disposals")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect("/asset_disposals")

    # Query all disposals and assets for dropdowns
    disposal_query = AssetDisposal.query.order_by(AssetDisposal.disposal_id).all()
    assets_query = Asset.query.order_by(Asset.asset_id).all()

    return render_template(
        "asset_disposals.html",
        disposals=disposal_query,
        assets=assets_query
    )

@asset_disposal_bp.route("/asset_disposals/delete/<int:disposal_id>", methods=["GET", "POST"])
def delete_asset_disposal(disposal_id):
    disposal = AssetDisposal.query.get(disposal_id)
    if disposal:
        db.session.delete(disposal)
        db.session.commit()
    return redirect("/asset_disposals")
