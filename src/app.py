import json
from flask import Flask, request, Response, abort
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource
from flask_restful import Api

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db/database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)
MASON = "application/vnd.mason+json"

coursemediarelation = db.Table("coursemediarelation",db.Model.metadata,
    db.Column("courseid", db.Integer, db.ForeignKey("TrainingCourse.id")),
    db.Column("mediaid", db.Integer, db.ForeignKey("CourseMedia.id"))
)

courseuserrelation = db.Table("courseuserrelation",
    db.Column("courseid", db.Integer, db.ForeignKey("TrainingCourse.id")),
    db.Column("userid", db.Integer, db.ForeignKey("User.id")),
    db.Column("addedtocourse", db.DateTime),
    db.Column("canModify", db.Boolean),
    db.Column("courseCompletionScore", db.Integer),
    db.Column("courseCompletionDate", db.DateTime)
)

class MasonBuilder(dict):
    """
    Class from course examples.
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href
def create_error_response(status_code, title, message=None):
    """
    Class from course examples.
    """
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    #body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)


# todo: on delete

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    email = db.Column(db.String(100))
    isAdmin = db.Column(db.Boolean, nullable=False)
    creationdate = db.Column(db.DateTime)

    def __repr__(self):
        return "<User %s %s>" % (self.firstname,self.lastname)

class TrainingCourse(db.Model):
    __tablename__ = 'TrainingCourse'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    creationdate = db.Column(db.DateTime)
    startdate = db.Column(db.DateTime)
    enddate = db.Column(db.DateTime)
    coursedatajson = db.Column(db.String)
    medialist = db.relationship("CourseMedia",secondary=coursemediarelation)
    users = db.relationship("User",secondary=courseuserrelation)

    def __repr__(self):
        return "TrainingCourse name : %s \n medias: %s \n users: %s \n" % (self.name,self.medialist,self.users)

class CourseMedia(db.Model):
    __tablename__ = 'CourseMedia'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255))
    type = db.Column(db.String(20))

    def __repr__(self):
        return "<CourseMedia %s %s>" % (self.url,self.type)

class TrainingCourseCollection(Resource):
    def get(self):
        items = TrainingCourse.query.all()
        returnlist = []
        for item in items:
            #iteminventory = []
            #storageitems = StorageItem.query.filter_by(product=item)
            #for storageitem in storageitems:
            #   iteminventory.append([storageitem.location,storageitem.qty])

            newitem = {
                "id":item.id,
                "name":item.name,
                "creationdate":item.creationdate,
                "startdate":item.startdate,
                "enddate":item.enddate,
                "coursedatajson":item.coursedatajson
            }
            #todo only courses media
            #coursemedias = TrainingCourse.query.join(CourseMedia,TrainingCourse.medialist)
            coursemedias = item.medialist

            medialist = []
            for mediaitem in coursemedias:
                newmediaitem = {
                    "id":mediaitem.id,
                    "url":mediaitem.url,
                    "type":mediaitem.type
                }
                medialist.append(newmediaitem)

            newitem["medialist"]=medialist
            returnlist.append(newitem)
        return returnlist

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

#api.add_resource(UserCollection, "/api/users/")
#api.add_resource(UserEntry, "/api/users/<id>/")
api.add_resource(TrainingCourseCollection, "/api/trainingcourses/")
#api.add_resource(MediaEntry, "api/coursemedia/<id>")
