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

class UserBuilder(MasonBuilder):
        def add_control_add_user(self):
            self.add_control(                
                "trainingmanager:add-user",
                api.url_for(UserCollection),
                method="POST",
                encoding="json",
                title="Add new user"
            )
        def add_control_delete_user(self,id):
            self.add_control(
                "trainingmanager:delete-user",
                api.url_for(UserItem, id=id),
                method="DELETE",
                title="Delete this user"
            )
        def add_control_modify_user(self,id):
            self.add_control(
                "edit",
                api.url_for(UserItem, id=id),
                method="PUT",
                encoding="json",
                title="Edit this user"    
            )

class MediaBuilder(MasonBuilder):
        def add_control_add_media(self):
            self.add_control(                
                "trainingmanager:add-media",
                api.url_for(CourseMediaCollection),
                method="POST",
                encoding="json",
                title="Add new media"
            )

class TrainingCourseBuilder(MasonBuilder):
        def add_control_delete_course(self, course):
            self.add_control(
                "trainingmanager:delete-course",
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
                title="Add new course"
            )

        def add_control_modify_course(self, course):
            self.add_control(
                "edit",
                api.url_for(TrainingCourseItem, course=course),
                method="PUT",
                encoding="json",
                title="Edit this course"          
            )

        def add_control_add_media(self, course):
            self.add_control(
                "addmedia",
                api.url_for(TrainingCourseItem, course=course),
                method="POST",
                encoding="json",
                title="Add media to course"
                )
        def add_control_add_user_to_course(self, course):
            self.add_control(
                "addcourseuser",
                api.url_for(TrainingCourseItem, course=course),
                method="POST",
                encoding="json",
                title="Add user to course"
                )


# todo: on delete

"""
Database ORM classes (SQLAlchemy)
"""
class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    email = db.Column(db.String(100))
    isAdmin = db.Column(db.Boolean, nullable=False)
    creationdate = db.Column(db.DateTime)
    courses = db.relationship("TrainingCourse",secondary=courseuserrelation,back_populates="users")

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
    medialist = db.relationship("CourseMedia",secondary=coursemediarelation,back_populates="courses")
    users = db.relationship("User",secondary=courseuserrelation,back_populates="courses")

    def __repr__(self):
        return "TrainingCourse name : %s \n medias: %s \n users: %s \n" % (self.name,self.medialist,self.users)

class CourseMedia(db.Model):
    __tablename__ = 'CourseMedia'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255))
    type = db.Column(db.String(20))
    courses = db.relationship("TrainingCourse",secondary=coursemediarelation,back_populates="medialist")

    def __repr__(self):
        return "<CourseMedia %s %s>" % (self.url,self.type)

"""
Resource classes for rest api
"""
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
        body.add_control_add_media(course)
        body.add_control_add_user_to_course(course)

        body.add_control("trainingmanager:coursemedias",
            api.url_for(CourseMediaCollection, course=course)
        )

        print(json.dumps(body))
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

        body = TrainingCourseBuilder()
        body.add_namespace("trainingmanager", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(TrainingCourseCollection))
        body.add_control_add_course()

        items = TrainingCourse.query.all()
        returnlist = []
        for item in items:

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

class CourseMediaCollection(Resource):
    def get(self,course):
        body = MediaBuilder()
        body.add_namespace("trainingmanager", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(CourseMediaCollection, course=course))
        print(body)

        items = CourseMedia.query.all()
        returnlist = []
        for item in items:            

            newitem = {
                "url":item.url,
                "type":item.type
            }
            
            returnlist.append(newitem)
        return returnlist

    def post(self,course):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        newmedia = CourseMedia(
            url=request.json["url"],
            type=request.json["type"]        
        )
            
        try:
            db.session.add(newmedia)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            return create_error_response(409, "Integrityerror, media add")

        return Response(status=201, headers={
            "Location": api.url_for(MediaItem, id=newmedia.id)
        })

