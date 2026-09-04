"""Ray casting by DDA grid traversal — the visibility half of the renderer."""

import math

from src import settings, world

EPSILON = 1e-9

SIDE_EW = 0  # ray crossed a vertical grid line, so it hit an east/west facing wall
SIDE_NS = 1  # ray crossed a horizontal grid line, so it hit a north/south facing wall

# Which of the four faces the ray struck. side is FACE >> 1, so the pair still says which
# grid line was crossed, while the value itself names the outward normal for shading.
FACE_WEST = 0
FACE_EAST = 1
FACE_NORTH = 2
FACE_SOUTH = 3
FACE_NORMALS = ((-1.0, 0.0), (1.0, 0.0), (0.0, -1.0), (0.0, 1.0))

# per-column ray angle relative to the view direction, evenly spaced across the projection plane
RAY_OFFSETS = [
    math.atan((2.0 * (column + 0.5) / settings.NUM_RAYS - 1.0) * settings.PLANE_HALF_WIDTH)
    for column in range(settings.NUM_RAYS)
]


def cast_ray(px, py, angle):
    """March a ray to the first wall tall enough to block the view.

    Returns (blocking_hit, low_hits): a step is short enough to see over, so the ray records
    it and keeps going instead of stopping. Each hit is
    (distance, tile, facing, u, hit_x, hit_y), and low_hits runs near to far.
    """
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

    low_hits = []
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
        if tile == world.EMPTY:
            continue

        distance = side_dist_x - delta_x if side == SIDE_EW else side_dist_y - delta_y
        hit_x = px + distance * dir_x
        hit_y = py + distance * dir_y

        # u is the hit's position along the face's tangent, which points -y / +y / +x / -x for
        # west / east / north / south faces. Negating instead of taking 1 - frac keeps a hit
        # exactly on a cell corner at u = 0 rather than wrapping it to an out-of-range 1.0.
        if side == SIDE_EW:
            facing, along = (FACE_WEST, -hit_y) if dir_x > 0 else (FACE_EAST, hit_y)
        else:
            facing, along = (FACE_NORTH, hit_x) if dir_y > 0 else (FACE_SOUTH, -hit_x)

        hit = (distance, tile, facing, along - math.floor(along), hit_x, hit_y)
        if tile != world.STEP:
            return hit, low_hits
        low_hits.append(hit)


def cast_all(player):
    """One ray per column: the wall that blocks it, and the steps standing in front of it.

    A blocking hit is (ray_angle, distance, perp_dist, tile, facing, u, hit_x, hit_y); a mini
    wall drops the two the minimap never asks for, leaving (perp_dist, tile, facing, u, x, y).
    """
    px, py, angle = player.x, player.y, player.angle
    hits = []
    obstacles = []
    for offset in RAY_OFFSETS:
        # offset is the ray's angle off the view axis, so its cosine projects the ray
        # length onto that axis — the depth the perspective divide needs
        (distance, tile, facing, u, hit_x, hit_y), low = cast_ray(px, py, angle + offset)
        cosine = math.cos(offset)
        hits.append((angle + offset, distance, distance * cosine, tile, facing, u, hit_x, hit_y))
        obstacles.append([(d * cosine, t, f, v, x, y) for d, t, f, v, x, y in low])
    return hits, obstacles
