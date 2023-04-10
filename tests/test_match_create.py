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
def setup_user(db):
    username = 'MatchCreateName'
    password = 'Foobar1-'
    email = 'MatchCreateName@hmail.con'
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email,
                   avatar=get_avatar_url(username, 'avatar.png'))
    yield username
    db_delete_user(db, name=username)


@pytest.fixture(scope='module')
def get_header(setup_user):
    token = create_access_token(setup_user)
    header = {'Authorization': f'Bearer {token}'}
    return header


@pytest.fixture(scope='module')
def get_invalid_header(db):
    token = create_access_token('NotCreated')
    header = {'Authorization': f'Bearer {token}'}
    return header


@pytest.fixture(scope='module')
def setup_robot(db, setup_user):
    robot1 = 'Robot1'
    db_create_robot(db,
                    owner_name=setup_user,
                    robot_name=robot1,
                    avatar=get_avatar_url(setup_user, f'{robot1}.jpeg'))
    db_create_stats(db,
                    owner_name=setup_user,
                    robot_name=robot1)
    yield robot1
    db_delete_robot(db,
                    owner_name=setup_user,
                    robot_name=robot1)


@pytest.fixture(scope='module')
def setup_match():
    name = 'MatchName'
    games = 200
    rounds = 10000
    min_players = 2
    max_players = 4
    password = 'Foobar1-'
    yield name, games, rounds, min_players, max_players, password


def test_with_invalid_user(get_invalid_header, setup_match):
    name, games, rounds, min_players, max_players, _ = setup_match
    response = client.post('/match/create',
                           headers=get_invalid_header,
                           json={'name': name,
                                 'games': games,
                                 'rounds': rounds,
                                 'num_players_min': min_players,
                                 'num_players_max': max_players,
                                 'owner_robot': 'Default1'})

    # assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'User does not exists'


def test_without_name(get_header, setup_match):
    _, games, rounds, min_players, max_players, _ = setup_match
    response = client.post('/match/create',
                           headers=get_header,
                           json={'games': games,
                                 'rounds': rounds,
                                 'num_players_min': min_players,
                                 'num_players_max': max_players})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["loc"][1] == "name"
    assert response.json()["detail"][0]["msg"] == "field required"


def test_with_invalid_num_players(get_header, setup_match):
    name, games, rounds, _, _, _ = setup_match
    response = client.post('/match/create',
                           headers=get_header,
                           json={'name': name,
                                 'games': games,
                                 'rounds': rounds,
                                 'num_players_min': 0,
                                 'num_players_max': 4000})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    msg = response.json()["detail"]
    assert msg[0]["loc"][1] == "num_players_min"
    assert msg[0]["msg"] == "ensure this value is greater than or equal to 2"
    assert msg[1]["loc"][1] == "num_players_max"
    assert msg[1]["msg"] == "ensure this value is less than or equal to 4"


def test_with_min_players_gt_max_players(get_header, setup_match):
    name, games, rounds, min_players, max_players, _ = setup_match
    response = client.post('/match/create',
                           headers=get_header,
                           json={'name': name,
                                 'games': games,
                                 'rounds': rounds,
                                 'num_players_min': max_players,
                                 'num_players_max': min_players})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()[
        "detail"][0]["msg"] == "Min players greater than max players"


def test_with_invalid_password(get_header, setup_robot, setup_match):
    name, games, rounds, min_players, max_players, _ = setup_match
    response = client.post('/match/create',
                           headers=get_header,
                           json={'name': name,
                                 'games': games,
                                 'rounds': rounds,
                                 'num_players_min': min_players,
                                 'num_players_max': max_players,
                                 'password': 'hola',
                                 'owner_robot': setup_robot})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()['detail'][0]['msg'] == 'Invalid password'


def test_with_invalid_robot(get_header, setup_match):
    name, games, rounds, min_players, max_players, _ = setup_match
    response = client.post('/match/create',
                           headers=get_header,
                           json={'name': name,
                                 'games': games,
                                 'rounds': rounds,
                                 'num_players_min': min_players,
                                 'num_players_max': max_players,
                                 'owner_robot': 'SuperCrazyRobot'})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Owner robot does not exists'


def test_successful_without_password(get_header, setup_robot, setup_match):
    name, games, rounds, min_players, max_players, _ = setup_match
    response = client.post('/match/create',
                           headers=get_header,
                           json={'name': name,
                                 'games': games,
                                 'rounds': rounds,
                                 'num_players_min': min_players,
                                 'num_players_max': max_players,
                                 'owner_robot': setup_robot})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {'room_id': 0, 'match_id': 1}


def test_successful_with_password(get_header, setup_robot, setup_match):
    name, games, rounds, min_players, max_players, password = setup_match
    response = client.post('/match/create',
                           headers=get_header,
                           json={'name': name,
                                 'games': games,
                                 'rounds': rounds,
                                 'num_players_min': min_players,
                                 'num_players_max': max_players,
                                 'password': password,
                                 'owner_robot': setup_robot})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {'room_id': 1, 'match_id': 2}
