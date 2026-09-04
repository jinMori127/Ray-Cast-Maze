"""The level currently being played, and the queries rays and the player run against it.

load() rebinds the module globals below, so every caller keeps reading `world.MAP` and
friends without carrying a level object down into the ray loop.
"""

import math

from src.levels import LEVELS

EMPTY = 0
OUTSIDE = 1

GOAL_RADIUS = 0.4  # how close the player's centre must come to the goal to count as escaped

LEVEL_INDEX = -1
NAME = ""
MAP = ()
MAP_WIDTH = 0
MAP_HEIGHT = 0
SPAWN = (0.0, 0.0)
SPAWN_ANGLE = 0.0
GOAL_CELL = (0, 0)
GOAL = (0.0, 0.0)


def load(index):
    """Make LEVELS[index] the level every query below answers about."""
    global LEVEL_INDEX, NAME, MAP, MAP_WIDTH, MAP_HEIGHT, SPAWN, SPAWN_ANGLE, GOAL_CELL, GOAL
    level = LEVELS[index]
    LEVEL_INDEX = index
    NAME = level.name
    MAP = level.grid
    MAP_HEIGHT = len(MAP)
    MAP_WIDTH = len(MAP[0])
    SPAWN = level.spawn
    SPAWN_ANGLE = level.spawn_angle
    GOAL_CELL = level.goal_cell
    GOAL = (GOAL_CELL[0] + 0.5, GOAL_CELL[1] + 0.5)


def tile_at(x, y):
    """Wall type id at world position (x, y); anything outside the grid is solid."""
    col, row = math.floor(x), math.floor(y)
    if 0 <= row < MAP_HEIGHT and 0 <= col < MAP_WIDTH:
        return MAP[row][col]
    return OUTSIDE


def is_wall(x, y):
    """True when (x, y) falls inside a solid cell."""
    return tile_at(x, y) != EMPTY


def at_goal(x, y):
    """True once the player stands close enough to the exit to end the run."""
    return math.hypot(x - GOAL[0], y - GOAL[1]) <= GOAL_RADIUS


load(0)
