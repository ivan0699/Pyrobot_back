# global imports
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# local imports
from authentication import get_password_hash
from database import setup_db, get_db
from database_utils import db_create_user, db_delete_user
from main import app

client = TestClient(app)


@pytest.fixture(scope='module')
def db():
    setup_db()
    db = get_db()
    yield db


@pytest.fixture(scope='module')
def setup(db):
    username = 'UserRecoverName1'
    password = 'Foobar1-'
    email = 'UserRecoverName1@hmail.pap'
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email)
    yield username, email
    db_delete_user(db, name=username)


@pytest.fixture(scope='module')
def setup_dummy_email(db):
    username = 'UserRecoverName2'
    password = 'Foobar1-'
    email = '@.com'
    db_create_user(db,
                   name=username,
                   password=get_password_hash(password),
                   email=email)
    yield username, email
    db_delete_user(db, name=username)


def test_without_name_and_email():
    response = client.post('/user/recover', json={})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Name or email fields not found'


def test_with_unregistered_name(setup):
    response = client.post('/user/recover', json={'name': 'NotCreated'})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Username not found'


def test_with_unregistered_email(setup):
    response = client.post('/user/recover',
                           json={'email': 'NotRegistered@email.com'})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Email not found'


def test_with_invalid_email():
    response = client.post('/user/recover',
                           json={'email': 'someinvalidemail'})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    msg = response.json()['detail'][0]
    assert msg['loc'][1] == 'email'
    assert msg['msg'] == 'Invalid email'


def test_with_empty_name():
    response = client.post('/user/recover',
                           json={'name': ''})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    msg = response.json()['detail'][0]
    assert msg['loc'][1] == 'name'
    assert msg['msg'] == 'Empty field'


def test_email_not_sent(setup_dummy_email):
    _, email = setup_dummy_email
    response = client.post('/user/recover',
                           json={'email': email})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Invalid email'


def test_successful_with_name(setup):
    name, _ = setup
    response = client.post('/user/recover',
                           json={'name': name})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}


def test_successful_with_email(setup):
    _, email = setup
    response = client.post('/user/recover',
                           json={'email': email})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}
