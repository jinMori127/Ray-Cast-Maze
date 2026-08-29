"""Projection of ray hits into the first-person view — one vertical strip per column.

Drawing goes into a low-resolution numpy buffer indexed [x, y, channel], matching
pygame.surfarray's column-major layout so a screen column is one contiguous slice.
The buffer is blown up to the window once per frame by present().
"""

import math

import numpy as np
import pygame

from src import raycaster, settings

HORIZON = settings.RENDER_HEIGHT // 2
# distance to the projection plane in rendered pixels, so both axes share one perspective scale
WALL_SCALE = settings.RENDER_WIDTH / (2 * settings.PLANE_HALF_WIDTH)
MIN_DISTANCE = 1e-4  # keeps the perspective divide finite when a wall face touches the camera

use_mipmaps = True  # toggled at runtime so the minification shimmer can be seen both ways

pixels = np.zeros((settings.RENDER_WIDTH, settings.RENDER_HEIGHT, 3), np.uint8)
_ROW_CENTERS = np.arange(settings.RENDER_HEIGHT, dtype=np.float64) + 0.5
_FOG_RGB = np.array(settings.FOG_COLOR, np.float64)
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


def mip_level(levels, strip_height):
    """Pick the level whose texels land about one per screen pixel.

    tex_height / strip_height is texels per pixel — the minification factor — and halving
    the texture once removes one power of two from it, so its log2 is the level wanted.
    """
    if not use_mipmaps:
        return 0
    texels_per_pixel = levels[0].shape[1] / strip_height
    return min(int(math.log2(max(1.0, texels_per_pixel))), len(levels) - 1)


def draw_background():
    """Flat ceiling above the horizon, flat floor below it."""
    pixels[:, :HORIZON] = settings.CEILING_COLOR
    pixels[:, HORIZON:] = settings.FLOOR_COLOR


def draw_world(hits, textures):
    """Ceiling and floor, then one lit, fogged, textured wall strip per ray hit."""
    draw_background()
    for column, (_, _, perp_dist, tile, facing, u, _, _) in enumerate(hits):
        levels = textures[tile]

        # the strip is never clamped: a wall taller than the screen must crop, not squash,
        # or its texels would compress as you walk into it instead of magnifying
        strip_height = WALL_SCALE / max(perp_dist, MIN_DISTANCE)
        top = HORIZON - strip_height / 2
        first = max(0, math.ceil(top))
        last = min(settings.RENDER_HEIGHT, math.ceil(top + strip_height))
        if first >= last:
            continue

        texture = levels[mip_level(levels, strip_height)]
        tex_width, tex_height = texture.shape[0], texture.shape[1]
        texel_column = texture[min(int(u * tex_width), tex_width - 1)]
        rows = (_ROW_CENTERS[first:last] - top) * (tex_height / strip_height)
        texels = texel_column[np.minimum(rows.astype(np.intp), tex_height - 1)]

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
