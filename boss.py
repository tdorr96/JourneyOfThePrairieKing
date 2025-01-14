import random
import pygame
from util import Timer
from settings import *


class Cowboy(pygame.sprite.Sprite):

    def __init__(self, pos, surfs, player, health, bullet_cooldown, create_random_drop, create_bullet, firing_strategy, audio, groups):

        super().__init__(groups)

        # Image & animation
        self.frames = surfs  # {'idle': [], 'moving': []}
        self.frame_index = 0
        self.status = 'idle'
        self.image = self.frames[self.status][self.frame_index]
        self.animation_speed = 6
        self.z = Z_LAYERS['main']

        # Rect, hit-box, & float-based movement
        self.start_pos = pygame.math.Vector2(pos)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-self.rect.width / 4, -self.rect.height / 4)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 30 * ZOOM_FACTOR
        self.direction = pygame.math.Vector2()

        # Attributes
        self.player = player
        self.firing_strategy = firing_strategy
        self.create_random_drop = create_random_drop
        self.create_bullet = create_bullet

        # Audio
        self.gun_shot_sound = audio['gunshot']

        # Health
        self.full_health = health
        self.current_health = health

        # Behaviour
        self.idle_timer = Timer(random.randint(3000, 5000), auto_start=True, func=self.start_firing)
        self.bullet_cooldown_timer = Timer(bullet_cooldown)

    def percent_health_left(self):

        return self.current_health / self.full_health

    def damage(self, damage):

        self.current_health -= damage
        if self.current_health <= 0:
            self.die()

    def die(self):
        # When boss dies, always spawns an extra life

        self.kill()
        self.create_random_drop(self.rect.center, {'extra_life': 1})

    def start_firing(self):

        self.status = 'moving'
        self.direction = pygame.math.Vector2(-1, 0)

    def fire(self):

        if self.status == 'moving' and not self.bullet_cooldown_timer.active:
            # Based on complexity of boss specified in level data, we can either fire straight up or towards the player
            if self.firing_strategy == 'upwards':
                bullet_direction = pygame.math.Vector2(0, -1)
            elif self.firing_strategy == 'towards_player':
                bullet_direction = (pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)).normalize()
            self.create_bullet(
                pos=pygame.math.Vector2(self.hitbox.midtop),
                direction=bullet_direction,
                damage=1,  # Doesn't matter - anything will kill player
                fired_by_player=False
            )
            self.gun_shot_sound.play()
            self.bullet_cooldown_timer.activate()

    def end_firing(self):

        self.status = 'idle'
        self.idle_timer.duration = random.randint(3000, 5000)
        self.idle_timer.activate()
        self.direction = pygame.math.Vector2()

    def move(self, dt):

        self.pos += self.direction * self.speed * dt
        self.hitbox.center = (round(self.pos.x), round(self.pos.y))
        self.rect.center = self.hitbox.center

        if self.rect.left <= (2 * TILE_SIZE * ZOOM_FACTOR):
            # Reverse to the right
            self.direction = pygame.math.Vector2(1, 0)

        elif self.rect.right >= (GAME_WIDTH - (2 * TILE_SIZE * ZOOM_FACTOR)):
            # Reverse to the left
            self.direction = pygame.math.Vector2(-1, 0)

        # NOTE: Maybe the '< 5' pixels should be scaled with zoom factor instead? And similarly in spike ball
        # Also, this will not work with the large dt when OS pauses window - see notebook to ignore if dt too large
        elif self.direction.x == 1 and (pygame.math.Vector2(self.rect.center) - self.start_pos).magnitude() < 5:
            # We're passing through the center
            # Small chance to stop firing. Remember this will be called many times as we pass through, so small chance
            if random.randint(0, 20) == 0:
                self.end_firing()

    def animate(self, dt):

        current_animation = self.frames[self.status]
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(current_animation):
            self.frame_index = 0
        self.image = current_animation[int(self.frame_index)]

    def update(self, dt):

        # Timers
        self.idle_timer.update()
        self.bullet_cooldown_timer.update()

        self.move(dt)
        self.fire()
        self.animate(dt)
