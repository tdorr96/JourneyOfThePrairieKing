from base_level import BaseLevel


class BossLevel(BaseLevel):

    def __init__(self, level_data, game_data, audio, assets, font, transition_to_next_level, transition_to_restart):

        super().__init__(level_data, game_data, audio, assets, font, transition_to_next_level, transition_to_restart)

        self.level_completed = False

    def check_level_completed(self):
        # You've completed the level if:
        # - No enemies on the map (i.e. boss dead)

        if self.level_completed:
            return

        if len(self.enemy_sprites.sprites()) == 0:

            self.level_completed = True

            # Delete the rock sprites at bottom of map, which when we walk past we will trigger next level
            # Also delete the middle river tile and relace it with a bridge there
            for obstruct in self.next_level_obstructable_sprites.sprites():
                obstruct.kill()
            self.spawn_bridge()
