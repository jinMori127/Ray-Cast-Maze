"""Level select — the screen between runs: start an unlocked level, or quit."""

import math

import pygame

from src import progress, settings
from src.levels import LEVELS

QUIT = -1  # pick() returns this rather than a level index

CLEARED, OPEN, LOCKED = 0, 1, 2

CARD_FILL = {
    CLEARED: settings.MENU_CARD_CLEARED_COLOR,
    OPEN: settings.MENU_CARD_OPEN_COLOR,
    LOCKED: settings.MENU_CARD_LOCKED_COLOR,
}
CARD_EDGE = {
    CLEARED: settings.MENU_CARD_CLEARED_EDGE_COLOR,
    OPEN: settings.MENU_CARD_EDGE_COLOR,
    LOCKED: settings.MENU_CARD_LOCKED_EDGE_COLOR,
}
CARD_TEXT = {
    CLEARED: settings.MENU_TEXT_COLOR,
    OPEN: settings.MENU_TEXT_COLOR,
    LOCKED: settings.MENU_MUTED_COLOR,
}
CARD_STATUS = {CLEARED: settings.MENU_CLEARED_TEXT, OPEN: settings.MENU_OPEN_TEXT, LOCKED: ""}
CARD_STATUS_COLOR = {
    CLEARED: settings.MENU_CARD_CLEARED_EDGE_COLOR,
    OPEN: settings.MENU_MUTED_COLOR,
    LOCKED: settings.MENU_MUTED_COLOR,
}

NUMBER_OFFSET = 58  # from a card's top down to the centre of its number or padlock
NAME_OFFSET = 118
STATUS_OFFSET = 28  # from a card's bottom up to the centre of its status line


def _card_rects():
    """One rect per level, laid out as a row centred on the screen."""
    width, height = settings.MENU_CARD_SIZE
    stride = width + settings.MENU_CARD_GAP
    span = len(LEVELS) * stride - settings.MENU_CARD_GAP
    left = (settings.SCREEN_WIDTH - span) // 2
    return tuple(
        pygame.Rect(left + index * stride, settings.MENU_CARD_TOP, width, height)
        for index in range(len(LEVELS))
    )


CARD_RECTS = _card_rects()
QUIT_RECT = pygame.Rect(0, 0, *settings.MENU_BUTTON_SIZE)
QUIT_RECT.midtop = (settings.SCREEN_WIDTH // 2, settings.MENU_BUTTON_TOP)

_fonts = None


def _font_set():
    """Title, number, name and status fonts, built on the first frame that draws the menu."""
    global _fonts
    if _fonts is None:
        _fonts = (
            pygame.font.SysFont(settings.HUD_FONT_NAME, settings.MENU_TITLE_SIZE, bold=True),
            pygame.font.SysFont(settings.HUD_FONT_NAME, settings.MENU_NUMBER_SIZE, bold=True),
            pygame.font.SysFont(settings.HUD_FONT_NAME, settings.MENU_NAME_SIZE),
            pygame.font.SysFont(settings.HUD_FONT_NAME, settings.MENU_STATUS_SIZE),
        )
    return _fonts


def _state(index, cleared, open_levels):
    """Whether a level is already beaten, open to play, or still locked."""
    if index < cleared:
        return CLEARED
    return OPEN if index < open_levels else LOCKED


def pick(pos, cleared):
    """What sits under the pointer: a level index, QUIT, or None for empty space."""
    if QUIT_RECT.collidepoint(pos):
        return QUIT
    open_levels = progress.unlocked(cleared)
    for index, rect in enumerate(CARD_RECTS):
        if index < open_levels and rect.collidepoint(pos):
            return index
    return None


def locked_at(pos, cleared):
    """True when the pointer is over a level card that has not been unlocked yet."""
    open_levels = progress.unlocked(cleared)
    return any(index >= open_levels and rect.collidepoint(pos)
               for index, rect in enumerate(CARD_RECTS))


def draw(surface, cleared, pointer):
    """Title, one card per level, the quit button and the hint line."""
    title_font, number_font, name_font, status_font = _font_set()
    open_levels = progress.unlocked(cleared)

    surface.fill(settings.MENU_BACKGROUND_COLOR)
    _blit(surface, title_font, settings.CAPTION.upper(), settings.MENU_TITLE_COLOR,
          midtop=(settings.SCREEN_WIDTH // 2, settings.MENU_TITLE_Y))

    fonts = (number_font, name_font, status_font)
    for index, rect in enumerate(CARD_RECTS):
        _draw_card(surface, index, rect, _state(index, cleared, open_levels), pointer, fonts)

    _draw_button(surface, QUIT_RECT, settings.MENU_QUIT_TEXT, status_font, pointer)
    _blit(surface, status_font, settings.MENU_HINT, settings.MENU_MUTED_COLOR,
          midtop=(settings.SCREEN_WIDTH // 2, settings.MENU_HINT_Y))


def _draw_card(surface, index, rect, state, pointer, fonts):
    """One level tile: its number and status when open, a padlock when it is not."""
    number_font, name_font, status_font = fonts
    hovered = state != LOCKED and rect.collidepoint(pointer)
    color = CARD_TEXT[state]

    fill = settings.MENU_CARD_HOVER_COLOR if hovered else CARD_FILL[state]
    pygame.draw.rect(surface, fill, rect, border_radius=settings.MENU_CARD_RADIUS)
    pygame.draw.rect(surface, CARD_EDGE[state], rect, 2, border_radius=settings.MENU_CARD_RADIUS)

    head = (rect.centerx, rect.top + NUMBER_OFFSET)
    if state == LOCKED:
        _draw_lock(surface, head, settings.MENU_LOCK_SIZE, color)
    else:
        _blit(surface, number_font, str(index + 1), color, center=head)

    _blit(surface, name_font, LEVELS[index].name, color, center=(rect.centerx, rect.top + NAME_OFFSET))
    if CARD_STATUS[state]:
        _blit(surface, status_font, CARD_STATUS[state], CARD_STATUS_COLOR[state],
              center=(rect.centerx, rect.bottom - STATUS_OFFSET))


def _draw_lock(surface, center, size, color):
    """A padlock glyph: a shackle arc, then the body painted over its ends."""
    body = pygame.Rect(0, 0, size, round(size * 0.72))
    body.midbottom = (center[0], center[1] + round(size * 0.42))
    shackle = pygame.Rect(0, 0, round(size * 0.60), round(size * 0.60))
    shackle.midbottom = (center[0], body.top + round(size * 0.12))
    pygame.draw.arc(surface, color, shackle, 0.0, math.pi, max(2, size // 9))
    pygame.draw.rect(surface, color, body, border_radius=max(2, size // 7))


def _draw_button(surface, rect, label, font, pointer):
    """A labelled rectangle that lights up under the pointer."""
    fill = settings.MENU_CARD_HOVER_COLOR if rect.collidepoint(pointer) else settings.MENU_CARD_OPEN_COLOR
    pygame.draw.rect(surface, fill, rect, border_radius=settings.MENU_CARD_RADIUS)
    pygame.draw.rect(surface, settings.MENU_CARD_EDGE_COLOR, rect, 2, border_radius=settings.MENU_CARD_RADIUS)
    _blit(surface, font, label, settings.MENU_TEXT_COLOR, center=rect.center)


def _blit(surface, font, text, color, **anchor):
    """Render one line of text and place it by a pygame.Rect keyword anchor."""
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(**anchor))
