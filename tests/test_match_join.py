# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import get_password_hash, create_access_token
from database import setup_db, get_db
from database_utils import *
from main import app
from room import Room, all_rooms, match_room
from utils import *

client = TestClient(app)


@pytest.fixture(scope='module')
def db():
    setup_db()
    db = get_db()
    yield db


@pytest.fixture(scope='module')
def setup_user(db):
    user_name = 'MatchJoinName'
    password = 'Foobar1-'
    email = 'MatchJoinName@hmail.con'
    db_create_user(db,
                   name=user_name,
                   password=get_password_hash(password),
                   email=email)
    yield user_name
    db_delete_user(db, name=user_name)


@pytest.fixture(scope='module')
def setup_robot(db, setup_user):
    user_name = setup_user
    robot_name = 'Robot1'
    db_create_robot(db,
                    owner_name=user_name,
                    robot_name=robot_name)
    db_create_stats(db,
                    owner_name=user_name,
                    robot_name=robot_name)
    yield robot_name
    db_delete_robot(db,
                    owner_name=user_name,
                    robot_name=robot_name)


@pytest.fixture(scope='module')
def get_header(setup_user):
    name = setup_user
    token = create_access_token(name)
    header = {'Authorization': f'Bearer {token}'}
    return header


@pytest.fixture(scope='module')
def setup_match(db):
    owner_name = 'MatchOwner1'
    owner_password = 'Foobar1-'
    owner_email = 'MatchOwner1@hmail.con'
    robot = 'OwnerRobot1'
    db_create_user(db,
                   name=owner_name,
                   password=get_password_hash(owner_password),
                   email=owner_email)
    db_create_robot(db,
                    owner_name=owner_name,
                    robot_name=robot)
    db_create_stats(db,
                    owner_name=owner_name,
                    robot_name=robot)
    match_data = {'name': 'Match1',
                  'games': 10,
                  'rounds': 100,
                  'num_players_min': 2,
                  'num_players_max': 4}
    match_id = db_create_match(db,
                               **match_data,
                               owner_name=owner_name,
                               owner_robot=robot)

    new_match_state = MatchToUserModel(**match_data,
                                       id=match_id,
                                       owner=owner_name,
                                       robots=[],
                                       player_count=0)
    new_room = Room(new_match_state)
    all_rooms.append(new_room)
    room_id = len(all_rooms) - 1
    match_room.update({match_id: room_id})
    yield match_id, room_id
    db_delete_user(db, name=owner_name)


@pytest.fixture(scope='module')
def setup_match_started(db):
    owner_name = 'MatchOwner2'
    owner_password = 'Foobar1-'
    owner_email = 'MatchOwner2@hmail.con'
    robot = 'OwnerRobot2'
    db_create_user(db,
                   name=owner_name,
                   password=get_password_hash(owner_password),
                   email=owner_email)
    db_create_robot(db,
                    owner_name=owner_name,
                    robot_name=robot)
    db_create_stats(db,
                    owner_name=owner_name,
                    robot_name=robot)
    match_id = db_create_match(db,
                               name='Match2',
                               games=100,
                               rounds=1000,
                               num_players_min=4,
                               num_players_max=4,
                               owner_name=owner_name,
                               owner_robot=robot,
                               is_started=True)
    yield match_id
    db_delete_user(db, name=owner_name)


@pytest.fixture(scope='module')
def setup_match_full(db):
    owner_name = 'MatchOwner3'
    owner_password = 'Foobar1-'
    owner_email = 'MatchOwner3@hmail.con'
    robot = 'OwnerRobot3'
    db_create_user(db,
                   name=owner_name,
                   password=get_password_hash(owner_password),
                   email=owner_email)
    db_create_robot(db,
                    owner_name=owner_name,
                    robot_name=robot)
    db_create_stats(db,
                    owner_name=owner_name,
                    robot_name=robot)
    match_id = db_create_match(db,
                               name='Match3',
                               games=200,
                               rounds=10000,
                               num_players_min=3,
                               num_players_max=3,
                               owner_name=owner_name,
                               owner_robot=robot,
                               is_full=True)
    yield match_id
    db_delete_user(db, name=owner_name)


