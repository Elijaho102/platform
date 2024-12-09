import pygame
import os
import random
import math
from os import listdir
from os.path import isfile, join

from pygame import font

pygame.init()

pygame.display.set_caption('Platform Game')


WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))



def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join('assets', dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0,0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace('.png', '') + '_right'] = sprites
            all_sprites[image.replace('.png', '') + '_left'] = flip(sprites)
        else:
            all_sprites[image.replace('.png', '')] = sprites

    return all_sprites


def get_block(size):
    path = join('assets', 'Terrain', 'Terrain.png')
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets('MainCharacters', 'MaskDude', 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = 'left'
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != 'left':
            self.direction = 'left'
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != 'right':
            self.direction = 'right'
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False

        self.fall_count += 1
        self.update_sprite()


    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1


    def update_sprite(self):
        sprite_sheet = 'idle'
        if self.hit:
            sprite_sheet = 'hit'
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = 'jump'
            elif self.jump_count == 2:
                sprite_sheet = 'double_jump'
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = 'fall'
        elif self.x_vel != 0:
            sprite_sheet = 'run'

        sprite_sheet_name = sprite_sheet + '_' + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name


    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class MovingPlatform(Block):
    def __init__(self, x, y, size, axis='horizontal', range=200, speed=2):
        super().__init__(x, y, size)
        self.axis = axis  # 'horizontal' or 'vertical'
        self.range = range  # Range of movement in pixels
        self.speed = speed  # Speed of movement
        self.initial_position = x if axis == 'horizontal' else y
        self.direction = 1  # 1 for forward, -1 for backward

    def move(self):
        if self.axis == 'horizontal':
            self.rect.x += self.speed * self.direction
            if abs(self.rect.x - self.initial_position) > self.range:
                self.direction *= -1
        elif self.axis == 'vertical':
            self.rect.y += self.speed * self.direction
            if abs(self.rect.y - self.initial_position) > self.range:
                self.direction *= -1


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, 'fire')
        self.fire = load_sprite_sheets('Traps', 'Fire', width, height)
        self.image = self.fire['off'][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = 'off'

    def on(self):
        self.animation_name = 'on'

    def off(self):
        self.animation_name = 'off'

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join('assets', 'Background', name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

def generate_platforms(block_size, num_platforms, height_range):
    platforms = []
    last_x = None
    for _ in range(num_platforms):
        while True:  # Keep generating until valid placement
            x = random.randint(0, WIDTH - block_size)
            y = random.randint(height_range[0], height_range[1])
            if last_x is None or abs(x - last_x) > block_size:  # Avoid overlap
                last_x = x
                break
        platforms.append(Block(x, y, block_size))
    return platforms




def draw(window, background, bg_image, player, objects, offset_x, coin_count, coins, coin_image, font):
    for tile in background:
        window.blit(bg_image, tile)

    for coin in coins:
        window.blit(coin_image, (coin.x - offset_x, coin.y))

    for obj in objects:
        obj.draw(window, offset_x)

    for obj in objects:
        if isinstance(obj, MovingPlatform):
            obj.move()

    player.draw(window, offset_x)

    coin_text = font.render(f'Coins: {coin_count}', True, (255, 255, 0))
    window.blit(coin_text, (10, 10))

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)
            #
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_coin_collection(player, coins, coin_count):
    for coin in coins[:]:  
        if player.rect.colliderect(coin): 
            coins.remove(coin) 
            coin_count += 1     
    return coin_count


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == 'fire':
            player.make_hit()

    for obj in to_check:
        if obj and obj.name == 'fire':
            player.make_hit()


import time

def main(window):
    coin_count = 0
    font = pygame.font.SysFont('comicsans', 30)
    clock = pygame.time.Clock()
    background, bg_image = get_background('Blue.png')

    block_size = 96
    player = Player(10, 100, 50, 50)
    fire = Fire(100, HEIGHT - block_size - 64, 16, 32)
    fire.on()

    # Ground floor blocks
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]

    # Additional platforms
    platforms = [
        Block(200, HEIGHT - block_size * 2, block_size),  # Platform 1
        Block(400, HEIGHT - block_size * 4, block_size),  # Platform 2
        Block(600, HEIGHT - block_size * 6, block_size),  # Platform 3
        Block(800, HEIGHT - block_size * 3, block_size),  # Platform 4
    ]

    moving_platforms = [
        MovingPlatform(300, HEIGHT - block_size * 3, block_size, axis='horizontal', range=150, speed=3),
        MovingPlatform(700, HEIGHT - block_size * 5, block_size, axis='vertical', range=100, speed=2),
    ]

    objects = [*floor, *platforms, *moving_platforms, fire]



    # Coin setup
    coin_image = pygame.image.load('C:/Users/elija/PycharmProjects/New platform game/assets/Items/coins/coin_0.png')
    coins = [pygame.Rect(100, 250, 23, 23)]

    offset_x = 0
    scroll_area_width = 200

    # Timer for spawning coins
    spawn_delay = 5  # in seconds
    last_spawn_time = time.time()

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        # Spawn a new coin every `spawn_delay` seconds
        if time.time() - last_spawn_time > spawn_delay:
            last_spawn_time = time.time()
            random_x = random.randint(0, WIDTH - 23)
            random_y = random.randint(100, HEIGHT - block_size - 23)
            new_coin = pygame.Rect(random_x, random_y, 23, 23)
            if not any(new_coin.colliderect(obj.rect) for obj in objects):
                coins.append(new_coin)

        # Player movement and object logic
        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)

        # Handle coin collection
        coin_count = handle_coin_collection(player, coins, coin_count)

        # Draw everything
        draw(window, background, bg_image, player, objects, offset_x, coin_count, coins, coin_image, font)

        # Adjust scrolling based on player's position
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit()




if __name__ == '__main__':
    main(window)