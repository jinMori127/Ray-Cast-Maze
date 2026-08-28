"""Ray casting by DDA grid traversal — the visibility half of the renderer."""

import math

from src import world

EPSILON = 1e-9

SIDE_EW = 0  # ray crossed a vertical grid line, so it hit an east/west facing wall
SIDE_NS = 1  # ray crossed a horizontal grid line, so it hit a north/south facing wall


def cast_ray(px, py, angle):
    """March a ray to the first wall it meets; returns (distance, tile, side, hit_x, hit_y)."""
    dir_x, dir_y = math.cos(angle), math.sin(angle)
    if abs(dir_x) < EPSILON:
        dir_x = math.copysign(EPSILON, dir_x)
    if abs(dir_y) < EPSILON:
        dir_y = math.copysign(EPSILON, dir_y)

    delta_x = abs(1.0 / dir_x)
    delta_y = abs(1.0 / dir_y)
    map_x = math.floor(px)
    map_y = math.floor(py)

    if dir_x < 0:
        step_x = -1
        side_dist_x = (px - map_x) * delta_x
    else:
        step_x = 1
        side_dist_x = (map_x + 1 - px) * delta_x
    if dir_y < 0:
        step_y = -1
        side_dist_y = (py - map_y) * delta_y
    else:
        step_y = 1
        side_dist_y = (map_y + 1 - py) * delta_y

    while True:
        if side_dist_x < side_dist_y:
            side_dist_x += delta_x
            map_x += step_x
            side = SIDE_EW
        else:
            side_dist_y += delta_y
            map_y += step_y
            side = SIDE_NS
        tile = world.tile_at(map_x, map_y)
        if tile != world.EMPTY:
            break

    distance = side_dist_x - delta_x if side == SIDE_EW else side_dist_y - delta_y
    return distance, tile, side, px + distance * dir_x, py + distance * dir_y
