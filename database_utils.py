# global imports
from typing import List

# local imports
from database import Database, db_session
from models import *


"""
        USER CRUD UTILS
"""


# CREATE
@db_session
def db_create_user(db: Database,
                   name: str,
                   password: str,
                   email: str,
                   avatar: str = None,
                   is_validated: bool = False,
                   validation_code: str = 'changeme',
                   recover_code: str = None) -> int:
    user_in_db = db.User(name=name,
                         password=password,
                         email=email,
                         avatar=avatar,
                         is_validated=is_validated,
                         validation_code=validation_code,
                         recover_code=recover_code)
    return user_in_db.id


# READ
@db_session
def db_read_user_by_name(db: Database,
                         name: str) -> UserInDB:
    user_in_db = db.User.get(name=name)
    result = None
    if user_in_db is not None:
        result = UserInDB.from_db(user_in_db)
    return result


@db_session
def db_read_user_by_email(db: Database,
                          email: str) -> UserInDB:
    user_in_db = db.User.get(email=email)
    result = None
    if user_in_db is not None:
        result = UserInDB.from_db(user_in_db)
    return result


# UPDATE
@db_session
def db_update_user_is_validated(db: Database,
                                name: str,
                                is_validated: bool):
    user_in_db = db.User.get(name=name)
    user_in_db.is_validated = is_validated


@db_session
def db_update_user_password(db: Database,
                            name: str,
                            password: str):
    user_in_db = db.User.get(name=name)
    user_in_db.password = password


@db_session
def db_update_user_avatar(db: Database,
                          name: str,
                          avatar: str = None):
    user_in_db = db.User.get(name=name)
    user_in_db.avatar = avatar


@db_session
def db_update_user_recover_code(db: Database,
                                name: str,
                                recover_code: str):
    user_in_db = db.User.get(name=name)
    user_in_db.recover_code = recover_code


# DELETE
@db_session
def db_delete_user(db: Database,
                   name: str):
    user_in_db = db.User.get(name=name)
    user_in_db.delete()


"""
        ROBOT CRUD UTILS
"""


# CREATE
@db_session
def db_create_robot(db: Database,
                    owner_name: str,
                    robot_name: str,
                    avatar: str = None) -> int:
    user_in_db = db.User.get(name=owner_name)
    robot_in_db = db.Robot(owner=user_in_db,
                           name=robot_name,
                           avatar=avatar)
    user_in_db.robots.add(robot_in_db)
    return robot_in_db.id


# READ
@db_session
def db_read_robot(db: Database,
                  owner_name: str,
                  robot_name: str) -> RobotInDB:
    user_in_db = db.User.get(name=owner_name)
    robot_in_db = db.Robot.get(owner=user_in_db,
                               name=robot_name)
    result = None
    if robot_in_db is not None:
        result = RobotInDB.from_db(robot_in_db)
    return result


@db_session
def db_read_robot_list(db: Database,
                       owner_name: str) -> List[RobotToUserModel]:
    user_in_db = db.User.get(name=owner_name)
    robots_in_db = db.Robot.select(owner=user_in_db)
    return [RobotToUserModel.from_db(r) for r in robots_in_db]


# UPDATE
@db_session
def db_update_robot_avatar(db: Database,
                           owner_name: str,
                           robot_name: str,
                           avatar: str = None):
    user_in_db = db.User.get(name=owner_name)
    robot_in_db = db.Robot.get(owner=user_in_db, name=robot_name)
    robot_in_db.avatar = avatar


# DELETE
@db_session
def db_delete_robot(db: Database,
                    owner_name: str,
                    robot_name: str):
    user_in_db = db.User.get(name=owner_name)
    robot_in_db = db.Robot.get(owner=user_in_db, name=robot_name)
    user_in_db.robots.remove(robot_in_db)
    robot_in_db.delete()


"""
        STATS CRUD UTILS
"""


