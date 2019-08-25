import json
from flask import Flask, request, Response, abort
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource
from flask_restful import Api

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db/database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)
MASON = "application/vnd.mason+json"
LINK_RELATIONS_URL = "/trainingmanager/link-relations/"

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


class TrainingCourseBuilder(MasonBuilder):
        def add_control_delete_course(self, course):
            self.add_control(
                "trainingmanager:delete",
                api.url_for(TrainingCourseItem, course=course),
                method="DELETE",
                title="Delete this course"
            )

        def add_control_add_course(self):
            self.add_control(
                "trainingmanager:add-course",
                api.url_for(TrainingCourseCollection),
                method="POST",
                encoding="json",
                title="Add a new course"
            )

        def add_control_modify_course(self, course):
            self.add_control(
                "edit",
                api.url_for(TrainingCourseItem, course=course),
                method="PUT",
                encoding="json",
                title="Edit this course"          
            )


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
    name = db.Column(db.String(50), unique=True)
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


class TrainingCourseItem(Resource):
    def get(self,course):
        db_course = TrainingCourse.query.filter_by(name=course).first()
        if db_course is None:
            return create_error_response(404, "Not found", 
                "No course was found with the name {}".format(course)
            )

        body = TrainingCourseBuilder(
            name=db_course.name
        )
        body.add_namespace("trainingmanager", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(TrainingCourseItem, course=course))
        body.add_control("collection", api.url_for(TrainingCourseCollection))
        body.add_control_delete_course(course)
        body.add_control_modify_course(course)
        #print(json.dumps(body))
        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self,course):
        db_course = TrainingCourse.query.filter_by(name=course).first()
        if db_course is None:
            return create_error_response(404, "Not found", 
                "No course was found with the name {}".format(course)
            )
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        db_course.name = request.json["name"]
        
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Course with name '{}' already exists.".format(request.json["name"])
            )
        
        return Response(status=204)

    def delete(self,course):
        db_course = TrainingCourse.query.filter_by(name=course).first()
        if db_course is None:
            return create_error_response(404, "Not found", 
                "No course was found with the name {}".format(course)
            )
        
        db.session.delete(db_course)
        db.session.commit()
        
        return Response(status=204)


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

        course = TrainingCourse(
            name=request.json["name"]            
        )

        try:
            db.session.add(course)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Course with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=201, headers={
            "Location": api.url_for(TrainingCourseItem, course=request.json["name"])
        })

#api.add_resource(UserCollection, "/api/users/")
#api.add_resource(UserEntry, "/api/users/<id>/")
api.add_resource(TrainingCourseCollection, "/api/trainingcourses/")
api.add_resource(TrainingCourseItem,"/api/trainingcourses/<course>/")
#api.add_resource(MediaEntry, "api/coursemedia/<id>")

@app.route(LINK_RELATIONS_URL)
def send_link_relations():
    return "link relations"

