"""Player state — the camera the whole renderer works from."""

import math

import pygame

from src import settings, world


class Player:
    """Position in world units and view angle in radians, angle 0 pointing along +x."""

    def __init__(self, x, y, angle=0.0):
        self.x = x
        self.y = y
        self.angle = angle
        self.z = settings.EYE_HEIGHT
        self.velocity_z = 0.0
        self.grounded = True

    @property
    def direction(self):
        """Unit forward vector (cos, sin) for the current angle."""
        return math.cos(self.angle), math.sin(self.angle)

    def jump(self):
        """Launch the eye upward; ignored while a jump is already in the air."""
        if self.grounded:
            self.velocity_z = settings.JUMP_SPEED
            self.grounded = False

    def _apply_gravity(self, dt):
        """Integrate the jump arc, landing back exactly on standing height.

        Gravity is constant, so the half-a-t-squared term makes this exact rather than
        approximate: the arc peaks at the same height whatever the frame rate.
        """
        if self.grounded:
            return
        self.z += self.velocity_z * dt - 0.5 * settings.GRAVITY * dt * dt
        self.velocity_z -= settings.GRAVITY * dt
        if self.z <= settings.EYE_HEIGHT:
            self.z = settings.EYE_HEIGHT
            self.velocity_z = 0.0
            self.grounded = True

    def turn(self, delta):
        """Rotate the view by delta radians, kept wrapped into [0, 2*pi)."""
        self.angle = (self.angle + delta) % math.tau

    def update(self, keys, mouse_dx, dt):
        """Turn, jump and walk for one frame of dt seconds, driven by the mouse and held keys."""
        if mouse_dx:
            # a mouse delta is already a displacement, not a rate, so dt must not scale it
            self.turn(mouse_dx * settings.MOUSE_SENSITIVITY)

        turn = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        if turn:
            self.turn(turn * settings.ROTATION_SPEED * dt)

        if keys[pygame.K_SPACE]:
            self.jump()
        self._apply_gravity(dt)

        forward = keys[pygame.K_w] - keys[pygame.K_s]
        strafe = keys[pygame.K_d] - keys[pygame.K_a]
        if not (forward or strafe):
            return

        dir_x, dir_y = self.direction
        move_x = dir_x * forward - dir_y * strafe
        move_y = dir_y * forward + dir_x * strafe
        length = math.hypot(move_x, move_y)
        if length > 1.0:  # walking and strafing at once must not outrun either alone
            move_x /= length
            move_y /= length

        step = settings.MOVE_SPEED * dt
        self._walk(move_x * step, move_y * step)

    def _walk(self, move_x, move_y):
        """Move one axis at a time, so a blocked direction still slides along the wall."""
        radius = settings.PLAYER_RADIUS
        if move_x:
            edge = self.x + move_x + math.copysign(radius, move_x)
            if not world.is_wall(edge, self.y - radius) and not world.is_wall(edge, self.y + radius):
                self.x += move_x
        if move_y:
            edge = self.y + move_y + math.copysign(radius, move_y)
            if not world.is_wall(self.x - radius, edge) and not world.is_wall(self.x + radius, edge):
                self.y += move_y
