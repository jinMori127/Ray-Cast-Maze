"""Projection of ray hits into the first-person view — one vertical strip per column.

Drawing goes into a low-resolution numpy buffer indexed [x, y, channel], matching
pygame.surfarray's column-major layout so a screen column is one contiguous slice.
The buffer is blown up to the window once per frame by present().
"""

import math

import numpy as np
import pygame

from src import raycaster, settings, textures

HORIZON = settings.RENDER_HEIGHT // 2
# distance to the projection plane in rendered pixels, so both axes share one perspective scale
WALL_SCALE = settings.RENDER_WIDTH / (2 * settings.PLANE_HALF_WIDTH)
MIN_DISTANCE = 1e-4  # keeps the perspective divide finite when a wall face touches the camera
CAMERA_HEIGHT = 0.5  # eye sits at mid-wall, which is what puts a wall's base on the horizon line
FLOOR_SCALE = WALL_SCALE * CAMERA_HEIGHT  # numerator of the row-distance inversion

use_mipmaps = True  # toggled at runtime so the minification shimmer can be seen both ways
use_bilinear = False  # nearest by default, keeping the blocky look these textures were drawn for

pixels = np.zeros((settings.RENDER_WIDTH, settings.RENDER_HEIGHT, 3), np.uint8)
_ROW_CENTERS = np.arange(settings.RENDER_HEIGHT, dtype=np.float64) + 0.5
_FOG_RGB = np.array(settings.FOG_COLOR, np.float64)
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


def draw_ceiling():
    """Flat colour above the horizon."""
    pixels[:, :HORIZON] = settings.CEILING_COLOR


def draw_floor(player, floor_texture):
    """Invert the projection row by row and sample the world line each row looks along."""
    dir_x, dir_y = player.direction
    plane_x = -dir_y * settings.PLANE_HALF_WIDTH
    plane_y = dir_x * settings.PLANE_HALF_WIDTH
    size = floor_texture.shape[0]

    for row in range(HORIZON, settings.RENDER_HEIGHT):
        distance = FLOOR_SCALE / (row + 0.5 - HORIZON)
        world_x = player.x + distance * (dir_x + _COLUMN_T * plane_x)
        world_y = player.y + distance * (dir_y + _COLUMN_T * plane_y)
        tex_x = np.floor(world_x * size).astype(np.intp) % size
        tex_y = np.floor(world_y * size).astype(np.intp) % size
        pixels[:, row] = floor_texture[tex_x, tex_y]


def draw_world(player, hits, wall_textures, floor_texture):
    """Ceiling, cast floor, then one lit, fogged, textured wall strip per ray hit."""
    draw_ceiling()
    draw_floor(player, floor_texture)
    sample = textures.sample_bilinear if use_bilinear else textures.sample_nearest
    for column, (_, _, perp_dist, tile, facing, u, _, _) in enumerate(hits):
        levels = wall_textures[tile]

        # the strip is never clamped: a wall taller than the screen must crop, not squash,
        # or its texels would compress as you walk into it instead of magnifying
        strip_height = WALL_SCALE / max(perp_dist, MIN_DISTANCE)
        top = HORIZON - strip_height / 2
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
        pixels[column, first:last] = lit.astype(np.uint8)


def present(screen):
    """Upscale the render buffer into the window."""
    global _upscale_source
    if _upscale_source is None:
        _upscale_source = pygame.Surface((settings.RENDER_WIDTH, settings.RENDER_HEIGHT))
    pygame.surfarray.blit_array(_upscale_source, pixels)
    pygame.transform.scale(_upscale_source, screen.get_size(), screen)
