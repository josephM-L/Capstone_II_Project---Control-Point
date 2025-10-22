from flask import Flask, render_template, jsonify
from models import db
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
from sqlalchemy import func
from models import Asset, AssetStatus, Department, Employee
app = Flask(__name__)
#TODO use something like import os to generate this later for security
app.secret_key = "dev-secret"

#connect to the DB
#let Joseph know if the database can't connect, the IP probably changed

#TODO add a user account with minimal privileges
#Default Admin Account:
user: str = "asset_admin"
password: str = "CapstoneII"
db_name: str = "asset_management"
host: str = "47.199.71.84"
port: int = 3306

db_link: str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

print(db_link)


#TODO this needs to be obscured and changed later for security purposes
#TODO we need to dynamically swap this to admin or user accounts
app.config["SQLALCHEMY_DATABASE_URI"] = db_link
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Init the DB from the models.py file
db.init_app(app)

# Define the index page (home page)
@app.route('/')
def index():
    return render_template('index.html')



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

@app.route('/chart-data/assets-by-department')
def assets_by_department():
    try:
        results = (
            db.session.query(
                Department.name.label('department'),
                func.count(Asset.asset_id).label('count')
            )
            .join(Employee, Employee.department_id == Department.department_id)
            .join(Asset, Asset.assigned_to == Employee.employee_id)
            .group_by(Department.name)
            .all()
        )

        data = [{"department": r.department, "count": r.count} for r in results]
        return jsonify(data)

    except Exception as e:
        print("Error fetching department chart data:", e)
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


# run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures tables exist
    app.run(debug=True)
