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
    
    print("App+Db test, test user columns")
    #test user has isAdmin flag set
    user = User()
    db_handle.session.add(user)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

    db_handle.session.rollback()

def test_course_columns(db_handle):

    print("App+Db test, test course columns")
    #test that course name is unique
    course1=get_course()
    course2=get_course()
    db_handle.session.add(course1)
    db_handle.session.add(course2)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

    db_handle.session.rollback()

