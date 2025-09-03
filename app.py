# 127.0.0.1:5000

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

#connect to the DB
#let Joseph know if the database can't connect, the IP probably changed
#TODO this needs to be obscured and changed later for security purposes
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://flaskuser:testpassword@47.199.71.84:3306/flaskdb"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False



db = SQLAlchemy(app)

# Create model to use DB from
class User(db.Model):
    __tablename__ = "test_users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

# Defines the file structure of the app and binds the files/pages to objects
@app.route('/')
def index():
    users = User.query.all()
    output ="<br>".join(f"{user.id}: {user.name}" for user in users)

    return "<h1> Hello World! </h1>" + output

    # This returns the html file, for testing the DB it has temporarily been changed to the
    #return render_template('index.html')

# run the app
if __name__ == '__main__':
    app.run(debug=True)
