"""Player state — the camera the whole renderer works from."""

import math


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
