# global imports
from random import randrange
from shapely.geometry import Point, Polygon
from typing import List
import importlib
from func_timeout import func_timeout

# local imports
from constants import *
from models import *
from missile import Missile
from robot import Robot
from utils import *


class Game:
    games: int
    rounds: int
    robots: List[Robot] = []
    players: List[str] = []
    damage_at_start: List[int] = []
    missiles: List[Missile] = []
    is_sim: bool

    def __init__(
            self,
            rounds: int,
            games: int,
            robots: List[RobotToUserModel],
            is_sim: bool):
        robots_in_game = []
        players_in_game = []
        damage = []
        for r in robots:
            try:
                module = importlib.import_module(
                    f'{ROBOTS_DIR}.{r.owner_name}.{camel_to_snake(r.name)}'
                )
                _class = getattr(module, r.name)
                instance = _class()
                damage.append(0)
            except BaseException:
                instance = Robot()
                damage.append(100)

            robots_in_game.append(instance)
            players_in_game.append(r.owner_name)

        self.rounds = rounds
        self.games = games
        self.robots = robots_in_game
        self.players = players_in_game
        self.damage_at_start = damage
        self.is_sim = is_sim
        self.missiles = []

    def scan(self, robot: Robot):
        direction = robot.scanner_direction
        resolution = robot.scanner_resolution
        # point 1
        x, y = robot.position
        # point 2
        x2 = round(x + (SCANNER_DISTANCE * cos_d(direction + resolution)))
        y2 = round(y + (SCANNER_DISTANCE * sin_d(direction + resolution)))
        # point 3
        x3 = round(x + (SCANNER_DISTANCE * cos_d(direction - resolution)))
        y3 = round(y + (SCANNER_DISTANCE * sin_d(direction - resolution)))
        area = Polygon([(x, y), (x2, y2), (x3, y3)])
        robots_in_scope = [r for r in self.robots
                           if area.contains(Point(r.position))]
        scanner_result = -1
        if len(robots_in_scope) > 0:
            scanner_result = min([
                get_distance(robot.position, r.position)
                for r in robots_in_scope
            ])

        robot.scanner_result = scanner_result

    def compute_next_position(self, robot: Robot):
        initial = robot.position
        if robot.is_alive():
            robot.update_accel()

            direction, accel = robot.direction, robot.accel
            change_x, change_y = cos_d(direction), sin_d(direction)

            x, y = robot.position
            next_x = round(x + (accel * change_x))
            next_y = round(y + (accel * change_y))

            invalid_x_position = (next_x < 0 or next_x > 999)
            invalid_y_position = (next_y < 0 or next_y > 999)
            if invalid_x_position or invalid_y_position:
                robot.make_damage(DAMAGE_COLLISION)

            final = clamp(0, next_x, 999), clamp(0, next_y, 999)
        else:
            final = initial

        return initial, final

    def check_position(self, i: int, positions: list):
        result = -1
        for j in range(i):
            if positions[i][1] == positions[j][1]:
                result = j
                break
        return result

    def fix_position(self, i: int, j: int, positions: list):
        initial_i, final_i = positions[i]
        robot_i = self.robots[i]
        initial_j, final_j = positions[j]
        robot_j = self.robots[j]

        if initial_i == final_i:
            change_x = cos_d(robot_j.direction)
            change_y = sin_d(robot_j.direction)

            final_x, final_y = final_j
            next_x = final_x - round(change_x)
            next_y = final_y - round(change_y)

            final_j = next_x, next_y
            positions[j] = initial_j, final_j
        else:
            change_x = cos_d(robot_i.direction)
            change_y = sin_d(robot_i.direction)

            final_x, final_y = final_i
            next_x = final_x - round(change_x)
            next_y = final_y - round(change_y)

            final_i = next_x, next_y
            positions[i] = initial_i, final_i

        robot_j.make_damage(DAMAGE_COLLISION)
        robot_i.make_damage(DAMAGE_COLLISION)

    def sanitize_positions(self, positions: list):
        i = 0
        while i < len(positions):
            j = self.check_position(i, positions)
            if j != -1:
                self.fix_position(i, j, positions)
                i = 0
            else:
                i += 1

    def fire(self, robot: Robot):
        can_fire = robot.is_cannon_ready() and robot.cannon_fired
        if can_fire:
            direction = robot.cannon_direction
            distance = robot.cannon_distance
            x, y = robot.position

            # compute final position of missile
            change_x, change_y = cos_d(direction), sin_d(direction)
            fx = clamp(0, round(x + (distance * change_x)), 999)
            fy = clamp(0, round(y + (distance * change_y)), 999)

            # Create new missile
            new_missile = Missile(direction, distance, (x, y), (fx, fy))
            self.missiles.append(new_missile)

            # Restart robot cannon state
            robot.rounds_to_cannon_ready = COOLDOWN_MISSILE
            robot.cannon_ready = False
            robot.cannon_fired = False
        elif not robot.is_cannon_ready():
            robot.rounds_to_cannon_ready -= 1
            if robot.rounds_to_cannon_ready == 0:
                robot.cannon_ready = True

    def missile_damage(self, robot: Robot):
        for m in self.missiles:
            distance = get_distance(m.final_position, robot.position)
            misil_to_explode = (m.is_active and m.position == m.final_position)
            damage_min = distance <= 40 and distance > 20
            damage_med = distance <= 20 and distance > 5
            damage_max = distance <= 5
            if misil_to_explode:
                if damage_min:
                    robot.damage = clamp(
                        0, robot.damage + DAMAGE_MISSIL_MIN, 100)
                elif damage_med:
                    robot.damage = clamp(
                        0, robot.damage + DAMAGE_MISSIL_MED, 100)
                elif damage_max:
                    robot.damage = clamp(
                        0, robot.damage + DAMAGE_MISSIL_MAX, 100)
                m.is_active = False

    def set_initial_states(self):
        for i, r in enumerate(self.robots):
            # status variables
            r.accel = 0
            r.damage = self.damage_at_start[i]
            r.direction = 0
            r.velocity = 0
            r.position = (randrange(0, 1000), randrange(0, 1000))

            # cannon variables
            r.rounds_to_cannon_ready = COOLDOWN_MISSILE
            r.cannon_direction = 0
            r.cannon_distance = 0
            r.cannon_ready = False
            r.cannon_fired = False

            # scanner variables
            r.scanner_direction = 0
            r.scanner_resolution = 0
            r.scanner_result = -1

    def get_robots_alive(self):
        return [r for r in self.robots if r.is_alive()]

    def log_round_state(self):
        robots = [{
            'damage': r.damage,
            'direction': r.direction,
            'velocity': r.velocity,
            'position': r.position,
            'scanner_direction': r.scanner_direction,
            'scanner_resolution': r.scanner_resolution}
            for r in self.robots
        ]

        missiles = [{
            'direction': m.direction,
            'position': m.position,
            'is_active': m.is_active}
            for m in self.missiles
        ]

        return {"robots": robots, "missiles": missiles}

    def play_round(self):
        res = {}

        # call robot code
        for r in self.robots:
            if r.is_alive():
                try:
                    func_timeout(0.05, r.respond)
                except BaseException:
                    r.make_damage(100)

        # scanner actions
        for r in self.robots:
            if r.is_alive():
                self.scan(r)

        # fire actions
        for r in self.robots:
            if r.is_alive():
                self.fire(r)

        # update missiles positions
        for m in self.missiles:
            m.move()

        # deal damage if missile explode
        for r in self.robots:
            if r.is_alive():
                self.missile_damage(r)

        # update robots positions
        next_positions = [self.compute_next_position(r) for r in self.robots]
        self.sanitize_positions(next_positions)

        for i, r in enumerate(self.robots):
            r.move(next_positions[i][1])

        # log round if simulation
        if self.is_sim:
            res = self.log_round_state()

        # update active missiles
        self.missiles = [m for m in self.missiles if m.is_active]

        return res

    def play_game(self):
        res = []
        self.missiles = []
        self.set_initial_states()

        for r in self.robots:
            try:
                func_timeout(0.05, r.initialize)
            except BaseException:
                r.make_damage(100)

        for _ in range(self.rounds):
            round_log = self.play_round()

            if self.is_sim:
                res.append(round_log)

            alive_robots = self.get_robots_alive()
            if len(alive_robots) < 2:
                break

        return res

    def play(self):
        log = []
        winner = None

        for _ in range(self.games):
            game_log = self.play_game()

            if self.is_sim:
                log.append(game_log)

            alive_robots = self.get_robots_alive()
            if len(alive_robots) == 1:
                winner_name = get_robot_name_from_object(alive_robots[0])
                i = self.robots.index(alive_robots[0])
                winner_owner = self.players[i]
                winner = {'name': winner_name, 'owner': winner_owner}
            log.append({'winner': winner})

        return log
