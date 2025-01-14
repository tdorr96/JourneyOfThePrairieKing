import math
import pygame
from settings import *


class Enemy(pygame.sprite.Sprite):

    def __init__(self, frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups):

        super().__init__(groups)

        # Image & animation
        self.frames = frames['run']
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.animation_speed = 6
        self.z = self.Z
        self.ashes_frames = frames['ashes']

        # Rect, hit-box & float-based movement
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-self.rect.width / 4, -self.rect.height / 4)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.direction = pygame.math.Vector2()
        self.speed = self.SPEED * ZOOM_FACTOR

        # Initial direction
        # When we spawn an enemy, we keep moving it inwards to the game map until we reach a certain point
        # Only then do we start it moving towards the player
        # When initial direction gets set to the empty vector we know we've moved in enough to start following player
        self.initial_direction = initial_direction

        # Store attributes and function references
        self.player = player
        self.collision_sprites = collision_sprites
        self.create_particle_effect = create_particle_effect
        self.create_random_drop = create_random_drop
        self.smoke_bomb_timer = smoke_bomb_timer
        self.tombstone_timer = tombstone_timer

        # Health
        self.health = self.INITIAL_HEALTH

    def damage(self, damage):
        # Called when bullet collides with us, takes damage off enemies health. Different bullets have different damage

        self.health -= damage
        if self.health <= 0:
            self.die()

    def die(self):
        # When enemy dies, we don't just kill() it
        # We also create a particle effect and possible spawn a random drop

        self.kill()
        self.create_particle_effect(self.rect.center, self.ashes_frames, self.PARTICLE_EFFECT_DEATH_DURATION)
        self.create_random_drop(self.rect.center, self.POWERUP_DROP_RATES)

    def collision(self, axis):

        for obstacle in self.collision_sprites.sprites():
            if obstacle.rect.colliderect(self.hitbox):

                if axis == 'x':

                    if self.direction.x > 0:
                        self.hitbox.right = obstacle.rect.left
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                    elif self.direction.x < 0:
                        self.hitbox.left = obstacle.rect.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                elif axis == 'y':

                    if self.direction.y > 0:
                        self.hitbox.bottom = obstacle.rect.top
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery

                    elif self.direction.y < 0:
                        self.hitbox.top = obstacle.rect.bottom
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery

    def initial_movement(self):
        # When we spawn an enemy we move in the initial direction vector till we're two full tiles inside the game map
        # When this is true we set the initial direction vector to (0, 0) so we know to not use it anymore

        if self.initial_direction.magnitude() > 0:
            # Once the initial direction gets set to (0, 0) it never changes, so this check stops us re-calculating
            # if player is within the game board once initial direction movement is disabled
            # I.e. check we have not yet disabled the initial direction movement

            two_tile_deep = 2 * TILE_SIZE * ZOOM_FACTOR
            if self.rect.left >= two_tile_deep and self.rect.top >= two_tile_deep and self.rect.right <= (GAME_WIDTH - two_tile_deep) and self.rect.bottom <= (GAME_HEIGHT - two_tile_deep):
                self.initial_direction = pygame.math.Vector2()

    def move(self, dt):
        # Three cases, in order of priority:
        # 1) If smoke bomb is active, we don't move them at all
        # 2) Otherwise if we have not long spawned we only move inwards into the game map, based on an initial direction
        # 3) Once we've moved inwards enough we disable the initial direction movement, and start moving towards player

        if self.smoke_bomb_timer.active:
            # If smoke bomb powerup is active, the enemy does not move - just animates on the spot
            return

        # We know we're going to move, so check if we're still moving in initial direction or we can follow the player
        self.initial_movement()

        if self.initial_direction.magnitude() > 0:
            # We have not disabled the initial direction yet as we're still not far enough into the game map
            self.direction = self.initial_direction.copy()

        else:
            # Normal movement (i.e. finished initial movement onto game board)
            # If zombie mode is active, we move in a direction vector the direct line away from player
            # Otherwise, we take our current direction vector and nudge it towards the player each frame

            vector_to_player = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)
            unit_vector_to_player = vector_to_player.normalize()

            if self.tombstone_timer.active:
                self.direction = unit_vector_to_player * -1
            else:
                # We are going to take two vectors:
                # - the current direction (momentum of movement)
                # - the direction towards the player we're trying to nudge the current direction
                # and combine to make a new vector slightly more in the direction of the player
                # We could just add the vectors and re-normalize but this is calculated so frequently
                # So we scale the vector we're trying to nudge the direction in to make this happen slower
                # We scale it based on the angle between the vectors,
                # - So a large angle (i.e. totally opposite direction) is taken more into account in resulting vector
                # - But a smaller angle (i.e. already quite close on track) is taken less into account
                dot_value = self.direction.dot(unit_vector_to_player)
                # Sometimes due to floating-point precision dot_value is e.g. 1.000000002, just make sure to truncate
                if dot_value > 1:
                    dot_value = 1
                elif dot_value < -1:
                    dot_value = -1
                angle = math.degrees(math.acos(dot_value))
                self.direction = (self.direction + (unit_vector_to_player * angle * self.MOMENTUM_FACTOR)).normalize()

        # Horizontal movement & collision
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('x')

        # Constrain reverse zombie mode movement to keep on game window
        # We could still try and move outside the window if zombie mode is not active due to momentum direction vector
        # So just check that initial direction movement has been disabled
        if self.initial_direction.magnitude() == 0:
            if self.rect.left < 0:
                self.rect.left = 0
                self.hitbox.centerx = self.rect.centerx
                self.pos.x = self.rect.centerx
            if self.rect.right > GAME_WIDTH:
                self.rect.right = GAME_WIDTH
                self.hitbox.centerx = self.rect.centerx
                self.pos.x = self.rect.centerx

        # Vertical movement & collision
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('y')

        # Constrain reverse zombie mode movement to keep on game window
        if self.initial_direction.magnitude() == 0:
            if self.rect.top < 0:
                self.rect.top = 0
                self.hitbox.centery = self.rect.centery
                self.pos.y = self.rect.centery
            if self.rect.bottom > GAME_HEIGHT:
                self.rect.bottom = GAME_HEIGHT
                self.hitbox.centery = self.rect.centery
                self.pos.y = self.rect.centery

    def animate(self, dt):
        # Just simple run animation between two frames

        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def update(self, dt):

        self.move(dt)
        self.animate(dt)


