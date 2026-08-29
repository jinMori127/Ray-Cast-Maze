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


def draw(surface, player, scale, hits):
    """Draw the world from above with the vision cone and the player marker on top."""
    org = origin(surface, scale)
    _, distance, _, _, _, hit_x, hit_y = hits[len(hits) // 2]
    _draw_grid(surface, scale, org)
    _draw_fan(surface, player, hits, scale, org)
    _draw_center_ray(surface, player, (hit_x, hit_y), scale, org)
    _draw_player(surface, player, distance, scale, org)


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


def _draw_fan(surface, player, hits, scale, org):
    """Every Nth ray of the vision cone, from the player out to the wall it found."""
    start = to_screen(player.x, player.y, scale, org)
    for _, _, _, _, _, hit_x, hit_y in hits[:: settings.DEBUG_RAY_STRIDE]:
        pygame.draw.line(surface, settings.DEBUG_FAN_COLOR, start, to_screen(hit_x, hit_y, scale, org))


def _draw_center_ray(surface, player, hit_point, scale, org):
    """The straight-ahead ray, ending in a dot on the exact wall hit point."""
    start = to_screen(player.x, player.y, scale, org)
    hit = to_screen(hit_point[0], hit_point[1], scale, org)
    pygame.draw.line(surface, settings.DEBUG_RAY_COLOR, start, hit, max(1, scale // 24))
    pygame.draw.circle(surface, settings.DEBUG_HIT_COLOR, hit, max(2, scale // 10))


def _draw_player(surface, player, wall_distance, scale, org):
    """Marker at the player position, with a heading line stopping short of the wall ahead."""
    dir_x, dir_y = player.direction
    length = min(settings.DEBUG_HEADING_LENGTH, wall_distance)
    center = to_screen(player.x, player.y, scale, org)
    heading = to_screen(player.x + dir_x * length, player.y + dir_y * length, scale, org)
    pygame.draw.line(surface, settings.DEBUG_HEADING_COLOR, center, heading, max(1, scale // 16))
    pygame.draw.circle(surface, settings.DEBUG_PLAYER_COLOR, center, max(2, round(settings.DEBUG_PLAYER_RADIUS * scale)))
