from sprites import LevelTimer
from base_level import BaseLevel


class NormalLevel(BaseLevel):

    def __init__(self, level_data, game_data, audio, assets, font, transition_to_next_level, transition_to_restart):

        super().__init__(level_data, game_data, audio, assets, font, transition_to_next_level, transition_to_restart)

        self.level_completed = False
        self.setup_level_timer(level_data)

    def setup_level_timer(self, level_data):
        # Level runs for x seconds (specified in level data), and doesn't start for 3 seconds on start up

        level_timer = LevelTimer(
            level_duration=level_data['duration'],
            delay_duration=3000,
            groups=self.level_timer_group
        )

        self.pause_able_timers.append(level_timer.level_timer)
        self.pause_able_timers.append(level_timer.delay_timer)

    def check_level_completed(self):
        # You've completed the level if:
        # - Level timer is not active (reached the end)
        # - No enemies on the map

        if self.level_completed:
            return

        if self.level_timer_group.sprite.is_level_timer_finished() and len(self.enemy_sprites.sprites()) == 0:

            self.level_completed = True

            # Delete the rock sprites at bottom of map, which when we walk past we will trigger next level
            for obstruct in self.next_level_obstructable_sprites.sprites():
                obstruct.kill()
