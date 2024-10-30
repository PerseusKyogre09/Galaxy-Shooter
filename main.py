import pygame
import random
import sys
import os

# Initialize pygame and set up screen
pygame.init()
WIDTH, HEIGHT = 800, 700 
GAME_HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galaxy Shooter")

# Images
player_img = pygame.image.load("assets/images/player.png")
enemy_img = pygame.image.load("assets/images/enemy.png")
meteor_img = pygame.image.load("assets/images/meteor.png")
player_laser_img = pygame.image.load("assets/images/player_laser.png")
enemy_laser_img = pygame.image.load("assets/images/enemy_laser.png")
background_img = pygame.image.load("assets/images/background.png")
life_icon_img = pygame.image.load("assets/ui/life_icon.png")
life_lost_icon_img = pygame.image.load("assets/ui/life_lost_icon.png")
explosion_img = pygame.image.load("assets/animations/explosion.png")

# Player damaged images
damage_imgs = [
    pygame.image.load("assets/animations/damage1.png"),
    pygame.image.load("assets/animations/damage2.png"),
    pygame.image.load("assets/animations/damage3.png")
]

# Load sounds
pygame.mixer.music.load("assets/sounds/background_music.mp3")
shoot_sound = pygame.mixer.Sound("assets/sounds/shoot.wav")
explosion_sound = pygame.mixer.Sound("assets/sounds/explosion.mp3")

# Set up constants
PLAYER_VELOCITY = 5
LASER_VELOCITY = 8
ENEMY_VELOCITY = 2
METEOR_VELOCITY = 4
ENEMY_LASER_VELOCITY = 6
ENEMY_SPAWN_RATE = 120
METEOR_SPAWN_RATE = 180
MAX_LIVES = 3

# Set up fonts
font = pygame.font.SysFont("comicsans", 30)
game_over_font = pygame.font.SysFont("comicsans", 60)

# High score file
HIGH_SCORE_FILE = "highscore.txt"

# Load or initialize high score
def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        with open(HIGH_SCORE_FILE, "r") as file:
            return int(file.read().strip())
    else:
        return 0

def save_high_score(score):
    with open(HIGH_SCORE_FILE, "w") as file:
        file.write(str(score))

# Classes for Player, Enemy, Laser, Meteor, and Explosion
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

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lives = MAX_LIVES
        self.score = 0
        self.img = player_img
        self.mask = pygame.mask.from_surface(self.img)
        self.lasers = []
        self.cool_down_counter = 0
        self.damage_counter = 0
        self.is_damaged = False

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

        # Draw damage overlay if damaged
        if self.is_damaged:
            damage_img = damage_imgs[self.damage_counter // 2]  # Cycle faster
            window.blit(damage_img, (self.x, self.y))
            self.damage_counter += 1
            if self.damage_counter >= 6:  # Stop damage effect after cycling through images
                self.is_damaged = False
                self.damage_counter = 0

        for laser in self.lasers:
            laser.draw(window)

    # Update move_lasers to accept explosions as a parameter
    def move_lasers(self, velocity, enemies, meteors, explosions):
        self.cooldown()
        for laser in self.lasers[:]:  # Use slicing to avoid issues while removing items
            laser.move(velocity)
            if laser.off_screen(GAME_HEIGHT):
                self.lasers.remove(laser)
            else:
                for enemy in enemies[:]:  # Check collision with each enemy individually
                    if laser.collision(enemy):
                        explosion_sound.play()
                        self.score += 10
                        enemies.remove(enemy)
                        explosions.append(Explosion(enemy.x, enemy.y))  # Append explosion to list
                        if laser in self.lasers:
                            self.lasers.remove(laser)
                            break  # Stop checking after removing laser

                # Check collision with meteors
                for meteor in meteors[:]:
                    if laser.collision(meteor):
                        explosion_sound.play()
                        meteors.remove(meteor)
                        explosions.append(Explosion(meteor.x, meteor.y))  # Append explosion to list
                        if laser in self.lasers:
                            self.lasers.remove(laser)
                            break  # Stop checking after removing laser

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

    def take_damage(self, explosions):  # Add explosions parameter here if needed
        if not self.is_damaged:
            self.lives -= 1
            self.is_damaged = True
            explosions.append(Explosion(self.x, self.y))

    def get_width(self):
        return self.img.get_width()

    def get_height(self):
        return self.img.get_height()

class Enemy:
    COOLDOWN = 60

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

    # Update move_lasers to accept explosions as a parameter
    def move_lasers(self, velocity, player, explosions):  
        self.cooldown()
        for laser in self.lasers[:]:  # Use slicing to avoid issues while removing items
            laser.move(velocity)
            if laser.off_screen(GAME_HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(player):
                player.take_damage(explosions)  # Pass explosions to take_damage
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

class Meteor:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, velocity):
        self.y += velocity

    def get_width(self):
        return self.img.get_width()

    def get_height(self):
        return self.img.get_height()

# Define Explosion class to manage explosions
class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.img = explosion_img
        self.timer = 6  # Adjust this for how long the explosion lasts

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))
        self.timer -= 1

# Helper function for collisions
def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None

