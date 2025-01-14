import sys
import pygame
import random
from ui import UI
import numpy as np
from util import Timer
from settings import *
from boss import Cowboy
from player import Player
from cameras import Camera
from shop import ShopKeeper
from particles import ParticleEffect
from pathfinding.core.grid import Grid
from pytmx.util_pygame import load_pygame
from sprites import Bullet, Coin, Powerup
from tiles import StaticTile, AnimatedTile
from pathfinding.finder.a_star import AStarFinder
from enemies import Orc, Ogre, Butterfly, Mushroom, Mummy, Imp, Spikeball


class BaseLevel:

    def __init__(self, level_data, game_data, audio, assets, font, transition_to_next_level, transition_to_restart):

        # General setup
        self.game_data = game_data
        self.audio = audio
        self.assets = assets
        self.transition_to_next_level = transition_to_next_level
        self.transition_to_restart = transition_to_restart

        # UI
        self.ui = UI(font, self.game_data, self.assets['powerup_drops'])

        # Sprite groups
        # Not all may be used in concrete subclasses of levels
        self.all_sprites = Camera(level_data['bg'], assets)
        self.player_collision_sprites = pygame.sprite.Group()
        self.enemy_collision_sprites = pygame.sprite.Group()
        self.flying_enemy_collision_sprites = pygame.sprite.Group()  # Always kept empty
        self.bullet_colliding_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.coin_sprites = pygame.sprite.Group()
        self.powerup_sprites = pygame.sprite.Group()
        self.particle_sprites = pygame.sprite.Group()
        self.next_level_obstructable_sprites = pygame.sprite.Group()
        self.shop_group = pygame.sprite.GroupSingle()
        self.level_timer_group = pygame.sprite.GroupSingle()
        self.spikeball_sprites = pygame.sprite.Group()
        self.ogre_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.GroupSingle()
        self.boss_group = pygame.sprite.GroupSingle()

        # Timers
        self.smoke_bomb_timer = Timer(4000)
        self.tombstone_timer = Timer(8000)
        self.lightening_timer = Timer(1000, func=self.apply_zombie_mode)

        # Initialise the grid of points (matrix) for pathfinding & the list of deploy-able positions for the spikeballs
        # We start with all grid points as walk-able and deploy-able, but setup() will narrow these down
        self.matrix = [[1 for x in range(TILES_WIDE)] for y in range(TILES_HIGH)]
        self.spikeball_positions = [(x, y) for x in range(TILES_WIDE) for y in range(TILES_HIGH)]

        # Create sprites for groups
        self.setup(level_data)

        # Setup grid object for pathfinding now matrix complete
        self.grid = Grid(matrix=self.matrix)

        # Timers that need to be paused on lightening effect
        # Sub-classes may extend this list, e.g. Normal Level will add the level & delay timers
        self.pause_able_timers = [
            self.smoke_bomb_timer, self.player.bullet_cooldown, self.player.coffee_timer, self.player.sheriff_timer,
            self.player.machine_gun_timer, self.player.shotgun_timer, self.player.wagon_wheel_timer
        ]
        if self.boss_group.sprite is not None:
            self.pause_able_timers.append(self.boss_group.sprite.idle_timer)
            self.pause_able_timers.append(self.boss_group.sprite.bullet_cooldown_timer)

        # Enemy timer events, one for each enemy type specified in level config
        # Each enemy spawn event can have extra attributes with it, so we store as a dictionary
        # E.g. for orcs, we have a probability distribution, that can vary with levels,
        # which specifies how likely we are to spawn 1-3 orcs on each event trigger
        self.enemy_timers = []
        for enemy_to_spawn in level_data['enemies']:
            event = pygame.event.custom_type()
            pygame.time.set_timer(event, enemy_to_spawn['spawn_rate'])
            list_entry = {'type': enemy_to_spawn['type'], 'event': event}
            if list_entry['type'] in [Orc, Mummy]:
                list_entry['p'] = enemy_to_spawn['p']
            self.enemy_timers.append(list_entry)

        # Game over variable
        # Set to True if we die in this level and are in process of restarting transition
        # Just used so we don't draw the UI while transition is taking place (e.g. so we don't see -1 lives )
        self.game_over = False

    def create_bullet(self, pos, direction, damage, fired_by_player=True):
        # Passing in a unit vector, and position for where to start bullet
        # Pass in damage bullet has, as they have different surfaces for different damage bullets
        # If the player fires the bullet, it should be looking for collisions with enemies & bosses
        # Otherwise if a boss/enemy fires a bullet, we are looking for collisions with the player

        Bullet(
            pos=pos,
            direction=direction,
            damage=damage,
            surf=self.assets['bullets'][str(damage - 1)],
            colliding_sprites=self.bullet_colliding_sprites,
            enemy_sprites=self.enemy_sprites if fired_by_player else self.player_group,
            monster_hit_sound=self.audio['monster_hit'],
            groups=self.all_sprites
        )

    def create_random_drop(self, pos, prob_distribution):
        # Called when an enemy dies (bullet kills it, or collide with it in zombie mode)
        # Randomly creates a drop (coin or powerup) on floor, with probability distribution for specific enemy passed in

        random_drop = random.choices(list(prob_distribution.keys()), weights=list(prob_distribution.values()))[0]
        if random_drop != 'none':

            if random_drop == 'one' or random_drop == 'five':
                # Coin
                Coin(
                    pos=pos,
                    surf=self.assets['coin_drops'][random_drop],
                    value=1 if random_drop == 'one' else 5,
                    player=self.player,
                    groups=[self.all_sprites, self.coin_sprites]
                )

            else:
                # powerup
                Powerup(
                    pos=pos,
                    surf=self.assets['powerup_drops'][random_drop],
                    powerup_name=random_drop,
                    player=self.player,
                    groups=[self.all_sprites, self.powerup_sprites]
                )

    def create_particle_effect(self, pos, frames, death_duration=None):
        # Creates a particle sprite at specified position, that runs through its frames then kills itself
        # Option `death_duration` keeps particle sprite around for specified time on last time
        # (e.g. when an orc dies we keep green moss on floor for a while)

        ParticleEffect(
            pos=pos,
            frames=frames,
            groups=[self.all_sprites, self.particle_sprites],
            death_duration=death_duration
        )

    def spawn_bridge(self):

        StaticTile(
            pos=(8 * TILE_SIZE * ZOOM_FACTOR, 8 * TILE_SIZE * ZOOM_FACTOR),
            surf=self.assets['bridge_surf'],
            groups=self.all_sprites
        )

    def setup(self, level_data):
        # Use tmx data to create all the sprites in the groups

        tmx_data = load_pygame(level_data['tmx'])

        if 'Obstructables' in tmx_data.layernames:
            # The tiles that go around where enemies spawn into map. Players can collide with them, but not enemies
            # The ones in the bottom row of the map also need to be in a special group, as we need to remove them
            # if we complete the level
            for x, y, surf in tmx_data.get_layer_by_name('Obstructables').tiles():

                obstruct_groups = [self.all_sprites, self.player_collision_sprites]
                if y == 15 and x in [7, 8, 9]:
                    obstruct_groups.append(self.next_level_obstructable_sprites)

                StaticTile(
                    pos=(x * TILE_SIZE * ZOOM_FACTOR, y * TILE_SIZE * ZOOM_FACTOR),
                    surf=pygame.transform.scale_by(surf, ZOOM_FACTOR),
                    groups=obstruct_groups
                )

                if (x, y) in self.spikeball_positions:
                    self.spikeball_positions.remove((x, y))

        if 'Details' in tmx_data.layernames:
            for x, y, surf in tmx_data.get_layer_by_name('Details').tiles():
                # Extra details to just draw under everything
                StaticTile(
                    pos=(x * TILE_SIZE * ZOOM_FACTOR, y * TILE_SIZE * ZOOM_FACTOR),
                    surf=pygame.transform.scale_by(surf, ZOOM_FACTOR),
                    groups=self.all_sprites
                )

        if 'Obstacles' in tmx_data.layernames:
            # Tiles the player & enemies collide with, and also kill bullets (e.g. fences & logs)
            for x, y, surf in tmx_data.get_layer_by_name('Obstacles').tiles():

                StaticTile(
                    pos=(x * TILE_SIZE * ZOOM_FACTOR, y * TILE_SIZE * ZOOM_FACTOR),
                    surf=pygame.transform.scale_by(surf, ZOOM_FACTOR),
                    groups=[self.all_sprites, self.player_collision_sprites, self.enemy_collision_sprites, self.bullet_colliding_sprites],
                    z=Z_LAYERS['main']
                )

                self.matrix[y][x] = 0
                if (x, y) in self.spikeball_positions:
                    self.spikeball_positions.remove((x, y))

        if 'River' in tmx_data.layernames:
            # Players & enemies cannot walk over rivers
            for x, y, surf in tmx_data.get_layer_by_name('River').tiles():

                river_groups = [self.all_sprites, self.player_collision_sprites, self.enemy_collision_sprites]
                if x == 8 and y == 8:
                    river_groups.append(self.next_level_obstructable_sprites)

                StaticTile(
                    pos=(x * TILE_SIZE * ZOOM_FACTOR, y * TILE_SIZE * ZOOM_FACTOR),
                    surf=pygame.transform.scale_by(surf, ZOOM_FACTOR),
                    groups=river_groups
                )

                self.matrix[y][x] = 0
                if (x, y) in self.spikeball_positions:
                    self.spikeball_positions.remove((x, y))

        if 'Bridges' in tmx_data.layernames:
            # Essentially just extra detail to draw, has no interaction with game
            for x, y, surf in tmx_data.get_layer_by_name('Bridges').tiles():

                StaticTile(
                    pos=(x * TILE_SIZE * ZOOM_FACTOR, y * TILE_SIZE * ZOOM_FACTOR),
                    surf=pygame.transform.scale_by(surf, ZOOM_FACTOR),
                    groups=self.all_sprites
                )

                if (x, y) in self.spikeball_positions:
                    self.spikeball_positions.remove((x, y))

        if 'Animated' in tmx_data.layernames:
            for x, y, _ in tmx_data.get_layer_by_name('Animated').tiles():
                # E.g. trees that players & enemies collide with, but bulltes can shoot through

                AnimatedTile(
                    pos=(x * TILE_SIZE * ZOOM_FACTOR, y * TILE_SIZE * ZOOM_FACTOR),
                    frames=self.assets['animated_tile_frames'][level_data['type']],
                    groups=[self.all_sprites, self.player_collision_sprites, self.enemy_collision_sprites]
                )

                self.matrix[y][x] = 0
                if (x, y) in self.spikeball_positions:
                    self.spikeball_positions.remove((x, y))

        for obj in tmx_data.get_layer_by_name('Entities'):
            # Create player

            if obj.name == 'Player':
                self.start_position = (obj.x * ZOOM_FACTOR, obj.y * ZOOM_FACTOR)
                self.player = Player(
                    pos=(obj.x * ZOOM_FACTOR, obj.y * ZOOM_FACTOR),
                    collision_sprites=self.player_collision_sprites,
                    create_bullet=self.create_bullet,
                    game_data=self.game_data,
                    apply_nuke=self.apply_nuke,
                    apply_smoke_bomb=self.apply_smoke_bomb,
                    tombstone_timer=self.tombstone_timer,
                    apply_tombstone=self.apply_tombstone,
                    lightening_timer=self.lightening_timer,
                    audio=self.audio,
                    destroy_player=self.destroy_player,
                    groups=[self.all_sprites, self.player_group]
                )

            if obj.name == 'Shop Keeper':
                self.shop_keeper = ShopKeeper(
                    pos=(obj.x * ZOOM_FACTOR, obj.y * ZOOM_FACTOR),
                    surfs=self.assets['shop_keeper'],
                    player=self.player,
                    groups=[self.all_sprites, self.player_collision_sprites]
                )

            if obj.name == 'Boss':
                Cowboy(
                    pos=(obj.x * ZOOM_FACTOR, obj.y * ZOOM_FACTOR),
                    surfs=self.assets['boss']['cowboy'],
                    player=self.player,
                    health=level_data['boss_health'],
                    bullet_cooldown=level_data['bullet_cooldown'],
                    create_random_drop=self.create_random_drop,
                    create_bullet=self.create_bullet,
                    firing_strategy=level_data['firing_strategy'],
                    audio=self.audio,
                    groups=[self.all_sprites, self.enemy_sprites, self.boss_group]
                )

    def destroy_player(self):

        # Check game over state
        self.game_data.lives -= 1
        if self.game_data.lives == -1:
            self.audio['dead'].play()
            self.transition_to_restart()
            self.game_over = True

        # Explosion particle effect
        self.create_particle_effect(self.player.rect.center, self.assets['player_death'])

        # Put player back in start position
        self.player.reset_player(self.start_position)

        # De-activate all active upgrades
        self.smoke_bomb_timer.deactivate()
        assert not self.tombstone_timer.active and not self.lightening_timer.active

        # Extend level
        if self.level_timer_group.sprite is not None:
            self.level_timer_group.sprite.extend_level_duration()

        # Kill all enemies & any drops on the floor
        for spikeball in self.spikeball_sprites.sprites():
            self.add_position_to_spikeball_positions(spikeball.deploy_position)
        for enemy in filter(lambda s: not isinstance(s, Cowboy), self.enemy_sprites.sprites()):
            enemy.kill()
        for coin in self.coin_sprites.sprites():
            coin.kill()
        for powerup in self.powerup_sprites.sprites():
            powerup.kill()

    def check_player_enemy_collisions(self):
        # If player collides with any enemies, either kill the player if in normal mode, or the enemy if in zombie mode

        # Collision between enemies & player use their hit boxes
        collided_enemies = []
        for enemy in self.enemy_sprites.sprites():
            if enemy.hitbox.colliderect(self.player.hitbox):
                collided_enemies.append(enemy)

        if len(collided_enemies) > 0:
            # Colliding with an enemy, see if we are in zombie mode to know how to response (kill player or enemy)

            if self.tombstone_timer.active:
                # Destroy enemy
                # By 'destroy' we mean: kill it, spawn a particle effect, and potentially create a drop
                for enemy in collided_enemies:
                    enemy.die()

            else:
                # Destroy the player
                self.destroy_player()

    def pause_all_active_timers(self):
        # Pause all relevant timers when we go into lightening active mode

        self.paused_timers = []

        for timer in self.pause_able_timers:
            if timer.active:
                timer.pause()
                self.paused_timers.append(timer)

        for drop in (self.coin_sprites.sprites() + self.powerup_sprites.sprites()):
            if drop.collectable_timer.active:
                drop.collectable_timer.pause()
                self.paused_timers.append(drop.collectable_timer)
            if drop.destruct_timer.active:
                drop.destruct_timer.pause()
                self.paused_timers.append(drop.destruct_timer)

        for particle in self.particle_sprites.sprites():
            if particle.death_timer is not None and particle.death_timer.active:
                particle.death_timer.pause()
                self.paused_timers.append(particle.death_timer)
            if particle.delay_timer is not None and particle.delay_timer.active:
                particle.delay_timer.pause()
                self.paused_timers.append(particle.delay_timer)

    def un_pause_all_active_timers(self):
        # When we finish the lightening animation mode, unpause all the timers we paused before

        for timer in self.paused_timers:
            timer.un_pause()

        self.paused_timers = []

    def apply_zombie_mode(self):
        # Called when the lightening animation from applying the tombstone has finished
        # Puts us in the zombie mode

        self.un_pause_all_active_timers()
        self.tombstone_timer.activate()

    def apply_tombstone(self):
        # To apply the tombstone, we set the lightening timer active to do our lightening animation
        # Also during this active timer, we do the bare minimum in the run() method, basically just animate the player
        # We also pause all the timers, to unpause once the lightening animation is finished
        # Once the timer runs out, it will call `apply_zombie_mode` which puts us in zombie mode and restarts the timers

        self.lightening_timer.activate()
        self.pause_all_active_timers()

    def apply_smoke_bomb(self):

        # Teleport player to random spot
        self.player.random_teleport(self.enemy_sprites)

        # Flicker the player
        self.player.flash_timer.activate()

        # Smoke effects across the game map
        for smoke in range(10):
            ParticleEffect(
                pos=(random.randint(0, GAME_WIDTH), random.randint(0, GAME_HEIGHT)),
                frames=self.assets['nuke_smoke'],
                groups=[self.all_sprites, self.particle_sprites],
                delay=random.randint(0, 750)
            )

        # Activate timer for smoke bomb effect,
        # i.e. put a question mark over enemies heads & stop them moving until timer runs out
        self.smoke_bomb_timer.activate()

    def apply_nuke(self):

        # Play sound effect
        self.audio['nuke'].play()

        # Kill all the enemies
        for spikeball in self.spikeball_sprites.sprites():
            self.add_position_to_spikeball_positions(spikeball.deploy_position)
        for enemy in filter(lambda s: not isinstance(s, Cowboy), self.enemy_sprites.sprites()):
            enemy.kill()

        # Create smoke effects across the game map, that all start at different random timers (`delay`)
        for smoke in range(25):
            ParticleEffect(
                pos=(random.randint(0, GAME_WIDTH), random.randint(0, GAME_HEIGHT)),
                frames=self.assets['nuke_smoke'],
                groups=[self.all_sprites, self.particle_sprites],
                delay=random.randint(0, 750)
            )

    def check_coin_collision(self):
        # We pick up a coin drop by checking collision between the player's hit-box and the coins rect
        # Coins can only be picked up (attribute `collectable`) after a certain delay from when they were created

        for coin in filter(lambda s: s.collectable, self.coin_sprites.sprites()):
            if coin.rect.colliderect(self.player.hitbox):

                coin.kill()
                self.game_data.coins += coin.value

    def check_powerup_collision(self):
        # We pick up a powerup by checking collision between the player's hit-box and its rect
        # Powerups can only be picked up (attribute `collectable`) after a certain delay from when they were created

        for powerup in filter(lambda s: s.collectable, self.powerup_sprites.sprites()):

            # Although we check the lightening timer is not active when we call the function,
            # if we collide with multiple powerups and one of them activates the lightening effect,
            # we need to check on each iteration of the for loop
            if not self.lightening_timer.active:

                if powerup.rect.colliderect(self.player.hitbox):

                    powerup.kill()

                    if powerup.powerup_name == 'extra_life':
                        self.game_data.lives += 1
                        self.audio['powerup'].play()

                    else:
                        # If we have a stored powerup already, apply it immediately, otherwise store it
                        if self.game_data.stored_powerup is None:
                            self.game_data.stored_powerup = powerup.powerup_name
                            self.audio['powerup'].play()
                        else:
                            self.player.apply_powerup(powerup.powerup_name)
                            if powerup.powerup_name not in ['machine_gun', 'nuke']:
                                self.audio['powerup'].play()

    def check_next_level(self):
        # We can move to the next level, once the level has been completed, which removes the rocks and allows
        # the player to move out of the screen to the bottom

        if self.player.hitbox.top >= GAME_HEIGHT:
            self.transition_to_next_level()

    def update_timers(self):

        self.smoke_bomb_timer.update()
        self.lightening_timer.update()
        self.tombstone_timer.update()
        self.level_timer_group.update()

    def add_position_to_spikeball_positions(self, position):
        # When a spikeball is spawned and we randomly pick a position to deploy it at,
        # we remove that position from the list of possible deploy positions so future ones cannot spawn there
        # But when a spikeball dies, we need to add it back, which is what this function does
        # We pass this function as a reference into spikeball's to call when they die
        # Also called when we kill all enemies, e.g. on death or nuke

        self.spikeball_positions.append(position)

    def spawn_enemy(self, event):

        if self.lightening_timer.active:
            return

        if self.level_timer_group.sprite is None or not self.level_timer_group.sprite.is_level_timer_active():
            return

        for enemy_timer in self.enemy_timers:

            if event.type == enemy_timer['event']:

                # Based on enemy type we use a certain spawn strategy

                if enemy_timer['type'] == Spikeball:

                    # Pick where we're spawning at
                    random_tile = random.choice(['1', '2', '3'])
                    side_to_spawn = random.choice(['top', 'left', 'bottom', 'right'])

                    # Randomly pick the position we're going to deploy at, and create the AStar Finder object
                    random_deploy_position = random.choice(self.spikeball_positions)
                    end = self.grid.node(*random_deploy_position)
                    finder = AStarFinder()

                    # Remove this randomly picked position from possible list, so future spikeballs don't get there too
                    # When it dies, we will add it back to the list
                    self.spikeball_positions.remove(random_deploy_position)

                    # Get the grid position for where we're spawning at
                    # and the start node for the path algorithm,

                    if side_to_spawn in ['top', 'bottom']:

                        x = 6 + int(random_tile)
                        y = -1 if side_to_spawn == 'top' else 16
                        start = self.grid.node(x, 0 if side_to_spawn == 'top' else 15)

                    else:

                        x = -1 if side_to_spawn == 'left' else 16
                        y = 6 + int(random_tile)
                        start = self.grid.node(0 if side_to_spawn == 'left' else 15, y)

                    pos = pygame.math.Vector2(x, y) * TILE_SIZE * ZOOM_FACTOR
                    path_to_deploy, _ = finder.find_path(start, end, self.grid)
                    self.grid.cleanup()

                    Spikeball(
                        frames=self.assets['enemies'][Spikeball],
                        pos=pos,              # pixel start position (off the grid)
                        path=path_to_deploy,  # path in terms of grid positions
                        deploy_position=random_deploy_position,
                        create_particle_effect=self.create_particle_effect,
                        create_random_drop=self.create_random_drop,
                        smoke_bomb_timer=self.smoke_bomb_timer,
                        add_position_to_spikeball_positions=self.add_position_to_spikeball_positions,
                        groups=[self.all_sprites, self.enemy_sprites, self.spikeball_sprites]
                    )

                else:

                    enemies_to_spawn = []  # list of (top-left positions, initial direction) for enemies

                    if enemy_timer['type'] in [Orc, Mummy]:
                        # At a random side, generate 1-3 orcs, in a random orientation
                        # Orientation (1, 2, 3) is L-to-R for top & bottom, and T-to-B for left & right

                        number_to_spawn = random.choices([1, 2, 3], weights=enemy_timer['p'], k=1)[0]
                        orientations = np.random.choice(('1', '2', '3'), number_to_spawn, replace=False)
                        side_to_spawn = random.choice(['top', 'left', 'bottom', 'right'])
                        collision_sprites = self.enemy_collision_sprites

                        if side_to_spawn in ['top', 'bottom']:

                            for orientation in orientations:

                                x = (6 + int(orientation)) * TILE_SIZE * ZOOM_FACTOR
                                y = (-1 if side_to_spawn == 'top' else 16) * TILE_SIZE * ZOOM_FACTOR
                                init_direction = pygame.math.Vector2(0, 1 if side_to_spawn == 'top' else -1)
                                enemies_to_spawn.append(((x, y), init_direction))

                        else:

                            for orientation in orientations:

                                x = (-1 if side_to_spawn == 'left' else 16) * TILE_SIZE * ZOOM_FACTOR
                                y = (6 + int(orientation)) * TILE_SIZE * ZOOM_FACTOR
                                init_direction = pygame.math.Vector2(1 if side_to_spawn == 'left' else -1, 0)
                                enemies_to_spawn.append(((x, y), init_direction))

                    elif enemy_timer['type'] in [Ogre, Mushroom]:

                        random_tile = random.choice(['1', '2', '3'])
                        side_to_spawn = random.choice(['top', 'left', 'bottom', 'right'])
                        collision_sprites = self.enemy_collision_sprites

                        if side_to_spawn in ['top', 'bottom']:

                            x = (6 + int(random_tile)) * TILE_SIZE * ZOOM_FACTOR
                            y = (-1 if side_to_spawn == 'top' else 16) * TILE_SIZE * ZOOM_FACTOR
                            init_direction = pygame.math.Vector2(0, 1 if side_to_spawn == 'top' else -1)
                            enemies_to_spawn.append(((x, y), init_direction))

                        else:

                            x = (-1 if side_to_spawn == 'left' else 16) * TILE_SIZE * ZOOM_FACTOR
                            y = (6 + int(random_tile)) * TILE_SIZE * ZOOM_FACTOR
                            init_direction = pygame.math.Vector2(1 if side_to_spawn == 'left' else -1, 0)
                            enemies_to_spawn.append(((x, y), init_direction))

                    elif enemy_timer['type'] in [Butterfly, Imp]:
                        # Unique things about the butterfly are:
                        # - Can spawn anywhere on the sides, not constrained to the 3 tiles on each side for land enemies
                        # - Can fly over obstacles, so their collision sprites need to be different

                        collision_sprites = self.flying_enemy_collision_sprites  # empty group
                        side_to_spawn = random.choice(['top', 'left', 'bottom', 'right'])

                        # Based on the random side we picked, place in the middle 80% of the game width/height
                        # The initial direction vector is then into the center of the map
                        # The vector to the center is calculated wrt. (x, y) which is technically the top-left
                        # not the center, but in reality isn't going to make much difference
                        if side_to_spawn in ['top', 'bottom']:

                            x = random.randint(int(0.1 * GAME_WIDTH), int(0.9 * GAME_WIDTH))
                            y = (-1 if side_to_spawn == 'top' else 16) * TILE_SIZE * ZOOM_FACTOR

                        else:

                            x = (-1 if side_to_spawn == 'left' else 16) * TILE_SIZE * ZOOM_FACTOR
                            y = random.randint(int(0.1 * GAME_HEIGHT), int(0.9 * GAME_HEIGHT))

                        unit_vector_to_center = (pygame.math.Vector2(GAME_WIDTH / 2, GAME_HEIGHT / 2) - pygame.math.Vector2(x, y)).normalize()
                        enemies_to_spawn.append(((x, y), unit_vector_to_center))

                    groups = [self.all_sprites, self.enemy_sprites]
                    if enemy_timer['type'] == Ogre:
                        groups.append(self.ogre_sprites)

                    for new_enemy in enemies_to_spawn:

                        enemy_timer['type'](
                            frames=self.assets['enemies'][enemy_timer['type']],
                            pos=new_enemy[0],
                            initial_direction=new_enemy[1],
                            collision_sprites=collision_sprites,
                            player=self.player,
                            create_particle_effect=self.create_particle_effect,
                            create_random_drop=self.create_random_drop,
                            smoke_bomb_timer=self.smoke_bomb_timer,
                            tombstone_timer=self.tombstone_timer,
                            groups=groups
                        )

    def check_ogre_spikeball_collisions(self):

        for spikeball in self.spikeball_sprites.sprites():
            # Go through all the spike balls and look for collisions with ogres
            # Ogres kill spikeballs if they are deployed on contact with them
            # (But we don't generate a random drop from this kind of death)
            if spikeball.status != 'deployed':
                continue
            collides_with_ogre = False
            for ogre in self.ogre_sprites.sprites():
                if ogre.hitbox.colliderect(spikeball.hitbox):
                    collides_with_ogre = True
            if collides_with_ogre:
                spikeball.die()

    def run(self, dt):

        # Update timers

        self.update_timers()

        # Event loop

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            self.spawn_enemy(event)

        # Updates
        # We call all the functions, that might only be relevant to certain subclasses
        # E.g. we check for coin collisions, even though can be no coins in shop levels
        # But this is fine, as that group will be empty an essentially do nothing, for example
        # Similarly, we update the shop group single, but if we're not on shop mode, group will be empty and do nothing

        if not self.lightening_timer.active:
            self.all_sprites.update(dt)

        if not self.lightening_timer.active:
            self.check_coin_collision()
            self.check_powerup_collision()

        if not self.lightening_timer.active:

            self.shop_group.update()
            self.check_ogre_spikeball_collisions()
            self.check_player_enemy_collisions()
            self.check_level_completed()
            self.check_next_level()

        if self.lightening_timer.active:
            self.player.update(dt)

        # Drawing

        self.all_sprites.custom_draw(self.lightening_timer.active, self.smoke_bomb_timer.active, self.player, self.level_completed, self.shop_group)
        if not self.game_over:
            self.ui.display(self.level_timer_group, self.boss_group)
