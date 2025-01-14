import time
import pygame
from settings import *
from intro_screen import IntroScreen
from game_data import GameData, LEVEL_DATA
from util import import_folder, import_folder_dict, import_image
from enemies import Orc, Ogre, Butterfly, Mushroom, Mummy, Imp, Spikeball


class Game:

    def __init__(self):

        # General Setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Journey of the Prairie King')
        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font('font/Stardew_Valley.ttf', int(10 * ZOOM_FACTOR))
        self.game_data = GameData()

        self.import_audio()   # Create dict of self.audio
        self.import_assets()  # Create dict of self.assets

        # Create the intro screen
        self.level = IntroScreen(self.game_data, self.assets, self.transition_to_next_level, self.update_volume)

        # Transition object to switch between levels
        self.transition = Transition(func=self.switch_to_next_level)

        # Transition object to restart the game
        self.game_over_transition = Transition(func=self.restart_game_over)

    def import_audio(self):

        self.audio = {
            'gunshot': pygame.mixer.Sound('sounds/gunshot.wav'),
            'dead': pygame.mixer.Sound('sounds/dead.wav'),
            'footstep': pygame.mixer.Sound('sounds/footstep.wav'),
            'machine_gun': pygame.mixer.Sound('sounds/machine_gun.wav'),
            'powerup': pygame.mixer.Sound('sounds/powerup.wav'),
            'nuke': pygame.mixer.Sound('sounds/nuke.wav'),
            'monster_hit': pygame.mixer.Sound('sounds/monster_hit.wav')
        }

        self.update_volume()

    def update_volume(self):

        for audio in self.audio:
            self.audio[audio].set_volume(self.game_data.volume / 10)

    def transition_to_next_level(self):
        # Called from within a level to start the transition
        # Once started, transition will animate and at some point call `switch_to_next_level`

        if not self.game_over_transition.active:
            self.transition.active = True

    def transition_to_restart(self):

        self.game_over_transition.active = True

    def restart_game_over(self):

        self.game_data = GameData(self.game_data.easy_mode, self.game_data.volume)
        self.level = IntroScreen(self.game_data, self.assets, self.transition_to_next_level, self.update_volume)

    def switch_to_next_level(self):
        # Called from transition object, when it's time to create the next level object

        self.game_data.current_level += 1
        if self.game_data.current_level in LEVEL_DATA:
            level_class = LEVEL_DATA[self.game_data.current_level]['level_type']
            self.level = level_class(LEVEL_DATA[self.game_data.current_level], self.game_data, self.audio, self.assets, self.font, self.transition_to_next_level, self.transition_to_restart)
        else:
            # Finished the last level, restart game
            self.restart_game_over()

    def import_assets(self):

        self.assets = {
            'animated_tile_frames': {
                area_type: [
                    import_image('graphics/tiles/%s/5.png' % area_type), import_image('graphics/tiles/%s/6.png' % area_type)
                ] for area_type in ['desert', 'forest', 'graveyard']
            },
            'bullets': import_folder_dict('graphics/bullets'),
            'enemies': {
                Orc: {
                    'run': import_folder('graphics/enemies/orc/run'),
                    'ashes': import_folder('graphics/enemies/orc/die'),
                },
                Ogre: {
                    'run': import_folder('graphics/enemies/ogre/run'),
                    'ashes': import_folder('graphics/enemies/ogre/die')
                },
                Butterfly: {
                    'run': import_folder('graphics/enemies/butterfly/run'),
                    'ashes': import_folder('graphics/enemies/butterfly/die')
                },
                Mushroom: {
                    'run': import_folder('graphics/enemies/mushroom/run'),
                    'ashes': import_folder('graphics/enemies/mushroom/die')
                },
                Mummy: {
                    'run': import_folder('graphics/enemies/mummy/run'),
                    'ashes': import_folder('graphics/enemies/mummy/die')
                },
                Imp: {
                    'run': import_folder('graphics/enemies/imp/run'),
                    'ashes': import_folder('graphics/enemies/imp/die')
                },
                Spikeball: {
                    'run': import_folder('graphics/enemies/spikeball/run'),
                    'ashes': import_folder('graphics/enemies/spikeball/die'),
                    'deploying': import_folder('graphics/enemies/spikeball/deploying'),
                    'deployed': import_folder('graphics/enemies/spikeball/deployed')
                }
            },
            'boss': {
                'cowboy': {
                    'idle': import_folder('graphics/bosses/cowboy/idle'),
                    'moving': import_folder('graphics/bosses/cowboy/moving')
                }
            },
            'sound_bars': {
                'on': import_image('graphics/ui/sound_on.png'),
                'off': import_image('graphics/ui/sound_off.png')
            },
            'difficulty_buttons': {
                'easy': import_image('graphics/ui/difficulty_easy.png', scale=ZOOM_FACTOR * 0.75),
                'hard': import_image('graphics/ui/difficulty_hard.png', scale=ZOOM_FACTOR * 0.75)
            },
            'bridge_surf': import_image('graphics/tiles/forest/10.png'),
            'player_death': import_folder('graphics/player/die/'),
            'coin_drops': import_folder_dict('graphics/coins'),
            'powerup_drops': import_folder_dict('graphics/powerups'),
            'nuke_smoke': import_folder('graphics/other/nuke_smoke'),
            'question_mark': self.font.render('?', False, 'Black'),
            'arrow': import_image('graphics/other/arrow.png'),
            'shop_keeper': import_folder_dict('graphics/shop_keeper/idle'),
            'shop_upgrade_box': import_image('graphics/other/upgrade_box.png'),
            'shop_coin_counter': import_image('graphics/ui/coin_counter.png', scale=ZOOM_FACTOR*0.75),
            'upgrades': {
                upgrade_type: import_folder_dict('graphics/upgrades/%s' % upgrade_type)
                for upgrade_type in ['boots', 'gun', 'ammo']
            },
            'intro': {
                'welcome_message': import_image('graphics/other/welcome_message.png', scale=ZOOM_FACTOR*1.25),
                'keyboard': import_image('graphics/other/keyboard.png')
            }
        }

    def run(self):

        last_time = time.time()
        while True:

            # Delta Time
            dt = time.time() - last_time
            last_time = time.time()

            # Clear Display Surface
            self.display_surface.fill('black')

            # Updates & Drawing
            self.level.run(dt)
            self.transition.run(dt)
            self.game_over_transition.run(dt)

            # Update display surface & limit max frame rate
            pygame.display.update()
            self.clock.tick(60)


class Transition:
    # Transition object we use to create a transition between levels
    # Once it's time to go to the next level, we set `self.active` to True, which starts the animation
    # Half-way through the animation, we call a function in Game to create the next level object
    # We then reverse the animation until we've finished and are no longer active

    def __init__(self, func):

        self.display_surface = pygame.display.get_surface()

        # `func` is the function to call to initiate the next level object, called half way through animation
        self.func = func
        self.active = False

        # Variables defining the circle transition animation
        self.border_width = 0
        self.direction = 1
        self.center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
        self.radius = pygame.math.Vector2(self.center).magnitude()
        self.threshold = self.radius + (30 * ZOOM_FACTOR)
        self.speed = 300 * ZOOM_FACTOR

    def run(self, dt):

        if self.active:

            self.border_width += self.speed * dt * self.direction
            if self.border_width >= self.threshold:
                self.direction = -1
                self.func()
            elif self.border_width < 0:
                self.active = False
                self.border_width = 0
                self.direction = 1

            pygame.draw.circle(self.display_surface, 'black', self.center, self.radius, int(self.border_width))


if __name__ == '__main__':

    game = Game()
    game.run()
