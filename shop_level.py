from shop import Shop
from base_level import BaseLevel


class ShopLevel(BaseLevel):

    def __init__(self, level_data, game_data, audio, assets, font, transition_to_next_level, transition_to_restart):

        super().__init__(level_data, game_data, audio, assets, font, transition_to_next_level, transition_to_restart)

        self.level_completed = True
        self.setup_shop()

    def setup_shop(self):

        Shop(
            box_surf=self.assets['shop_upgrade_box'],
            upgrade_surfs=self.assets['upgrades'],
            coin_cost_surf=self.assets['shop_coin_counter'],
            shop_keeper=self.shop_keeper,
            player=self.player,
            game_data=self.game_data,
            groups=self.shop_group
        )

    def check_level_completed(self):
        # We've always completed a shop level. Implement as all level sub-classes need to implement this function

        return
