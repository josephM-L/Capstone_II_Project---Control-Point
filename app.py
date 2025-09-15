# 127.0.0.1:5000
from flask import Flask, render_template, request, redirect, flash, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
#TODO use something like import os to generate this later for security
app.secret_key = "dev-secret"

#connect to the DB
#let Joseph know if the database can't connect, the IP probably changed

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



db = SQLAlchemy(app)

# Create model to use DB from
class Asset(db.Model):
    __tablename__ = "assets"
    asset_id = db.Column(db.Integer, primary_key=True)
    asset_tag = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    purchase_date = db.Column(db.Date)
    purchase_cost = db.Column(db.Numeric(12,2))
    serial_number = db.Column(db.String(150))

# Defines the file structure of the app and binds the files/pages to objects
@app.route('/')
def index():
    return render_template('index.html')

@app.route("/assets/new", methods=["GET", "POST"])
def create_asset():
    if request.method == "POST":
        asset_tag = request.form.get("asset_tag", "").strip()
        name = request.form.get("name", "").strip()
        description = request.form.get("description")
        purchase_date = request.form.get("purchase_date")
        purchase_cost = request.form.get("purchase_cost")
        serial_number = request.form.get("serial_number")

        if not asset_tag or not name:
            flash("Asset tag and name are required!", "danger")
            return redirect("/assets/new")

        try:
            purchase_date_parsed = datetime.strptime(purchase_date, "%Y-%m-%d").date() if purchase_date else None
            purchase_cost_val = float(purchase_cost) if purchase_cost else None

            new_asset = Asset(
                asset_tag=asset_tag,
                name=name,
                description=description,
                purchase_date=purchase_date_parsed,
                purchase_cost=purchase_cost_val,
                serial_number=serial_number
            )

            db.session.add(new_asset)
            db.session.commit()
            flash("Asset added successfully!", "success")
            return redirect("/assets/new")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect("/assets/new")

    return render_template("add_asset.html")

@app.route("/assets/show", methods=["GET"])
def show_asset():
    # Query all assets
    asset_query = Asset.query.order_by(Asset.asset_id).all()
    return render_template("show_assets.html", assets=asset_query)

@app.route("/assets/delete/<int:asset_id>", methods=["GET", "POST"])
def delete_asset(asset_id):
    asset = Asset.query.get(asset_id)
    if asset:
        db.session.delete(asset)
        db.session.commit()
    return redirect("/assets/show")

# run the app
if __name__ == '__main__':
    app.run(debug=True)
