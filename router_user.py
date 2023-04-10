# global imports
from fastapi import Depends, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

# local imports
from authentication import *
from database import get_db
from database_utils import *
from models import *
from send_email import send_validation_code, send_recover_code
from utils import *

router = APIRouter(prefix='/user')


@router.post('/create', status_code=status.HTTP_201_CREATED)
async def user_create(user: UserCreateModel,
                      db: Database = Depends(get_db)):
    name, password, email, avatar = user.dict().values()

    # check if name is registered
    user_with_name = db_read_user_by_name(db, name)
    if user_with_name is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Username already exists'
        )

    # check if email is registered
    user_with_email = db_read_user_by_email(db, email)
    if user_with_email is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email already taken'
        )

    # create avatar file if exists
    avatar_url = None
    if avatar is not None:
        ext, content = avatar.values()
        file_name = f'avatar.{ext}'
        avatar_url = get_avatar_url(name, file_name)
        avatar_dir = f'{IMAGES_DIR}/{name}'
        saved = save_avatar(avatar_dir, file_name, content)
        if not saved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid avatar content'
            )

    # create and send validation code
    validation_code = create_validation_code(name)
    sent = send_validation_code(email, validation_code, name)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid email'
        )

    # create database entry
    hashed = get_password_hash(password)
    db_create_user(db,
                   name=name,
                   password=hashed,
                   email=email,
                   avatar=avatar_url,
                   validation_code=validation_code)

    # create default robots
    robots_dir = f'{ROBOTS_DIR}/{name}'
    for robot_name, code in DEFAULT_ROBOTS.items():
        file_name = f'{camel_to_snake(robot_name)}.py'
        save_robot(robots_dir, file_name, code)
        db_create_robot(db, owner_name=name, robot_name=robot_name)
        db_create_stats(db, name, robot_name)
    return {}


@router.post("/login", response_model=Token)
async def user_login(user_data: OAuth2PasswordRequestForm = Depends(),
                     db: Database = Depends(get_db)):
    name, password = user_data.username, user_data.password

    # check if user exists
    user = authenticate_user(db, name, password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password'
        )

    # check if user is validated
    if not user.is_validated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='User not validated'
        )

    # create and return access token
    access_token = create_access_token(user.name)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/validation")
async def user_validation(validation: UserValidationModel,
                          db: Database = Depends(get_db)):
    name, code = validation.dict().values()

    # check if user exists
    user = db_read_user_by_name(db, name)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid username'
        )

    # check if validation code is correct
    if user.validation_code != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid validation code'
        )

    # validate user
    db_update_user_is_validated(db, name, True)
    return {}


@router.post('/recover')
async def user_recover(user_data: UserRecoverModel,
                       db: Database = Depends(get_db)):
    name, email = user_data.dict().get('name'), user_data.dict().get('email')

    if name is None and email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Name or email fields not found'
        )

    if email is None:
        user = db_read_user_by_name(db, name)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Username not found'
            )
        email = user.email
    else:
        user = db_read_user_by_email(db, email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Email not found'
            )
        name = user.name

    recover_code = create_recover_code()
    sent = send_recover_code(email, recover_code, name)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid email'
        )

    db_update_user_recover_code(db, name, recover_code)

    return {}


@router.post("/recover/new")
async def recover_password(recover_pass: UserRecoveryPassword,
                           db: Database = Depends(get_db)):
    name, code, new_pass = recover_pass.dict().values()
    user = db_read_user_by_name(db, name)

    # check user exist
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not exist"
        )

    # check recovery code
    if user.recover_code != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recovery code"
        )

    # check new password
    if not valid_password(new_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )

    # check old password
    in_use = verify_password(new_pass, user.password)
    if in_use:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password already in use"
        )

    # update password
    hashed = get_password_hash(new_pass)
    db_update_user_password(db, name, hashed)
    return {}


@router.get("/profile")
async def show_profile_data(current_user: str = Depends(get_current_user_name),
                            db: Database = Depends(get_db)):
    user = db_read_user_by_name(db, current_user)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not exist"
        )
    name = user.name
    avatar = user.avatar
    robots = user.robots
    result = {"name": name, "avatar": avatar, "robots": robots}
    return result


@router.put('/password')
async def user_change_pass(update_pass: UserUpdatePassword,
                           db: Database = Depends(get_db),
                           current_user: str = Depends(get_current_user_name)):
    new_pass = update_pass.password

    # check user exist
    user = db_read_user_by_name(db, current_user)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not exist"
        )

    # check new password
    if not valid_password(new_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )

    # check old password
    in_use = verify_password(new_pass, user.password)
    if in_use:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password already in use"
        )

    # update password
    hashed = get_password_hash(new_pass)
    db_update_user_password(db, user.name, hashed)
    return {}


@router.put('/avatar')
async def user_change_avatar(
        updateAvatar: UserUpdateAvatar,
        db: Database = Depends(get_db),
        current_user: str = Depends(get_current_user_name)):
    user = db_read_user_by_name(db, current_user)
    new_avatar = updateAvatar.avatar
    # check user exist
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not exist"
        )

    # create avatar file if exists
    avatar_url = None
    if new_avatar is not None:
        ext, content = new_avatar.dict().values()
        file_name = f'avatar.{ext}'
        avatar_url = get_avatar_url(user.name, file_name)
        avatar_dir = f'{IMAGES_DIR}/{user.name}'
        saved = save_avatar(avatar_dir, file_name, content)
        if not saved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid avatar content'
            )

        if user.avatar is not None:
            old_file_name = user.avatar.split("/")[-1]
            if old_file_name != file_name:
                remove_file(f'{avatar_dir}/{old_file_name}')

    # update avatar
    db_update_user_avatar(db, user.name, avatar_url)
    return {}
