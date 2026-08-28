import pygame

import settings


class Game:
    """Window, timing and the top-level frame loop."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption(settings.CAPTION)
        self.clock = pygame.time.Clock()
        self.dt = 0.0
        self.running = True

    def handle_events(self):
        """Drain the event queue and set the quit flag."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def update(self):
        """Advance the world by self.dt seconds."""

    def draw(self):
        """Compose the frame and present it."""
        self.screen.fill(settings.CEILING_COLOR)
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
