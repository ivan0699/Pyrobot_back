# global imports
from fastapi.testclient import TestClient
import pytest

# local imports
from database_utils import *
from room import Room, all_rooms
from utils import *
from main import app


client = TestClient(app)


@pytest.fixture(scope='module')
def setup_create():
    all_rooms.clear()
    username = 'match_owner'
    robot_name = 'Default56'
    match_id, room_id = 0, 0
    robot_in_match = RobotToUserModel(name=robot_name,
                                      owner_name=username)

    new_match_state = MatchToUserModel(name="Pepe's match",
                                       games=200,
                                       rounds=10000,
                                       num_players_min=2,
                                       num_players_max=4,
                                       id=match_id,
                                       owner=username,
                                       robots=[],
                                       player_count=0)
    new_room = Room(new_match_state)
    new_room.add_player(robot_in_match)
    all_rooms.append(new_room)
    yield match_id, room_id


@pytest.fixture(scope='module')
def setup_other():
    username = 'match_owner2'
    robot_name = 'Default562'
    match_id, room_id = 1, 1
    robot_in_match = RobotToUserModel(name=robot_name,
                                      owner_name=username)

    new_match_state = MatchToUserModel(name="Jose's match",
                                       games=200,
                                       rounds=10000,
                                       num_players_min=2,
                                       num_players_max=4,
                                       id=match_id,
                                       owner=username,
                                       robots=[],
                                       player_count=0)
    new_room = Room(new_match_state)
    new_room.add_player(robot_in_match)
    all_rooms.append(new_room)
    yield match_id, room_id


@pytest.fixture(scope='module')
def setup_join(setup_create):
    match_id, room_id = setup_create
    username = 'player1'
    robot_name = 'Default65'
    robot_in_match = RobotToUserModel(name=robot_name,
                                      owner_name=username)

    all_rooms[room_id].add_player(robot_in_match)
    yield match_id, room_id


def test_ws_connect(setup_create):
    match_id, room_id = setup_create
    with client.websocket_connect(f'/ws/{room_id}') as websocket:
        data = websocket.receive_json()
        assert data['id'] == match_id
        assert data['player_count'] == 1
        assert len(data['robots']) == 1
        assert data['robots'][0]['name'] == 'Default56'
        assert data['robots'][0]['owner_name'] == 'match_owner'


def test_ws_join(setup_join):
    match_id, room_id = setup_join
    with client.websocket_connect(f'/ws/{room_id}') as websocket:
        data = websocket.receive_json()
        assert data['id'] == match_id
        assert data['player_count'] == 2
        assert len(data['robots']) == 2
        assert data['robots'][0]['name'] == 'Default56'
        assert data['robots'][0]['owner_name'] == 'match_owner'
        assert data['robots'][1]['name'] == 'Default65'
        assert data['robots'][1]['owner_name'] == 'player1'


def test_ws_leave(setup_join):
    match_id, room_id = setup_join
    with client.websocket_connect(f'/ws/{room_id}') as ws1:
        ws1.receive_json()
        with client.websocket_connect(f'/ws/{room_id}') as ws2:
            ws2.receive_json()
            with client.websocket_connect(f'/ws/{room_id}') as ws3:
                ws3.receive_json()

            data1 = ws1.receive_json()
            data2 = ws2.receive_json()
            assert data1 == data2
            assert data1['id'] == match_id
            assert data1['player_count'] == 2
            assert len(data1['robots']) == 2
            assert data1['robots'][0]['name'] == 'Default56'
            assert data1['robots'][0]['owner_name'] == 'match_owner'
            assert data1['robots'][1]['name'] == 'Default65'
            assert data1['robots'][1]['owner_name'] == 'player1'


@pytest.mark.asyncio
async def test_ws_start(setup_join):
    _, room_id = setup_join
    room = all_rooms[room_id]
    winner = {'name': 'Default1', 'owner_name': 'jorge'}

    with client.websocket_connect(f'/ws/{room_id}') as ws:
        ws.receive_json()
        await room.win_notify(winner)
        data = ws.receive_json()
        assert data == {'winner': winner}


def test_ws_few_rooms(setup_create, setup_other):
    _, room_id1 = setup_create
    _, room_id2 = setup_other
    room1 = all_rooms[room_id1]
    room2 = all_rooms[room_id2]

    with client.websocket_connect(f'/ws/{room_id1}') as ws1:
        with client.websocket_connect(f'/ws/{room_id2}') as ws2:
            data1 = ws1.receive_json()
            data2 = ws2.receive_json()

            assert data1['name'] == "Pepe's match"
            assert len(room1.players) == 1
            assert data2['name'] == "Jose's match"
            assert len(room2.players) == 1
