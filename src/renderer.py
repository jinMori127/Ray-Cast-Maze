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
NS_FACE_SHADE = 0.7  # the two face orientations meet a fixed light at different angles

pixels = np.zeros((settings.RENDER_WIDTH, settings.RENDER_HEIGHT, 3), np.uint8)
_ROW_CENTERS = np.arange(settings.RENDER_HEIGHT, dtype=np.float64) + 0.5
_upscale_source = None  # built on first present, once a display mode exists


def shade(color, side):
    """Flat shading — one fixed intensity per face orientation, N/S darker than E/W."""
    if side != raycaster.SIDE_NS:
        return color
    red, green, blue = color
    return int(red * NS_FACE_SHADE), int(green * NS_FACE_SHADE), int(blue * NS_FACE_SHADE)


def fog(color, perp_dist):
    """Blend a colour toward FOG_COLOR by the exponential factor f = e^(-distance * density)."""
    visibility = math.exp(-perp_dist * settings.FOG_DENSITY)
    haze = 1.0 - visibility
    fog_red, fog_green, fog_blue = settings.FOG_COLOR
    red, green, blue = color
    return (
        int(min(255.0, max(0.0, haze * fog_red + visibility * red))),
        int(min(255.0, max(0.0, haze * fog_green + visibility * green))),
        int(min(255.0, max(0.0, haze * fog_blue + visibility * blue))),
    )


def draw_background():
    """Flat ceiling above the horizon, flat floor below it."""
    pixels[:, :HORIZON] = settings.CEILING_COLOR
    pixels[:, HORIZON:] = settings.FLOOR_COLOR


def draw_world(hits, textures):
    """Ceiling and floor, then one textured wall strip per ray hit."""
    draw_background()
    for column, (_, _, perp_dist, tile, _, u, _, _) in enumerate(hits):
        texture = textures[tile]
        tex_width, tex_height = texture.shape[0], texture.shape[1]

        # the strip is never clamped: a wall taller than the screen must crop, not squash,
        # or its texels would compress as you walk into it instead of magnifying
        strip_height = WALL_SCALE / max(perp_dist, MIN_DISTANCE)
        top = HORIZON - strip_height / 2
        first = max(0, math.ceil(top))
        last = min(settings.RENDER_HEIGHT, math.ceil(top + strip_height))
        if first >= last:
            continue

        texel_column = texture[min(int(u * tex_width), tex_width - 1)]
        rows = (_ROW_CENTERS[first:last] - top) * (tex_height / strip_height)
        pixels[column, first:last] = texel_column[np.minimum(rows.astype(np.intp), tex_height - 1)]


def present(screen):
    """Upscale the render buffer into the window."""
    global _upscale_source
    if _upscale_source is None:
        _upscale_source = pygame.Surface((settings.RENDER_WIDTH, settings.RENDER_HEIGHT))
    pygame.surfarray.blit_array(_upscale_source, pixels)
    pygame.transform.scale(_upscale_source, screen.get_size(), screen)
