# global imports
from collections import defaultdict
from fastapi import APIRouter, Depends, status
from typing import List

# local imports
from authentication import *
from constants import *
from database import get_db
from database_utils import *
from game import Game
from room import Room, match_room, all_rooms
from models import *
from utils import *

router = APIRouter(prefix='/match')


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def match_create(match: MatchCreateModel,
                       current_user: str = Depends(get_current_user_name),
                       db: Database = Depends(get_db)):
    # check if user exists
    user = db_read_user_by_name(db, name=current_user)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User does not exists'
        )

    # check if owner robot exists
    robot = db_read_robot(db,
                          owner_name=current_user,
                          robot_name=match.owner_robot)
    if robot is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Owner robot does not exists'
        )

    # create database entry
    if match.password is not None:
        match.password = get_password_hash(match.password)
    match_id = db_create_match(db,
                               **match.dict(),
                               owner_name=current_user)

    # create room and match inside
    new_match_state = MatchToUserModel(**match.dict(),
                                       id=match_id,
                                       owner=current_user,
                                       robots=[],
                                       player_count=0)
    new_room = Room(new_match_state)

    # add owner robot to room
    owner = db_read_user_by_name(db, name=current_user)
    robot_in_match = RobotToUserModel(name=match.owner_robot,
                                      avatar=robot.avatar,
                                      owner_name=current_user,
                                      owner_avatar=owner.avatar,
                                      stats=robot.stats)
    new_room.add_player(robot_in_match)
    all_rooms.append(new_room)

    # return id for created room
    room_id = len(all_rooms) - 1
    match_room.update({match_id: room_id})
    return {'room_id': room_id, 'match_id': match_id}


@router.get('/list', response_model=List[MatchToUserModel])
async def match_list(_: str = Depends(get_current_user_name),
                     db: Database = Depends(get_db)):
    return db_read_match_list(db)


@router.post("/join")
async def match_join(join_model: MatchJoinModel,
                     current_user: str = Depends(get_current_user_name),
                     db: Database = Depends(get_db)):
    match_id, robot_name, password = join_model.dict().values()

    # check if match exists
    match = db_read_match(db, match_id=match_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Match does not exists'
        )

    # check if match is not started
    if match.is_started:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Match is started'
        )

    # check if match is not full
    if match.is_full:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Match is full'
        )

    # check if password is valid
    pass_ok = verify_password(password, match.password)
    if (match.password is not None) and (not pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid password for match'
        )

    # check if selected robot is valid
    robot = db_read_robot(db,
                          owner_name=current_user,
                          robot_name=robot_name)
    if robot is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Robot does not exists'
        )

    # check if user is not in match already
    user = db_read_user_by_name(db, name=current_user)
    is_already_in_match = any(r.owner_name == current_user
                              for r in match.robots)
    if is_already_in_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User is already in match'
        )

    # find room for match
    room_id = match_room.get(match_id)
    if room_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Room does not exists'
        )

    # update database entry
    db_update_match_add_player(db,
                               match_id=match_id,
                               robot_name=robot_name,
                               user_name=current_user)

    # update room
    robot_model = RobotToUserModel(name=robot.name,
                                   avatar=robot.avatar,
                                   owner_name=robot.owner,
                                   owner_avatar=user.avatar,
                                   stats=robot.stats)

    room = all_rooms[room_id]
    room.add_player(robot_model)
    return {"room_id": room_id, "match_id": match_id}


@router.post('/leave')
async def match_leave(match: MatchLeaveModel,
                      current_user: str = Depends(get_current_user_name),
                      db: Database = Depends(get_db)):
    match_id = match.id

    # Check if match exists in db
    match = db_read_match(db, match_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Match does not exists'
        )

    # Check if match is started
    if match.is_started:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Match is started'
        )

    # Check if user is the match owner
    if match.owner == current_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='The owner of the match cannot leave'
        )

    # Check if user is in the match
    is_in_match = any(r.owner_name == current_user for r in match.robots)
    if not is_in_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User is not in match'
        )

    # Check if exists a room for the match
    room_id = match_room.get(match_id)
    if room_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Room does not exists'
        )

    # Remove robot from match in db
    db_update_match_remove_player(db,
                                  match_id=match_id,
                                  user_name=current_user)

    # Remove robot from match in room
    room = all_rooms[room_id]
    room.remove_player(current_user)
    await room.leave_notify(current_user)
    return {}


@router.post('/start')
async def match_start(match: MatchStartModel,
                      current_user: str = Depends(get_current_user_name),
                      db: Database = Depends(get_db)):
    match_id = match.id

    # check if match exists
    match = db_read_match(db, match_id=match_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Match does not exists'
        )

    # check if user is the owner
    if match.owner != current_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User is not the owner'
        )

    # check if match is started
    if match.is_started:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Match is already started'
        )

    # check if match has enough players to start
    if len(match.robots) < match.num_players_min:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Not enough players'
        )

    # find room for match
    room_id = match_room.get(match_id)
    if room_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Room does not exists'
        )

    # update database entry
    db_update_match_is_started(db, match_id, True)

    # update stats player
    for r in match.robots:
        db_update_stats_played(db, r.owner_name, r.name)

    # create game, play and return results
    game = Game(match.rounds, match.games, match.robots, False)
    results_p = game.play()

    win_count = defaultdict(lambda: 0)
    for r in results_p:
        game_winner = r.get('winner')
        if game_winner:
            winner_name, winner_owner = game_winner.values()
            win_count[(winner_name, winner_owner)] += 1

    room = all_rooms[room_id]
    winner = None
    if len(win_count) != 0:
        winner_robot = max(win_count, key=win_count.get)
        winner_name, winner_owner = winner_robot
        winner = {'name': winner_name, 'owner': winner_owner}

    # update stats winner
    if winner is not None:
        db_update_stats_won(db, winner['owner'], winner['name'])

    await room.win_notify(winner)
    return {}
