import csv
from io import TextIOWrapper
from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, AssetDisposal, Asset


asset_disposal_bp = Blueprint("asset_disposal", __name__)


@asset_disposal_bp.route("/asset_disposals", methods=["GET", "POST"])
def asset_disposals():
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE asset_disposals AUTO_INCREMENT = 1;"))
		db.session.commit()

		# Handle CSV upload
		if "csv_file" in request.files and request.files["csv_file"].filename:
			file = request.files["csv_file"]
			try:
				stream = TextIOWrapper(file.stream, encoding="utf-8")
				csv_reader = csv.DictReader(stream)
				count = 0

				for row in csv_reader:
					# Find asset by ID or tag
					asset = (
						Asset.query.filter_by(asset_id=row.get("asset_id")).first()
						if row.get("asset_id") else None
					)

					if not asset:
						continue

					disposal = AssetDisposal(
						asset_id=asset.asset_id,
						disposal_date=row.get("disposal_date"),
						method=row.get("method"),
						sale_value=row.get("sale_value") or None,
						notes=row.get("notes") or None,
					)

					db.session.add(disposal)
					count += 1

				db.session.commit()
				flash(f"Successfully imported {count} disposals from CSV!", "success")

			except Exception as e:
				db.session.rollback()
				flash(f"Error importing CSV: {e}", "danger")

			return redirect("/asset_disposals")

		# Manual form entry
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

	# DISPLAY TABLE ------------------------------------------------------------------------

	assets = Asset.query.order_by(Asset.name).all()

	# Handle sorting
	sort = request.args.get("sort", "disposal_id")
	direction = request.args.get("direction", "asc")
	search = request.args.get("search", None)

	valid_columns = {
		"disposal_id": AssetDisposal.disposal_id,
		"asset_id": AssetDisposal.asset_id,
		"disposal_date": AssetDisposal.disposal_date,
		"method": AssetDisposal.method,
		"sale_value": AssetDisposal.sale_value,
		"notes": AssetDisposal.notes,
	}

	sort_column = valid_columns.get(sort, AssetDisposal.disposal_id)

	# Apply search if necessary
	disposals = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		disposals = disposals.order_by(sort_column.desc())
	else:
		disposals = disposals.order_by(sort_column.asc())

	return render_template(
		"asset_disposals.html",
		disposals=disposals,
		assets=assets,
		sort=sort,
		direction=direction
	)


@asset_disposal_bp.route("/asset_disposals/delete/<int:disposal_id>", methods=["GET", "POST"])
def delete_asset_disposal(disposal_id):
	record = AssetDisposal.query.get(disposal_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/asset_disposals")

# Search function
def search_for(search):
	query = AssetDisposal.query.join(Asset, AssetDisposal.asset_id == Asset.asset_id)

	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(AssetDisposal.disposal_id.cast(db.String).ilike(search_pattern)) |
			(Asset.asset_tag.ilike(search_pattern)) |
			(Asset.name.ilike(search_pattern)) |
			(AssetDisposal.method.ilike(search_pattern)) |
			(AssetDisposal.sale_value.cast(db.String).ilike(search_pattern)) |
			(AssetDisposal.notes.ilike(search_pattern)) |
			(AssetDisposal.disposal_date.cast(db.String).ilike(search_pattern))
		)

	return query
