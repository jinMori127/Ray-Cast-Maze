"""Player state — the camera the whole renderer works from."""

import math

import pygame

from src import settings


class Player:
    """Position in world units and view angle in radians, angle 0 pointing along +x."""

    def __init__(self, x, y, angle=0.0):
        self.x = x
        self.y = y
        self.angle = angle

    @property
    def direction(self):
        """Unit forward vector (cos, sin) for the current angle."""
        return math.cos(self.angle), math.sin(self.angle)

    def turn(self, delta):
        """Rotate the view by delta radians, kept wrapped into [0, 2*pi)."""
        self.angle = (self.angle + delta) % math.tau

    def update(self, keys, dt):
        """Turn and walk for one frame of dt seconds, driven by the current key state."""
        turn = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        if turn:
            self.turn(turn * settings.ROTATION_SPEED * dt)

        forward = keys[pygame.K_w] - keys[pygame.K_s]
        strafe = keys[pygame.K_e] - keys[pygame.K_q]
        if not (forward or strafe):
            return

        dir_x, dir_y = self.direction
        move_x = dir_x * forward - dir_y * strafe
        move_y = dir_y * forward + dir_x * strafe
        length = math.hypot(move_x, move_y)
        if length > 1.0:  # walking and strafing at once must not outrun either alone
            move_x /= length
            move_y /= length

        self.x += move_x * settings.MOVE_SPEED * dt
        self.y += move_y * settings.MOVE_SPEED * dt