@pytest.fixture(scope='module')
def setup_user_in_match(db, setup_user, setup_robot):
    owner_name = 'MatchOwner4'
    owner_password = 'Foobar1-'
    owner_email = 'MatchOwner4@hmail.con'
    robot = 'OwnerRobot4'
    db_create_user(db,
                   name=owner_name,
                   password=get_password_hash(owner_password),
                   email=owner_email)
    db_create_robot(db,
                    owner_name=owner_name,
                    robot_name=robot)
    db_create_stats(db,
                    owner_name=owner_name,
                    robot_name=robot)
    match_id = db_create_match(db,
                               name='Match4',
                               games=200,
                               rounds=10000,
                               num_players_min=2,
                               num_players_max=4,
                               owner_name=owner_name,
                               owner_robot=robot)
    db_update_match_add_player(db, match_id, setup_robot, setup_user)
    yield match_id
    db_delete_user(db, name=owner_name)


@pytest.fixture(scope='module')
def setup_match_with_pw(db):
    owner_name = 'MatchOwner5'
    owner_password = 'Foobar1-'
    owner_email = 'MatchOwner5@hmail.con'
    robot = 'OwnerRobot5'
    db_create_user(db,
                   name=owner_name,
                   password=get_password_hash(owner_password),
                   email=owner_email)
    db_create_robot(db,
                    owner_name=owner_name,
                    robot_name=robot)
    db_create_stats(db,
                    owner_name=owner_name,
                    robot_name=robot)
    match_data = {'name': 'Match5',
                  'games': 200,
                  'rounds': 10000,
                  'num_players_min': 2,
                  'num_players_max': 4}
    match_id = db_create_match(db,
                               **match_data,
                               owner_name=owner_name,
                               owner_robot=robot,
                               password=get_password_hash(owner_password))

    new_match_state = MatchToUserModel(**match_data,
                                       id=match_id,
                                       owner=owner_name,
                                       robots=[],
                                       player_count=0)
    new_room = Room(new_match_state)
    all_rooms.append(new_room)
    room_id = len(all_rooms) - 1
    match_room.update({match_id: room_id})
    yield match_id, owner_password, room_id
    db_delete_user(db, name=owner_name)


def test_robot_doesnt_exist(get_header, setup_match):
    match_id, _ = setup_match
    response = client.post("/match/join",
                           headers=get_header,
                           json={'id': match_id,
                                 'robot': 'Joaquin'})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Robot does not exists'


def test_match_doesnt_exist(get_header, setup_robot):
    robot_name = setup_robot
    response = client.post("/match/join",
                           headers=get_header,
                           json={'id': '1000',
                                 'robot': robot_name})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Match does not exists'


def test_is_started(get_header, setup_robot, setup_match_started):
    match_id = setup_match_started
    robot_name = setup_robot
    response = client.post("/match/join",
                           headers=get_header,
                           json={'id': match_id,
                                 'robot': robot_name})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Match is started'


def test_is_full(get_header, setup_robot, setup_match_full):
    match_id = setup_match_full
    robot_name = setup_robot
    response = client.post("/match/join",
                           headers=get_header,
                           json={'id': match_id,
                                 'robot': robot_name})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Match is full'


def test_user_already_in(get_header, setup_robot, setup_user_in_match):
    match_id = setup_user_in_match
    robot_name = setup_robot
    response = client.post("/match/join",
                           headers=get_header,
                           json={'id': match_id,
                                 'robot': robot_name})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'User is already in match'


def test_with_invalid_password(get_header, setup_robot, setup_match_with_pw):
    match_id, *_ = setup_match_with_pw
    response = client.post("/match/join",
                           headers=get_header,
                           json={'id': match_id,
                                 'robot': setup_robot,
                                 'password': ''})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Invalid password for match'


def test_successful_without_pw(get_header, setup_robot, setup_match):
    match_id, room_id = setup_match
    robot_name = setup_robot
    response = client.post("/match/join",
                           headers=get_header,
                           json={'id': match_id,
                                 'robot': robot_name})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'match_id': match_id, 'room_id': room_id}


def test_successful_with_pw(get_header, setup_robot, setup_match_with_pw):
    match_id, password, room_id = setup_match_with_pw
    response = client.post("/match/join",
                           headers=get_header,
                           json={'id': match_id,
                                 'robot': setup_robot,
                                 'password': password})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'match_id': match_id, 'room_id': room_id}
