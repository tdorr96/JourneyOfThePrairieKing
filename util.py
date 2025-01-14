import os
import math
import pygame
from settings import *


def rotate_vector(vector, angle):

    radians = math.radians(angle)

    return pygame.math.Vector2(
        (vector.x * math.cos(radians)) - (vector.y * math.sin(radians)),
        (vector.x * math.sin(radians)) + (vector.y * math.cos(radians))
    )


def import_image(path_to_image, scale=ZOOM_FACTOR):

    return pygame.transform.scale_by(pygame.image.load(path_to_image).convert_alpha(), scale)


def import_folder(path_to_folder):

    files = [f for f in os.listdir(path_to_folder) if not f.startswith('.')]
    files = sorted(files, key=lambda f: int(f.split('.')[0]))

    return [pygame.transform.scale_by(pygame.image.load(os.path.join(path_to_folder, f)).convert_alpha(), ZOOM_FACTOR) for f in files]


def import_folder_dict(path_to_folder, scale=ZOOM_FACTOR):

    files = [f for f in os.listdir(path_to_folder) if not f.startswith('.')]
    return {
        f.split('.')[0]: pygame.transform.scale_by(pygame.image.load(os.path.join(path_to_folder, f)).convert_alpha(), scale)
        for f in files
    }


class Timer:

    def __init__(self, duration, auto_start=False, func=None):

        self.duration = duration
        self.active = False
        self.start_time = None
        self.paused_time = None
        self.func = func

        if auto_start:
            self.activate()

    def percent_left(self):

        if self.active:
            current_time = pygame.time.get_ticks() if self.paused_time is None else self.paused_time
            # Could be a frame when hadn't updated and current time is past duration, so just cap at 0
            return max(0, 1 - ((current_time - self.start_time) / self.duration))
        else:
            return 0

    def activate(self):

        assert self.paused_time is None

        self.active = True
        self.start_time = pygame.time.get_ticks()

    def pause(self):

        assert self.active

        self.paused_time = pygame.time.get_ticks()

    def un_pause(self):

        assert self.active and self.paused_time is not None

        paused_for = pygame.time.get_ticks() - self.paused_time
        self.paused_time = None
        self.extend_timer(paused_for)

    def extend_timer(self, extension):
        # If active, know back timer to either full limit again or just by extension
        # If not active, turn on with only extension left to run for

        assert self.paused_time is None

        if self.active:
            current_time = pygame.time.get_ticks()
            self.start_time += min(extension, current_time - self.start_time)
        else:
            self.active = True
            self.start_time = pygame.time.get_ticks() - self.duration + extension

    def deactivate(self):

        assert self.paused_time is None

        self.active = False
        self.start_time = None

    def update(self):

        if self.active and self.paused_time is None:
            current_time = pygame.time.get_ticks()
            if current_time - self.start_time >= self.duration:
                self.deactivate()
                if self.func is not None:
                    self.func()
