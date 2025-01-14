import pygame
import random
from settings import *
from enemies import Enemy, Spikeball
from util import import_folder, import_image


class Camera(pygame.sprite.Group):

    def __init__(self, bg, assets):

        super().__init__()

        self.display_surface = pygame.display.get_surface()
        self.bg = import_image(bg)

        # We draw onto a separate surface that has the exact dimension of the game,
        # then blit this surface onto the actual display surface
        self.game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)

        # Extra Assets
        self.lightening_surfaces = import_folder('graphics/other/lightening')
        self.question_mark_surf = assets['question_mark']
        self.arrow_surf = assets['arrow']
        self.arrow_rect = self.arrow_surf.get_rect(midbottom=(GAME_WIDTH / 2, GAME_HEIGHT * 0.975))

    def draw_lightening_active(self, player):
        # If lightening is active, we don't draw the background or the other sprites
        # We just draw the player and some lightening surfaces across the screen

        self.game_surface.blit(player.image, player.rect)

        height_of_lightening = self.lightening_surfaces[0].get_height()
        for lightening in range(int(player.rect.top / height_of_lightening) + 1):
            self.game_surface.blit(
                random.choice(self.lightening_surfaces),
                (player.rect.left, player.rect.top - (height_of_lightening * (lightening + 1)))
            )

    def draw_sprites(self):
        # Regular for loop to iterate over all sprites, in order of z component,
        # and draw in right-down order for 3D effect

        for z_layer in Z_LAYERS:
            z_sprites = filter(lambda s: s.z == Z_LAYERS[z_layer], self.sprites())
            for sprite in sorted(z_sprites, key=lambda s: (s.rect.centery, s.rect.centerx)):
                self.game_surface.blit(sprite.image, sprite.rect)

    def custom_draw(self, lightening_active, smoke_bomb_active, player, level_completed, shop):

        # Clear surface
        self.game_surface.fill('black')

        if not lightening_active:

            # Background
            self.game_surface.blit(self.bg, (0, 0))

            # Draw the shop
            if shop.sprite is not None and shop.sprite.active:
                shop.draw(self.game_surface)

            # Sprites
            self.draw_sprites()

            # Question marks above enemies
            if smoke_bomb_active:
                for enemy in filter(lambda s: isinstance(s, Enemy) or isinstance(s, Spikeball), self.sprites()):
                    question_mark_rect = self.question_mark_surf.get_rect(midbottom=enemy.rect.midtop)
                    self.game_surface.blit(self.question_mark_surf, question_mark_rect)

            # Arrow pointing towards bottom of screen if level completed
            if level_completed:
                self.game_surface.blit(self.arrow_surf, self.arrow_rect)

        else:
            self.draw_lightening_active(player)

        # Draw surface on actual display surface
        self.display_surface.blit(self.game_surface, (0, 0))
