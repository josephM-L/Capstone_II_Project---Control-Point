# 127.0.0.1:5000

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

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

# Defines the file structure of the app and binds the files/pages to objects
@app.route('/')
def index():
    assets = Asset.query.all()
    output ="<br>".join(f"{assets.id}: {assets.name}" for asset in assets)

    return "<h1> Hello World! </h1>" + output

    # This returns the html file, for testing the DB it has temporarily been changed to the
    #return render_template('index.html')

# run the app
if __name__ == '__main__':
    app.run(debug=True)
