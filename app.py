import traceback
from collections import Counter

from flask import Flask, render_template, jsonify, flash, session
from werkzeug.utils import redirect

from models import db, Location
from AssetManagement.assets import assets_bp
from AssetManagement.asset_types import asset_type_bp
from AssetManagement.asset_statuses import asset_status_bp
from AssetManagement.locations import location_bp
from AssetManagement.vendors import vendor_bp
from AssetManagement.departments import department_bp
from AssetManagement.employees import employee_bp
from AssetManagement.asset_assignments import asset_assignment_bp
from AssetManagement.asset_maintenance import asset_maintenance_bp
from AssetManagement.asset_disposals import asset_disposal_bp
from MiscPages.login import login_bp
from MiscPages.manage_users import users_bp
from sqlalchemy import func
from models import Asset, AssetStatus, Department, Employee, Vendor, User, AssetType
from route_decorators import role_required
from misc_functions import *

app = Flask(__name__)
#TODO use something like import os to generate this later for security
app.secret_key = "dev-secret"

#connect to the DB
#let Joseph know if the database can't connect, the IP probably changed

#Default Admin Account:
user: str = "asset_admin"
password: str = "CapstoneII"
db_name: str = "asset_management"
#host: str = "IPADDRES"
host: str = "127.0.0.1"
port: int = 3306

db_link: str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

#print(db_link)

app.config["SQLALCHEMY_DATABASE_URI"] = db_link
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Init the DB from the models.py file
db.init_app(app)

# Define the index page (home page/dashboard)
@app.route('/')
def index():
    if "username" in session:
        username = session.get('username')
        user = User.query.filter_by(username=username).first() if username else ""

        if not user or not user.employee_id:
            flash("No linked employee record found.", "warning")

        employee = Employee.query.get(user.employee_id) if user and user.employee_id else None
        first_name = employee.first_name if employee else None
        last_name = employee.last_name if employee else None
        full_name = f"{first_name} {last_name}"

        # Filter assets based on employee full name
        if user and user.employee_id:
            employee = Employee.query.get(user.employee_id)
            first_name = employee.first_name
            last_name = employee.last_name
            full_name = f"{first_name} {last_name}"

            assets = (
                Asset.query
                .filter_by(assigned_to=employee.employee_id)
                .options(
                    db.joinedload(Asset.status),
                    db.joinedload(Asset.location),
                )
                .all()
            )
        else:
            employee = None
            full_name = "SYSTEM"
            assets = []

        # Calculate total and average purchase cost
        val_query = Asset.query.all()
        total_value = 0
        for a in val_query:
            total_value += a.purchase_cost
            print(str(total_value))
        average_value = total_value / len(val_query)

        return render_template('index.html', full_name=full_name, assets=assets, total_value=total_value, average_value=average_value)
    else:
        return render_template('index.html', full_name="", assets=[])

# Export the entire DB to CSV
@app.route('/export')
@role_required('admin')
def export():
    return export_db()



@app.route('/chart-data/assets-by-status')
def assets_by_status():

    try:
        results = (
            db.session.query(
                AssetStatus.status_name.label('status'),
                func.count(Asset.asset_id).label('count')
            )
            .join(Asset, Asset.status_id == AssetStatus.status_id)
            .group_by(AssetStatus.status_name)
            .all()
        )

        data = [{"status": r.status, "count": r.count} for r in results]
        return jsonify(data)

    except Exception as e:
        print("Error fetching chart data:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/chart-data/assets-by-vendor')
def assets_by_vendor():
    try:
        results = (
            db.session.query(
                Vendor.name.label('vendor'),
                func.count(Asset.asset_id).label('count')
            )
            .outerjoin(Asset, Asset.vendor_id == Vendor.vendor_id)
            .group_by(Vendor.name)
            .order_by(func.count(Asset.asset_id).desc())
            .all()
        )

        data = [{"vendor": r.vendor, "count": r.count} for r in results]
        return jsonify(data)

    except Exception as e:
        app.logger.error(f"Error fetching vendor chart data: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/chart-data/assets-by-type')
def assets_by_type():
    try:
        results = (
            db.session.query(
                AssetType.name.label('type'),
                func.count(Asset.asset_id).label('count')
            )
            .join(Asset, Asset.asset_type_id == AssetType.asset_type_id)
            .group_by(AssetType.name)
            .order_by(func.count(Asset.asset_id).desc())
            .all()
        )

        data = [{"type": r.type, "count": r.count} for r in results]
        return jsonify(data)

    except Exception as e:
        import traceback
        print("Exception in /chart-data/assets-by-type:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# Register all pages using blueprints
app.register_blueprint(assets_bp)                # assets.py
app.register_blueprint(asset_type_bp)            # asset_type.py
app.register_blueprint(asset_status_bp)          # asset_status.py
app.register_blueprint(location_bp)             # locations.py
app.register_blueprint(vendor_bp)               # vendors.py
app.register_blueprint(department_bp)           # departments.py
app.register_blueprint(employee_bp)             # employees.py
app.register_blueprint(asset_assignment_bp)      # asset_assignments.py
app.register_blueprint(asset_maintenance_bp)     # asset_maintenance.py
app.register_blueprint(asset_disposal_bp)        # asset_disposals.py

app.register_blueprint(login_bp)                 # login.py
app.register_blueprint(users_bp)                 # login.py


# run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures tables exist

    app.run(debug=False)
