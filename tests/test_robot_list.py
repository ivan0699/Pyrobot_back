# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import create_access_token, get_password_hash
from constants import *
from database import setup_db, get_db
from database_utils import *
from utils import get_avatar_url
from main import app

client = TestClient(app)


@pytest.fixture(scope='module')
def db():
    setup_db()
    db = get_db()
    yield db


@pytest.fixture(scope='module')
def setup_user1(db):
    username = 'RobotListName1'
    password = 'Foobar1-'
    email = 'RobotListName1@hmail.con'
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email)
    yield username
    db_delete_user(db, name=username)


@pytest.fixture(scope='module')
def get_header1(setup_user1):
    token = create_access_token(setup_user1)
    header = {'Authorization': f'Bearer {token}'}
    return header


@pytest.fixture(scope='module')
def setup_user2(db):
    username = 'RobotListName2'
    password = 'Foobar1-'
    email = 'RobotListName2@hmail.con'
    avatar = get_avatar_url(username, 'avatar.jpeg')
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email,
                   avatar=avatar)
    yield username, avatar
    db_delete_user(db, name=username)


@pytest.fixture(scope='module')
def get_header2(setup_user2):
    username, _ = setup_user2
    token = create_access_token(username)
    header = {'Authorization': f'Bearer {token}'}
    return header


@pytest.fixture(scope='module')
def setup_robots(db, setup_user2):
    username, avatar = setup_user2
    robot1 = {'name': 'SuperMegaRobot',
              'avatar': None,
              'owner_name': username,
              'owner_avatar': avatar,
              'stats': {'matches_played': 0,
                        'matches_won': 0}}
    robot2 = {'name': 'UltraMegaRobot',
              'avatar': get_avatar_url(setup_user2, 'UltraMegaRobot.png'),
              'owner_name': username,
              'owner_avatar': avatar,
              'stats': {'matches_played': 165,
                        'matches_won': 165}}
    db_create_robot(db,
                    owner_name=username,
                    robot_name=robot1['name'],
                    avatar=robot1['avatar'])
    db_create_stats(db,
                    owner_name=username,
                    robot_name=robot1['name'],
                    played=robot1['stats']['matches_played'],
                    won=robot1['stats']['matches_won'])
    db_create_robot(db,
                    owner_name=username,
                    robot_name=robot2['name'],
                    avatar=robot2['avatar'])
    db_create_stats(db,
                    owner_name=username,
                    robot_name=robot2['name'],
                    played=robot2['stats']['matches_played'],
                    won=robot2['stats']['matches_won'])
    yield robot1, robot2
    db_delete_robot(db, owner_name=username, robot_name=robot1['name'])
    db_delete_robot(db, owner_name=username, robot_name=robot2['name'])


def test_robot_list_without_token():
    response = client.get('/robot/list')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Not authenticated'


def test_robot_list_empty(get_header1):
    response = client.get('/robot/list', headers=get_header1)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_robot_list_some(get_header2, setup_robots):
    robot1, robot2 = setup_robots
    response = client.get('/robot/list', headers=get_header2)

    assert response.status_code == status.HTTP_200_OK
    robots = sorted(response.json(), key=lambda r: r['name'])
    assert robots[0] == robot1
    assert robots[1] == robot2
