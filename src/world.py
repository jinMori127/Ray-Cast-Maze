"""The level currently being played, and the queries rays and the player run against it.

load() rebinds the module globals below, so every caller keeps reading `world.MAP` and
friends without carrying a level object down into the ray loop.
"""

import math

import numpy as np

from src.levels import LEVELS

EMPTY = 0
OUTSIDE = 1
STEP = 4  # a one-cell block you jump onto, walk along and drop off the far side

FULL_HEIGHT = 1.0  # a normal wall spans floor to ceiling and stops the ray
STEP_HEIGHT = 0.35  # the step's top, in cells — under the jump's peak, and clear of the ceiling
LANDING_EPSILON = 1e-6  # keeps a foot landed exactly on a step's top from re-colliding with it

GOAL_RADIUS = 0.4  # how close the player's centre must come to the goal to count as escaped

LEVEL_INDEX = -1
NAME = ""
MAP = ()
GRID = np.zeros((1, 1), np.uint8)  # MAP as an array, for the renderer's vectorised cell lookups
STEP_CENTRES = ()  # where the steps are, so the renderer can bound the rows that need testing
HAS_STEPS = False
MAP_WIDTH = 0
MAP_HEIGHT = 0
SPAWN = (0.0, 0.0)
SPAWN_ANGLE = 0.0
GOAL_CELL = (0, 0)
GOAL = (0.0, 0.0)


def load(index):
    """Make LEVELS[index] the level every query below answers about."""
    global LEVEL_INDEX, NAME, MAP, GRID, STEP_CENTRES, HAS_STEPS, MAP_WIDTH, MAP_HEIGHT
    global SPAWN, SPAWN_ANGLE, GOAL_CELL, GOAL
    level = LEVELS[index]
    LEVEL_INDEX = index
    NAME = level.name
    MAP = level.grid
    GRID = np.array(MAP, np.uint8)
    STEP_CENTRES = tuple((col + 0.5, row + 0.5) for row, col in zip(*np.nonzero(GRID == STEP)))
    HAS_STEPS = bool(STEP_CENTRES)  # a level without steps skips the second floor plane entirely
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
    """True when (x, y) falls inside a solid cell, however tall it stands."""
    return tile_at(x, y) != EMPTY


def tile_height(tile):
    """How tall a tile stands, in cells: 0 for open floor, under 1 for a step."""
    if tile == EMPTY:
        return 0.0
    return STEP_HEIGHT if tile == STEP else FULL_HEIGHT


def blocks(x, y, feet):
    """True when the cell at (x, y) stands taller than feet carried at this height."""
    return tile_height(tile_at(x, y)) > feet + LANDING_EPSILON


def stand_height(x, y):
    """Top of the surface underfoot at (x, y): a step's top, or 0 on open floor."""
    height = tile_height(tile_at(x, y))
    return height if height < FULL_HEIGHT else 0.0


def at_goal(x, y):
    """True once the player stands close enough to the exit to end the run."""
    return math.hypot(x - GOAL[0], y - GOAL[1]) <= GOAL_RADIUS


load(0)
