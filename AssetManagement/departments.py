from flask import Blueprint, render_template, redirect, request, flash
from models import db, Department, Employee

department_bp = Blueprint("department", __name__)

@department_bp.route("/departments", methods=["GET", "POST"])
def departments():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        manager_id = request.form.get("manager_id")

        if not name:
            flash("Department name is required!", "danger")
            return redirect("/departments")

        try:
            manager_id_value = int(manager_id) if manager_id else None
            new_department = Department(
                name=name,
                manager_id=manager_id_value
            )
            db.session.add(new_department)
            db.session.commit()
            flash("Department added successfully!", "success")
            return redirect("/departments")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect("/departments")

    # Query all departments
    department_query = Department.query.order_by(Department.department_id).all()
    employees_query = Employee.query.order_by(Employee.first_name, Employee.last_name).all()
    return render_template("departments.html", departments=department_query, employees=employees_query)

@department_bp.route("/departments/delete/<int:department_id>", methods=["GET", "POST"])
def delete_department(department_id):
    department = Department.query.get(department_id)
    if department:
        db.session.delete(department)
        db.session.commit()
    return redirect("/departments")
