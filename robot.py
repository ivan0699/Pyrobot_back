from constants import *
from utils import clamp


class Robot:
    def __init__(self):
        # status variables
        self.accel = 0
        self.damage = 0
        self.direction = 0
        self.velocity = 0
        self.position = (0, 0)

        # cannon variables
        self.rounds_to_cannon_ready = COOLDOWN_MISSILE
        self.cannon_direction = 0
        self.cannon_distance = 0
        self.cannon_ready = False
        self.cannon_fired = False

        # scanner variables
        self.scanner_direction = 0
        self.scanner_resolution = 0
        self.scanner_result = -1

    def initialize(self):
        pass

    def respond(self):
        pass

    def get_direction(self):
        return self.direction

    def get_velocity(self):
        return self.velocity

    def get_position(self):
        return self.position

    def get_damage(self):
        return self.damage

    def is_alive(self) -> bool:
        return self.damage < 100

    def drive(self, direction: int, velocity: int):
        if self.accel <= MAX_ACCEL_TO_TURN:
            self.direction = direction % 360
        self.velocity = clamp(0, velocity, 100)

    def point_scanner(self, direction: int, resolution_in_degrees: int):
        self.scanner_direction = direction % 360
        self.scanner_resolution = clamp(0, resolution_in_degrees, 10)

    def scanned(self) -> int:
        return self.scanner_result

    def cannon(self, degree: int, distance: int):
        self.cannon_fired = True
        self.cannon_direction = degree % 360
        self.cannon_distance = clamp(0, distance, 700)

    def is_cannon_ready(self) -> bool:
        return self.cannon_ready

    def make_damage(self, damage: int):
        self.damage = clamp(0, self.damage + damage, 100)

    def move(self, position: int):
        x, y = position
        self.position = clamp(0, x, 999), clamp(0, y, 999)

    def update_accel(self):
        velocity, accel = self.velocity, self.accel
        if (accel - VAR_ACCEL) > velocity:
            accel -= VAR_ACCEL
        elif (accel + VAR_ACCEL) < velocity:
            accel += VAR_ACCEL
        else:
            accel = velocity
        self.accel = accel