class Spikeball(pygame.sprite.Sprite):
    # A very different type of enemy
    # When created, we randomly choose a position on the map where it is going to deploy, and use pathfinding
    # to create that path. Hence it does not need a lot of the logic (e.g. collisions) of base enemy class
    # Also when ogres collide with this enemy type if we're deployed we get destroyed

    # Has a health of 2 while moving, and 7 while deployed
    # But damage done while moving effective after it deploys, so if health was 1 when deployed, has 3 not 7
    HEALTH = {
        'initial': 2,
        'deployed': {
            2: 7,
            1: 3
        }
    }
    Z = Z_LAYERS['main']
    SPEED = 35
    MOMENTUM_FACTOR = 0.001
    PARTICLE_EFFECT_DEATH_DURATION = 10000
    # Only has a chance to drop if killed when moving, not deployed
    POWERUP_DROP_RATES = {
        # coins
        'one': 30,
        'five': 20,
        # powerups
        'coffee': 2,
        'extra_life': 3,
        'machine_gun': 3,
        'nuke': 2,
        'sheriff_badge': 3,
        'shotgun': 2,
        'smoke_bomb': 2,
        'tombstone': 2,
        'wagon_wheel': 3,
        'none': 250
    }

    def __init__(self, frames, pos, path, deploy_position, create_particle_effect, create_random_drop, smoke_bomb_timer, add_position_to_spikeball_positions, groups):

        super().__init__(groups)

        # Image & animation
        self.frames = frames
        self.status = 'run'  # 'run', 'deploying', or 'deployed'
        self.frame_index = 0
        self.image = self.frames[self.status][self.frame_index]
        self.animation_speed = {
            'run': 6,
            'deploying': 3
        }
        self.z = self.Z

        # Rect, hit-box & float-based movement
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-self.rect.width / 4, -self.rect.height / 4)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = self.SPEED * ZOOM_FACTOR
        self.path = path
        self.next_grid = 0  # Index in self.path of where we are aiming for

        # Attributes
        self.deploy_position = deploy_position
        self.create_particle_effect = create_particle_effect
        self.create_random_drop = create_random_drop
        self.smoke_bomb_timer = smoke_bomb_timer
        self.add_position_to_spikeball_positions = add_position_to_spikeball_positions

        # Health
        self.health = self.HEALTH['initial']

    def damage(self, damage):
        # Called when bullet collides with us, takes damage off enemies health. Different bullets have different damage

        self.health -= damage
        if self.health <= 0:
            self.die()

    def die(self):
        # When enemy dies, we don't just kill() it
        # We also create a particle effect and possible spawn a random drop
        # For spike ball, we only spawn a particle effect if not deployed
        # Call a function in the level to re-add its deploy position back to possible options list for future spikeballs

        self.kill()
        self.create_particle_effect(self.rect.center, self.frames['ashes'], self.PARTICLE_EFFECT_DEATH_DURATION)
        self.add_position_to_spikeball_positions(self.deploy_position)
        if self.status != 'deployed':
            self.create_random_drop(self.rect.center, self.POWERUP_DROP_RATES)

    def update(self, dt):

        self.move(dt)
        self.animate(dt)

    def animate(self, dt):

        if self.status == 'run':
            current_animation = self.frames[self.status]
            self.frame_index += self.animation_speed[self.status] * dt
            if self.frame_index >= len(current_animation):
                self.frame_index = 0
            self.image = current_animation[int(self.frame_index)]

        elif self.status == 'deploying':
            current_animation = self.frames[self.status]
            self.frame_index += self.animation_speed[self.status] * dt
            if self.frame_index >= len(current_animation):
                # Move to deployed stage. Update our health and set the image as it no longer animates after this
                self.health = self.HEALTH['deployed'][self.health]
                self.status = 'deployed'
                self.image = self.frames['deployed'][0]
                self.z = Z_LAYERS['deployed_spikeball']
            else:
                self.image = current_animation[int(self.frame_index)]

    def move(self, dt):

        if self.status == 'run' and not self.smoke_bomb_timer.active:

            # Figure out the unit vector to move rect in direction of next grid on path
            target_grid_pos = (self.path[self.next_grid].x, self.path[self.next_grid].y)
            target_pixel_pos = pygame.math.Vector2(target_grid_pos) * TILE_SIZE * ZOOM_FACTOR
            distance_vector = target_pixel_pos - pygame.math.Vector2(self.rect.topleft)
            direction = distance_vector.normalize()

            # Do the movement
            self.pos += direction * self.speed * dt
            self.hitbox.center = (round(self.pos.x), round(self.pos.y))
            self.rect.center = self.hitbox.center

            # See if we've reached the target grid position
            moved_distance_vector = target_pixel_pos - pygame.math.Vector2(self.rect.topleft)

            if moved_distance_vector.magnitude() < 5:
                # We've reached the next grid

                # Increment the target grid position. If at last position on path (i.e. where to deploy) change status
                self.next_grid += 1
                if self.next_grid == len(self.path):
                    self.status = 'deploying'
                    self.frame_index = 0

                # Fully align the rects
                self.rect.topleft = target_pixel_pos
                self.hitbox.center = self.rect.center
                self.pos = pygame.math.Vector2(self.rect.center)


