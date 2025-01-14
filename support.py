import sys
import pygame


def import_sprite_sheet(cols, rows, path):

    frames = {}
    surf = pygame.image.load(path).convert_alpha()

    # for some reason the sprite sheet dimensions a bit odd. Need to offset +/- 1
    cell_width = (surf.get_width()+1)/cols
    cell_height = (surf.get_height()-1)/rows

    for col in range(cols):
        for row in range(rows):

            x, y = col*cell_width-1, row*cell_height
            cutout_rect = pygame.Rect(x, y, cell_width, cell_height)
            cutout_surf = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            cutout_surf.blit(surf, (0, 0), cutout_rect)
            frames[(col, row)] = cutout_surf

    return frames


def create_object(left, top, cols_wide, rows_high, sprite_sheet, path_to_save):

    object_surf = pygame.Surface((cols_wide * 16, rows_high * 16), pygame.SRCALPHA)
    for col in range(cols_wide):
        for row in range(rows_high):
            object_surf.blit(
                sprite_sheet[(left+col, top+row)],
                (col*16, row*16)
            )
    pygame.image.save(object_surf, path_to_save)


def build_running_animation():

    # Get the 4 leg surfaces, each 16 x 3 pixels

    legs = pygame.image.load('graphics/player/moving/legs.png').convert_alpha()
    leg_surfaces = {
        0: pygame.Surface((16, 3), pygame.SRCALPHA),
        1: pygame.Surface((16, 3), pygame.SRCALPHA),
        2: pygame.Surface((16, 3), pygame.SRCALPHA),
        3: pygame.Surface((16, 3), pygame.SRCALPHA)
    }

    # frame 0
    cutout_rect = pygame.Rect(0, 0, 16, 3)
    leg_surfaces[0].blit(legs, (0, 0), cutout_rect)

    # frame 1
    cutout_rect = pygame.Rect(0, 4, 16, 3)
    leg_surfaces[1].blit(legs, (0, 0), cutout_rect)

    # frame 2
    cutout_rect = pygame.Rect(0, 9, 16, 3)
    leg_surfaces[2].blit(legs, (0, 0), cutout_rect)

    # frame 3
    cutout_rect = pygame.Rect(0, 13, 16, 3)
    leg_surfaces[3].blit(legs, (0, 0), cutout_rect)

    # Build running animation for each frame

    for direction in ['down', 'left', 'right', 'up']:

        animation_without_legs = pygame.image.load('graphics/player/moving/%s.png' % direction).convert_alpha()

        for leg_frame in range(4):

            complete_animation = pygame.Surface((16, 16), pygame.SRCALPHA)

            # put legs on first
            complete_animation.blit(leg_surfaces[leg_frame], (0, 13))

            # then put the body on
            complete_animation.blit(animation_without_legs, (0, 0))

            # save it
            pygame.image.save(complete_animation, 'graphics/player/moving/%s/%s.png' % (direction, leg_frame))


def tighten_bounding_rect(path):

    surf = pygame.image.load(path).convert_alpha()

    bounding_rect = surf.get_bounding_rect()

    new_surf = pygame.Surface(bounding_rect.size, pygame.SRCALPHA)
    new_surf.blit(surf, (0, 0), bounding_rect)

    pygame.image.save(new_surf, path)


if __name__ == '__main__':

    pygame.init()
    screen = pygame.display.set_mode((1280, 720))

    # sprite_sheet = import_sprite_sheet(4, 8, 'graphics/ui/UI Settings Buttons.png')
    # pygame.image.save(sprite_sheet[(1, 5)], 'graphics/ui/difficulty_hard.png')

    # create_object(21, 2, 11, 1, sprite_sheet, 'graphics/arrow.png')

    # build_running_animation()
    #
    tighten_bounding_rect('graphics/ui/difficulty_hard.png')


