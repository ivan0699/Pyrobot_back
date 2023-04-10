from typing import Tuple

from utils import cos_d, sin_d, clamp
from constants import *


class Missile:
    def __init__(self,
                 direction: int,
                 distance: int,
                 position: Tuple[int, int],
                 final_position: Tuple[int, int]):
        self.direction = direction
        self.distance = distance
        self.position = position
        self.final_position = final_position
        self.is_active = True

    def move(self):
        direction = self.direction
        change_x, change_y = cos_d(direction), sin_d(direction)

        x, y = self.position
        x = clamp(0, round(x + (DISTANCE_MISSILE_ROUND * change_x)), 999)
        y = clamp(0, round(y + (DISTANCE_MISSILE_ROUND * change_y)), 999)

        self.distance -= DISTANCE_MISSILE_ROUND
        if self.distance <= 0:
            self.position = self.final_position
        else:
            self.position = x, y
