from flask import Blueprint, render_template, redirect, request, flash
from models import db, AssetStatus

asset_status_bp = Blueprint("asset_status", __name__)

@asset_status_bp.route("/asset_status", methods=["GET", "POST"])
def asset_statuses():
    if request.method == "POST":
        status_name = request.form.get("status_name", "").strip()

        if not status_name:
            flash("Status name is required!", "danger")
            return redirect("/asset_status")

        try:
            new_status = AssetStatus(
                status_name=status_name
            )
            db.session.add(new_status)
            db.session.commit()
            flash("Asset status added successfully!", "success")
            return redirect("/asset_status")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect("/asset_status")

    # Query all asset statuses
    status_query = AssetStatus.query.order_by(AssetStatus.status_id).all()
    return render_template("asset_status.html", statuses=status_query)

@asset_status_bp.route("/asset_status/delete/<int:status_id>", methods=["GET", "POST"])
def delete_asset_status(status_id):
    status = AssetStatus.query.get(status_id)
    if status:
        db.session.delete(status)
        db.session.commit()
    return redirect("/asset_status")
