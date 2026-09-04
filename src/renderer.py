"""Projection of ray hits into the first-person view — one vertical strip per column.

Drawing goes into a low-resolution numpy buffer indexed [x, y, channel], matching
pygame.surfarray's column-major layout so a screen column is one contiguous slice.
The buffer is blown up to the window once per frame by present().
"""

import math

import numpy as np
import pygame

from src import raycaster, settings, textures, world

HORIZON = settings.RENDER_HEIGHT // 2
# distance to the projection plane in rendered pixels, so both axes share one perspective scale
WALL_SCALE = settings.RENDER_WIDTH / (2 * settings.PLANE_HALF_WIDTH)
MIN_DISTANCE = 1e-4  # keeps the perspective divide finite when a wall face touches the camera
# Eye height is player.z, so both projections below take it per frame rather than as a constant:
# the horizon never moves with height, only the rate at which the floor and wall tops climb to it.

use_mipmaps = True  # toggled at runtime so the minification shimmer can be seen both ways
use_bilinear = False  # nearest by default, keeping the blocky look these textures were drawn for

pixels = np.zeros((settings.RENDER_WIDTH, settings.RENDER_HEIGHT, 3), np.uint8)
_ROW_CENTERS = np.arange(settings.RENDER_HEIGHT, dtype=np.float64) + 0.5
_FOG_RGB = np.array(settings.FOG_COLOR, np.float64)
_GOAL_LIGHT_RGB = np.array(settings.GOAL_LIGHT_COLOR, np.float64)
_COLUMN_T = 2.0 * (np.arange(settings.RENDER_WIDTH) + 0.5) / settings.RENDER_WIDTH - 1.0
_upscale_source = None  # built on first present, once a display mode exists


def shade(normal):
    """Lambert's cosine law for one face: ambient plus diffuse scaled by max(0, l.n)."""
    light_x, light_y = settings.LIGHT_DIRECTION
    lambert = max(0.0, light_x * normal[0] + light_y * normal[1])
    return min(1.0, settings.AMBIENT_LIGHT + settings.DIFFUSE_LIGHT * lambert)


# Flat shading means one intensity per face orientation, and the grid only ever presents
# four, so the cosine law is evaluated once here instead of per column.
FACE_INTENSITY = tuple(shade(normal) for normal in raycaster.FACE_NORMALS)


def toggle_mipmaps():
    """Flip mip selection; returns the new state so the caller can report it."""
    global use_mipmaps
    use_mipmaps = not use_mipmaps
    return use_mipmaps


def toggle_bilinear():
    """Flip between nearest and bilinear sampling; returns the new state."""
    global use_bilinear
    use_bilinear = not use_bilinear
    return use_bilinear


def mip_level(levels, strip_height):
    """Pick the level whose texels land about one per screen pixel.

    tex_height / strip_height is texels per pixel — the minification factor — and halving
    the texture once removes one power of two from it, so its log2 is the level wanted.
    """
    if not use_mipmaps:
        return 0
    texels_per_pixel = levels[0].shape[1] / strip_height
    return min(int(math.log2(max(1.0, texels_per_pixel))), len(levels) - 1)


def goal_light_on_floor(world_x, world_y, goal_x, goal_y):
    """Falloff squared to zero at GOAL_LIGHT_RANGE, so the pool has an edge instead of a tail."""
    offset_x = world_x - goal_x
    offset_y = world_y - goal_y
    fade = 1.0 - np.sqrt(offset_x * offset_x + offset_y * offset_y) / settings.GOAL_LIGHT_RANGE
    np.clip(fade, 0.0, 1.0, out=fade)
    return fade * fade


def goal_light_on_face(hit_x, hit_y, facing, goal_x, goal_y):
    """The same falloff times Lambert, so a face turned away from the exit stays unlit.

    That cosine is what keeps the beacon from bleeding through walls: the only faces angled
    toward the goal cell are the ones that enclose it, which are exactly the ones you see
    when you look at the exit.
    """
    offset_x = goal_x - hit_x
    offset_y = goal_y - hit_y
    distance = math.hypot(offset_x, offset_y)
    fade = 1.0 - distance / settings.GOAL_LIGHT_WALL_RANGE
    if fade <= 0.0:
        return 0.0
    normal_x, normal_y = raycaster.FACE_NORMALS[facing]
    lambert = (normal_x * offset_x + normal_y * offset_y) / distance
    return fade * fade * lambert if lambert > 0.0 else 0.0


