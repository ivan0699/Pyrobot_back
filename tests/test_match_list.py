# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import get_password_hash, create_access_token
from database import setup_db, get_db
from database_utils import *
from main import app
from utils import *

client = TestClient(app)


@pytest.fixture(scope='module')
def db():
    setup_db()
    db = get_db()
    yield db


@pytest.fixture(scope='module')
def setup_user1(db):
    user_name = 'MatchListName1'
    robot_name = 'Robot1'
    password = 'Foobar1-'
    email = 'MatchListName1@hmail.con'
    user_avatar = get_avatar_url(user_name, 'avatar.png')
    robot_avatar = None
    db_create_user(db,
                   name=user_name,
                   password=get_password_hash(password),
                   email=email,
                   avatar=user_avatar)
    db_create_robot(db,
                    owner_name=user_name,
                    robot_name=robot_name,
                    avatar=robot_avatar)
    db_create_stats(db,
                    owner_name=user_name,
                    robot_name=robot_name,
                    played=10,
                    won=5)
    yield user_name, user_avatar, robot_name, robot_avatar
    db_delete_user(db, name=user_name)


@pytest.fixture(scope='module')
def setup_user2(db):
    user_name = 'MatchListName2'
    robot_name = 'Robot2'
    password = 'Foobar1-'
    email = 'MatchListName2@hmail.con'
    user_avatar = None
    robot_avatar = get_avatar_url(user_name, f'{robot_name}.jpg')
    db_create_user(db,
                   name=user_name,
                   password=get_password_hash(password),
                   email=email,
                   avatar=user_avatar)
    db_create_robot(db,
                    owner_name=user_name,
                    robot_name=robot_name,
                    avatar=robot_avatar)
    db_create_stats(db,
                    owner_name=user_name,
                    robot_name=robot_name)
    yield user_name, user_avatar, robot_name, robot_avatar
    db_delete_user(db, name=user_name)


@pytest.fixture(scope='module')
def get_header(setup_user1):
    name, *_ = setup_user1
    token = create_access_token(name)
    header = {'Authorization': f'Bearer {token}'}
    return header


@pytest.fixture(scope='module')
def setup_matches(db, setup_user1, setup_user2):
    user1, user_avatar1, robot1, robot_avatar1 = setup_user1
    user2, user_avatar2, robot2, robot_avatar2 = setup_user2
    match1 = {'name': 'Match1',
              'games': 200,
              'rounds': 10000,
              'num_players_min': 2,
              'num_players_max': 4}
    match2 = {'name': 'Match2',
              'games': 167,
              'rounds': 1500,
              'num_players_min': 4,
              'num_players_max': 4}

    id1 = db_create_match(db,
                          **match1,
                          owner_name=user1,
                          owner_robot=robot1,
                          password='somepass-')
    match1.update({'id': id1})
    match1.update({'owner': user1})
    match1.update({'player_count': 1})
    match1.update({'robots': [{'name': robot1,
                               'avatar': robot_avatar1,
                               'owner_name': user1,
                               'owner_avatar': user_avatar1,
                               'stats': {'matches_played': 10,
                                         'matches_won': 5}}]})

    id2 = db_create_match(db,
                          **match2,
                          owner_name=user2,
                          owner_robot=robot2)
    match2.update({'id': id2})
    match2.update({'owner': user2})
    match2.update({'player_count': 1})
    match2.update({'robots': [{'name': robot2,
                               'avatar': robot_avatar2,
                               'owner_name': user2,
                               'owner_avatar': user_avatar2,
                               'stats': {'matches_played': 0,
                                         'matches_won': 0}}]})
    yield match1, match2
    db_delete_match(db, match_id=id1)
    db_delete_match(db, match_id=id2)


def test_not_authenticated():
    response = client.get('/match/list')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_empty(get_header):
    response = client.get('/match/list', headers=get_header)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_some(get_header, setup_matches):
    match1, match2 = setup_matches
    response = client.get('/match/list', headers=get_header)

    assert response.status_code == status.HTTP_200_OK
    matches = sorted(response.json(), key=lambda m: m['id'])
    assert matches[0] == match1
    assert matches[1] == match2
