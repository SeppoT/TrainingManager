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

from app import app, db
from app import User,TrainingCourse,CourseMedia

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def client():
    print('starting api test...')
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
    for i in range(1, 4):
        s = TrainingCourse(
            name="test-course-{}".format(i)
        )
        db.session.add(s)
    db.session.commit()

class TestTrainingCourseCollection(object):
    
    RESOURCE_URL = "/api/trainingcourses/"

    def test_get(self, client):
        print('TrainingCourseCollection api get test...')
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200        

