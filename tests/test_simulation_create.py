# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import create_access_token, get_password_hash
from constants import *
from database import setup_db, get_db
from database_utils import *
from utils import *
from main import app

client = TestClient(app)


@pytest.fixture(scope='module')
def setup():
    setup_db()
    db = get_db()
    username = 'SimulationCreateName'
    password = 'Foobar1-'
    email = 'SimulationCreateName@hmail.con'
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email)

    robots_dir = f'{ROBOTS_DIR}/{username}'
    for robot_name, code in DEFAULT_ROBOTS.items():
        file_name = f'{camel_to_snake(robot_name)}.py'
        save_robot(robots_dir, file_name, code)
        db_create_robot(db,
                        owner_name=username,
                        robot_name=robot_name)
    yield username
    remove_dir(robots_dir)
    db_delete_user(db, username)


@pytest.fixture(scope='module')
def get_header(setup):
    token = create_access_token(setup)
    header = {'Authorization': f'Bearer {token}'}
    return header


def test_bad_token():
    response = client.post("/simulation/create",
                           headers={'Authorization': 'Bearer tokencito'})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_many_robots(get_header):
    response = client.post("/simulation/create",
                           headers=get_header,
                           json={"rounds": GAME_ROUNDS,
                                 "robots_names": ["Default1",
                                                  "Default2",
                                                  "Default1",
                                                  "Default1",
                                                  "Default1"]})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()['detail'] == 'Too many robots'


def test_no_robots(get_header):
    response = client.post("/simulation/create",
                           headers=get_header,
                           json={"rounds": GAME_ROUNDS,
                                 "robots_names": []})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()['detail'] == 'No robots to simulate'


def test_one_robot(get_header):
    response = client.post("/simulation/create",
                           headers=get_header,
                           json={"rounds": GAME_ROUNDS,
                                 "robots_names": ["Default1"]})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()['detail'] == 'Add at least one more robot'


def test_0_rounds(get_header):
    response = client.post("/simulation/create",
                           headers=get_header,
                           json={"rounds": 0,
                                 "robots_names": ["Default1",
                                                  "Default2"]})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()['detail'] == 'Rounds must be between 1 and 10000'


def test_10001_rounds(get_header):
    response = client.post("/simulation/create",
                           headers=get_header,
                           json={"rounds": 10001,
                                 "robots_names": ["Default1",
                                                  "Default2"]})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()['detail'] == 'Rounds must be between 1 and 10000'


def test_successful(get_header):
    response = client.post("/simulation/create",
                           headers=get_header,
                           json={"rounds": GAME_ROUNDS,
                                 "robots_names": ["Default1",
                                                  "Default2",
                                                  "Default1",
                                                  "Default2"]})

    assert response.status_code == status.HTTP_200_OK
