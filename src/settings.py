"""Tunable constants shared by every module."""

import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
CAPTION = "Ray-Cast Maze"

TILE_SIZE = 64

ROTATION_SPEED = math.radians(150)  # radians per second

CEILING_COLOR = (28, 30, 38)
FLOOR_COLOR = (58, 52, 46)
FOG_COLOR = CEILING_COLOR

DEBUG_BACKGROUND_COLOR = (10, 11, 14)  # outside the grid
DEBUG_FLOOR_COLOR = (198, 202, 210)  # walkable cells — bright so corridors read as paths
DEBUG_GRID_COLOR = (122, 128, 140)  # cell borders, mid tone to stay visible on floor and walls
DEBUG_WALL_COLORS = {  # solid cells, keyed by tile id
    1: (70, 44, 32),  # border brick
    2: (44, 50, 62),  # inner stone
    3: (92, 66, 22),  # central chamber
}
DEBUG_UNKNOWN_COLOR = (220, 60, 60)  # tile id missing from the palette — a bug, not a wall type
DEBUG_PLAYER_COLOR = (214, 62, 54)  # the player marker
DEBUG_HEADING_COLOR = (250, 190, 70)  # the line showing where the player looks
DEBUG_PLAYER_RADIUS = 0.16  # marker radius, in world units
DEBUG_HEADING_LENGTH = 0.9  # heading line length, in world units
