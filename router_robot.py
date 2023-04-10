# global imports
from fastapi import Depends, status, APIRouter
from typing import List

# local imports
from authentication import *
from database import get_db
from database_utils import *
from models import *
from utils import *

router = APIRouter(prefix='/robot')


@router.post('/create', status_code=status.HTTP_201_CREATED)
async def robot_create(robot: RobotCreateModel,
                       current_user: str = Depends(get_current_user_name),
                       db: Database = Depends(get_db)):
    name, code, avatar = robot.dict().values()

    # create python file from code
    robot_dir = f'{ROBOTS_DIR}/{current_user}'
    robot_file = f'{camel_to_snake(name)}.py'
    save_robot(robot_dir, robot_file, code, overwrite=True)

    robot_in_db = db_read_robot(db,
                                owner_name=current_user,
                                robot_name=name)

    # create avatar file if exists
    avatar_url = None
    if avatar is not None:
        ext, content = avatar.values()
        file_name = f'{name}.{ext}'
        avatar_url = get_avatar_url(current_user, file_name)
        avatar_dir = f'{IMAGES_DIR}/{current_user}'
        if not save_avatar(avatar_dir, file_name, content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid avatar content'
            )

        if robot_in_db is not None and robot_in_db.avatar is not None:
            old_file_name = robot_in_db.avatar.split("/")[-1]
            if old_file_name != file_name:
                remove_file(f'{avatar_dir}/{old_file_name}')

    # create or update database entry
    if robot_in_db is None:
        db_create_robot(db,
                        owner_name=current_user,
                        robot_name=name,
                        avatar=avatar_url)
        db_create_stats(db, current_user, name)
    else:
        db_update_robot_avatar(db,
                               owner_name=current_user,
                               robot_name=name,
                               avatar=avatar_url)
    return {}


@router.get('/list', response_model=List[RobotToUserModel])
async def robot_list(current_user: str = Depends(get_current_user_name),
                     db: Database = Depends(get_db)):
    return db_read_robot_list(db, owner_name=current_user)
