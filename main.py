import pygame

from src import minimap, raycaster, renderer, settings, textures, world
from src.player import Player


class Game:
    """Window, timing and the top-level frame loop."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption(settings.CAPTION)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(settings.HUD_FONT_NAME, settings.HUD_FONT_SIZE)
        self.banner_font = pygame.font.SysFont(settings.HUD_FONT_NAME, settings.BANNER_FONT_SIZE, bold=True)
        self.dim = pygame.Surface(self.screen.get_size()).convert()
        self.dim.fill(settings.BANNER_DIM_COLOR)
        self.dim.set_alpha(settings.BANNER_DIM_ALPHA)
        self.dt = 0.0
        self.running = True
        self.textures = textures.load_textures()
        self.floor_texture = textures.load_floor()
        self.debug_view = False
        self.minimap_visible = True
        self.mouse_dx = 0
        self.grab_mouse()
        self.restart()

    def grab_mouse(self):
        """Hide and confine the pointer so it reports unbounded turning motion."""
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        try:
            pygame.mouse.set_relative_mode(True)
        except pygame.error:
            pass  # driver without relative mode — the grab alone still delivers motion

    def handle_events(self):
        """Drain the event queue, collecting this frame's mouse turn and setting the quit flag."""
        self.mouse_dx = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_dx += event.rel[0]
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_TAB:
                    self.debug_view = not self.debug_view
                elif event.key == pygame.K_b:
                    renderer.toggle_bilinear()
                elif event.key == pygame.K_l:
                    renderer.toggle_mipmaps()
                elif event.key == pygame.K_m:
                    self.minimap_visible = not self.minimap_visible
                elif event.key == pygame.K_r:
                    self.restart()

    def restart(self):
        """Put the player back on the spawn tile and open the run again."""
        self.player = Player(*world.SPAWN, world.SPAWN_ANGLE)
        self.won = False

    def update(self):
        """Advance the world by self.dt seconds; an escaped player is frozen where they stand."""
        if self.won:
            return
        self.player.update(pygame.key.get_pressed(), self.mouse_dx, self.dt)
        self.won = world.at_goal(self.player.x, self.player.y)

    def draw(self):
        """Compose the frame and present it."""
        hits = raycaster.cast_all(self.player)
        if self.debug_view:
            minimap.draw_debug(self.screen, self.player, hits)
        else:
            renderer.draw_world(self.player, hits, self.textures, self.floor_texture)
            renderer.present(self.screen)
            if self.minimap_visible:
                minimap.draw_overlay(self.screen, self.player, hits)
        if self.won:
            self.draw_banner()
        self.draw_fps()
        pygame.display.flip()

    def draw_banner(self):
        """Fade the frozen frame down and centre the end-of-run message on it."""
        self.screen.blit(self.dim, (0, 0))
        message = self.banner_font.render(settings.WIN_TEXT, True, settings.BANNER_COLOR)
        hint = self.font.render(settings.WIN_HINT, True, settings.HUD_COLOR)
        message_rect = message.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(message, message_rect)
        self.screen.blit(hint, hint.get_rect(midtop=(message_rect.centerx, message_rect.bottom + settings.BANNER_GAP)))

    def draw_fps(self):
        """Blit the rolling frame rate into the top-left corner, one decimal."""
        readout = self.font.render(f"{self.clock.get_fps():5.1f} FPS", True, settings.HUD_COLOR)
        self.screen.blit(readout, (settings.HUD_MARGIN, settings.HUD_MARGIN))

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
