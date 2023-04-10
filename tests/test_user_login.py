# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import create_access_token, get_password_hash
from database import setup_db, get_db
from database_utils import db_create_user, db_delete_user
from main import app

client = TestClient(app)


@pytest.fixture(scope='module')
def db():
    setup_db()
    db = get_db()
    return db


@pytest.fixture(scope='module')
def setup_not_validated(db):
    username = 'UserLoginNotValidated'
    password = 'Foobar1-'
    email = 'UserLoginNotValidated@hmail.con'
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email)
    yield username, password
    db_delete_user(db, name=username)


@pytest.fixture(scope='module')
def setup_validated(db):
    username = 'UserLoginName'
    password = 'Foobar1-'
    email = 'UserLoginName@hmail.pap'
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email,
                   is_validated=True)
    yield username, password
    db_delete_user(db, username)


def test_not_validated(setup_not_validated):
    name, password = setup_not_validated
    response = client.post("/user/login", {"username": name,
                                           "password": password})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()['detail'] == 'User not validated'


def test_unauthorized():
    response = client.post("/user/login", {"username": "joaquin",
                                           "password": "origlia"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Incorrect username or password'


def test_with_wrong_fields():
    response = client.post("/user/login", {"wrong": "test"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()['detail'][0]['loc'][1] == 'username'
    assert response.json()['detail'][0]['msg'] == 'field required'
    assert response.json()['detail'][1]['loc'][1] == 'password'
    assert response.json()['detail'][1]['msg'] == 'field required'


def test_without_name(setup_validated):
    name, password = setup_validated
    response = client.post("/user/login", {"wrong": name,
                                           "password": password})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()['detail'][0]['loc'][1] == 'username'
    assert response.json()['detail'][0]['msg'] == 'field required'


def test_without_password(setup_validated):
    name, password = setup_validated
    response = client.post("/user/login", {"username": name,
                                           "wrong": password})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()['detail'][0]['loc'][1] == 'password'
    assert response.json()['detail'][0]['msg'] == 'field required'


def test_with_wrong_password(setup_validated):
    name, _ = setup_validated
    response = client.post("/user/login", {"username": name,
                                           "password": "secrets--"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Incorrect username or password'


def test_successful(setup_validated):
    name, password = setup_validated
    response = client.post("/user/login", {"username": name,
                                           "password": password})

    assert response.status_code == status.HTTP_200_OK
    token = create_access_token(name)
    assert response.json()['access_token'] == token
    assert response.json()['token_type'] == 'bearer'
