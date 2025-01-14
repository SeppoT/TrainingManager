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
    """API test db creation, test data, based on course example"""
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

def _check_namespace(client, response):
    """
    Check namespace (from course example)
    """
    ns_href = response["@namespaces"]["trainingmanager"]["name"]
    resp = client.get(ns_href)
    print("Check namespace")
    #print(resp)
    assert resp.status_code == 200
    
def _check_control_get_method(ctrl, client, obj):
    """
    Check get control (from course example)
    """
    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    print("Check get control")
    #print(resp)
    assert resp.status_code == 200
    
def _check_control_delete_method(ctrl, client, obj):
    """
    Check delete control (from course example)
    """
    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    print("Check delete control")
    #print(resp)
    assert resp.status_code == 204
    
def _check_control_put_method(ctrl, client, obj):
    """
    Check put control (from course example)
    """
    
    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    assert method == "put"
    assert encoding == "json"
    body = {}
    body["name"] = obj["name"] 
    body["coursedatajson"] = obj["coursedatajson"]
    resp = client.put(href, json=body)
    print("Check put control")
    #print(resp)
    assert resp.status_code == 204
    
def _check_control_post_method(ctrl, client, obj):
    """
    Check post control (from course example)
    """
    
    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()    
    assert method == "post"
    assert encoding == "json"
    body = _get_sensor_json()    
    resp = client.post(href, json=body)

    assert resp.status_code == 201

#test recourse apis, based on course examples
class TestTrainingCourseCollection(object):
    
    RESOURCE_URL = "/api/trainingcourses/"

    def test_get(self, client):
        print('TrainingCourseCollection api get test(should return 3 items with id and name)')
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        #print(body)
        assert len(body["items"]) == 3
        for item in body["items"]:   
            assert "id" in item
            assert "name" in item    

    def test_post(self, client):
        valid = {"name":"test-course-validname","coursedatajson":"<h5>content</h5>"}

        #test wrong content type:
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        print('TrainingCourseCollection api post test, invalid media format',)
        #print(resp)
        assert resp.status_code == 415

        #test with valid content:
        print('TrainingCourseCollection api post test, valid content')
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        #print(resp)
        
        assert resp.headers["Location"].endswith("/")
        
        resp = client.get(resp.headers["Location"])
        
        assert resp.status_code == 200
        body = json.loads(resp.data)      
        assert body["name"] == "test-course-validname"

class TestTrainingCourse(object):

    RESOURCE_URL = "/api/trainingcourses/1/"
    INVALID_URL = "/api/trainingcourses/non-course-x/"    

    def test_get(self, client):
        print('TrainingCourse api  test, get course')
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == "test-course-1"
        _check_namespace(client, body)       
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body)
        _check_control_delete_method("trainingmanager:delete-course", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        print('TrainingCourse api test, put course')
        valid = {"name":"test-course-validname","coursedatajson":"<h5>content</h5>"}
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        #print(resp)
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        #print(resp)
        assert resp.status_code == 404
        
        # test with another name
        valid["name"] = "test-course-2"
        resp = client.put(self.RESOURCE_URL, json=valid)
        #print(resp)
        assert resp.status_code == 409
        
        # test with valid 
        valid["name"] = "test-course-1"
        resp = client.put(self.RESOURCE_URL, json=valid)
        #print(resp)
        assert resp.status_code == 204
        
                
    def test_delete(self, client):
        print('TrainingCourse api test, delete course')
        resp = client.delete(self.RESOURCE_URL)
        #print(resp)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        #print(resp)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        #print(resp)
        assert resp.status_code == 404


class TestUser(object):

    RESOURCE_URL = "/api/users/1/"
    INVALID_URL = "/api/users/0/"

    def test_get(self, client):
        print('User api test, get')
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        #print(body)
        assert body["firstname"] == "test-firstname-1"
        _check_namespace(client, body)       
        _check_control_get_method("collection", client, body)
        _check_control_delete_method("trainingmanager:delete-user", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        print('User api test, put')
    
        valid = {"firstname":"test-user-validname"}
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        #print(resp)
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        #print(resp)
        assert resp.status_code == 404
        
        # test with valid 
        valid["firstname"] = "test-firstname-1"
        valid["lastname"] = "test-lastname-1"
        valid["email"] = "test-email-1"

        resp = client.put(self.RESOURCE_URL, json=valid)
        #print(resp)
        assert resp.status_code == 204


    def test_delete(self, client):
        print('User api test, delete')
        resp = client.delete(self.RESOURCE_URL)
        #print(resp)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        #print(resp)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        #print(resp)
        assert resp.status_code == 404

class TestUserCollection(object):
    
    RESOURCE_URL = "/api/users/"

    def test_get(self, client):
        print('User collection api test(should return 3 items with id and first name)')
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        #print(body)
        assert len(body["items"]) == 9
        for item in body["items"]:            
            assert "id" in item
            assert "firstname" in item    

    def test_post(self, client):
        valid = {"firstname":"test-valid-firstname"}
        valid["lastname"] = "test-lastname"
        valid["email"] = "test-email"
        valid["isAdmin"] = False

        #test wrong content type:
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        print('User collection api test,post invalid media format')
        #print(resp)
        assert resp.status_code == 415

        #test with valid content:
        print('User collection api test, valid content')
        #print(valid)
        resp = client.post(self.RESOURCE_URL, json=valid)        
        assert resp.status_code == 201
        
        assert resp.headers["Location"].endswith("/")
        #print(resp.headers["Location"])
        resp = client.get(resp.headers["Location"])
        
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["firstname"] == "test-valid-firstname"

class TestMediaItem(object):
    RESOURCE_URL = "/api/coursemedia/1/"
    INVALID_URL = "/api/coursemedia/0/"

    def test_get(self, client):
        print('Media api test, get')
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        #print(body)
        assert body["url"] == "test-url-1-1"
        _check_namespace(client, body)               
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        print('Media api test, put')
    
        valid = {"url":"valid-url"}
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        #print(resp)
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        #print(resp)
        assert resp.status_code == 404
        
        # test with valid 
        valid["url"] = "valid-url-1"
        valid["type"] = "valid-type-1"

        resp = client.put(self.RESOURCE_URL, json=valid)
        #print(resp)
        assert resp.status_code == 204



class TestCourseMediaCollection(object):
    RESOURCE_URL = "/api/trainingcourses/1/medias/"

    def test_get(self, client):
        print('Media collection api test(should return 3 items with id and url)')
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        #print(body)
        assert len(body) == 3
        for item in body:
            assert "type" in item
            assert "url" in item 

    def test_post(self, client):
        valid = {"url":"test-valid-url"}
        valid["type"] = "image"

        #test wrong content type:
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        print('User collection api test,post invalid media format')
        #print(resp)
        assert resp.status_code == 415

        #test with valid content:
        print('User collection api test, valid content')
        #print(valid)
        resp = client.post(self.RESOURCE_URL, json=valid)        
        assert resp.status_code == 201
        
        assert resp.headers["Location"].endswith("/")
        #print(resp.headers["Location"])
        resp = client.get(resp.headers["Location"])
        #print(resp)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["url"] == "test-valid-url"


