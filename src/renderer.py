"""Projection of ray hits into the first-person view — one vertical strip per column."""

import pygame

from src import raycaster, settings

HORIZON = settings.SCREEN_HEIGHT // 2
# distance to the projection plane in pixels, so both axes share one perspective scale
WALL_SCALE = settings.SCREEN_WIDTH / (2 * settings.PLANE_HALF_WIDTH)
MIN_DISTANCE = 1e-4  # keeps the perspective divide finite when a wall face touches the camera
NS_FACE_SHADE = 0.7  # the two face orientations meet a fixed light at different angles


def shade(color, side):
    """Flat shading — one fixed intensity per face orientation, N/S darker than E/W."""
    if side != raycaster.SIDE_NS:
        return color
    red, green, blue = color
    return int(red * NS_FACE_SHADE), int(green * NS_FACE_SHADE), int(blue * NS_FACE_SHADE)


def draw_world(surface, hits):
    """Draw ceiling and floor, then one wall strip per ray hit, scaled by 1 / distance."""
    draw_background(surface)
    for column, (_, _, perp_dist, tile, side, _, _) in enumerate(hits):
        strip_height = min(WALL_SCALE / max(perp_dist, MIN_DISTANCE), settings.SCREEN_HEIGHT)
        top = HORIZON - strip_height / 2
        color = shade(settings.WALL_COLORS.get(tile, settings.WALL_UNKNOWN_COLOR), side)
        pygame.draw.rect(surface, color, (column, round(top), 1, round(strip_height)))


def draw_background(surface):
    """Flat ceiling above the horizon, flat floor below it."""
    surface.fill(settings.CEILING_COLOR, (0, 0, settings.SCREEN_WIDTH, HORIZON))
    surface.fill(settings.FLOOR_COLOR, (0, HORIZON, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - HORIZON))
