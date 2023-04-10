from pony.orm import *

db: Database = None


def define_entities(db: Database):
    class User(db.Entity):
        id = PrimaryKey(int, auto=True)
        name = Required(str)
        password = Required(str)
        email = Required(str)
        avatar = Optional(str, nullable=True)
        robots = Set('Robot')
        matches = Set('Match')
        is_validated = Required(bool)
        validation_code = Required(str)
        recover_code = Optional(str, nullable=True)

    class Stats(db.Entity):
        id = PrimaryKey(int, auto=True)
        robot = Required('Robot')
        matches_played = Required(int)
        matches_won = Required(int)

    class Robot(db.Entity):
        id = PrimaryKey(int, auto=True)
        owner = Required('User')
        name = Required(str)
        avatar = Optional(str, nullable=True)
        matches = Set('Match')
        stats = Optional('Stats', cascade_delete=True)

    class Match(db.Entity):
        id = PrimaryKey(int, auto=True)
        name = Required(str)
        games = Required(int)
        rounds = Required(int)
        num_players_min = Required(int)
        num_players_max = Required(int)
        password = Optional(str, nullable=True)
        is_started = Required(bool)
        is_full = Required(bool)
        owner = Required('User')
        robots = Set('Robot')


def setup_db(mode: str = None):
    global db
    db = Database()
    define_entities(db)
    filename = ':sharedmemory:'
    if mode:
        filename = f'{mode}.sqlite'
    db.bind('sqlite', filename, create_db=True)
    db.generate_mapping(create_tables=True)


def get_db() -> Database:
    return db
