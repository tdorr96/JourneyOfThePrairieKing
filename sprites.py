import math
import pygame
from settings import *
from util import Timer, import_image


class Bullet(pygame.sprite.Sprite):

    def __init__(self, pos, direction, damage, surf, colliding_sprites, enemy_sprites, monster_hit_sound, groups):

        super().__init__(groups)

        # Image
        self.image = surf
        self.z = Z_LAYERS['bullets']

        # Rect & float-based movement
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.direction = direction  # already normalized
        self.speed = 150 * ZOOM_FACTOR

        # Attributes
        self.colliding_sprites = colliding_sprites
        self.enemy_sprites = enemy_sprites
        self.damage = damage

        # Audio
        self.monster_hit_sound = monster_hit_sound

    def update(self, dt):

        # Move the bullet
        self.pos += self.direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Check for collisions with tiles that destroy bullets (e.g. fences)
        if pygame.sprite.spritecollide(self, self.colliding_sprites, False):
            self.kill()

        # Check for collisions with enemy and damage them
        # If bullet collides with multiple enemies only damage 1
        for enemy in self.enemy_sprites.sprites():
            if enemy.hitbox.colliderect(self.rect):
                enemy.damage(self.damage)
                self.monster_hit_sound.play()
                self.kill()
                break

        # Check for out of bounds of map
        if self.rect.right < 0 or self.rect.left > GAME_WIDTH:
            self.kill()
        if self.rect.bottom < 0 or self.rect.top > GAME_HEIGHT:
            self.kill()


class Drop(pygame.sprite.Sprite):

    def __init__(self, pos, surf, player, groups):

        super().__init__(groups)

        # Image
        # We create a copy as if we change the alpha value when it flickers, don't want to affect other drop's surfaces
        self.image = surf.copy()
        self.z = Z_LAYERS['drops']

        # Rect
        self.rect = self.image.get_rect(center=pos)

        # If it's too far out of the boundary, nudge in a bit so player can see it
        boundary_buffer = 10 * ZOOM_FACTOR
        if self.rect.right < boundary_buffer:
            self.rect.right = boundary_buffer
        if self.rect.left > GAME_WIDTH - boundary_buffer:
            self.rect.left = GAME_WIDTH - boundary_buffer
        if self.rect.bottom < boundary_buffer:
            self.rect.bottom = boundary_buffer
        if self.rect.top > GAME_HEIGHT - boundary_buffer:
            self.rect.top = GAME_HEIGHT - boundary_buffer

        # Magnet effect that moves it towards player if within a certain radius
        self.pos = pygame.math.Vector2(self.rect.center)
        self.magnet_radius = 30 * ZOOM_FACTOR
        self.player = player

        # Destructs after a certain time
        self.destruct_timer = Timer(8000, auto_start=True, func=self.kill)

        # Have a small window in which we cannot pick up the drop, just so we can see it if e.g. spawn under us
        self.collectable = False
        self.collectable_timer = Timer(1000, auto_start=True, func=self.set_to_collectable)

    def set_to_collectable(self):

        self.collectable = True

    def animate(self):
        # Flicker for last 10%

        percent_left = self.destruct_timer.percent_left()

        if percent_left <= 0.1:
            if math.sin(pygame.time.get_ticks() * 0.05) >= 0:
                self.image.set_alpha(0)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def move(self, dt):
        # If we're within a certain radius of the player, move in the player's direction
        # at a speed relative to the gap between the two

        vector_to_player = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)

        if 0 < vector_to_player.magnitude() < self.magnet_radius:

            speed = vector_to_player.magnitude() * 0.75
            direction = vector_to_player.normalize()

            self.pos += direction * speed * dt
            self.rect.center = (round(self.pos.x), round(self.pos.y))

    def update(self, dt):

        self.collectable_timer.update()
        self.destruct_timer.update()

        self.move(dt)
        self.animate()


class Coin(Drop):

    def __init__(self, pos, surf, value, player, groups):

        super().__init__(pos, surf, player, groups)
        self.value = value


class Powerup(Drop):

    def __init__(self, pos, surf, powerup_name, player, groups):

        super().__init__(pos, surf, player, groups)
        self.powerup_name = powerup_name


class LevelTimer(pygame.sprite.Sprite):
    # We put the level timer logic in a sprite & group single, so we can draw it easier to the UI
    # This way if the group is left empty (for no level timer, e.g. shop level), we don't need lots of checks
    # as drawing an empty group does nothing
    # Basically just wrapper for a timer representing length of level (with a delay), that has a visible representation

    def __init__(self, level_duration, delay_duration, groups):

        super().__init__(groups)

        self.level_timer = Timer(level_duration)
        self.delay_timer = Timer(delay_duration, auto_start=True, func=self.level_timer.activate)

        # Image is the panel for which the clock display is drawn under game map
        # Positioning is with respect to (0, 0) as the UI will offset this when drawing
        self.clock_surf = import_image('graphics/ui/clock.png')
        self.clock_rect = self.clock_surf.get_rect(midleft=(0.01 * GAME_WIDTH, TIMER_HEIGHT / 2))
        self.image = pygame.Surface((GAME_WIDTH, TIMER_HEIGHT), pygame.SRCALPHA)

    def is_level_timer_active(self):

        return self.level_timer.active

    def is_level_timer_finished(self):
        # Both need to be not active, as level timer starts out not active until delay runs out
        # So not sufficient to just check level timer alone

        return not self.level_timer.active and not self.delay_timer.active

    def extend_level_duration(self, proportion=0.25):
        # Extend level by proportion of its duration, called when player dies

        self.level_timer.extend_timer(proportion * self.level_timer.duration)

    def update(self):

        # Update timers
        self.delay_timer.update()
        self.level_timer.update()

        # Re-build image

        self.image.fill('black')
        self.image.blit(self.clock_surf, self.clock_rect)

        # Draw a rectangle that decreases in width as level timer counts down, and progressively turns more red
        timer_bar_total_width = GAME_WIDTH - (0.11 * GAME_WIDTH) - self.clock_surf.get_width()
        timer_bar_height = TIMER_HEIGHT/3
        percent_timer_left = self.level_timer.percent_left()
        timer_bar_active_width = timer_bar_total_width * percent_timer_left
        x = 0.06 * GAME_WIDTH + self.clock_surf.get_width()
        y = TIMER_HEIGHT / 3
        timer_bar_rect = pygame.Rect(x, y, timer_bar_active_width, timer_bar_height)
        color = ((1 - percent_timer_left) * 255, percent_timer_left * 255, 0)
        pygame.draw.rect(self.image, color, timer_bar_rect)
