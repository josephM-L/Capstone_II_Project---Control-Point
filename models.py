from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class AssetType(db.Model):
    __tablename__ = "asset_types"
    asset_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.Enum("Tangible", "Intangible"), nullable=False)
    description = db.Column(db.Text)

    assets = db.relationship("Asset", back_populates="asset_type")


class AssetStatus(db.Model):
    __tablename__ = "asset_statuses"
    status_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status_name = db.Column(db.String(50), nullable=False)

    assets = db.relationship("Asset", back_populates="status")


class Department(db.Model):
    __tablename__ = "departments"
    department_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id", ondelete="SET NULL"), nullable=True)

    employees = db.relationship("Employee", back_populates="department", foreign_keys="[Employee.department_id]")
    manager = db.relationship("Employee", foreign_keys=[manager_id], post_update=True)


class Employee(db.Model):
    __tablename__ = "employees"
    employee_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id", ondelete="SET NULL"), nullable=True)
    role = db.Column(db.String(100))
    status = db.Column(db.Enum("Active", "Inactive"), default="Active")

    department = db.relationship("Department", back_populates="employees", foreign_keys=[department_id], passive_deletes=True)

    assignments = db.relationship("AssetAssignment", back_populates="employee", passive_deletes=True)
    assigned_assets = db.relationship("Asset", back_populates="assigned_employee")


class Location(db.Model):
    __tablename__ = "locations"
    location_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))

    assets = db.relationship("Asset", back_populates="location")


class Vendor(db.Model):
    __tablename__ = "vendors"
    vendor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    contact_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    address = db.Column(db.String(255))

    assets = db.relationship("Asset", back_populates="vendor")


class Asset(db.Model):
    __tablename__ = "assets"
    asset_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_tag = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    asset_type_id = db.Column(db.Integer, db.ForeignKey("asset_types.asset_type_id", ondelete="SET NULL"), nullable=True)
    status_id = db.Column(db.Integer, db.ForeignKey("asset_statuses.status_id", ondelete="SET NULL"), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.location_id", ondelete="SET NULL"), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("employees.employee_id", ondelete="SET NULL"), nullable=True)
    purchase_date = db.Column(db.Date)
    purchase_cost = db.Column(db.Numeric(12, 2))
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.vendor_id"))
    warranty_expiry = db.Column(db.Date)
    serial_number = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset_type = db.relationship("AssetType", back_populates="assets", passive_deletes=True)
    status = db.relationship("AssetStatus", back_populates="assets", passive_deletes=True)
    location = db.relationship("Location", back_populates="assets", passive_deletes=True)
    vendor = db.relationship("Vendor", back_populates="assets", passive_deletes=True)
    assigned_employee = db.relationship("Employee", back_populates="assigned_assets", passive_deletes=True)

    assignments = db.relationship("AssetAssignment", back_populates="asset", cascade="all, delete-orphan")
    maintenances = db.relationship("AssetMaintenance", back_populates="asset", cascade="all, delete-orphan")
    disposals = db.relationship("AssetDisposal", back_populates="asset", cascade="all, delete-orphan")


class AssetAssignment(db.Model):
    __tablename__ = "asset_assignments"
    assignment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.asset_id", ondelete="CASCADE"))
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.employee_id", ondelete="CASCADE"))
    assigned_date = db.Column(db.Date, nullable=False)
    returned_date = db.Column(db.Date)

    asset = db.relationship("Asset", back_populates="assignments")
    employee = db.relationship("Employee", back_populates="assignments")


class AssetMaintenance(db.Model):
    __tablename__ = "asset_maintenance"
    maintenance_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.asset_id", ondelete="CASCADE"))
    maintenance_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    performed_by = db.Column(db.String(150))
    cost = db.Column(db.Numeric(12, 2))
    next_due_date = db.Column(db.Date)

    asset = db.relationship("Asset", back_populates="maintenances")


class AssetDisposal(db.Model):
    __tablename__ = "asset_disposals"
    disposal_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.asset_id", ondelete="CASCADE"))
    disposal_date = db.Column(db.Date, nullable=False)
    method = db.Column(db.Enum("Sold", "Recycled", "Scrapped", "Donated"), nullable=False)
    sale_value = db.Column(db.Numeric(12, 2))
    notes = db.Column(db.Text)

    asset = db.relationship("Asset", back_populates="disposals")

class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150))
    role = db.Column(db.Enum("admin", "manager", "user"), default="user", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)