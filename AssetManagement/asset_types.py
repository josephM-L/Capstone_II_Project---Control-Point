from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, AssetType

asset_type_bp = Blueprint("asset_type", __name__)


@asset_type_bp.route("/asset_type", methods=["GET", "POST"])
def asset_types():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE asset_types AUTO_INCREMENT = 1;"))
		db.session.commit()

		# Manual form entry
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

	# DISPLAY TABLE ------------------------------------------------------------------------

	# Handle sorting
	sort = request.args.get("sort", "asset_type_id")
	direction = request.args.get("direction", "asc")

	valid_columns = {
		"asset_type_id": AssetType.asset_type_id,
		"name": AssetType.name,
		"category": AssetType.category,
		"description": AssetType.description,
	}

	sort_column = valid_columns.get(sort, AssetType.asset_type_id)

	if direction == "desc":
		asset_types = AssetType.query.order_by(sort_column.desc()).all()
	else:
		asset_types = AssetType.query.order_by(sort_column.asc()).all()

	return render_template(
		"asset_type.html",
		asset_types=asset_types,
		sort=sort,
		direction=direction
	)


@asset_type_bp.route("/asset_type/delete/<int:asset_type_id>", methods=["GET", "POST"])
def delete_asset_type(asset_type_id):
	record = AssetType.query.get(asset_type_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/asset_type")
