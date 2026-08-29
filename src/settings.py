"""Tunable constants shared by every module."""

import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
CAPTION = "Ray-Cast Maze"

RENDER_SCALE = 2  # window pixels per rendered pixel — set to 1 for a native-resolution image
RENDER_WIDTH = SCREEN_WIDTH // RENDER_SCALE
RENDER_HEIGHT = SCREEN_HEIGHT // RENDER_SCALE

TILE_SIZE = 64

MOVE_SPEED = 3.0  # world units (cells) per second
PLAYER_RADIUS = 0.2  # half-width of the box kept clear of walls, in cells
ROTATION_SPEED = math.radians(150)  # radians per second

FOV = math.radians(60)  # horizontal field of view
NUM_RAYS = RENDER_WIDTH  # one ray per rendered column
PLANE_HALF_WIDTH = math.tan(FOV / 2)  # half the projection plane, one unit from the camera

CEILING_COLOR = (28, 30, 38)
FLOOR_COLOR = (58, 52, 46)
FOG_COLOR = CEILING_COLOR
FOG_DENSITY = 0.20  # tuned so the longest sight line in MAP (13.5 cells) just reaches the fog colour

WALL_COLORS = {  # first-person wall faces, keyed by tile id
    1: (150, 96, 68),  # border brick
    2: (104, 116, 138),  # inner stone
    3: (176, 138, 70),  # central chamber
}
WALL_UNKNOWN_COLOR = (220, 60, 60)  # tile id missing from the palette — a bug, not a wall type

LIGHT_DIRECTION = (-0.6, -0.8)  # unit vector pointing toward the light, in world space
AMBIENT_LIGHT = 0.40  # base level every face receives, however it is turned
DIFFUSE_LIGHT = 0.75  # weight on the Lambert term; ambient + diffuse * 0.8 reaches exactly 1.0

HUD_COLOR = (226, 232, 240)  # near-white, readable over the fogged scene and the debug backdrop
HUD_FONT_NAME = "consolas,dejavusansmono,couriernew,monospace"  # first one installed wins
HUD_FONT_SIZE = 18
HUD_MARGIN = 8  # inset from the screen corner, in pixels

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
DEBUG_RAY_COLOR = (30, 158, 182)  # the straight-ahead ray
DEBUG_HIT_COLOR = (226, 46, 120)  # the exact point where a ray meets a wall
DEBUG_FAN_COLOR = (96, 176, 194)  # the rest of the vision cone
DEBUG_RAY_STRIDE = 8  # draw every Nth ray only, so single rays stay visible

MINIMAP_SCALE = 8  # pixels per cell in the corner overlay
MINIMAP_MARGIN = 12  # inset from the screen corner, in pixels
MINIMAP_ALPHA = 165  # opacity of the whole panel, so the 3D view still reads through it
MINIMAP_RAY_STRIDE = 20  # far fewer rays than the debug view — the panel is 16x smaller
MINIMAP_BORDER_COLOR = (150, 156, 168)  # frame that separates the panel from the scene