class Ogre(Enemy):

    INITIAL_HEALTH = 3
    Z = Z_LAYERS['main']
    SPEED = 20
    MOMENTUM_FACTOR = 0.001
    PARTICLE_EFFECT_DEATH_DURATION = 10000
    POWERUP_DROP_RATES = {
        # coins
        'one': 35,
        'five': 10,
        # powerups
        'coffee': 3,
        'extra_life': 3,
        'machine_gun': 2,
        'nuke': 2,
        'sheriff_badge': 2,
        'shotgun': 2,
        'smoke_bomb': 2,
        'tombstone': 2,
        'wagon_wheel': 3,
        'none': 250
    }

    def __init__(self, frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups):

        super().__init__(frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups)


class Orc(Enemy):

    INITIAL_HEALTH = 1
    Z = Z_LAYERS['main']
    SPEED = 30
    MOMENTUM_FACTOR = 0.001
    PARTICLE_EFFECT_DEATH_DURATION = 10000
    POWERUP_DROP_RATES = {
        # coins
        'one': 35,
        'five': 0,
        # powerups
        'coffee': 4,
        'extra_life': 2,
        'machine_gun': 3,
        'nuke': 3,
        'sheriff_badge': 1,
        'shotgun': 4,
        'smoke_bomb': 4,
        'tombstone': 3,
        'wagon_wheel': 4,
        'none': 250
    }

    def __init__(self, frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups):

        super().__init__(frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups)


