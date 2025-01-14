import pygame
from settings import *
from util import import_image, import_folder_dict


class UI:

    def __init__(self, font, game_data, powerup_assets):

        # Basic setup
        self.display_surface = pygame.display.get_surface()
        self.font = font
        self.game_data = game_data
        self.powerup_assets = powerup_assets

        self.import_assets()

        self.info_panel_strip = pygame.Surface((INFO_PANEL_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        self.boss_health_strip = pygame.Surface((GAME_WIDTH, TIMER_HEIGHT), pygame.SRCALPHA)

    def import_assets(self):

        # Import surfaces

        self.assets = {
            'stored_power': import_image('graphics/ui/stored_power.png'),
            'coin_counter': import_image('graphics/ui/coin_counter.png'),
            'life_counter': import_image('graphics/ui/life_counter.png'),
            'upgrades': {
                upgrade_type: import_folder_dict('graphics/upgrades/%s' % upgrade_type, scale=ZOOM_FACTOR*0.5)
                for upgrade_type in ['boots', 'gun', 'ammo']
            }
        }

        # Create rects that are static

        self.rects = {
            'stored_power': self.assets['stored_power'].get_rect(midtop=(INFO_PANEL_WIDTH/2, 0.01 * GAME_HEIGHT))
        }

        self.rects['coin_counter'] = self.assets['coin_counter'].get_rect(midtop=(INFO_PANEL_WIDTH/4, self.rects['stored_power'].bottom + 0.02 * GAME_HEIGHT))
        self.rects['life_counter'] = self.assets['life_counter'].get_rect(midtop=(INFO_PANEL_WIDTH/4, self.rects['coin_counter'].bottom + 0.01 * GAME_HEIGHT))

    def display(self, level_timer, boss):
        # If we are in a normal level, level_timer will be a non-empty sprite group
        # If we are in a boss level, boss will be a non-empty sprite group
        # Otherwise, both will be empty groups

        # BOSS HEALTH PANEL

        if boss.sprite is not None:
            # Draw a rectangle that decreases in width as health goes down
            self.boss_health_strip.fill('black')
            health_bar_total_width = GAME_WIDTH - (0.2 * GAME_WIDTH)
            health_bar_height = TIMER_HEIGHT / 3
            percent_health_left = boss.sprite.percent_health_left()
            health_bar_active_width = health_bar_total_width * percent_health_left
            x = 0.1 * GAME_WIDTH
            y = TIMER_HEIGHT / 3
            health_bar_rect = pygame.Rect(x, y, health_bar_active_width, health_bar_height)
            pygame.draw.rect(self.boss_health_strip, 'red', health_bar_rect)

        # Clear the surface
        self.info_panel_strip.fill('black')

        # INFO PANEL

        # Static images

        self.info_panel_strip.blit(self.assets['stored_power'], self.rects['stored_power'])
        self.info_panel_strip.blit(self.assets['coin_counter'], self.rects['coin_counter'])
        self.info_panel_strip.blit(self.assets['life_counter'], self.rects['life_counter'])

        # Render text for amount of coins & lives we hve

        coin_counter_surf = self.font.render("x %s" % self.game_data.coins, False, 'White')
        coin_counter_rect = coin_counter_surf.get_rect(midleft=(INFO_PANEL_WIDTH/2, self.rects['coin_counter'].centery))
        self.info_panel_strip.blit(coin_counter_surf, coin_counter_rect)

        lives_counter_surf = self.font.render("x %s" % self.game_data.lives, False, 'White')
        lives_counter_rect = lives_counter_surf.get_rect(midleft=(INFO_PANEL_WIDTH/2, self.rects['life_counter'].centery))
        self.info_panel_strip.blit(lives_counter_surf, lives_counter_rect)

        # Draw stored powerup

        if self.game_data.stored_powerup is not None:

            powerup_surf = self.powerup_assets[self.game_data.stored_powerup]
            powerup_rect = powerup_surf.get_rect(center=self.rects['stored_power'].center)
            self.info_panel_strip.blit(powerup_surf, powerup_rect)

        # Draw tiny images for any of the upgrades we've purchased

        upgrade_image_width, upgrade_image_height = self.assets['upgrades']['boots']['0'].get_width(), self.assets['upgrades']['boots']['0'].get_height()
        for y, upgrade_type in enumerate(['boots', 'gun', 'ammo']):
            for x in range(0, self.game_data.upgrades[upgrade_type]+1):
                self.info_panel_strip.blit(
                    self.assets['upgrades'][upgrade_type][str(x)],
                    ((0.01 * INFO_PANEL_WIDTH) + (x * (upgrade_image_width + (0.01 * INFO_PANEL_WIDTH))),
                     self.rects['life_counter'].bottom + (0.05 * GAME_HEIGHT) + (y * (upgrade_image_height + (0.01 * GAME_HEIGHT))))
                )

        # Draw surfaces on display surface

        self.display_surface.blit(self.info_panel_strip, (GAME_WIDTH, 0))

        if level_timer.sprite is not None:
            self.display_surface.blit(level_timer.sprite.image, (0, GAME_HEIGHT))

        if boss.sprite is not None:
            self.display_surface.blit(self.boss_health_strip, (0, GAME_HEIGHT))
