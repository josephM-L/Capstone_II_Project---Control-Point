from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class AssetType(db.Model):
    __tablename__ = "asset_types"
    asset_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.Enum("Tangible", "Intangible"), nullable=False)
    description = db.Column(db.Text)


class AssetStatus(db.Model):
    __tablename__ = "asset_statuses"
    status_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status_name = db.Column(db.String(50), nullable=False)


class Department(db.Model):
    __tablename__ = "departments"
    department_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"))


class Employee(db.Model):
    __tablename__ = "employees"
    employee_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id"))
    role = db.Column(db.String(100))
    status = db.Column(db.Enum("Active", "Inactive"), default="Active")


class Location(db.Model):
    __tablename__ = "locations"
    location_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))


class Vendor(db.Model):
    __tablename__ = "vendors"
    vendor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    contact_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    address = db.Column(db.String(255))


class Asset(db.Model):
    __tablename__ = "assets"
    asset_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_tag = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    asset_type_id = db.Column(db.Integer, db.ForeignKey("asset_types.asset_type_id"))
    status_id = db.Column(db.Integer, db.ForeignKey("asset_statuses.status_id"))
    location_id = db.Column(db.Integer, db.ForeignKey("locations.location_id"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("employees.employee_id"))
    purchase_date = db.Column(db.Date)
    purchase_cost = db.Column(db.Numeric(12, 2))
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.vendor_id"))
    warranty_expiry = db.Column(db.Date)
    serial_number = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class AssetAssignment(db.Model):
    __tablename__ = "asset_assignments"
    assignment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.asset_id"))
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id"))
    assigned_date = db.Column(db.Date, nullable=False)
    returned_date = db.Column(db.Date)


class AssetMaintenance(db.Model):
    __tablename__ = "asset_maintenance"
    maintenance_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.asset_id"))
    maintenance_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    performed_by = db.Column(db.String(150))
    cost = db.Column(db.Numeric(12, 2))
    next_due_date = db.Column(db.Date)


class AssetDisposal(db.Model):
    __tablename__ = "asset_disposals"
    disposal_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.asset_id"))
    disposal_date = db.Column(db.Date, nullable=False)
    method = db.Column(db.Enum("Sold", "Recycled", "Scrapped", "Donated"), nullable=False)
    sale_value = db.Column(db.Numeric(12, 2))
    notes = db.Column(db.Text)
