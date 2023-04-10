# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import get_password_hash
from database import setup_db, get_db
from database_utils import db_create_user, db_delete_user
from main import app
from utils import create_recover_code

client = TestClient(app)


@pytest.fixture(scope='module')
def setup():
    setup_db()
    db = get_db()
    username = 'UserRecoverNewName'
    password = 'Foobar1-'  # TODO usar mismo validator en create
    email = 'UserRecoverNewName@hmail.pap'
    recover_code = create_recover_code()
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email,
                   recover_code=recover_code)
    yield username, password, recover_code
    db_delete_user(db, name=username)


def test_invalid_user(setup):
    _, password, recover_code = setup
    response = client.post("/user/recover/new",
                           json={"name": "NotCreated",
                                 "recover_code": recover_code,
                                 "password": password})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == "User does not exist"


def test_invalid_code(setup):
    name, password, _ = setup
    response = client.post("/user/recover/new",
                           json={"name": name,
                                 "recover_code": "hola",
                                 "password": password})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == "Invalid recovery code"


def test_invalid_password(setup):
    name, _, code = setup
    response = client.post("/user/recover/new",
                           json={"name": name,
                                 "recover_code": code,
                                 "password": "chau"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == "Invalid password"


def test_same_as_old_password(setup):
    name, password, code = setup
    response = client.post("/user/recover/new",
                           json={"name": name,
                                 "recover_code": code,
                                 "password": password})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == "Password already in use"


def test_successful(setup):
    name, _, code = setup
    response = client.post(
        "/user/recover/new",
        json={
            "name": name,
            "recover_code": code,
            "password": "Hola1234-"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}
