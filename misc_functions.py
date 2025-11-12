import csv
import io
import zipfile

from flask import send_file

from models import Asset, AssetStatus, Employee, AssetAssignment, AssetType, AssetMaintenance, AssetDisposal, Department, Vendor, Location


def export_db():
    # Create an in-memory bytes buffer for the zip
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # --- ASSETS ---
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "asset_id", "asset_tag", "name", "description", "asset_type_id", "status_id",
            "location_id", "assigned_to", "purchase_date", "purchase_cost",
            "vendor_id", "warranty_expiry", "serial_number"
        ])
        for a in Asset.query.all():
            writer.writerow([
                a.asset_id,
                a.asset_tag,
                a.name,
                a.description,
                a.asset_type_id,
                a.status_id,
                a.location_id,
                a.assigned_to,
                a.purchase_date,
                a.purchase_cost,
                a.vendor_id,
                a.warranty_expiry,
                a.serial_number
            ])
        zip_file.writestr("assets.csv", output.getvalue())
        output.close()

        # --- EMPLOYEES ---
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["employee_id", "first_name", "last_name", "email", "phone", "department_id", "role", "status"])
        for e in Employee.query.all():
            writer.writerow([
                e.employee_id,
                e.first_name,
                e.last_name,
                e.email,
                e.phone,
                e.department_id,
                e.role,
                e.status
            ])
        zip_file.writestr("employees.csv", output.getvalue())
        output.close()

        # --- ASSET TYPES ---
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["asset_type_id", "name", "category", "description"])
        for a in AssetType.query.all():
            writer.writerow([
                a.asset_type_id,
                a.name,
                a.category,
                a.description
            ])
        zip_file.writestr("asset_types.csv", output.getvalue())
        output.close()

        # --- ASSET STATUSES ---
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["status_id", "status_name"])
        for a in AssetStatus.query.all():
            writer.writerow([
                a.status_id,
                a.status_name,
            ])
        zip_file.writestr("asset_statuses.csv", output.getvalue())
        output.close()

        # --- LOCATIONS ---
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["location_id", "name","address","city","country"])
        for l in Location.query.all():
            writer.writerow([
                l.location_id,
                l.name,
                l.address,
                l.city,
                l.country
            ])
        zip_file.writestr("locations.csv", output.getvalue())
        output.close()

        # --- VENDORS ---
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["vendor_id","name","contact_name","phone","email","address"])
        for v in Vendor.query.all():
            writer.writerow([
                v.vendor_id,
                v.name,
                v.contact_name,
                v.phone,
                v.email,
                v.address
            ])
        zip_file.writestr("vendors.csv", output.getvalue())
        output.close()

        # --- ASSET ASSIGNMENTS ---
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["assignment_id","asset_id","employee_id","assigned_date","returned_date"])
        for a in AssetAssignment.query.all():
            writer.writerow([
                a.assignment_id,
                a.asset_id,
                a.employee_id,
                a.assigned_date,
                a.returned_date,
            ])
        zip_file.writestr("asset_assignments.csv", output.getvalue())
        output.close()

        # --- ASSET MAINTENANCES ---
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["maintenance_id","asset_id","maintenance_date","performed_by","cost","next_due_date"])
        for a in AssetMaintenance.query.all():
            writer.writerow([
                a.maintenance_id,
                a.asset_id,
                a.maintenance_date,
                a.performed_by,
                a.cost,
                a.next_due_date
            ])
        zip_file.writestr("asset_maintenances.csv", output.getvalue())
        output.close()

        # --- ASSET DISPOSALS ---
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["disposal_id","asset_id","disposal_date","method","sale_value","notes"])
        for a in AssetDisposal.query.all():
            writer.writerow([
                a.disposal_id,
                a.asset_id,
                a.disposal_date,
                a.method,
                a.sale_value,
                a.notes
            ])
        zip_file.writestr("asset_disposals.csv", output.getvalue())
        output.close()

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="full_database_export.zip"
    )