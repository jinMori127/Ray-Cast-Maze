"""Procedural wall textures — 64x64 numpy arrays built once at startup.

Arrays are indexed [x, y] to match pygame.surfarray's column-major layout, so a wall
strip is one contiguous slice: texture[column] is every texel down that column.
"""

import os

import numpy as np
import pygame

from src import settings

TEXTURE_SIZE = 64
MIN_MIP_SIZE = 8  # smallest level in the pyramid, so 64 -> 32 -> 16 -> 8
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
ASSET_SUFFIXES = (".png", ".bmp", ".jpg")

BRICK_COURSES = 8  # brick rows down the texture
BRICK_PER_COURSE = 4
STONE_BLOCKS = 2  # ashlar blocks are far larger than bricks, so the two never look alike
CHECKER_CELLS = 8
JOINT_THICKNESS = 2  # mortar / joint width in texels


def _scale(color, factor):
    """Multiply a colour by a factor, clamped into 0..255."""
    return tuple(min(255, max(0, int(channel * factor))) for channel in color)


def _hash01(a, b):
    """Deterministic pseudo-random value in [0, 1) for a pair of non-negative integers."""
    mixed = (a * 73856093) ^ (b * 19349663)
    return ((mixed * 2654435761) % 4294967296) / 4294967296


def _masonry(size, base, blocks, joint_shade, tone_spread, grain_spread):
    """Offset courses of blocks separated by joints — the shared skeleton of brick and stone."""
    texture = np.empty((size, size, 3), np.uint8)
    course_height = size // blocks[0]
    block_width = size // blocks[1]
    joint = _scale(base, joint_shade)
    for y in range(size):
        course = y // course_height
        offset = (course % 2) * (block_width // 2)
        on_joint_row = y % course_height < JOINT_THICKNESS
        for x in range(size):
            shifted = x + offset
            if on_joint_row or shifted % block_width < JOINT_THICKNESS:
                texture[x, y] = joint
                continue
            tone = 1.0 - tone_spread + 2 * tone_spread * _hash01(course, shifted // block_width)
            grain = 1.0 - grain_spread + 2 * grain_spread * _hash01(x, y)
            texture[x, y] = _scale(base, tone * grain)
    return texture


def make_brick(size=TEXTURE_SIZE, base=(150, 96, 68)):
    """Running-bond brick: small courses, each offset half a brick from the one above."""
    return _masonry(size, base, (BRICK_COURSES, BRICK_PER_COURSE), 0.45, 0.14, 0.03)


def make_stone(size=TEXTURE_SIZE, base=(104, 116, 138)):
    """Ashlar masonry: a few large blocks with heavy grain, deliberately coarser than brick."""
    return _masonry(size, base, (STONE_BLOCKS, STONE_BLOCKS), 0.55, 0.10, 0.07)


def make_checker(size=TEXTURE_SIZE, base=(176, 138, 70)):
    """Two-tone checkerboard — the pattern that makes any texture-mapping error obvious."""
    texture = np.empty((size, size, 3), np.uint8)
    cell = size // CHECKER_CELLS
    light, dark = _scale(base, 1.0), _scale(base, 0.55)
    for y in range(size):
        for x in range(size):
            texture[x, y] = light if (x // cell + y // cell) % 2 == 0 else dark
    return texture


def _halve(level):
    """Box-filter a level to half size: each texel is the average of a 2x2 block above it."""
    wide = level.astype(np.uint16)
    averaged = wide[0::2, 0::2] + wide[1::2, 0::2] + wide[0::2, 1::2] + wide[1::2, 1::2]
    return ((averaged + 2) // 4).astype(np.uint8)  # +2 rounds to nearest rather than truncating


def build_mipmaps(texture):
    """Pyramid of pre-filtered copies, level 0 full size and each level half the one above.

    A distant wall squeezes many texels into one pixel, and picking just one of them makes
    the choice depend on sub-pixel alignment — that is the shimmer. Averaging the texels in
    advance means the pixel gets all of them however the sample lands.
    """
    levels = [texture]
    while levels[-1].shape[0] > MIN_MIP_SIZE:
        levels.append(_halve(levels[-1]))
    return tuple(levels)


GENERATORS = {1: make_brick, 2: make_stone, 3: make_checker}
ASSET_NAMES = {1: "brick", 2: "stone", 3: "checker"}


def _load_asset(name, size):
    """Return assets/<name>.<ext> as an [x, y] rgb array, or None when no such file exists."""
    for suffix in ASSET_SUFFIXES:
        path = os.path.join(ASSETS_DIR, name + suffix)
        if not os.path.isfile(path):
            continue
        surface = pygame.image.load(path)
        if surface.get_size() != (size, size):
            surface = pygame.transform.smoothscale(surface, (size, size))
        return pygame.surfarray.array3d(surface)
    return None


def load_textures(size=TEXTURE_SIZE):
    """Every wall id mapped to its mip pyramid, preferring a file in assets/ over the generator."""
    textures = {}
    for tile, generator in GENERATORS.items():
        from_disk = _load_asset(ASSET_NAMES[tile], size)
        full = from_disk if from_disk is not None else generator(size, settings.WALL_COLORS[tile])
        textures[tile] = build_mipmaps(full)
    return textures


def to_surface(texture):
    """Wrap a texture array in a Surface, for preview blits and debugging."""
    return pygame.surfarray.make_surface(texture)
