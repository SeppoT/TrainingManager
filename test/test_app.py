import os
import pytest
import tempfile
import time
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
from datetime import datetime
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError

import app
from app import User,TrainingCourse,CourseMedia

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def db_handle():
    db_fd, db_fname = tempfile.mkstemp()
    app.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.app.config["TESTING"] = True
    
    with app.app.app_context():
        app.db.create_all()
        
    yield app.db
    
    app.db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

def get_user():
    return User(
        firstname="testfirst",
        lastname="testlast",
        email="testemail",
        isAdmin=False
    )

def get_course():
    return TrainingCourse(
        name="testcoursename"
    )

def get_media():
    return CourseMedia(
        url="testurl",
        type="image"
    )

def test_create_instances(db_handle):
    """
    Create instances, based on course example
    """
    print("App+Db test, create instances")
    user = get_user()
    course = get_course()
    media = get_media()

    course.users.append(user)
    course.medialist.append(media)

    db_handle.session.add(user)
    db_handle.session.add(course)
    db_handle.session.add(media)

    db_handle.session.commit();

    #check that tables exist
    assert User.query.count() == 1
    assert CourseMedia.query.count() == 1
    assert TrainingCourse.query.count() == 1

    db_user = User.query.first()
    db_course = TrainingCourse.query.first()
    db_media = CourseMedia.query.first()

    #Check that course countain appended user and media
    assert db_user in db_course.users
    assert db_media in db_course.medialist

def test_user_columns(db_handle):
    
    '''
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    email = db.Column(db.String(100))
    isAdmin = db.Column(db.Boolean, nullable=False)
    creationdate = db.Column(db.DateTime)
    courses = db.relationship("TrainingCourse",secondary=courseuserrelation,back_populates="users")
    '''

    print("App+Db test, test user columns")
    #test user has isAdmin flag set
    user = User()
    db_handle.session.add(user)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

    db_handle.session.rollback()

    user = User()
    user.isAdmin=True;
    db_handle.session.add(user)
    db_handle.session.commit()

    db_handle.session.rollback()

    user = User()
    user.isAdmin=True;
    user.firstname='testi1'
    user.lastname='testi2'
    user.email='testemail@com'    
    db_handle.session.add(user)
    db_handle.session.commit()

    print("test user update and delete")
    print(user.id)
    getuser = User.query.filter_by(id=user.id).first()
    assert getuser.firstname == 'testi1'

    getuser.firstname = 'nameedited'
    db_handle.session.add(getuser)
    db_handle.session.commit()
    getuser2 = User.query.filter_by(id=getuser.id).first()
    with pytest.raises(AssertionError):
        assert getuser2.firstname == 'nameeditedwrong'

    db_handle.session.delete(getuser2)
    db_handle.session.commit()
    getuser3 = User.query.filter_by(id=getuser2.id).first()
    #check if deleted
    with pytest.raises(AttributeError):
        assert getuser3.firstname == 'nameedited'


def test_course_columns(db_handle):
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    creationdate = db.Column(db.DateTime)
    startdate = db.Column(db.DateTime)
    enddate = db.Column(db.DateTime)
    coursedatajson = db.Column(db.String)
    medialist = db.relationship("CourseMedia",backref="trainingcourse", lazy=True)
    users = db.relationship("User",secondary=courseuserrelation,back_populates="courses")
    '''

    print("App+Db test, test course columns")
    #test that course name is unique
    course1=get_course()
    course2=get_course()
    db_handle.session.add(course1)
    db_handle.session.add(course2)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

    db_handle.session.rollback()

    course = TrainingCourse()
    course.isAdmin=True;
    db_handle.session.add(course)
    db_handle.session.commit()

    db_handle.session.rollback()

    course = TrainingCourse()
    course.name='testi1'
    db_handle.session.add(course)
    db_handle.session.commit()

    print("test course update and delete")
    print(course.id)
    getcourse = TrainingCourse.query.filter_by(id=course.id).first()
    assert getcourse.name == 'testi1'

    getcourse.name = 'nameedited'
    db_handle.session.add(getcourse)
    db_handle.session.commit()
    getcourse2 = TrainingCourse.query.filter_by(id=getcourse.id).first()
    with pytest.raises(AssertionError):
        assert getcourse2.name == 'nameeditedwrong'

    db_handle.session.delete(getcourse2)
    db_handle.session.commit()
    getcourse3 = TrainingCourse.query.filter_by(id=getcourse2.id).first()
    #check if deleted
    with pytest.raises(AttributeError):
        assert getcourse3.name == 'nameedited'

def test_coursemedia_columns(db_handle):
    '''
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255))
    type = db.Column(db.String(20))
    course_id = db.Column(db.Integer, db.ForeignKey('TrainingCourse.id', ondelete="SET NULL"))
    '''
    print("App+Db test, test coursemedia columns")
    media = CourseMedia()
    media.url='testi1'
    db_handle.session.add(media)
    db_handle.session.commit()

    print("test media update and delete")
    print(media.id)
    getmedia = CourseMedia.query.filter_by(id=media.id).first()
    assert getmedia.url == 'testi1'

    getmedia.url = 'nameedited'
    db_handle.session.add(getmedia)
    db_handle.session.commit()
    getmedia2 = CourseMedia.query.filter_by(id=getmedia.id).first()
    with pytest.raises(AssertionError):
        assert getmedia2.url == 'nameeditedwrong'

    db_handle.session.delete(getmedia2)
    db_handle.session.commit()
    getmedia3 = CourseMedia.query.filter_by(id=getmedia2.id).first()
    #check if deleted
    with pytest.raises(AttributeError):
        assert getmedia3.url == 'nameedited'

