import sys
import pygame
import random
from settings import *
from util import import_image


class DifficultyButton(pygame.sprite.Sprite):

    def __init__(self, surfs, pos, easy, groups):

        super().__init__(groups)

        self.easy_surf = surfs['easy']
        self.hard_surf = surfs['hard']

        self.easy = easy  # True for easy, False for hard

        self.update_image()
        self.rect = self.image.get_rect(midtop=pos)

    def update_image(self):

        self.image = self.easy_surf if self.easy else self.hard_surf

    def handle_click(self):

        self.easy = not self.easy
        self.update_image()


class SoundVolumeSlider(pygame.sprite.Sprite):

    def __init__(self, surfs, pos, init_volume, groups):

        super().__init__(groups)

        self.on_surf = surfs['on']
        self.off_surf = surfs['off']
        self.bar_width = self.on_surf.get_width()
        self.bar_height = self.on_surf.get_height()

        self.current_volume = init_volume
        self.max_volume = 10

        self.update_image()
        self.rect = self.image.get_rect(midtop=pos)

    def update_image(self):

        self.image = pygame.Surface((self.max_volume * self.bar_width, self.bar_height), pygame.SRCALPHA)

        for on in range(0, self.current_volume):
            self.image.blit(self.on_surf, (on * self.bar_width, 0))

        for off in range(self.current_volume, self.max_volume):
            self.image.blit(self.off_surf, (off * self.bar_width, 0))

    def handle_click(self, pos):

        x_click = pos[0] - self.rect.left
        new_volume = int(x_click / self.bar_width) + 1
        if new_volume != self.current_volume:
            self.current_volume = new_volume
            self.update_image()
            return True
        else:
            return False


class RotatingSprite(pygame.sprite.Sprite):

    def __init__(self, surf, pos, angle1, angle2, animation_speed, groups):

        super().__init__(groups)

        self.frames = [
            pygame.transform.rotozoom(surf, angle1, 1),
            pygame.transform.rotozoom(surf, angle2, 1)
        ]
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rects = [
            self.frames[0].get_rect(center=pos),
            self.frames[1].get_rect(center=pos)
        ]
        self.rect = self.rects[self.frame_index]
        self.animation_speed = animation_speed

    def animate(self, dt):

        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]
        self.rect = self.rects[int(self.frame_index)]

    def update(self, dt):

        self.animate(dt)


class IntroScreen:

    def __init__(self, game_data, assets, transition_to_next_level, update_volume):

        # Setup
        self.game_data = game_data
        self.display_surface = pygame.display.get_surface()
        self.transition_to_next_level = transition_to_next_level
        self.update_volume = update_volume

        # Assets & rects

        self.keyboard_surf = assets['intro']['keyboard']
        self.keyboard_rect = self.keyboard_surf.get_rect(center=(SCREEN_WIDTH/2, 4*SCREEN_HEIGHT/5))

        self.welcome_message_surf = assets['intro']['welcome_message']
        self.welcome_message_rect = self.welcome_message_surf.get_rect(center=(SCREEN_WIDTH/2, 2*SCREEN_HEIGHT/5))

        # Font
        self.font = pygame.font.Font('font/Stardew_Valley.ttf', int(15 * ZOOM_FACTOR))

        # Sprite group
        self.all_sprites = pygame.sprite.Group()

        # Sprites
        RotatingSprite(
            surf=assets['powerup_drops']['extra_life'],
            pos=(SCREEN_WIDTH/6, SCREEN_HEIGHT/6),
            angle1=-10,
            angle2=10,
            animation_speed=3,
            groups=self.all_sprites
        )
        RotatingSprite(
            surf=assets['powerup_drops']['coffee'],
            pos=(SCREEN_WIDTH / 7, 4 * SCREEN_HEIGHT / 6),
            angle1=-20,
            angle2=-10,
            animation_speed=2,
            groups=self.all_sprites
        )
        RotatingSprite(
            surf=assets['powerup_drops']['sheriff_badge'],
            pos=(6 * SCREEN_WIDTH / 7, 6 * SCREEN_HEIGHT / 7),
            angle1=5,
            angle2=15,
            animation_speed=4,
            groups=self.all_sprites
        )
        RotatingSprite(
            surf=assets['coin_drops']['one'],
            pos=(6 * SCREEN_WIDTH / 7, SCREEN_HEIGHT / 4),
            angle1=10,
            angle2=20,
            animation_speed=4,
            groups=self.all_sprites
        )
        RotatingSprite(
            surf=import_image('graphics/player/upgrade_stance.png'),
            pos=(SCREEN_WIDTH / 2, 5 * SCREEN_HEIGHT / 8),
            angle1=-5,
            angle2=5,
            animation_speed=4,
            groups=self.all_sprites
        )
        self.sound_control = SoundVolumeSlider(
            surfs=assets['sound_bars'],
            pos=(4 * SCREEN_WIDTH / 7, 10),
            init_volume=self.game_data.volume,
            groups=self.all_sprites
        )
        self.difficulty_button = DifficultyButton(
            surfs=assets['difficulty_buttons'],
            pos=(SCREEN_WIDTH / 2, self.sound_control.rect.bottom + 25),
            easy=self.game_data.easy_mode,
            groups=self.all_sprites
        )

        # Sound Text
        self.sound_text_surf = self.font.render('Sound', False, (230, 230, 230))
        self.sound_text_rect = self.sound_text_surf.get_rect(midright=(self.sound_control.rect.left - 50, self.sound_control.rect.centery))

        # Difficulty Text
        self.easy_text_surf = self.font.render('Easy', False, (230, 230, 230))
        self.easy_text_rect = self.easy_text_surf.get_rect(midright=(self.difficulty_button.rect.left - 50, self.difficulty_button.rect.centery))
        self.hard_text_surf = self.font.render('Hard', False, (230, 230, 230))
        self.hard_text_rect = self.hard_text_surf.get_rect(midleft=(self.difficulty_button.rect.right + 50, self.difficulty_button.rect.centery))

    def run(self, dt):

        # Event Loop

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:

                if self.sound_control.rect.collidepoint(event.pos):
                    if self.sound_control.handle_click(event.pos):
                        # Returns true if it changed
                        self.game_data.volume = self.sound_control.current_volume
                        self.update_volume()

                elif self.difficulty_button.rect.collidepoint(event.pos):
                    self.difficulty_button.handle_click()
                    self.game_data.easy_mode = self.difficulty_button.easy

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.transition_to_next_level()

        # Updates
        self.all_sprites.update(dt)

        # Drawing

        self.display_surface.fill((238, 183, 81))
        self.all_sprites.draw(self.display_surface)
        self.display_surface.blit(self.sound_text_surf, self.sound_text_rect)
        self.display_surface.blit(self.easy_text_surf, self.easy_text_rect)
        self.display_surface.blit(self.hard_text_surf, self.hard_text_rect)
        self.display_surface.blit(self.welcome_message_surf, self.welcome_message_rect)
        self.display_surface.blit(self.keyboard_surf, self.keyboard_rect)
