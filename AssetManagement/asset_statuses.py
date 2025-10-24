from flask import Blueprint, render_template, redirect, request, flash
from sqlalchemy import text
from models import db, AssetStatus
from route_decorators import role_required

asset_status_bp = Blueprint("asset_status", __name__)


@asset_status_bp.route("/asset_status", methods=["GET", "POST"])
@role_required("admin", "manager")
def asset_statuses():
	# ADD / UPDATE ------------------------------------------------------------------------
	if request.method == "POST":
		# Reset auto increment
		db.session.execute(text("ALTER TABLE asset_statuses AUTO_INCREMENT = 1;"))
		db.session.commit()

		# Manual form entry
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

	# DISPLAY TABLE ------------------------------------------------------------------------

	# Handle sorting
	sort = request.args.get("sort", "status_id")
	direction = request.args.get("direction", "asc")
	search = request.args.get("search", None)

	valid_columns = {
		"status_id": AssetStatus.status_id,
		"status_name": AssetStatus.status_name,
	}

	sort_column = valid_columns.get(sort, AssetStatus.status_id)

	# Apply search if necessary
	statuses = search_for(search)

	# Apply sorting and ordering from input
	if direction == "desc":
		statuses = statuses.order_by(sort_column.desc())
	else:
		statuses = statuses.order_by(sort_column.asc())

	return render_template(
		"asset_status.html",
		statuses=statuses,
		sort=sort,
		direction=direction
	)


@asset_status_bp.route("/asset_status/delete/<int:status_id>", methods=["GET", "POST"])
@role_required("admin", "manager")
def delete_asset_status(status_id):
	record = AssetStatus.query.get(status_id)
	if record:
		db.session.delete(record)
		db.session.commit()
	return redirect("/asset_status")


# Search function
def search_for(search):
	query = AssetStatus.query
	if search:
		search_pattern = f"%{search}%"
		query = query.filter(
			(AssetStatus.status_id.ilike(search_pattern)) |
			(AssetStatus.status_name.ilike(search_pattern))
		)
	return query
