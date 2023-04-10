# global imports
from pydantic import *
from typing import List, Optional

# local imports
from constants import *
from utils import validate_email, valid_password


class UserRecoverModel(BaseModel):
    name: Optional[str]
    email: Optional[str]

    @validator('name')
    def recover_name_validator(cls, name):
        if len(name) == 0:
            raise ValueError('Empty field')
        return name

    @validator('email')
    def recover_email_validator(cls, email):
        if not validate_email(email):
            raise ValueError("Invalid email")
        return email


class UserRecoveryPassword(BaseModel):
    name: str
    recover_code: str
    password: str


class UserUpdatePassword(BaseModel):
    password: str


"""
        EXTERNAL MODELS
"""


class Token(BaseModel):
    access_token: str
    token_type: str


class ImageModel(BaseModel):
    ext: str
    content: str


class UserUpdateAvatar(BaseModel):
    avatar: Optional[ImageModel]


class UserCreateModel(BaseModel):
    name: str = Field(example="Foo")
    password: str = Field(example="Foobar1-")
    email: str = Field(example="Foo@gmail.com")
    avatar: Optional[ImageModel]

    @validator("name")
    def user_name_validator(cls, name):
        if len(name) == 0:
            raise ValueError("Invalid name")
        return name

    @validator("password")
    def user_password_validator(cls, password):
        if not valid_password(password):
            raise ValueError("Invalid password")
        return password

    @validator("email")
    def user_email_validator(cls, email):
        if not validate_email(email):
            raise ValueError("Invalid email")
        return email


class UserValidationModel(BaseModel):
    name: str
    code: str


class RobotCreateModel(BaseModel):
    name: str
    code: str
    avatar: Optional[ImageModel]


class RobotToUserModel(BaseModel):
    name: str
    avatar: Optional[str]
    owner_name: str
    owner_avatar: Optional[str]
    stats: dict = {'matches_played': 0, 'matches_won': 0}

    @classmethod
    def from_db(cls, obj):
        res = obj.to_dict()
        res.update({'avatar': obj.avatar})
        res.update({'owner_name': obj.owner.name})
        res.update({'owner_avatar': obj.owner.avatar})
        res.update({'stats': {'matches_won': obj.stats.matches_won,
                              'matches_played': obj.stats.matches_played}})
        return RobotToUserModel(**res)


class MatchModel(BaseModel):
    name: str
    games: conint(ge=1, le=200)
    rounds: conint(ge=1, le=10000)
    num_players_min: conint(ge=2, le=4)
    num_players_max: conint(ge=2, le=4)

    @root_validator(pre=True)
    def match_players_validator(cls, values):
        max_players = values.get('num_players_max')
        min_players = values.get('num_players_min')
        if max_players < min_players:
            raise ValueError('Min players greater than max players')
        return values


class MatchToUserModel(MatchModel):
    id: int
    player_count: int
    owner: str
    robots: List[RobotToUserModel]

    @classmethod
    def from_db(cls, obj):
        res = obj.to_dict()
        res.update({'player_count': len(obj.robots)})
        res.update({'owner': obj.owner.name})
        res.update({'robots': [RobotToUserModel.from_db(r)
                               for r in obj.robots]})
        return MatchToUserModel(**res)


class MatchCreateModel(MatchModel):
    owner_robot: str
    password: Optional[str]

    @validator("password")
    def user_password_validator(cls, password):
        if not valid_password(password):
            raise ValueError("Invalid password")
        return password


class MatchJoinModel(BaseModel):
    id: int
    robot: str
    password: Optional[str]


class MatchLeaveModel(BaseModel):
    id: int


class MatchStartModel(BaseModel):
    id: int


class SimulationModel(BaseModel):
    rounds: int
    robots_names: List[str]


"""
        INTERNAL MODELS
"""


class UserInDB(BaseModel):
    id: int
    name: str
    password: str
    email: str
    avatar: Optional[str]
    robots: List[RobotToUserModel]
    matches: List[MatchToUserModel]
    is_validated: bool
    validation_code: str
    recover_code: Optional[str]

    @classmethod
    def from_db(cls, obj):
        res = obj.to_dict()
        res.update({'robots': [RobotToUserModel.from_db(r)
                               for r in obj.robots]})
        res.update({'matches': [MatchToUserModel.from_db(m)
                                for m in obj.matches]})
        return UserInDB(**res)


class RobotInDB(BaseModel):
    id: int
    name: str
    owner: str
    avatar: Optional[str]
    matches: List[MatchToUserModel]
    stats: dict

    @classmethod
    def from_db(cls, obj):
        res = obj.to_dict()
        res.update({'owner': obj.owner.name})
        res.update({'matches': [MatchToUserModel.from_db(m)
                                for m in obj.matches]})
        res.update({'stats': {'matches_played': obj.stats.matches_played,
                              'matches_won': obj.stats.matches_won}})
        return RobotInDB(**res)


class MatchInDB(BaseModel):
    id: int
    name: str
    games: int
    rounds: int
    num_players_min: int
    num_players_max: int
    password: Optional[str]
    is_started: bool
    is_full: bool
    owner: str
    robots: List[RobotToUserModel]

    @classmethod
    def from_db(cls, obj):
        res = obj.to_dict()
        res.update({'owner': obj.owner.name})
        res.update({'robots': [RobotToUserModel.from_db(r)
                               for r in obj.robots]})
        return MatchInDB(**res)
