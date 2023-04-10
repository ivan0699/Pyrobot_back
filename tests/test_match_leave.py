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
    user_name = 'MatchLeaveName'
    password = 'Foobar1-'
    email = 'MatchLeaveName@hmail.con'
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
def setup_match_started(db):
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
                  'games': 200,
                  'rounds': 10000,
                  'num_players_min': 2,
                  'num_players_max': 4}
    match_id = db_create_match(db,
                               **match_data,
                               owner_name=owner_name,
                               owner_robot=robot,
                               is_started=True)
    yield match_id
    db_delete_match(db, match_id=match_id)


@pytest.fixture(scope='module')
def setup_user_match(db, setup_user, setup_robot):
    match_data = {'name': 'Match2',
                  'games': 200,
                  'rounds': 10000,
                  'num_players_min': 2,
                  'num_players_max': 4}
    match_id = db_create_match(db,
                               **match_data,
                               owner_name=setup_user,
                               owner_robot=setup_robot)
    yield match_id
    db_delete_match(db, match_id=match_id)


@pytest.fixture(scope='module')
def setup_match(db):
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
    match_data = {'name': 'Match3',
                  'games': 200,
                  'rounds': 10000,
                  'num_players_min': 2,
                  'num_players_max': 2}
    match_id = db_create_match(db,
                               **match_data,
                               owner_name=owner_name,
                               owner_robot=robot)
    yield match_data, match_id
    db_delete_match(db, match_id=match_id)


@pytest.fixture(scope='module')
def setup_match_with_user(db, setup_user, setup_robot, setup_match):
    match_data, match_id = setup_match
    db_update_match_add_player(db,
                               match_id=match_id,
                               robot_name=setup_robot,
                               user_name=setup_user)

    new_match_state = MatchToUserModel(**match_data,
                                       id=match_id,
                                       owner='',
                                       robots=[],
                                       player_count=0)
    new_room = Room(new_match_state)
    robot_from_user = RobotToUserModel(name=setup_robot,
                                       owner_name=setup_user)
    new_room.add_player(robot_from_user)
    all_rooms.append(new_room)
    room_id = len(all_rooms) - 1
    match_room.update({match_id: room_id})
    yield match_id


def test_match_doesnt_exist(get_header):
    response = client.post("/match/leave",
                           headers=get_header,
                           json={'id': 671})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Match does not exists'


def test_is_started(get_header, setup_match_started):
    match_id = setup_match_started
    response = client.post("/match/leave",
                           headers=get_header,
                           json={'id': match_id})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Match is started'


def test_is_owner(get_header, setup_user_match):
    match_id = setup_user_match
    response = client.post("/match/leave",
                           headers=get_header,
                           json={'id': match_id})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'The owner of the match cannot leave'


def test_user_not_in_match(get_header, setup_match):
    _, match_id = setup_match
    response = client.post("/match/leave",
                           headers=get_header,
                           json={'id': match_id})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'User is not in match'


def test_successful(get_header, setup_match_with_user):
    match_id = setup_match_with_user
    response = client.post("/match/leave",
                           headers=get_header,
                           json={'id': match_id})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}
