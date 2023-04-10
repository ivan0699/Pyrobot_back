# global imports
from base64 import decodebytes
import binascii
from math import radians, cos, sin
from pathlib import Path
from random import choices
from shutil import rmtree
from typing import Tuple

# local imports
from constants import *


def ensure_directory(directory: str):
    Path(directory).mkdir(parents=True, exist_ok=True)


def path_exists(path: str):
    return Path(path).exists()


def remove_file(directory: str):
    Path(directory).unlink()


def remove_dir(directory: str):
    if path_exists(directory):
        rmtree(directory)


def camel_to_snake(s: str):
    res = ''.join(
        ['_' + c.lower() if c.isupper() else c for c in s]
    )
    if res[0] == '_':
        res = res[1:]
    return res


def get_avatar_url(username: str, filename: str):
    return f'{STATIC_IMAGES_URL}/{username}/{filename}'


def get_robot_name_from_object(robot: object):
    return robot.__class__.__name__


def create_validation_code(name: str):
    return f'{abs(hash(name))}'[:VALIDATION_CODE_LENGTH]


def create_recover_code():
    return ''.join(choices(RECOVER_CODE_ELEMS, k=RECOVER_CODE_LENGTH))


def clamp(min_value: int, value: int, max_value: int):
    return max(min(max_value, value), min_value)


def cos_d(degrees: int):
    return cos(radians(degrees))


def sin_d(degrees: int):
    return sin(radians(degrees))


def get_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]):
    x1, y1 = pos1
    x2, y2 = pos2
    distance = round(((x1 - x2)**2 + (y1 - y2)**2)**0.5)
    return distance


def validate_email(email: str) -> bool:
    res = True

    if len(email) == 0 or email.find('@') == -1:
        res = False
    else:
        email_s = email.split("@")[1]
        if email_s.find(".") == -1:
            res = False
        elif len(email_s.split(".")[1]) != 3:
            res = False

    return res


def save_robot(directory: str, file_name: str,
               code: str, overwrite: bool = False):
    ensure_directory(directory)
    path = f'{directory}/{file_name}'
    if overwrite or not path_exists(path):
        with open(path, 'w+') as fd:
            fd.write(code)


def save_avatar(directory: str, file_name: str, content: str) -> bool:
    saved: bool = True
    content_bytes: bytes = b''
    ensure_directory(directory)
    try:
        content_bytes = decodebytes(content.encode(AVATAR_STRING_ENCODE))
    except binascii.Error:
        saved = False
    else:
        path = f'{directory}/{file_name}'
        with open(path, 'wb+') as fd:
            fd.write(content_bytes)
    return saved


def valid_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if password.find('-') == -1:
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.isnumeric() for c in password):
        return False
    return True