# CREATE
@db_session
def db_create_stats(db: Database,
                    owner_name: str,
                    robot_name: str,
                    played: int = 0,
                    won: int = 0) -> int:
    user_in_db = db.User.get(name=owner_name)
    robot_in_db = db.Robot.get(owner=user_in_db,
                               name=robot_name)
    stats_in_db = db.Stats(robot=robot_in_db,
                           matches_played=played,
                           matches_won=won)
    return stats_in_db.id


# UPDATE
@db_session
def db_update_stats_played(db: Database,
                           owner_name: str,
                           robot_name: str):
    user_in_db = db.User.get(name=owner_name)
    robot_in_db = db.Robot.get(owner=user_in_db, name=robot_name)
    stats_in_db = db.Stats.get(robot=robot_in_db)
    stats_in_db.matches_played += 1


@db_session
def db_update_stats_won(db: Database,
                        owner_name: str,
                        robot_name: str):
    user_in_db = db.User.get(name=owner_name)
    robot_in_db = db.Robot.get(owner=user_in_db, name=robot_name)
    stats_in_db = db.Stats.get(robot=robot_in_db)
    stats_in_db.matches_won += 1


"""
        MATCH CRUD UTILS
"""


# CREATE
@db_session
def db_create_match(db: Database,
                    name: str,
                    games: int,
                    rounds: int,
                    num_players_min: int,
                    num_players_max: int,
                    owner_name: str,
                    owner_robot: str,
                    is_started: bool = False,
                    is_full: bool = False,
                    password: str = None) -> int:
    user_in_db = db.User.get(name=owner_name)
    match_in_db = db.Match(name=name,
                           games=games,
                           rounds=rounds,
                           num_players_min=num_players_min,
                           num_players_max=num_players_max,
                           password=password,
                           is_started=is_started,
                           is_full=is_full,
                           owner=user_in_db)
    robot_in_db = db.Robot.get(owner=user_in_db,
                               name=owner_robot)
    match_in_db.robots.add(robot_in_db)
    user_in_db.matches.add(match_in_db)
    robot_in_db.matches.add(match_in_db)
    return match_in_db.id


# READ
@db_session
def db_read_match(db: Database,
                  match_id: int) -> MatchInDB:
    match_in_db = db.Match.get(id=match_id)
    result = None
    if match_in_db is not None:
        result = MatchInDB.from_db(match_in_db)
    return result


@db_session
def db_read_match_list(db: Database) -> List[MatchToUserModel]:
    matches_in_db = db.Match.select(is_started=False, is_full=False)
    return [MatchToUserModel.from_db(m) for m in matches_in_db]


# UPDATE
@db_session
def db_update_match_is_started(db: Database,
                               match_id: int,
                               is_started: bool):
    match_in_db = db.Match.get(id=match_id)
    match_in_db.is_started = is_started


@db_session
def db_update_match_add_player(db: Database,
                               match_id: int,
                               robot_name: str,
                               user_name: str):
    user_in_db = db.User.get(name=user_name)
    robot_in_db = db.Robot.get(owner=user_in_db, name=robot_name)
    match_in_db = db.Match.get(id=match_id)

    match_in_db.robots.add(robot_in_db)
    robot_in_db.matches.add(match_in_db)

    if len(match_in_db.robots) == match_in_db.num_players_max:
        match_in_db.is_full = True


@db_session
def db_update_match_remove_player(db: Database,
                                  match_id: int,
                                  user_name: str):
    match_in_db = db.Match.get(id=match_id)
    user_in_db = db.User.get(name=user_name)
    robot_in_db = db.Robot.get(
        lambda r: (r.owner is user_in_db) and (match_in_db in r.matches)
    )

    match_in_db.robots.remove(robot_in_db)
    robot_in_db.matches.remove(match_in_db)

    match_in_db.is_full = False


# DELETE
@db_session
def db_delete_match(db: Database,
                    match_id: int):
    match_in_db = db.Match.get(id=match_id)
    for r in match_in_db.robots:
        r.matches.remove(match_in_db)
        r.owner.matches.remove(match_in_db)
    match_in_db.delete()


def db_delete_useless_matches(db: Database):
    db.drop_table('Match', with_all_data=True)
    db.drop_table('Match_Robot', with_all_data=True)
