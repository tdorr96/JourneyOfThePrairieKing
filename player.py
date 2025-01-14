import math
import pygame
import random
from settings import *
from util import import_folder, Timer, rotate_vector, import_image


class Player(pygame.sprite.Sprite):

    def __init__(self, pos, collision_sprites, create_bullet, game_data, apply_nuke, apply_smoke_bomb, tombstone_timer, apply_tombstone, lightening_timer, audio, destroy_player, groups):

        super().__init__(groups)

        # Attributes & function call references
        self.game_data = game_data
        self.collision_sprites = collision_sprites
        self.create_bullet = create_bullet
        self.apply_nuke = apply_nuke
        self.apply_smoke_bomb = apply_smoke_bomb
        self.tombstone_timer = tombstone_timer
        self.apply_tombstone = apply_tombstone
        self.lightening_timer = lightening_timer
        self.destroy_player = destroy_player

        # Audio
        self.gun_shot_sound = audio['gunshot']
        self.footstep_sound = audio['footstep']
        self.footstep_timer = Timer(250)
        self.machine_gun_sound = audio['machine_gun']

        # Image & animation
        self.import_assets()
        self.status = 'idle'
        self.frame_index = 0
        self.image = self.animations[self.status][self.frame_index]
        self.animation_speed = 8
        self.z = Z_LAYERS['main']

        # Rect, hit-box, & float-based movement
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-self.rect.width/4, -self.rect.height/4)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.direction = pygame.math.Vector2()

        # Speed attributes
        self.default_speed = 50 * ZOOM_FACTOR  # Need to scale with zoom size
        self.sheriff_speed = self.default_speed * 1.4
        self.coffee_speed = self.default_speed * 1.5
        self.zombie_speed = self.default_speed * 2.0

        # Bullet attributes
        self.default_bullet_cooldown = 300
        self.sheriff_bullet_cooldown = int(self.default_bullet_cooldown * 0.33)
        self.machine_gun_bullet_cooldown = int(self.default_bullet_cooldown * 0.25)
        self.direction_shooting = None

        # Every time we create a player, the default speed and bullet cooldown are fixed, as are the buffs for powerups
        # What can be affected is the base speed & bullet fire speed, which depends on what upgrades have been purchased
        # So by purchasing upgrades our base attributes increase, but when powerups are active, they are calculated
        # from that fixed default speed (i.e. don't stack on-top of purchases)
        self.calculate_base_stats()

        # Timers
        self.bullet_cooldown = Timer(self.base_bullet_cooldown)
        self.flash_timer = Timer(1500)
        self.coffee_timer = Timer(10000)
        self.sheriff_timer = Timer(20000)
        self.machine_gun_timer = Timer(8000)
        self.shotgun_timer = Timer(10000)
        self.wagon_wheel_timer = Timer(7000)

    def damage(self, bullet_damage):
        # Called when a boss bullet hits the player

        assert not self.lightening_timer.active
        if not self.tombstone_timer.active:
            # Invincible in zombie mode
            self.destroy_player()

    def calculate_active_bullet_cooldown(self):
        # Calculate the bullet cooldown timer's duration based on the active buffs

        active_bullet_cooldowns = [self.base_bullet_cooldown]  # Base cooldown can change with purchasing gun upgrades

        if self.sheriff_timer.active:
            active_bullet_cooldowns.append(self.sheriff_bullet_cooldown)
        if self.machine_gun_timer.active:
            active_bullet_cooldowns.append(self.machine_gun_bullet_cooldown)

        return min(active_bullet_cooldowns)

    def update_timers(self):

        self.flash_timer.update()
        self.coffee_timer.update()
        self.sheriff_timer.update()
        self.machine_gun_timer.update()
        self.shotgun_timer.update()
        self.wagon_wheel_timer.update()
        self.footstep_timer.update()

        # Update other timers first, as the bullet cooldown duration depends on other timers
        self.bullet_cooldown.duration = self.calculate_active_bullet_cooldown()
        self.bullet_cooldown.update()

    def calculate_base_stats(self):
        # Uses the game data to set our base stats (speed, bullet cooldown, and bullet damage)
        # Called whenever we initialise player (on level init) or when we purchase an upgrade (in shop level mode)
        # Upgrading our speed and bullet cooldown makes us faster & shoot more frequently with each upgrade
        # Up to the maximum upgrade, which is just under the best powerup buff for that attribute

        # SPEED

        if self.game_data.upgrades['boots'] == -1:
            self.base_speed = self.default_speed
        elif self.game_data.upgrades['boots'] == 0:
            self.base_speed = self.default_speed * 1.2
        elif self.game_data.upgrades['boots'] == 1:
            self.base_speed = self.default_speed * 1.35

        # BULLET COOLDOWN

        if self.game_data.upgrades['gun'] == -1:
            self.base_bullet_cooldown = self.default_bullet_cooldown
        elif self.game_data.upgrades['gun'] == 0:
            self.base_bullet_cooldown = int(self.default_bullet_cooldown * 0.8)
        elif self.game_data.upgrades['gun'] == 1:
            self.base_bullet_cooldown = int(self.default_bullet_cooldown * 0.6)
        elif self.game_data.upgrades['gun'] == 2:
            self.base_bullet_cooldown = int(self.default_bullet_cooldown * 0.4)

        # BULLET DAMAGE

        if self.game_data.upgrades['ammo'] == -1:
            self.bullet_damage = 1
        elif self.game_data.upgrades['ammo'] == 0:
            self.bullet_damage = 2
        elif self.game_data.upgrades['ammo'] == 1:
            self.bullet_damage = 3
        elif self.game_data.upgrades['ammo'] == 2:
            self.bullet_damage = 4

    def reset_player(self, reset_position):
        # Called on death (collision with enemy)

        # Put player back to start position
        self.rect.center = reset_position
        self.hitbox.center = self.rect.center
        self.pos = pygame.math.Vector2(self.rect.center)

        # Make the player flash for a bit
        self.flash_timer.activate()

        # De-activate all powerups
        self.coffee_timer.deactivate()
        self.machine_gun_timer.deactivate()
        self.shotgun_timer.deactivate()
        self.wagon_wheel_timer.deactivate()
        self.sheriff_timer.deactivate()

    def import_assets(self):

        self.animations = {}

        self.animations['idle'] = [import_image('graphics/player/idle.png')]
        self.animations['zombie'] = import_folder('graphics/player/zombie')
        self.animations['lightening'] = import_folder('graphics/player/lightening')

        for direction in ['down', 'left', 'right', 'up']:
            self.animations[direction] = import_folder('graphics/player/moving/%s/' % direction)

    def apply_powerup(self, powerup_name):
        # Activate a powerup, either called because
        # - We had one stored and pressed space
        # - We already had one stored and collected another

        if powerup_name == 'coffee':
            self.coffee_timer.activate()

        elif powerup_name == 'machine_gun':
            self.machine_gun_timer.activate()
            self.machine_gun_sound.play()

        elif powerup_name == 'nuke':
            self.apply_nuke()

        elif powerup_name == 'smoke_bomb':
            self.apply_smoke_bomb()

        elif powerup_name == 'shotgun':
            self.shotgun_timer.activate()

        elif powerup_name == 'wagon_wheel':
            self.wagon_wheel_timer.activate()

        elif powerup_name == 'tombstone':
            self.apply_tombstone()
            self.flash_timer.deactivate()

        elif powerup_name == 'sheriff_badge':
            self.sheriff_timer.activate()

    def random_teleport(self, enemy_sprites):
        # Randomly teleport player to anywhere on map but make sure that position
        # - isn't somewhere we can't be on (i.e. doesn't collide with collision sprites)
        # - doesn't collide with any of the enemies
        # - not off the map
        # Not the most optimal way, but keep randomly generating coordinates until it meets those conditions
        # Although ordinarily we use hit-boxes for collisions, by using rects it gives us a bit more room away
        # from those objects, which is a feature I want

        coordinates_found = False
        while not coordinates_found:

            # represent the top left of the rect
            random_x, random_y = random.randint(0, GAME_WIDTH), random.randint(0, GAME_HEIGHT)

            new_rect = self.rect.copy()
            new_rect.topleft = (random_x, random_y)

            # 1) check it's on the map
            if new_rect.left < 0 or new_rect.right > GAME_WIDTH or new_rect.top < 0 or new_rect.bottom > GAME_HEIGHT:
                continue

            # 2) check doesn't collide with any of the collide-able tiles
            if new_rect.collidelist([s.rect for s in self.collision_sprites.sprites()]) != -1:
                continue

            # 3) not colliding with any enemies
            if new_rect.collidelist([e.rect for e in enemy_sprites.sprites()]) != -1:
                continue

            coordinates_found = True

        # Change actual position of player (rect, hit-box, and position vector)
        self.rect.topleft = (random_x, random_y)
        self.hitbox.center = self.rect.center
        self.pos = pygame.math.Vector2(self.rect.center)

    def input(self):

        keys = pygame.key.get_pressed()

        # Movement

        if keys[pygame.K_w]:
            self.direction.y = -1
        elif keys[pygame.K_s]:
            self.direction.y = 1
        else:
            self.direction.y = 0

        if keys[pygame.K_d]:
            self.direction.x = 1
        elif keys[pygame.K_a]:
            self.direction.x = -1
        else:
            self.direction.x = 0

        # Apply power up if we have stored one

        if keys[pygame.K_SPACE] and self.game_data.stored_powerup is not None:
            self.apply_powerup(self.game_data.stored_powerup)
            self.game_data.stored_powerup = None

        # Bullet shooting, only if not in zombie mode

        if not self.tombstone_timer.active and not self.bullet_cooldown.active:

            up_pressed = keys[pygame.K_UP]
            down_pressed = keys[pygame.K_DOWN]
            left_pressed = keys[pygame.K_LEFT]
            right_pressed = keys[pygame.K_RIGHT]

            if up_pressed or down_pressed or left_pressed or right_pressed:
                # We know we're pressing - time to create bullet(s)

                # Find the direction we're going to face for animation
                if right_pressed:
                    self.direction_shooting = 'right'
                elif left_pressed:
                    self.direction_shooting = 'left'
                elif down_pressed:
                    self.direction_shooting = 'down'
                else:
                    self.direction_shooting = 'up'

                # Activate the bullet cooldown timer and play gunshot sound
                self.bullet_cooldown.activate()
                self.gun_shot_sound.play()

                # Build up a list of bullets to create, either 8 for wagon wheel active, or 1 otherwise
                # For each of these bullets to create, later on we will create an extra 2 per if shotgun/sheriff active
                bullets_to_create = []  # (unit vector direction, position)

                if self.wagon_wheel_timer.active:

                    for direction in [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]:
                        bullets_to_create.append((
                            pygame.math.Vector2(direction).normalize(),
                            pygame.math.Vector2(
                                self.hitbox.centerx + direction[0] * self.hitbox.width/2,
                                self.hitbox.centery + direction[1] * self.hitbox.height/2
                        )))

                else:

                    bullet_direction = pygame.math.Vector2()
                    bullet_position = pygame.math.Vector2(self.hitbox.center)

                    if right_pressed:
                        bullet_direction.x = 1
                        bullet_position.x += self.hitbox.width/2
                    elif left_pressed:
                        bullet_direction.x = -1
                        bullet_position.x -= self.hitbox.width/2

                    if down_pressed:
                        bullet_direction.y = 1
                        bullet_position.y += self.hitbox.height/2
                    elif up_pressed:
                        bullet_direction.y = -1
                        bullet_position.y -= self.hitbox.height/2

                    bullet_direction = bullet_direction.normalize()
                    bullets_to_create.append((bullet_direction, bullet_position))

                for bullet in bullets_to_create:

                    self.create_bullet(bullet[1], bullet[0], self.bullet_damage)

                    if self.shotgun_timer.active or self.sheriff_timer.active:
                        self.create_bullet(bullet[1], rotate_vector(bullet[0], 10), self.bullet_damage)
                        self.create_bullet(bullet[1], rotate_vector(bullet[0], -10), self.bullet_damage)

    def update_status(self):

        if self.tombstone_timer.active:
            # Zombie mode

            self.status = 'zombie'

        elif self.bullet_cooldown.active:
            # Shooting

            self.status = self.direction_shooting

        else:
            # Not shooting

            if self.direction.x == 0 and self.direction.y == 0:
                self.status = 'idle'
            elif self.direction.x > 0:
                self.status = 'right'
            elif self.direction.x < 0:
                self.status = 'left'
            elif self.direction.y < 0:
                self.status = 'up'
            else:
                self.status = 'down'

    def calculate_active_speed(self):
        # Take the maximum of all the speeds that are active

        active_speeds = [self.base_speed]  # Base speed can change with purchasing boot upgrades

        if self.tombstone_timer.active:
            active_speeds.append(self.zombie_speed)
        if self.coffee_timer.active:
            active_speeds.append(self.coffee_speed)
        if self.sheriff_timer.active:
            active_speeds.append(self.sheriff_speed)

        return max(active_speeds)

    def move(self, dt):

        # Normalize vector
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()
            # Play footstep sound
            if not self.footstep_timer.active:
                self.footstep_timer.activate()
                self.footstep_sound.play()

        active_speed = self.calculate_active_speed()

        # Horizontal movement & collision
        self.pos.x += self.direction.x * active_speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('x')

        # Vertical movement & collision
        self.pos.y += self.direction.y * active_speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('y')

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

    def animate(self, dt):

        if self.lightening_timer.active:
            self.status = 'lightening'

        current_animation = self.animations[self.status]

        if self.direction.magnitude() > 0 or self.lightening_timer.active:
            self.frame_index += self.animation_speed * dt

        if self.frame_index >= len(current_animation):
            self.frame_index = 0

        self.image = current_animation[int(self.frame_index)]

        if self.flash_timer.active:
            if math.sin(pygame.time.get_ticks() * 0.05) >= 0:
                self.image.set_alpha(0)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def update(self, dt):

        self.update_timers()

        if not self.lightening_timer.active:
            self.input()

        if not self.lightening_timer.active:
            self.update_status()

        if not self.lightening_timer.active:
            self.move(dt)

        self.animate(dt)
