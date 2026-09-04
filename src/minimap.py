"""Top-down view of the grid — a corner overlay while playing, full screen on TAB."""

import math

import pygame

from src import raycaster, settings, world

CLEAR = (0, 0, 0, 0)  # written into the shadow to punch a hole rather than blend one

_grid_cache = {}  # keyed by (level, scale): a level's grid never changes, so each size is painted once
_overlay = None
_shadow = None


def draw_overlay(surface, player, hits):
    """Corner panel showing only the ground the player can currently see, plus the exit."""
    global _overlay
    scale = settings.MINIMAP_SCALE
    grid = _grid(scale)
    if _overlay is None or _overlay.get_size() != grid.get_size():  # levels differ in size
        _overlay = pygame.Surface(grid.get_size()).convert()
        _overlay.set_alpha(settings.MINIMAP_ALPHA)

    _overlay.blit(grid, (0, 0))
    _draw_fan(_overlay, player, hits, scale, (0, 0), settings.MINIMAP_RAY_STRIDE)
    _draw_shadow(_overlay, player, hits, scale, (0, 0))
    # the exit and the player marker are drawn through the shadow: one is the objective, the
    # other is where you are, and neither is any use hidden
    _draw_goal(_overlay, scale, (0, 0))
    _draw_player(_overlay, player, hits[len(hits) // 2][1], scale, (0, 0))

    corner = (surface.get_width() - _overlay.get_width() - settings.MINIMAP_MARGIN, settings.MINIMAP_MARGIN)
    surface.blit(_overlay, corner)
    pygame.draw.rect(surface, settings.MINIMAP_BORDER_COLOR, (*corner, *_overlay.get_size()), 1)


def draw_debug(surface, player, hits):
    """Full-screen debugger: the whole cone, the centre ray and its exact hit point."""
    scale = fit_scale(surface)
    org = _centered_origin(surface, scale)
    _, distance, _, _, _, _, hit_x, hit_y = hits[len(hits) // 2]

    surface.fill(settings.DEBUG_BACKGROUND_COLOR)
    surface.blit(_grid(scale), org)
    _draw_fan(surface, player, hits, scale, org, settings.DEBUG_RAY_STRIDE)
    _draw_goal(surface, scale, org)
    _draw_center_ray(surface, player, (hit_x, hit_y), scale, org)
    _draw_player(surface, player, distance, scale, org)


def fit_scale(surface):
    """Largest whole pixels-per-cell that shows the entire grid on this surface."""
    return min(surface.get_width() // world.MAP_WIDTH, surface.get_height() // world.MAP_HEIGHT)


def to_screen(x, y, scale, org):
    """World position to a pixel in the top-down view."""
    left, top = org
    return round(left + x * scale), round(top + y * scale)


def _centered_origin(surface, scale):
    """Top-left pixel of the grid, centered on the surface."""
    return (
        (surface.get_width() - world.MAP_WIDTH * scale) // 2,
        (surface.get_height() - world.MAP_HEIGHT * scale) // 2,
    )


def _grid(scale):
    """The static half of the view at this scale, painted on the first frame that asks for it."""
    key = (world.LEVEL_INDEX, scale)
    grid = _grid_cache.get(key)
    if grid is None:
        grid = pygame.Surface((world.MAP_WIDTH * scale, world.MAP_HEIGHT * scale)).convert()
        _paint_grid(grid, scale)
        _grid_cache[key] = grid
    return grid


def _paint_grid(grid, scale):
    """Floor bed, wall cells colored by tile id, then the cell lines."""
    width, height = grid.get_size()
    grid.fill(settings.DEBUG_FLOOR_COLOR)

    for row in range(world.MAP_HEIGHT):
        for col in range(world.MAP_WIDTH):
            tile = world.MAP[row][col]
            if tile != world.EMPTY:
                color = settings.DEBUG_WALL_COLORS.get(tile, settings.DEBUG_UNKNOWN_COLOR)
                pygame.draw.rect(grid, color, (col * scale, row * scale, scale, scale))

    for col in range(world.MAP_WIDTH + 1):
        x = min(col * scale, width - 1)  # the closing line lands one pixel inside, not off the surface
        pygame.draw.line(grid, settings.DEBUG_GRID_COLOR, (x, 0), (x, height))
    for row in range(world.MAP_HEIGHT + 1):
        y = min(row * scale, height - 1)
        pygame.draw.line(grid, settings.DEBUG_GRID_COLOR, (0, y), (width, y))


def _draw_fan(surface, player, hits, scale, org, stride):
    """Every Nth ray of the vision cone, from the player out to the wall it found."""
    start = to_screen(player.x, player.y, scale, org)
    for _, _, _, _, _, _, hit_x, hit_y in hits[::stride]:
        pygame.draw.line(surface, settings.DEBUG_FAN_COLOR, start, to_screen(hit_x, hit_y, scale, org))


def _draw_shadow(surface, player, hits, scale, org):
    """Hide every part of the map the vision cone does not reach, wall faces included."""
    global _shadow
    if _shadow is None or _shadow.get_size() != surface.get_size():
        _shadow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    _shadow.fill((*settings.MINIMAP_SHADOW_COLOR, settings.MINIMAP_SHADOW_ALPHA))

    # the rays already stop at the first wall, so the fan they trace out is the visible region
    cone = [to_screen(player.x, player.y, scale, org)]
    cone.extend(to_screen(hit_x, hit_y, scale, org) for *_, hit_x, hit_y in hits)
    pygame.draw.polygon(_shadow, CLEAR, cone)

    left, top = org
    for col, row in {_wall_cell(hit) for hit in hits}:
        pygame.draw.rect(_shadow, CLEAR, (left + col * scale, top + row * scale, scale, scale))

    surface.blit(_shadow, (0, 0))


def _wall_cell(hit):
    """The cell a ray landed in, taken from the face it struck so a boundary hit never rounds away."""
    _, _, _, _, facing, _, hit_x, hit_y = hit
    if facing >> 1 == raycaster.SIDE_EW:
        return round(hit_x) - (facing == raycaster.FACE_EAST), math.floor(hit_y)
    return math.floor(hit_x), round(hit_y) - (facing == raycaster.FACE_SOUTH)


def _draw_goal(surface, scale, org):
    """The exit cell, painted over the vision cone so it stays legible when rays cross it."""
    left, top = org
    col, row = world.GOAL_CELL
    cell = (left + col * scale, top + row * scale, scale, scale)
    pygame.draw.rect(surface, settings.DEBUG_GOAL_COLOR, cell)
    pygame.draw.rect(surface, settings.DEBUG_GOAL_OUTLINE_COLOR, cell, 1)


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