class Mummy(Enemy):

    INITIAL_HEALTH = 6
    Z = Z_LAYERS['main']
    SPEED = 10
    MOMENTUM_FACTOR = 0.001
    PARTICLE_EFFECT_DEATH_DURATION = None
    POWERUP_DROP_RATES = {
        # coins
        'one': 25,
        'five': 10,
        # powerups
        'coffee': 2,
        'extra_life': 5,
        'machine_gun': 3,
        'nuke': 3,
        'sheriff_badge': 4,
        'shotgun': 3,
        'smoke_bomb': 2,
        'tombstone': 2,
        'wagon_wheel': 2,
        'none': 250
    }

    def __init__(self, frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups):

        super().__init__(frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups)


class Mushroom(Enemy):

    INITIAL_HEALTH = 2
    Z = Z_LAYERS['main']
    SPEED = 50
    MOMENTUM_FACTOR = 0.005
    PARTICLE_EFFECT_DEATH_DURATION = 10000
    POWERUP_DROP_RATES = {
        # coins
        'one': 25,
        'five': 10,
        # powerups
        'coffee': 4,
        'extra_life': 2,
        'machine_gun': 3,
        'nuke': 3,
        'sheriff_badge': 1,
        'shotgun': 4,
        'smoke_bomb': 4,
        'tombstone': 3,
        'wagon_wheel': 4,
        'none': 250
    }

    def __init__(self, frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups):

        super().__init__(frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups)


class Butterfly(Enemy):

    INITIAL_HEALTH = 1
    Z = Z_LAYERS['flying_enemies']
    SPEED = 25
    MOMENTUM_FACTOR = 0.001
    PARTICLE_EFFECT_DEATH_DURATION = None
    POWERUP_DROP_RATES = {
        # coins
        'one': 30,
        'five': 5,
        # powerups
        'coffee': 4,
        'extra_life': 2,
        'machine_gun': 3,
        'nuke': 3,
        'sheriff_badge': 1,
        'shotgun': 4,
        'smoke_bomb': 4,
        'tombstone': 3,
        'wagon_wheel': 4,
        'none': 250
    }

    def __init__(self, frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups):

        super().__init__(frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups)


class Imp(Enemy):

    INITIAL_HEALTH = 3
    Z = Z_LAYERS['flying_enemies']
    SPEED = 35
    MOMENTUM_FACTOR = 0.002
    PARTICLE_EFFECT_DEATH_DURATION = None
    POWERUP_DROP_RATES = {
        # coins
        'one': 25,
        'five': 10,
        # powerups
        'coffee': 4,
        'extra_life': 2,
        'machine_gun': 3,
        'nuke': 3,
        'sheriff_badge': 1,
        'shotgun': 4,
        'smoke_bomb': 4,
        'tombstone': 3,
        'wagon_wheel': 4,
        'none': 250
    }

    def __init__(self, frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups):

        super().__init__(frames, pos, initial_direction, collision_sprites, player, create_particle_effect, create_random_drop, smoke_bomb_timer, tombstone_timer, groups)
