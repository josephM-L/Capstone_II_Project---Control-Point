from flask import Blueprint, render_template, redirect, request, flash
from models import db, Employee, Department

employee_bp = Blueprint("employee", __name__)

@employee_bp.route("/employees", methods=["GET", "POST"])
def employees():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        department_id = request.form.get("department_id")
        role = request.form.get("role", "").strip()
        status = request.form.get("status", "Active").strip()

        if not first_name or not last_name or not email:
            flash("First name, last name, and email are required!", "danger")
            return redirect("/employees")

        try:
            department_id_value = int(department_id) if department_id else None
            new_employee = Employee(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                department_id=department_id_value,
                role=role,
                status=status
            )
            db.session.add(new_employee)
            db.session.commit()
            flash("Employee added successfully!", "success")
            return redirect("/employees")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect("/employees")

    # Query all employees and departments
    employee_query = Employee.query.order_by(Employee.last_name, Employee.first_name).all()
    department_query = Department.query.order_by(Department.name).all()
    return render_template("employees.html", employees=employee_query, departments=department_query)

@employee_bp.route("/employees/delete/<int:employee_id>", methods=["GET", "POST"])
def delete_employee(employee_id):
    employee = Employee.query.get(employee_id)
    if employee:
        db.session.delete(employee)
        db.session.commit()
    return redirect("/employees")
