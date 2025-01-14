import pygame
from util import Timer
from settings import *


class ParticleEffect(pygame.sprite.Sprite):
    # Simple sprite to iterate through animation frames, and once reached the end kill itself: simple particle effect
    # We have optional parameters to:
    # - delay starting the animation (default is to start immediately)
    # - when reaching last frame, delay killing ourselves for some time (default is to kill immediately on last frame)

    def __init__(self, pos, frames, groups, death_duration=None, delay=None):

        super().__init__(groups)

        # Image & animation
        # Copy the surfaces, as settings their alpha values will affect all with a reference to it
        self.frames = [s.copy() for s in frames]
        self.frame_index = 0
        self.animation_speed = 9
        self.image = self.frames[self.frame_index]
        self.z = Z_LAYERS['particles']

        # If we are delaying drawing & animating the sprite, dirty trick is just to set the alpha to 0 until delay over
        if delay is not None:
            self.image.set_alpha(0)

        # Rect
        self.rect = self.image.get_rect(center=pos)

        # Timers
        self.death_timer = None if death_duration is None else Timer(death_duration, func=self.kill)
        self.delay_timer = None if delay is None else Timer(delay, auto_start=True)

    def update_timers(self):

        if self.delay_timer is not None:
            self.delay_timer.update()
        if self.death_timer is not None:
            self.death_timer.update()

    def update(self, dt):

        self.update_timers()

        # Bit redundant to keep settings alpha to 0 or 255 each frame, but seems to be a big (with MacOS?)
        # that can randomly set alpha to 0 if we set it once earlier on - this seems to avoid
        # Alternatively, could filter out particles with delay timer active in the camera before drawing,
        # but seems nice to contain all the logic in this class
        if self.delay_timer is None or not self.delay_timer.active:
            self.animate(dt)
            self.image.set_alpha(255)
        else:
            self.image.set_alpha(0)

    def animate(self, dt):

        if self.death_timer is not None:
            # If there is a death timer, and we've not activated it yet, animate like normal
            # Except when we reach the last frame in the animation, activate the timer
            # By updating the timer every frame (`update_timers`), once it runs out it will call kill() itself

            if not self.death_timer.active:

                self.frame_index += self.animation_speed * dt
                if int(self.frame_index) == len(self.frames) - 1:
                    self.death_timer.activate()
                self.image = self.frames[int(self.frame_index)]

        else:
            # If there is no death timer, just animate like normal
            # And when we reach the last frame, kill

            self.frame_index += self.animation_speed * dt
            if self.frame_index >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[int(self.frame_index)]
