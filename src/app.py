from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db/database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	firstname = db.Column(db.String(30))
	lastname = db.Column(db.String(30))
	email = db.Column(db.String(100))
	isAdmin = db.Column(db.Boolean, nullable=False)
	creationdate = db.Column(db.DateTime)


class TrainingCourse(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30))
	creationdate = db.Column(db.DateTime)
	startdate = db.Column(db.DateTime)
	enddate = db.Column(db.DateTime)
	coursedatajson = db.Column(db.String)

class CourseMedia(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	url = db.Column(db.String(255))
	type = db.Column(db.String(20))


#coursemediarelation = db.Table("coursemediarelation",
#	db.Column("courseid", db.Integer, db.ForeignKey("TrainingCourse.id"), primary_key=True),
#	db.Column("mediaid", db.Integer, db.ForeignKey("CourseMedia.id"), primary_key=True)
#)
