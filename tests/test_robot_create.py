# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import create_access_token, get_password_hash
from constants import *
from database import setup_db, get_db
from database_utils import *
from utils import remove_dir
from main import app

client = TestClient(app)


@pytest.fixture(scope='module')
def setup_user():
    setup_db()
    db = get_db()
    username = 'RobotCreateName'
    password = 'Foobar1-'
    email = 'RobotCreateName@hmail.con'
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email)
    yield username
    db_delete_user(db, name=username)
    remove_dir(f'{IMAGES_DIR}/{username}')
    remove_dir(f'{ROBOTS_DIR}/{username}')


@pytest.fixture(scope='module')
def get_header(setup_user):
    token = create_access_token(setup_user)
    header = {'Authorization': f'Bearer {token}'}
    return header


@pytest.fixture(scope='module')
def setup_robot():
    name = 'Robot1'
    code = 'code'
    avatar = {'ext': 'png', 'content': '1234'}
    yield name, code, avatar


def test_without_token(setup_robot):
    name, code, _ = setup_robot
    response = client.post('/robot/create',
                           json={'name': name,
                                 'code': code})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_with_invalid_avatar(get_header, setup_robot):
    name, code, _ = setup_robot
    response = client.post('/robot/create',
                           headers=get_header,
                           json={'name': name,
                                 'code': code,
                                 'avatar': {'ext': 'html',
                                            'content': 'x'}})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid avatar content"


def test_successful_without_avatar(get_header, setup_robot):
    name, code, _ = setup_robot
    response = client.post('/robot/create',
                           headers=get_header,
                           json={'name': name,
                                 'code': code})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {}


def test_successful_with_avatar(get_header, setup_robot):
    name, code, avatar = setup_robot
    response = client.post('/robot/create',
                           headers=get_header,
                           json={'name': name,
                                 'code': code,
                                 'avatar': avatar})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {}


def test_successful_update_avatar(get_header, setup_robot):
    name, code, _ = setup_robot
    response = client.post('/robot/create',
                           headers=get_header,
                           json={'name': name,
                                 'code': code,
                                 'avatar': {'ext': 'foo',
                                            'content': 'barr'}})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {}
