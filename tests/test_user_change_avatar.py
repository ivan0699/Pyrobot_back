# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import create_access_token, get_password_hash
from constants import IMAGES_DIR
from database import setup_db, get_db
from database_utils import db_create_user, db_delete_user
from main import app
from utils import remove_dir

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
    yield username
    db_delete_user(db, name=username)
    remove_dir(f'{IMAGES_DIR}/{username}')


@pytest.fixture(scope='module')
def get_header(setup_user):
    name = setup_user
    token = create_access_token(name)
    header = {'Authorization': f'Bearer {token}'}
    return header


@pytest.fixture(scope='module')
def get_invalid_header(db):
    token = create_access_token('NotCreated')
    header = {'Authorization': f'Bearer {token}'}
    return header


def test_invalid_user(get_invalid_header):
    response = client.put('/user/avatar',
                          headers=get_invalid_header,
                          json={'avatar': {'ext': 'gif',
                                           'content': '1234'}})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "User does not exist"


def test_invalid_content(get_header):
    response = client.put('/user/avatar',
                          headers=get_header,
                          json={'avatar': {'ext': 'gif',
                                           'content': '1'}})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid avatar content"


def test_successful(get_header):
    response = client.put('/user/avatar',
                          headers=get_header,
                          json={'avatar': {'ext': 'png',
                                           'content': 'asdf'}})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}


def test_update_successful(get_header):
    response = client.put('/user/avatar',
                          headers=get_header,
                          json={'avatar': {'ext': 'jpeg',
                                           'content': 'asdf'}})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}
