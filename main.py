import pygame

from src import audio, menu, minimap, progress, raycaster, renderer, settings, textures, world
from src.levels import LEVELS
from src.player import Player


class Game:
    """Window, timing, and the frame loop across the two screens: level select and a run."""

    def __init__(self):
        pygame.mixer.pre_init(*settings.AUDIO_MIXER)
        pygame.init()
        audio.load()  # a machine with no sound device just plays nothing
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
        self.cleared = progress.load()
        self.level_index = 0
        self.restart()
        self.open_menu()

    def grab_mouse(self):
        """Hide and confine the pointer so it reports unbounded turning motion."""
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        try:
            pygame.mouse.set_relative_mode(True)
        except pygame.error:
            pass  # driver without relative mode — the grab alone still delivers motion

    def release_mouse(self):
        """Hand the pointer back to the desktop so the menu buttons can be clicked."""
        try:
            pygame.mouse.set_relative_mode(False)
        except pygame.error:
            pass
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)

    def open_menu(self):
        """Leave any run in progress and show level select."""
        self.in_menu = True
        self.release_mouse()

    def start_level(self, index):
        """Make that level current, spawn in it, and take the pointer back for mouse look."""
        self.level_index = index
        world.load(index)
        self.in_menu = False
        self.grab_mouse()
        self.restart()

    def restart(self):
        """Put the player back on the spawn tile and open the run again."""
        self.player = Player(*world.SPAWN, world.SPAWN_ANGLE)
        self.won = False

    def advance(self):
        """Start the level after this one, or fall back to level select past the last."""
        if self.level_index + 1 < len(LEVELS):
            self.start_level(self.level_index + 1)
        else:
            self.open_menu()

    def win(self):
        """Freeze the run, bank the clear, and unlock whatever comes next."""
        self.won = True
        if self.cleared < self.level_index + 1:
            self.cleared = self.level_index + 1
            progress.save(self.cleared)

    def handle_events(self):
        """Drain the queue, routing each event to whichever screen is up."""
        self.mouse_dx = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.in_menu:
                self.handle_menu_event(event)
            else:
                self.handle_run_event(event)

    def handle_menu_event(self, event):
        """Level select: a left click either starts a level or leaves the game."""
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        choice = menu.pick(event.pos, self.cleared)
        if choice is None:
            if menu.locked_at(event.pos, self.cleared):
                audio.play(audio.LOCKED)
            return
        audio.play(audio.SELECT)
        if choice == menu.QUIT:
            audio.wait(audio.SELECT)  # let the click finish before the window goes
            self.running = False
        else:
            self.start_level(choice)

    def handle_run_event(self, event):
        """In a run: mouse look, the render toggles, restart, and Esc back to level select."""
        if event.type == pygame.MOUSEMOTION:
            self.mouse_dx += event.rel[0]
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.open_menu()
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
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.won:
                self.advance()

    def update(self):
        """Advance the world by self.dt seconds; an escaped player is frozen where they stand."""
        if self.in_menu or self.won:
            return
        self.player.update(pygame.key.get_pressed(), self.mouse_dx, self.dt)
        if world.at_goal(self.player.x, self.player.y):
            self.win()

    def draw(self):
        """Compose the frame for whichever screen is up, and present it."""
        if self.in_menu:
            menu.draw(self.screen, self.cleared, pygame.mouse.get_pos())
        else:
            self.draw_run()
        pygame.display.flip()

    def draw_run(self):
        """The first-person view or the debug map, plus the overlays over it."""
        hits, obstacles = raycaster.cast_all(self.player)
        if self.debug_view:
            minimap.draw_debug(self.screen, self.player, hits)
        else:
            renderer.draw_world(self.player, hits, obstacles, self.textures, self.floor_texture)
            renderer.present(self.screen)
            if self.minimap_visible:
                minimap.draw_overlay(self.screen, self.player, hits)
        if self.won:
            self.draw_banner()
        self.draw_hud()

    def draw_banner(self):
        """Fade the frozen frame down and centre the end-of-run message on it."""
        self.screen.blit(self.dim, (0, 0))
        last = self.level_index + 1 >= len(LEVELS)
        message = self.banner_font.render(settings.WIN_TEXT, True, settings.BANNER_COLOR)
        hint = self.font.render(settings.WIN_LAST_HINT if last else settings.WIN_HINT, True, settings.HUD_COLOR)
        message_rect = message.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(message, message_rect)
        self.screen.blit(hint, hint.get_rect(midtop=(message_rect.centerx, message_rect.bottom + settings.BANNER_GAP)))

    def draw_hud(self):
        """Frame rate and the level being played, stacked in the top-left corner."""
        readout = self.font.render(f"{self.clock.get_fps():5.1f} FPS", True, settings.HUD_COLOR)
        label = self.font.render(f"{self.level_index + 1}. {world.NAME}", True, settings.HUD_COLOR)
        self.screen.blit(readout, (settings.HUD_MARGIN, settings.HUD_MARGIN))
        self.screen.blit(label, (settings.HUD_MARGIN, settings.HUD_MARGIN + readout.get_height()))

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
