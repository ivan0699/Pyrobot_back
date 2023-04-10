# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import get_password_hash
from database import setup_db, get_db
from database_utils import db_create_user, db_delete_user
from main import app
from utils import create_validation_code

client = TestClient(app)


@pytest.fixture(scope='module')
def setup():
    setup_db()
    db = get_db()
    username = 'UserValidationName'
    password = 'Foobar1-'
    email = 'UserValidationName@hmail.pap'
    validation_code = create_validation_code(username)
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email,
                   validation_code=validation_code)
    yield username, validation_code
    db_delete_user(db, name=username)


def test_not_valid_user(setup):
    _, code = setup
    response = client.post("/user/validation",
                           json={"name": "some_unregistered_username",
                                 "code": code})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Invalid username'


def test_not_valid_code(setup):
    name, _ = setup
    response = client.post("/user/validation",
                           json={"name": name,
                                 "code": "changeme"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Invalid validation code'


def test_successful(setup):
    name, code = setup
    response = client.post("/user/validation",
                           json={"name": name,
                                 "code": code})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}
