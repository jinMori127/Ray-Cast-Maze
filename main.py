import pygame

from src import minimap, raycaster, renderer, settings, world
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
        self.debug_view = False

    def handle_events(self):
        """Drain the event queue and set the quit flag."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_TAB:
                    self.debug_view = not self.debug_view

    def update(self):
        """Advance the world by self.dt seconds."""
        self.player.update(pygame.key.get_pressed(), self.dt)

    def draw(self):
        """Compose the frame and present it."""
        hits = raycaster.cast_all(self.player)
        if self.debug_view:
            minimap.draw(self.screen, self.player, self.debug_scale, hits)
        else:
            renderer.draw_world(self.screen, hits)
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