# Function for game over screen
def game_over_screen(player, high_score):
    screen.blit(background_img, (0, 0))
    game_over_label = game_over_font.render("GAME OVER", 1, (255, 0, 0))
    score_label = font.render(f"Score: {player.score}", 1, (255, 255, 255))
    high_score_label = font.render(f"High Score: {high_score}", 1, (255, 255, 255))
    
    screen.blit(game_over_label, (WIDTH // 2 - game_over_label.get_width() // 2, HEIGHT // 2 - game_over_label.get_height() // 2))
    screen.blit(score_label, (WIDTH // 2 - score_label.get_width() // 2, HEIGHT // 2 + 50))
    screen.blit(high_score_label, (WIDTH // 2 - high_score_label.get_width() // 2, HEIGHT // 2 + 100))
    
    pygame.display.update()
    pygame.time.delay(3000)
    pygame.quit()
    sys.exit()

# Function to draw the status bar with lives and score
def draw_status_bar(player, high_score):
    lives_label = font.render("Lives: ", 1, (255, 255, 255))
    score_label = font.render(f"Score: {player.score}", 1, (255, 255, 255))
    high_score_label = font.render(f"High Score: {high_score}", 1, (255, 255, 255))
    screen.blit(lives_label, (10, GAME_HEIGHT + 10))
    screen.blit(score_label, (WIDTH - score_label.get_width() - 10, GAME_HEIGHT + 10))
    screen.blit(high_score_label, (WIDTH // 2 - high_score_label.get_width() // 2, GAME_HEIGHT + 10))

    for i in range(MAX_LIVES):
        icon = life_icon_img if i < player.lives else life_lost_icon_img
        screen.blit(icon, (10 + lives_label.get_width() + i * (icon.get_width() + 5), GAME_HEIGHT + 10))

# Main game loop
def main():
    clock = pygame.time.Clock()
    run = True
    player = Player(300, 500)
    high_score = load_high_score()
    enemies = []
    meteors = []
    explosions = []  # Initialize explosions list here
    enemy_spawn_counter = 0
    meteor_spawn_counter = 0

    pygame.mixer.music.play(-1)

    while run:
        clock.tick(60)
        screen.blit(background_img, (0, 0))
        player.draw(screen)

        # Draw and update enemies, meteors, and explosions
        for enemy in enemies:
            enemy.draw(screen)
        for meteor in meteors:
            meteor.draw(screen)
        for explosion in explosions:
            explosion.draw(screen)
            if explosion.timer <= 0:  # Remove explosion when timer runs out
                explosions.remove(explosion)

        draw_status_bar(player, high_score)
        pygame.display.update()

        # Check for game over
        if player.lives <= 0:
            if player.score > high_score:
                save_high_score(player.score)
            game_over_screen(player, high_score)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Handle player movement and shooting
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.x - PLAYER_VELOCITY > 0:
            player.x -= PLAYER_VELOCITY
        if keys[pygame.K_RIGHT] and player.x + PLAYER_VELOCITY + player.get_width() < WIDTH:
            player.x += PLAYER_VELOCITY
        if keys[pygame.K_UP] and player.y - PLAYER_VELOCITY > 0:
            player.y -= PLAYER_VELOCITY
        if keys[pygame.K_DOWN] and player.y + PLAYER_VELOCITY + player.get_height() < GAME_HEIGHT:
            player.y += PLAYER_VELOCITY
        if keys[pygame.K_SPACE]:
            player.shoot()

        # Spawn enemies and meteors
        if enemy_spawn_counter == 0:
            enemy_x = random.randint(0, WIDTH - enemy_img.get_width())
            enemy_y = random.randint(-100, -40)
            enemy = Enemy(enemy_x, enemy_y, enemy_img)
            enemies.append(enemy)
        if meteor_spawn_counter == 0:
            meteor_x = random.randint(0, WIDTH - meteor_img.get_width())
            meteor_y = random.randint(-100, -40)
            meteor = Meteor(meteor_x, meteor_y, meteor_img)
            meteors.append(meteor)

        # Update counters
        enemy_spawn_counter = (enemy_spawn_counter + 1) % ENEMY_SPAWN_RATE
        meteor_spawn_counter = (meteor_spawn_counter + 1) % METEOR_SPAWN_RATE

        # Update enemy, meteor, and player laser movements
        for enemy in enemies[:]:
            enemy.move(ENEMY_VELOCITY)
            enemy.move_lasers(ENEMY_LASER_VELOCITY, player, explosions)  # Pass explosions

            if random.randint(0, 2 * 60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.take_damage(explosions)  # Pass explosions
                explosion_sound.play()
                enemies.remove(enemy)
                explosions.append(Explosion(enemy.x, enemy.y))

            elif enemy.y + enemy.get_height() > GAME_HEIGHT:
                enemies.remove(enemy)

        for meteor in meteors[:]:
            meteor.move(METEOR_VELOCITY)
            if collide(meteor, player):
                player.take_damage(explosions)  # Pass explosions
                explosion_sound.play()
                meteors.remove(meteor)
                explosions.append(Explosion(meteor.x, meteor.y))

            elif meteor.y + meteor.get_height() > GAME_HEIGHT:
                meteors.remove(meteor)

        player.move_lasers(-LASER_VELOCITY, enemies, meteors, explosions)  # Pass explosions

if __name__ == "__main__":
    main()