"""Top-down view of the grid — the debugger for every later rendering task."""

import pygame

from src import settings, world


def fit_scale(surface):
    """Largest whole pixels-per-cell that shows the entire grid on this surface."""
    return min(surface.get_width() // world.MAP_WIDTH, surface.get_height() // world.MAP_HEIGHT)


def origin(surface, scale):
    """Top-left pixel of the grid, centered on the surface."""
    return (
        (surface.get_width() - world.MAP_WIDTH * scale) // 2,
        (surface.get_height() - world.MAP_HEIGHT * scale) // 2,
    )


def draw(surface, player, scale):
    """Draw the grid from above: floor bed, wall cells colored by tile id, then grid lines."""
    left, top = origin(surface, scale)
    width, height = world.MAP_WIDTH * scale, world.MAP_HEIGHT * scale

    surface.fill(settings.DEBUG_BACKGROUND_COLOR)
    pygame.draw.rect(surface, settings.DEBUG_FLOOR_COLOR, (left, top, width, height))

    for row in range(world.MAP_HEIGHT):
        for col in range(world.MAP_WIDTH):
            tile = world.MAP[row][col]
            if tile != world.EMPTY:
                color = settings.DEBUG_WALL_COLORS.get(tile, settings.DEBUG_UNKNOWN_COLOR)
                pygame.draw.rect(surface, color, (left + col * scale, top + row * scale, scale, scale))

    for col in range(world.MAP_WIDTH + 1):
        x = left + col * scale
        pygame.draw.line(surface, settings.DEBUG_GRID_COLOR, (x, top), (x, top + height))
    for row in range(world.MAP_HEIGHT + 1):
        y = top + row * scale
        pygame.draw.line(surface, settings.DEBUG_GRID_COLOR, (left, y), (left + width, y))
