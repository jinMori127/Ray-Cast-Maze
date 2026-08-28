"""Projection of ray hits into the first-person view — one vertical strip per column."""

import pygame

from src import settings

HORIZON = settings.SCREEN_HEIGHT // 2
WALL_SCALE = settings.SCREEN_HEIGHT  # pixel height of a one-unit wall seen from one unit away
MIN_DISTANCE = 1e-4  # keeps the perspective divide finite when a wall face touches the camera


def draw_world(surface, hits):
    """Draw ceiling and floor, then one wall strip per ray hit, scaled by 1 / distance."""
    draw_background(surface)
    for column, (_, distance, tile, _, _, _) in enumerate(hits):
        strip_height = min(WALL_SCALE / max(distance, MIN_DISTANCE), settings.SCREEN_HEIGHT)
        top = HORIZON - strip_height / 2
        color = settings.WALL_COLORS.get(tile, settings.WALL_UNKNOWN_COLOR)
        pygame.draw.rect(surface, color, (column, round(top), 1, round(strip_height)))


def draw_background(surface):
    """Flat ceiling above the horizon, flat floor below it."""
    surface.fill(settings.CEILING_COLOR, (0, 0, settings.SCREEN_WIDTH, HORIZON))
    surface.fill(settings.FLOOR_COLOR, (0, HORIZON, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - HORIZON))
