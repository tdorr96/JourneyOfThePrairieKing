from boss_level import BossLevel
from shop_level import ShopLevel
from normal_level import NormalLevel
from enemies import Orc, Ogre, Butterfly, Mushroom, Mummy, Imp, Spikeball


class GameData:

    def __init__(self, old_easy_mode=None, old_volume=None):

        self.lives = 0
        self.coins = 0
        self.stored_powerup = None
        self.current_level = -1
        self.volume = old_volume if old_volume is not None else 1
        self.easy_mode = old_easy_mode if old_easy_mode is not None else True

        # -1 represents no upgrades purchased
        # current number + 1 represents the next available upgrade
        self.upgrades = {
            'boots': -1,
            'gun': -1,
            'ammo': -1
        }


LEVEL_DATA = {
    0: {
        'bg': 'data/desert_bg.png',
        'tmx': 'data/0/level_0.tmx',
        'duration': 30000,
        'type': 'desert',
        'level_type': NormalLevel,
        'enemies': [
            {'type': Orc, 'spawn_rate': 1000, 'p': [0.5, 0.3, 0.2]}
        ]
    },
    1: {
        'bg': 'data/desert_bg.png',
        'tmx': 'data/1/level_1.tmx',
        'duration': 35000,
        'type': 'desert',
        'level_type': NormalLevel,
        'enemies': [
            {'type': Orc, 'spawn_rate': 900, 'p': [0.4, 0.3, 0.3]},
            {'type': Spikeball, 'spawn_rate': 5000}
        ]
    },
    2: {
        'bg': 'data/desert_bg.png',
        'tmx': 'data/2/level_2.tmx',
        'duration': 35000,
        'type': 'desert',
        'level_type': NormalLevel,
        'enemies': [
            {'type': Orc, 'spawn_rate': 900, 'p': [0.3, 0.3, 0.4]},
            {'type': Ogre, 'spawn_rate': 2500},
            {'type': Spikeball, 'spawn_rate': 4500}
        ]
    },
    3: {
        'bg': 'data/desert_bg.png',
        'tmx': 'data/3/level_3.tmx',
        'duration': 40000,
        'type': 'desert',
        'level_type': NormalLevel,
        'enemies': [
            {'type': Orc, 'spawn_rate': 800, 'p': [0.1, 0.5, 0.4]},
            {'type': Ogre, 'spawn_rate': 2000},
            {'type': Spikeball, 'spawn_rate': 4000}
        ]
    },
    4: {
        'bg': 'data/desert_bg.png',
        'tmx': 'data/4/level_4.tmx',
        'type': 'desert',
        'level_type': ShopLevel,
        'enemies': []
    },
    5: {
        'bg': 'data/desert_bg.png',
        'tmx': 'data/5/level_5.tmx',
        'type': 'desert',
        'level_type': BossLevel,
        'boss_health': 50,
        'bullet_cooldown': 300,
        'firing_strategy': 'upwards',
        'enemies': []
    },
    6: {
        'bg': 'data/forest_bg.png',
        'tmx': 'data/6/level_6.tmx',
        'duration': 40000,
        'type': 'forest',
        'level_type': NormalLevel,
        'enemies': [
            {'type': Ogre, 'spawn_rate': 2000},
            {'type': Mushroom, 'spawn_rate': 1600},
            {'type': Butterfly, 'spawn_rate': 1800}
        ]
    },
    7: {
        'bg': 'data/forest_bg.png',
        'tmx': 'data/7/level_7.tmx',
        'duration': 45000,
        'type': 'forest',
        'level_type': NormalLevel,
        'enemies': [
            {'type': Ogre, 'spawn_rate': 2000},
            {'type': Mushroom, 'spawn_rate': 1500},
            {'type': Butterfly, 'spawn_rate': 1700}
        ]
    },
    8: {
        'bg': 'data/forest_bg.png',
        'tmx': 'data/8/level_8.tmx',
        'duration': 50000,
        'type': 'forest',
        'level_type': NormalLevel,
        'enemies': [
            {'type': Ogre, 'spawn_rate': 1750},
            {'type': Mushroom, 'spawn_rate': 1300},
            {'type': Butterfly, 'spawn_rate': 1500}
        ]
    },
    9: {
        'bg': 'data/forest_bg.png',
        'tmx': 'data/9/level_9.tmx',
        'type': 'forest',
        'level_type': ShopLevel,
        'enemies': []
    },
    10: {
        'bg': 'data/forest_bg.png',
        'tmx': 'data/10/level_10.tmx',
        'type': 'forest',
        'level_type': BossLevel,
        'boss_health': 100,
        'bullet_cooldown': 200,
        'firing_strategy': 'towards_player',
        'enemies': []
    },
    11: {
        'bg': 'data/graveyard_bg.png',
        'tmx': 'data/11/level_11.tmx',
        'duration': 50000,
        'type': 'graveyard',
        'level_type': NormalLevel,
        'enemies': [
            {'type': Mummy, 'spawn_rate': 1200, 'p': [0.1, 0.2, 0.7]},
            {'type': Imp, 'spawn_rate': 1300}
        ]
    },
    12: {
        'bg': 'data/graveyard_bg.png',
        'tmx': 'data/12/level_12.tmx',
        'duration': 50000,
        'type': 'graveyard',
        'level_type': NormalLevel,
        'enemies': [
            {'type': Mummy, 'spawn_rate': 1000, 'p': [0.1, 0.1, 0.8]},
            {'type': Imp, 'spawn_rate': 1100}
        ]
    },
    13: {
        'bg': 'data/graveyard_bg.png',
        'tmx': 'data/13/level_13.tmx',
        'duration': 60000,
        'type': 'graveyard',
        'level_type': NormalLevel,
        'enemies': [
            {'type': Mummy, 'spawn_rate': 800, 'p': [0.0, 0.1, 0.9]},
            {'type': Imp, 'spawn_rate': 900}
        ]
    }
}
