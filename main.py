import pygame

from src import minimap, raycaster, settings, world
from src.player import Player


class Game:
    """Window, timing and the top-level frame loop."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption(settings.CAPTION)
        self.clock = pygame.time.Clock()
        self.dt = 0.0
        self.running = True
        self.player = Player(*world.SPAWN, world.SPAWN_ANGLE)
        self.debug_scale = minimap.fit_scale(self.screen)

    def handle_events(self):
        """Drain the event queue and set the quit flag."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def update(self):
        """Advance the world by self.dt seconds."""
        keys = pygame.key.get_pressed()
        turn = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        if turn:
            self.player.turn(turn * settings.ROTATION_SPEED * self.dt)

    def draw(self):
        """Compose the frame and present it."""
        hits = raycaster.cast_all(self.player)
        minimap.draw(self.screen, self.player, self.debug_scale, hits)
        pygame.display.flip()

    def run(self):
        """Run until the quit flag drops, capped at settings.FPS."""
        while self.running:
            self.dt = self.clock.tick(settings.FPS) / 1000.0
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
