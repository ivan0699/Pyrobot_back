# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from constants import ROBOTS_DIR, IMAGES_DIR
from database import setup_db, get_db
from database_utils import db_delete_user
from main import app
from utils import remove_dir

client = TestClient(app)


@pytest.fixture(scope='module')
def setup():
    setup_db()
    db = get_db()
    username = 'UserCreateName'
    password = 'Foobar1-'
    email = 'UserCreateName@hmail.con'
    avatar = {'ext': 'png', 'content': '1234'}
    yield username, password, email, avatar
    remove_dir(f'{ROBOTS_DIR}/{username}')
    remove_dir(f'{IMAGES_DIR}/{username}')
    db_delete_user(db, name=username)


def test_with_name_empy(setup):
    _, password, email, avatar = setup
    response = client.post('/user/create',
                           json={'name': '',
                                 'password': password,
                                 'email': email,
                                 'avatar': avatar})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()['detail'][0]['loc'][1] == 'name'
    assert response.json()['detail'][0]['msg'] == 'Invalid name'


def test_invalid_password_length(setup):
    name, _, email, _ = setup
    response = client.post('/user/create',
                           json={'name': name,
                                 'password': 'ola',
                                 'email': email})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_msg = response.json()["detail"][0]
    assert error_msg["loc"][1] == "password"
    assert error_msg["msg"] == "Invalid password"


def test_invalid_password_dash(setup):
    name, _, email, _ = setup
    response = client.post('/user/create',
                           json={'name': name,
                                 'password': 'pepe1919',
                                 'email': email})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_msg = response.json()["detail"][0]
    assert error_msg["loc"][1] == "password"
    assert error_msg["msg"] == "Invalid password"


def test_invalid_email(setup):
    name, password, _, _ = setup
    response = client.post('/user/create',
                           json={'name': name,
                                 'password': password,
                                 'email': 'queeseso'})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_msg = response.json()["detail"][0]
    assert error_msg["loc"][1] == "email"
    assert error_msg["msg"] == "Invalid email"


def test_invalid_email_empty(setup):
    name, password, _, _ = setup
    response = client.post('/user/create',
                           json={'name': name,
                                 'password': password,
                                 'email': ''})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_msg = response.json()["detail"][0]
    assert error_msg["loc"][1] == "email"
    assert error_msg["msg"] == "Invalid email"


def test_invalid_email_not_dot(setup):
    name, password, _, _ = setup
    response = client.post('/user/create',
                           json={'name': name,
                                 'password': password,
                                 'email': 'correo@gmailcom'})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_msg = response.json()["detail"][0]
    assert error_msg["loc"][1] == "email"
    assert error_msg["msg"] == "Invalid email"


def test_invalid_email_domain(setup):
    name, password, _, _ = setup
    response = client.post('/user/create',
                           json={'name': name,
                                 'password': password,
                                 'email': 'correo@gmail.cuatro.ar'})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_msg = response.json()["detail"][0]
    assert error_msg["loc"][1] == "email"
    assert error_msg["msg"] == "Invalid email"


def test_invalid_email_cant_send(setup):
    name, password, _, _ = setup
    response = client.post('/user/create',
                           json={'name': name,
                                 'password': password,
                                 'email': '@.com'})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid email"


def test_wrong_avatar(setup):
    name, password, email, _ = setup
    response = client.post('/user/create',
                           json={'name': name,
                                 'password': password,
                                 'email': email,
                                 'avatar': {'ext': 'gif',
                                            'content': '1'}})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid avatar content"


def test_successful(setup):
    name, password, email, avatar = setup
    response = client.post('/user/create',
                           json={'name': name,
                                 'password': password,
                                 'email': email,
                                 'avatar': avatar})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {}


def test_name_already_exists(setup):
    name, password, email, _ = setup
    response = client.post('/user/create',
                           json={'name': name,
                                 'password': password,
                                 'email': email})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Username already exists"


def test_email_already_taken(setup):
    _, password, email, _ = setup
    response = client.post('/user/create',
                           json={'name': 'OtherName',
                                 'password': password,
                                 'email': email})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already taken"
