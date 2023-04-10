from starlette.websockets import WebSocket
from typing import Dict

from models import *


class Room:
    players: List[WebSocket]
    match: MatchToUserModel
    is_over: bool

    def __init__(self, match: MatchToUserModel):
        self.players = []
        self.match = match
        self.is_over = False

    def add_player(self, robot: RobotToUserModel):
        self.match.robots.append(robot)
        self.match.player_count += 1

    def remove_player(self, user_name: str):
        robot = None
        for r in self.match.robots:
            if r.owner_name == user_name:
                robot = r
        self.match.robots.remove(robot)
        self.match.player_count -= 1

    async def broadcast(self, message: dict):
        for p in self.players:
            await p.send_json(message)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.players.append(websocket)
        await self.broadcast(self.match.dict())

    async def disconnect(self, websocket: WebSocket):
        self.players.remove(websocket)
        if not self.is_over:
            await self.broadcast(self.match.dict())

    async def leave_notify(self, user_name: str):
        await self.broadcast({'user': user_name})

    async def win_notify(self, winner: dict):
        await self.broadcast({'winner': winner})
        self.is_over = True


all_rooms: List[Room] = []
match_room: Dict[int, int] = {}
