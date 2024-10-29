import pygame
import random
import sys

# Initialize pygame and set up screen
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galaxy Shooter")

# Load images
player_img = pygame.image.load("assets/player.png")
enemy_img = pygame.image.load("assets/enemy.png")
player_laser_img = pygame.image.load("assets/player_laser.png")
enemy_laser_img = pygame.image.load("assets/enemy_laser.png")
background_img = pygame.image.load("assets/background.png")

# Load sounds
pygame.mixer.music.load("assets/background_music.mp3")
shoot_sound = pygame.mixer.Sound("assets/shoot.wav")
explosion_sound = pygame.mixer.Sound("assets/explosion.wav")

# Set up constants
PLAYER_VELOCITY = 5
LASER_VELOCITY = 8
ENEMY_VELOCITY = 2
ENEMY_LASER_VELOCITY = 6
ENEMY_SPAWN_RATE = 100  # Increased to make it less frequent
PLAYER_MAX_HEALTH = 100

# Set up fonts
font = pygame.font.SysFont("comicsans", 30)
game_over_font = pygame.font.SysFont("comicsans", 60)

# Classes for Player, Enemy, and Laser
class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, velocity):
        self.y += velocity

    def off_screen(self, height):
        return not (0 <= self.y <= height)

    def collision(self, obj):
        return collide(self, obj)

class Player:
    COOLDOWN = 20  # frames between each laser shot

    def __init__(self, x, y, health=PLAYER_MAX_HEALTH):
        self.x = x
        self.y = y
        self.health = health
        self.img = player_img
        self.mask = pygame.mask.from_surface(self.img)
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, velocity, enemies):
        self.cooldown()
        for laser in self.lasers:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for enemy in enemies:
                    if laser.collision(enemy):
                        explosion_sound.play()
                        enemies.remove(enemy)
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + self.img.get_width() // 2 - player_laser_img.get_width() // 2, self.y, player_laser_img)
            self.lasers.append(laser)
            shoot_sound.play()
            self.cool_down_counter = 1

    def get_width(self):
        return self.img.get_width()

    def get_height(self):
        return self.img.get_height()

class Enemy:
    COOLDOWN = 60  # Frames between each laser shot

    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move(self, velocity):
        self.y += velocity

    def move_lasers(self, velocity, player):
        self.cooldown()
        for laser in self.lasers:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(player):
                player.health -= 10
                explosion_sound.play()
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + self.img.get_width() // 2 - enemy_laser_img.get_width() // 2, self.y + self.img.get_height(), enemy_laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.img.get_width()

    def get_height(self):
        return self.img.get_height()

# Helper function for collisions
def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None

# Function for game over screen
def game_over_screen():
    screen.blit(background_img, (0, 0))
    game_over_label = game_over_font.render("GAME OVER", 1, (255, 0, 0))
    screen.blit(game_over_label, (WIDTH//2 - game_over_label.get_width()//2, HEIGHT//2 - game_over_label.get_height()//2))
    pygame.display.update()
    pygame.time.delay(3000)
    pygame.quit()
    sys.exit()

# Main game loop
def main():
    run = True
    FPS = 60
    clock = pygame.time.Clock()
    player = Player(300, 500)
    enemies = []
    wave_length = 5
    score = 0

    pygame.mixer.music.play(-1)

    while run:
        clock.tick(FPS)
        screen.blit(background_img, (0, 0))

        # Check for game over condition
        if player.health <= 0:
            game_over_screen()

        # Draw and update player, enemies, and lasers
        player.draw(screen)
        for enemy in enemies:
            enemy.move(ENEMY_VELOCITY)
            enemy.draw(screen)
            enemy.move_lasers(ENEMY_LASER_VELOCITY, player)
            if random.randrange(0, 2*ENEMY_SPAWN_RATE) == 1:  # Enemy shoots less frequently
                enemy.shoot()

        player.move_lasers(-LASER_VELOCITY, enemies)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        # Movement keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.x - PLAYER_VELOCITY > 0:  # Move left
            player.x -= PLAYER_VELOCITY
        if keys[pygame.K_RIGHT] and player.x + player.get_width() + PLAYER_VELOCITY < WIDTH:  # Move right
            player.x += PLAYER_VELOCITY
        if keys[pygame.K_UP] and player.y - PLAYER_VELOCITY > 0:  # Move up
            player.y -= PLAYER_VELOCITY
        if keys[pygame.K_DOWN] and player.y + player.get_height() + PLAYER_VELOCITY < HEIGHT:  # Move down
            player.y += PLAYER_VELOCITY
        if keys[pygame.K_SPACE]:  # Shoot laser
            player.shoot()

        # Spawn enemies
        if len(enemies) == 0:
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100), enemy_img)
                enemies.append(enemy)
            wave_length += 5

        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()