class MediaItem(Resource):
    def get(self,id):        
        db_media = CourseMedia.query.filter_by(id=id).first()
        if db_media is None:
            return create_error_response(404, "Not found", 
                "No media was found with the id {}".format(id)
            )

        body = MediaBuilder(
            url=db_media.url,
            type=db_media.type
        )
        body.add_namespace("trainingmanager", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(MediaItem, id=id))
        #Should return all media items, not implemented
        #body.add_control("collection", api.url_for(AllMediaCollection))

        print(json.dumps(body))
        return Response(json.dumps(body), 200, mimetype=MASON)
    def put(self,id):
        db_media = CourseMedia.query.filter_by(id=id).first()
        if db_media is None:
            return create_error_response(404, "Not found", 
                "No media was found with the id {}".format(id)
            )
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )      
        db_media.url = request.json["url"]
        db_media.type = request.json["type"]       

        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Media with id '{}' put error".format(request.json["id"])
            )
        
        return Response(status=204) 
    def delete(self):
        db_media = CourseMedia.query.filter_by(id=id).first()
        if db_media is None:
            return create_error_response(404, "Not found", 
                "No media was found with the id {}".format(id)
            )
        
        db.session.delete(db_media)
        db.session.commit()
        
        return Response(status=204)

class UserCollection(Resource):
    def get(self):
        body = UserBuilder()
        body.add_namespace("trainingmanager", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(UserCollection))
        body.add_control_add_user()
        body["items"] = []
        for item in User.query.all():         

            newitem = UserBuilder(
                id=item.id,
                firstname=item.firstname,
                lastname=item.lastname,
                email=item.email
            )
            newitem.add_control("self", api.url_for(UserItem, id=item.id))            
            body["items"].append(newitem)
            
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        newuser = User(
            firstname=request.json["firstname"],
            lastname=request.json["lastname"],
            isAdmin=request.json["isAdmin"],            
        )
              
        try:
            db.session.add(newuser)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            return create_error_response(409, "Integrityerror, user add")

        return Response(status=201, headers={
            "Location": api.url_for(UserItem, id=newuser.id)
        })

class UserItem(Resource):
    def get(self,id):
        db_user = User.query.filter_by(id=id).first()
        if db_user is None:
            return create_error_response(404, "Not found", 
                "No user was found with the id {}".format(id)
            )

        body = UserBuilder(
            firstname=db_user.firstname,
            lastname=db_user.lastname
        )
        body.add_namespace("trainingmanager", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(UserItem, id=id))
        body.add_control("collection", api.url_for(UserCollection))
        body.add_control_delete_user(id)
        body.add_control_modify_user(id)

        print(json.dumps(body))
        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self,id):
        db_user = User.query.filter_by(id=id).first()
        if db_user is None:
            return create_error_response(404, "Not found", 
                "No user was found with the id {}".format(id)
            )
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        db_user.firstname = request.json["firstname"]
        db_user.lastname = request.json["lastname"]
        db_user.email = request.json["email"]

        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "User with id '{}' put error".format(request.json["id"])
            )
        
        return Response(status=204)    

    def delete(self,id):
        db_user = User.query.filter_by(id=id).first()
        if db_user is None:
            return create_error_response(404, "Not found", 
                "No user was found with the id {}".format(id)
            )
        
        db.session.delete(db_user)
        db.session.commit()
        
        return Response(status=204)

api.add_resource(UserCollection, "/api/users/")
api.add_resource(UserItem, "/api/users/<id>/")
api.add_resource(TrainingCourseCollection, "/api/trainingcourses/")
api.add_resource(TrainingCourseItem,"/api/trainingcourses/<course>/")
api.add_resource(MediaItem, "/api/coursemedia/<id>/")
#all medias from all cources, not implemented:
#api.add_resource(MediaItemCollection, "/api/coursemedia/") 
api.add_resource(CourseMediaCollection, "/api/trainingcourses/<course>/medias/")

@app.route(LINK_RELATIONS_URL)
def send_link_relations():
    return "link relations"
