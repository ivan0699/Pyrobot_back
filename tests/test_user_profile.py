# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import create_access_token, get_password_hash
from database import setup_db, get_db
from database_utils import *
from utils import get_avatar_url
from main import app

client = TestClient(app)


@pytest.fixture(scope='module')
def setup():
    setup_db()
    db = get_db()
    username = 'UserProfileName'
    password = 'Foobar1-'
    email = 'UserProfileName@hmail.pap'
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email,
                   avatar=get_avatar_url(username, 'avatar.png'))

    robot1 = 'Robot1'
    db_create_robot(db,
                    owner_name=username,
                    robot_name=robot1,
                    avatar=get_avatar_url(username, f'{robot1}.jpeg'))
    db_create_stats(db,
                    owner_name=username,
                    robot_name=robot1,
                    played=16,
                    won=5)

    robot2 = 'Robot2'
    db_create_robot(db,
                    owner_name=username,
                    robot_name=robot2)
    db_create_stats(db,
                    owner_name=username,
                    robot_name=robot2,
                    played=9,
                    won=1)

    token = create_access_token(username)
    headers = {'Authorization': f'Bearer {token}'}
    yield headers
    db_delete_user(db, name=username)


def test_invalid_user(setup):
    name = "NotCreated"
    token = create_access_token(name)
    header = {'Authorization': f'Bearer {token}'}
    response = client.get("/user/profile", headers=header)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == "User does not exist"


def test_successful(setup):
    headers = setup
    response = client.get("/user/profile", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['avatar'] == '/images/UserProfileName/avatar.png'
    assert response.json()['name'] == 'UserProfileName'
    robots = sorted(response.json()['robots'], key=lambda r: r['name'])
    assert robots[0] == {'avatar': '/images/UserProfileName/Robot1.jpeg',
                         'name': 'Robot1',
                         'owner_avatar': '/images/UserProfileName/avatar.png',
                         'owner_name': 'UserProfileName',
                         'stats': {'matches_played': 16,
                                   'matches_won': 5}}
    assert robots[1] == {'avatar': None,
                         'name': 'Robot2',
                         'owner_avatar': '/images/UserProfileName/avatar.png',
                         'owner_name': 'UserProfileName',
                         'stats': {'matches_played': 9,
                                   'matches_won': 1}}
