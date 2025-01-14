import pygame
from util import Timer
from settings import *


UPGRADE_COSTS = {
    'boots': {
        0: 8,
        1: 20
    },
    'gun': {
        0: 10,
        1: 20,
        2: 30
    },
    'ammo': {
        0: 15,
        1: 30,
        2: 45
    }
}


class ShopKeeper(pygame.sprite.Sprite):
    # Simple sprite displayed on a shop level, that faces down, left, or right, depending on where player is on map

    def __init__(self, pos, surfs, player, groups):

        super().__init__(groups)

        # Attributes
        self.player = player

        # Image
        self.surfs = surfs  # {'down': _, 'left': _, 'right': _}
        self.status = 'down'
        self.image = self.surfs[self.status]
        self.z = Z_LAYERS['main']

        # Rect
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):

        x_distance_to_player = self.rect.centerx - self.player.rect.centerx

        if -100 <= x_distance_to_player <= 100:
            self.status = 'down'
        elif x_distance_to_player >= 100:
            self.status = 'left'
        else:
            self.status = 'right'

        self.image = self.surfs[self.status]


class Shop(pygame.sprite.Sprite):

    def __init__(self, box_surf, upgrade_surfs, coin_cost_surf, shop_keeper, player, game_data, groups):

        super().__init__(groups)

        # Attributes
        self.box_surf = box_surf
        self.upgrade_surfs = upgrade_surfs
        self.coin_cost_surf = coin_cost_surf
        self.game_data = game_data
        self.player = player

        # Fonts (two different sizes)
        self.font_unselected = pygame.font.Font('font/Stardew_Valley.ttf', int(5 * ZOOM_FACTOR))
        self.font_selected = pygame.font.Font('font/Stardew_Valley.ttf', int(7 * ZOOM_FACTOR))

        # Image & rect
        # The image for now is just a blank copy of the box surface
        # Every frame the shop is active in (i.e. player close enough), we re-create the image
        # as built from the box surface, the upgrade images, coin image, rendered text for cost, etc.
        self.image = self.box_surf.copy()
        self.rect = self.image.get_rect(midtop=shop_keeper.rect.midbottom).move(0, 10)

        # Create rects for where the upgrade images are going to go
        # We need them both in reference to:
        # - (0, 0), as they are being blitted onto the image surface
        # - relative to the game surface, for collisions with the player

        self.upgrade_rects = {
            'image': {
                'boots': self.upgrade_surfs['boots']['0'].get_rect(center=(0.2 * self.rect.width, 0.35 * self.rect.height)),
                'gun': self.upgrade_surfs['gun']['0'].get_rect(center=(0.5 * self.rect.width, 0.35 * self.rect.height)),
                'ammo': self.upgrade_surfs['ammo']['0'].get_rect(center=(0.8 * self.rect.width, 0.35 * self.rect.height))
            },
            'game': {}
        }

        for upgrade_type in ['boots', 'gun', 'ammo']:
            rect_on_image = self.upgrade_rects['image'][upgrade_type]                # rect relative to image
            rect_on_game = rect_on_image.copy().move(self.rect.left, self.rect.top)  # rect relative to game
            self.upgrade_rects['game'][upgrade_type] = rect_on_game

        # Create rects for where the coin images are going to go, only needed in reference to image (0, 0)

        self.coin_rects = {
            'boots': self.coin_cost_surf.get_rect(midleft=(self.upgrade_rects['image']['boots'].left, 0.7 * self.rect.height)),
            'gun': self.coin_cost_surf.get_rect(midleft=(self.upgrade_rects['image']['gun'].left, 0.7 * self.rect.height)),
            'ammo': self.coin_cost_surf.get_rect(midleft=(self.upgrade_rects['image']['ammo'].left, 0.7 * self.rect.height))
        }

        # Shop becomes active when player gets within distance radius
        self.active = False
        self.active_radius = 50 * ZOOM_FACTOR

        # Timer
        self.purchase_timer = Timer(500)

    def update_image(self):
        # Whenever the shop is active, we re-create the image of the sprite
        # This means, starting with a base image of just the box surface
        # And building it up, by drawing the upgrade images on it, the coin surfaces, text of the cost,
        # font size & color depending on if the player is on-top of one, etc.
        # Might be more efficient to only re-create if something changes?

        self.image = self.box_surf.copy()

        for upgrade_type in ['boots', 'gun', 'ammo']:

            next_upgrade_index = self.game_data.upgrades[upgrade_type] + 1

            # If we've reached the maximum upgrade, don't draw anything
            if next_upgrade_index not in UPGRADE_COSTS[upgrade_type]:
                continue

            # Draw image for the upgrade and a coin that'll be next to the text for cost
            self.image.blit(self.upgrade_surfs[upgrade_type][str(next_upgrade_index)], self.upgrade_rects['image'][upgrade_type])
            self.image.blit(self.coin_cost_surf, self.coin_rects[upgrade_type])

            # Draw text for the cost of the upgrade
            # If we're selecting a specific upgrade, to help the player see it, use a larger font with different color

            if self.upgrade_rects['game'][upgrade_type].collidepoint(self.player.rect.center):
                font = self.font_selected
                color = '#228B22'
            else:
                font = self.font_unselected
                color = 'black'

            cost_surf = font.render("x" + str(UPGRADE_COSTS[upgrade_type][next_upgrade_index]), False, color)
            cost_rect = cost_surf.get_rect(midright=(self.upgrade_rects['image'][upgrade_type].right, self.coin_rects[upgrade_type].centery))
            self.image.blit(cost_surf, cost_rect)

    def input(self):

        if not self.purchase_timer.active:

            keys = pygame.key.get_pressed()
            if keys[pygame.K_RETURN]:

                for upgrade_type in ['boots', 'gun', 'ammo']:

                    # If we're bought the maximum upgrade for this type already, don't check any further
                    next_upgrade_index = self.game_data.upgrades[upgrade_type] + 1
                    if next_upgrade_index not in UPGRADE_COSTS[upgrade_type]:
                        continue

                    if self.upgrade_rects['game'][upgrade_type].collidepoint(self.player.rect.center):

                        self.purchase_timer.activate()  # Activate timer whether-or-not we could afford it

                        # Attempt the purchase if we can afford it
                        cost = UPGRADE_COSTS[upgrade_type][next_upgrade_index]
                        if self.game_data.coins >= cost:

                            self.game_data.coins -= cost
                            self.game_data.upgrades[upgrade_type] += 1
                            self.player.calculate_base_stats()

    def update(self):

        self.purchase_timer.update()

        # We are active if player is within a certain radius
        # Once active, we check for input, update the image, and draw it
        vector_to_player = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)
        self.active = vector_to_player.magnitude() < self.active_radius

        if self.active:
            self.input()
            self.update_image()
