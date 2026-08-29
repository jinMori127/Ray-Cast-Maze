"""The static level: a grid of wall type ids and the queries rays and the player run against it."""

import math

EMPTY = 0
OUTSIDE = 1

# 0 empty · 1 border brick · 2 inner stone · 3 the walls of the central chamber
MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 2, 2, 0, 2, 0, 2, 2, 2, 2, 2, 0, 2, 0, 1],
    [1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 1],
    [1, 0, 2, 0, 2, 2, 2, 2, 0, 2, 2, 2, 0, 2, 0, 1],
    [1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 1],
    [1, 0, 2, 2, 2, 0, 3, 3, 3, 3, 0, 2, 0, 2, 2, 1],
    [1, 0, 0, 0, 0, 0, 3, 0, 0, 3, 0, 2, 0, 0, 0, 1],
    [1, 0, 2, 2, 2, 0, 3, 0, 3, 3, 0, 2, 2, 2, 0, 1],
    [1, 0, 2, 0, 0, 0, 3, 0, 0, 0, 0, 0, 2, 0, 0, 1],
    [1, 0, 2, 0, 2, 2, 2, 2, 2, 0, 2, 0, 2, 0, 2, 1],
    [1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 2, 0, 0, 1],
    [1, 0, 2, 2, 2, 0, 2, 2, 2, 2, 2, 0, 2, 2, 0, 1],
    [1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 1],
    [1, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

MAP_HEIGHT = len(MAP)
MAP_WIDTH = len(MAP[0])

SPAWN = (1.5, 1.5)
SPAWN_ANGLE = 0.0

GOAL_CELL = (7, 13)  # a dead end walled on three sides, 26 of the maze's 27 steps from the spawn
GOAL = (GOAL_CELL[0] + 0.5, GOAL_CELL[1] + 0.5)
GOAL_RADIUS = 0.4  # how close the player's centre must come to the goal to count as escaped


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
