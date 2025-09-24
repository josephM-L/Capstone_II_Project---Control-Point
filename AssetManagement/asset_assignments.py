from flask import Blueprint, render_template, redirect, request, flash
from models import db, AssetAssignment, Asset, Employee

asset_assignment_bp = Blueprint("asset_assignment", __name__)

@asset_assignment_bp.route("/asset_assignments", methods=["GET", "POST"])
def asset_assignments():
    if request.method == "POST":
        asset_id = request.form.get("asset_id")
        employee_id = request.form.get("employee_id")
        assigned_date = request.form.get("assigned_date")
        returned_date = request.form.get("returned_date") or None

        if not asset_id or not employee_id or not assigned_date:
            flash("Asset, employee, and assigned date are required!", "danger")
            return redirect("/asset_assignments")

        try:
            new_assignment = AssetAssignment(
                asset_id=int(asset_id),
                employee_id=int(employee_id),
                assigned_date=assigned_date,
                returned_date=returned_date
            )
            db.session.add(new_assignment)
            db.session.commit()
            flash("Asset assignment added successfully!", "success")
            return redirect("/asset_assignments")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect("/asset_assignments")

    # Query all assignments, assets, and employees for dropdowns
    assignment_query = AssetAssignment.query.order_by(AssetAssignment.assignment_id).all()
    assets_query = Asset.query.order_by(Asset.asset_id).all()
    employees_query = Employee.query.order_by(Employee.last_name, Employee.first_name).all()

    return render_template(
        "asset_assignments.html",
        assignments=assignment_query,
        assets=assets_query,
        employees=employees_query
    )

@asset_assignment_bp.route("/asset_assignments/delete/<int:assignment_id>", methods=["GET", "POST"])
def delete_asset_assignment(assignment_id):
    assignment = AssetAssignment.query.get(assignment_id)
    if assignment:
        db.session.delete(assignment)
        db.session.commit()
    return redirect("/asset_assignments")
