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
    yield db


@pytest.fixture(scope='module')
def setup_user(db):
    username = 'UserChangeAvatarName'
    password = 'Foobar1-'
    email = 'UserChangeAvatarName@hmail.pap'
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email)
    yield username, password
    db_delete_user(db, name=username)


@pytest.fixture(scope='module')
def get_header(setup_user):
    name, password = setup_user
    token = create_access_token(name)
    header = {'Authorization': f'Bearer {token}'}
    return header, password


@pytest.fixture(scope='module')
def get_invalid_header(db):
    token = create_access_token('NotCreated')
    header = {'Authorization': f'Bearer {token}'}
    return header


def test_invalid_password(get_header):
    headers, _ = get_header
    response = client.put("/user/password",
                          headers=headers,
                          json={"password": "chau"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == "Invalid password"


def test_same_as_old_password(get_header):
    headers, password = get_header
    response = client.put("/user/password",
                          headers=headers,
                          json={"password": password})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == "Password already in use"


def test_successful(get_header):
    headers, _ = get_header
    response = client.put("/user/password",
                          headers=headers,
                          json={"password": "Hola1234--"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}


def test_invalid_user(get_invalid_header):
    response = client.put('/user/password',
                          headers=get_invalid_header,
                          json={"password": "Hola1234--"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "User does not exist"
