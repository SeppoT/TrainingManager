import os
import pytest
import tempfile
import time
import sys
import json
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
from datetime import datetime
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError

from app import app, db
from app import User,TrainingCourse,CourseMedia

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def client():
    
    db_fd, db_fname = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.config["TESTING"] = True

    db.create_all()
    _populate_db()

    yield app.test_client()

    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

def _populate_db():
    """API test db creation, test data"""
    for i in range(1, 4):
        s = TrainingCourse(
            name="test-course-{}".format(i)
        )
        
        for a in range(1,4):
            media = CourseMedia(
                url="test-url-{}-{}".format(i,a),
                type="image"
            )                
            s.medialist.append(media)

        for z in range(1,4):
            user = User(
                firstname="test-firstname-{}".format(z),
                lastname="test-lastname-{}".format(z),
                email="test-email-{}".format(z),
                isAdmin=False
            )
            s.users.append(user)

        #print(s)
        db.session.add(s)

    db.session.commit()

class TestTrainingCourseCollection(object):
    
    RESOURCE_URL = "/api/trainingcourses/"

    def test_get(self, client):
        print('TrainingCourseCollection api get test(should return 3 items with id and name)')
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        print(body)
        assert len(body) == 3
        for item in body:
            assert "id" in item
            assert "name" in item    

    def test_post(self, client):
        valid = {"name":"test-course-validname"}

        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        print('TrainingCourseCollection api post test, invalid media format')
        print(resp)
        assert resp.status_code == 415