def draw_ceiling():
    """Flat colour above the horizon."""
    pixels[:, :HORIZON] = settings.CEILING_COLOR


def draw_floor(player, floor_texture):
    """Invert the projection row by row and sample the world line each row looks along."""
    dir_x, dir_y = player.direction
    plane_x = -dir_y * settings.PLANE_HALF_WIDTH
    plane_y = dir_x * settings.PLANE_HALF_WIDTH
    size = floor_texture.shape[0]

    # a row can only hold lit floor when its own distance is within the light's reach of the
    # goal's, by the triangle inequality — so most rows skip the pool with one scalar test
    goal_x, goal_y = world.GOAL
    goal_distance = math.hypot(goal_x - player.x, goal_y - player.y)
    nearest_lit = goal_distance - settings.GOAL_LIGHT_RANGE
    farthest_lit = goal_distance + settings.GOAL_LIGHT_RANGE

    floor_scale = WALL_SCALE * player.z  # a jump raises the eye, so each row sees further out
    for row in range(HORIZON, settings.RENDER_HEIGHT):
        distance = floor_scale / (row + 0.5 - HORIZON)
        world_x = player.x + distance * (dir_x + _COLUMN_T * plane_x)
        world_y = player.y + distance * (dir_y + _COLUMN_T * plane_y)
        tex_x = np.floor(world_x * size).astype(np.intp) % size
        tex_y = np.floor(world_y * size).astype(np.intp) % size
        if not nearest_lit <= distance <= farthest_lit:
            pixels[:, row] = floor_texture[tex_x, tex_y]
            continue
        glow = goal_light_on_floor(world_x, world_y, goal_x, goal_y)
        lit = floor_texture[tex_x, tex_y] + _GOAL_LIGHT_RGB * glow[:, None]
        pixels[:, row] = np.clip(lit, 0.0, 255.0).astype(np.uint8)


def draw_world(player, hits, wall_textures, floor_texture):
    """Ceiling, cast floor, then one lit, fogged, textured wall strip per ray hit."""
    draw_ceiling()
    draw_floor(player, floor_texture)
    goal_x, goal_y = world.GOAL
    sample = textures.sample_bilinear if use_bilinear else textures.sample_nearest
    for column, (_, _, perp_dist, tile, facing, u, hit_x, hit_y) in enumerate(hits):
        levels = wall_textures[tile]

        # the strip is never clamped: a wall taller than the screen must crop, not squash,
        # or its texels would compress as you walk into it instead of magnifying
        strip_height = WALL_SCALE / max(perp_dist, MIN_DISTANCE)
        # the wall's top (world height 1) projects to HORIZON + WALL_SCALE * (z - 1) / d, so
        # raising the eye slides the whole strip down the screen without resizing it
        top = HORIZON + strip_height * (player.z - 1.0)
        first = max(0, math.ceil(top))
        last = min(settings.RENDER_HEIGHT, math.ceil(top + strip_height))
        if first >= last:
            continue

        texture = levels[mip_level(levels, strip_height)]
        rows = (_ROW_CENTERS[first:last] - top) * (texture.shape[1] / strip_height)
        texels = sample(texture, u, rows)

        # one multiply-add lights the texel and blends it toward the fog: both the face
        # intensity and the fog factor are scalars, so the whole strip is done at once
        visibility = math.exp(-perp_dist * settings.FOG_DENSITY)
        lit = texels * (FACE_INTENSITY[facing] * visibility) + _FOG_RGB * (1.0 - visibility)

        # the beacon is added after the fog blend and fogged at its own gentler rate, so it
        # still reads from the far end of a corridor the walls have already faded out of
        glow = goal_light_on_face(hit_x, hit_y, facing, goal_x, goal_y)
        if glow:
            lit = lit + _GOAL_LIGHT_RGB * (glow * visibility ** settings.GOAL_LIGHT_FOG_RESISTANCE)
            np.clip(lit, 0.0, 255.0, out=lit)
        pixels[column, first:last] = lit.astype(np.uint8)


def present(screen):
    """Upscale the render buffer into the window."""
    global _upscale_source
    if _upscale_source is None:
        _upscale_source = pygame.Surface((settings.RENDER_WIDTH, settings.RENDER_HEIGHT))
    pygame.surfarray.blit_array(_upscale_source, pixels)
    pygame.transform.scale(_upscale_source, screen.get_size(), screen)
