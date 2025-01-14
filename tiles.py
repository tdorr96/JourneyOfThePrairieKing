import pygame
from settings import *


class StaticTile(pygame.sprite.Sprite):

    def __init__(self, pos, surf, groups, z=Z_LAYERS['bg']):

        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = z


class AnimatedTile(pygame.sprite.Sprite):

    def __init__(self, pos, frames, groups):

        super().__init__(groups)

        self.frames = frames
        self.frame_index = 0
        self.animation_speed = 2
        self.image = self.frames[self.frame_index]
        self.z = Z_LAYERS['main']

        self.rect = self.image.get_rect(topleft=pos)

    def animate(self, dt):

        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def update(self, dt):

        self.animate(dt)
