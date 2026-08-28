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


def to_screen(x, y, scale, org):
    """World position to a pixel in the top-down view."""
    left, top = org
    return round(left + x * scale), round(top + y * scale)


def draw(surface, player, scale):
    """Draw the world from above, player marker on top."""
    org = origin(surface, scale)
    _draw_grid(surface, scale, org)
    _draw_player(surface, player, scale, org)


def _draw_grid(surface, scale, org):
    """Floor bed, wall cells colored by tile id, then the cell lines."""
    left, top = org
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


def _draw_player(surface, player, scale, org):
    """Marker at the player position with a line along the view direction."""
    dir_x, dir_y = player.direction
    center = to_screen(player.x, player.y, scale, org)
    heading = to_screen(
        player.x + dir_x * settings.DEBUG_HEADING_LENGTH,
        player.y + dir_y * settings.DEBUG_HEADING_LENGTH,
        scale,
        org,
    )
    pygame.draw.line(surface, settings.DEBUG_HEADING_COLOR, center, heading, max(1, scale // 16))
    pygame.draw.circle(surface, settings.DEBUG_PLAYER_COLOR, center, max(2, round(settings.DEBUG_PLAYER_RADIUS * scale)))
