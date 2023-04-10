# global imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocket

# local imports
from authentication import *
from constants import *
from database import setup_db, get_db
from database_utils import *
from room import all_rooms
from router_match import router as router_match
from router_robot import router as router_robot
from router_simulation import router as router_simulation
from router_user import router as router_user
from models import *
from utils import *


origins = [
    f'{FRONTEND_URL}'
]

app: FastAPI = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router_match)
app.include_router(router_robot)
app.include_router(router_simulation)
app.include_router(router_user)


@app.on_event('startup')
async def app_startup():
    ensure_directory(ROBOTS_DIR)
    ensure_directory(IMAGES_DIR)
    app.mount(STATIC_IMAGES_URL, StaticFiles(directory=f'{IMAGES_DIR}'))
    setup_db(DB_NAME)


@app.on_event("shutdown")
def shutdown_event():
    db = get_db()
    db_delete_useless_matches(db)


@app.websocket('/ws/{room_id}')
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    if len(all_rooms) > room_id:
        room = all_rooms[room_id]
        await room.connect(websocket)

        msg = dict()
        while msg.get('type') != 'websocket.disconnect':
            msg = await websocket.receive()

        await room.disconnect(websocket)
