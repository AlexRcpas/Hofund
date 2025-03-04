import pygame
import random
import sys
import os
from pygame.locals import *

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 800
FPS = 60

# Area dimensions
WORMHOLE_HEIGHT = SCREEN_HEIGHT * 0.2  # Top 20% for wormhole area
DEFENSE_HEIGHT = SCREEN_HEIGHT * 0.3    # Bottom 30% for defense area
ATTACK_HEIGHT = SCREEN_HEIGHT * 0.5     # Middle 50% for attack area

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# Game variables
armor = 100
score = 0
killed_monsters = 0
game_over = False

# Sword types
NORMAL_SWORD = 0
ICE_SWORD = 1
FIRE_SWORD = 2

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
pic_dir = os.path.join(current_dir, "pic")

# Create the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hofund - Tower Defense")
clock = pygame.time.Clock()

# Load images
try:
    player_img = pygame.image.load(os.path.join(pic_dir, "Hofund.png")).convert_alpha()
    player_img = pygame.transform.scale(player_img, (80, 80))
except pygame.error:
    # Fallback if image loading fails
    player_img = pygame.Surface((80, 80), pygame.SRCALPHA)
    pygame.draw.circle(player_img, BLUE, (40, 40), 40)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        # Position player at 1/3 from the top of defense area
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.centery = SCREEN_HEIGHT - DEFENSE_HEIGHT + (DEFENSE_HEIGHT // 3)
        
        # Sword attributes
        self.sword_type = NORMAL_SWORD
        self.sword_count = 1
        self.fire_rate = 1.0  # Shots per second
        self.damage = 10
        self.last_shot = 0
        self.sword_range = 20  # Radius of damage area

    def update(self):
        # Player doesn't move, but could add movement controls here
        pass
    
    def find_nearest_monster(self, monsters):
        nearest_monster = None
        min_distance = float('inf')
        attack_line = SCREEN_HEIGHT - DEFENSE_HEIGHT - ATTACK_HEIGHT
        
        for monster in monsters:
            # 只考虑已经进入攻防区域的怪物
            if monster.rect.bottom >= attack_line:
                # 计算与玩家的距离
                dx = monster.rect.centerx - self.rect.centerx
                dy = monster.rect.centery - self.rect.centery
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_monster = monster
        
        if nearest_monster:
            print(f"Nearest monster at: {nearest_monster.rect.topleft}, Distance: {min_distance}")
        else:
            print("No monsters in attack area.")
        
        return nearest_monster
    
    def calculate_angle_to_target(self, target):
        # 计算射击角度
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx))  # 使用负dy因为pygame的y轴向下
        return angle
    
    def shoot(self, current_time, all_sprites, swords, monsters):
        # Check if enough time has passed since last shot
        if current_time - self.last_shot > 1000 / self.fire_rate:
            # 寻找最近的怪物
            nearest_monster = self.find_nearest_monster(monsters)
            
            if nearest_monster:
                self.last_shot = current_time
                base_angle = self.calculate_angle_to_target(nearest_monster)
                print(f"Shooting at angle: {base_angle}")
                
                # Create sword based on type
                for i in range(self.sword_count):
                    # Adjust angle for multiple swords
                    angle_offset = 0
                    if self.sword_count > 1:
                        angle_offset = (i - (self.sword_count - 1) / 2) * 15
                    
                    new_sword = Sword(self.rect.centerx, self.rect.centery, 
                                     self.sword_type, self.damage, self.sword_range,
                                     base_angle + angle_offset)
                    all_sprites.add(new_sword)
                    swords.add(new_sword)
                    print(f"Sword created at: {new_sword.rect.topleft} with angle: {base_angle + angle_offset}")

# Sword class
class Sword(pygame.sprite.Sprite):
    def __init__(self, x, y, sword_type, damage, damage_range, angle):
        super().__init__()
        self.sword_type = sword_type
        self.damage = damage
        self.damage_range = damage_range
        self.angle = angle  # 直接使用计算好的角度
        self.speed = 50
        
        # Create sword image based on type
        if sword_type == NORMAL_SWORD:
            self.image = pygame.Surface((10, 30), pygame.SRCALPHA)
            pygame.draw.rect(self.image, WHITE, (0, 0, 10, 30))
        elif sword_type == ICE_SWORD:
            self.image = pygame.Surface((10, 30), pygame.SRCALPHA)
            pygame.draw.rect(self.image, CYAN, (0, 0, 10, 30))
        elif sword_type == FIRE_SWORD:
            self.image = pygame.Surface((10, 30), pygame.SRCALPHA)
            pygame.draw.rect(self.image, ORANGE, (0, 0, 10, 30))
        
        # 旋转飞剑图像以匹配射击角度
        self.original_image = self.image
        self.image = pygame.transform.rotate(self.original_image, -angle)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Convert angle to radians for movement calculation
        self.angle_rad = math.radians(angle)
        
    def update(self):
        # Move sword based on angle
        self.rect.x += self.speed * math.cos(self.angle_rad)
        self.rect.y -= self.speed * math.sin(self.angle_rad)  # 减去是因为pygame的y轴向下
        
        # Remove if off-screen
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or \
           self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

# Monster class
class Monster(pygame.sprite.Sprite):
    def __init__(self, monster_type):
        super().__init__()
        self.monster_type = monster_type
        
        # Different monster types
        if monster_type == 0:  # Basic monster
            self.image = pygame.Surface((40, 40))
            self.image.fill(RED)
            self.health = 20
            self.speed = 2
            self.damage = 5
        elif monster_type == 1:  # Fast monster
            self.image = pygame.Surface((30, 30))
            self.image.fill(GREEN)
            self.health = 10
            self.speed = 4
            self.damage = 3
        elif monster_type == 2:  # Tank monster
            self.image = pygame.Surface((50, 50))
            self.image.fill(BLUE)
            self.health = 40
            self.speed = 1
            self.damage = 10
        
        self.rect = self.image.get_rect()
        # Random x position in wormhole area
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-50, int(WORMHOLE_HEIGHT) - self.rect.height)
        
        # For smooth movement
        self.y_float = float(self.rect.y)
        
        # Flag for upgrade drop
        self.drops_upgrade = False
        
        # Flag to check if monster is attacking
        self.attacking = False
        
    def update(self):
        global armor
        
        # If monster is attacking, reduce armor
        if self.attacking:
            armor -= self.damage * 0.1  # Adjust the rate of damage as needed
            if armor < 0:
                armor = 0
            return
        
        # Move monster down
        self.y_float += self.speed
        self.rect.y = int(self.y_float)
        
        # Check if monster reached defense line
        if self.rect.bottom >= SCREEN_HEIGHT - DEFENSE_HEIGHT:
            self.attacking = True
            self.y_float = SCREEN_HEIGHT - DEFENSE_HEIGHT  # Stop moving
            self.rect.y = int(self.y_float)

# Upgrade popup class
class UpgradePopup:
    def __init__(self):
        self.active = False
        self.rect = pygame.Rect(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, 
                               SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # Define upgrade buttons
        button_width = 180
        button_height = 40
        button_margin = 20
        
        self.buttons = [
            {"rect": pygame.Rect(self.rect.centerx - button_width // 2, 
                                self.rect.y + button_margin, 
                                button_width, button_height),
             "text": "Normal Sword", "action": lambda: self.change_sword_type(NORMAL_SWORD)},
            
            {"rect": pygame.Rect(self.rect.centerx - button_width // 2, 
                                self.rect.y + button_margin * 2 + button_height, 
                                button_width, button_height),
             "text": "Ice Sword", "action": lambda: self.change_sword_type(ICE_SWORD)},
            
            {"rect": pygame.Rect(self.rect.centerx - button_width // 2, 
                                self.rect.y + button_margin * 3 + button_height * 2, 
                                button_width, button_height),
             "text": "Fire Sword", "action": lambda: self.change_sword_type(FIRE_SWORD)},
            
            {"rect": pygame.Rect(self.rect.centerx - button_width // 2, 
                                self.rect.y + button_margin * 4 + button_height * 3, 
                                button_width, button_height),
             "text": "Add Sword", "action": self.add_sword},
            
            {"rect": pygame.Rect(self.rect.centerx - button_width // 2, 
                                self.rect.y + button_margin * 5 + button_height * 4, 
                                button_width, button_height),
             "text": "Increase Fire Rate", "action": self.increase_fire_rate},
            
            {"rect": pygame.Rect(self.rect.centerx - button_width // 2, 
                                self.rect.y + button_margin * 6 + button_height * 5, 
                                button_width, button_height),
             "text": "Increase Range", "action": self.increase_range}
        ]
        
        self.font = pygame.font.Font(None, 28)
    
    def draw(self, surface):
        if not self.active:
            return
            
        # Draw popup background
        pygame.draw.rect(surface, (50, 50, 50), self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)
        
        # Draw title
        title = self.font.render("Choose Upgrade", True, WHITE)
        surface.blit(title, (self.rect.centerx - title.get_width() // 2, self.rect.y + 10))
        
        # Draw buttons
        for button in self.buttons:
            pygame.draw.rect(surface, (100, 100, 100), button["rect"])
            pygame.draw.rect(surface, WHITE, button["rect"], 2)
            
            text = self.font.render(button["text"], True, WHITE)
            text_pos = (button["rect"].centerx - text.get_width() // 2, 
                        button["rect"].centery - text.get_height() // 2)
            surface.blit(text, text_pos)
    
    def handle_click(self, pos, player):
        if not self.active:
            return False
            
        for button in self.buttons:
            if button["rect"].collidepoint(pos):
                button["action"]()
                self.active = False
                return True
                
        return False
    
    def change_sword_type(self, sword_type):
        global player
        player.sword_type = sword_type
    
    def add_sword(self):
        global player
        player.sword_count += 1
    
    def increase_fire_rate(self):
        global player
        player.fire_rate *= 1.2
    
    def increase_range(self):
        global player
        player.sword_range += 10

# Game functions
def spawn_monster(all_sprites, monsters):
    # Determine monster type based on probabilities
    monster_type = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
    
    # Create monster
    new_monster = Monster(monster_type)
    
    # Determine if this monster will drop an upgrade (20 out of first 200)
    global killed_monsters
    if killed_monsters < 200 and random.random() < 0.1:  # 10% chance for first 200
        new_monster.drops_upgrade = True
    
    all_sprites.add(new_monster)
    monsters.add(new_monster)

def check_collisions(swords, monsters, upgrade_popup):
    global score, killed_monsters
    
    # Check sword-monster collisions
    for sword in swords:
        monsters_hit = pygame.sprite.spritecollide(sword, monsters, False)
        for monster in monsters_hit:
            monster.health -= sword.damage
            
            # Special effects based on sword type
            if sword.sword_type == ICE_SWORD:
                monster.speed *= 0.8  # Slow effect
            elif sword.sword_type == FIRE_SWORD:
                monster.health -= 5  # Extra damage
            
            # Check if monster is defeated
            if monster.health <= 0:
                score += 10
                killed_monsters += 1
                
                # Check if monster drops upgrade
                if monster.drops_upgrade:
                    upgrade_popup.active = True
                
                monster.kill()
            
            # Remove sword after hit
            sword.kill()
            break

def draw_game_areas(surface):
    # Draw wormhole area
    pygame.draw.rect(surface, (30, 30, 50), (0, 0, SCREEN_WIDTH, WORMHOLE_HEIGHT))
    
    # Draw attack area
    pygame.draw.rect(surface, (50, 50, 70), 
                    (0, WORMHOLE_HEIGHT, SCREEN_WIDTH, ATTACK_HEIGHT))
    
    # Draw defense area
    pygame.draw.rect(surface, (70, 70, 90), 
                    (0, WORMHOLE_HEIGHT + ATTACK_HEIGHT, SCREEN_WIDTH, DEFENSE_HEIGHT))
    
    # Draw defense line
    pygame.draw.line(surface, WHITE, 
                    (0, SCREEN_HEIGHT - DEFENSE_HEIGHT), 
                    (SCREEN_WIDTH, SCREEN_HEIGHT - DEFENSE_HEIGHT), 3)

def draw_hud(surface):
    font = pygame.font.Font(None, 36)
    
    # Draw armor
    armor_text = font.render(f"Armor: {armor}", True, WHITE)
    surface.blit(armor_text, (20, SCREEN_HEIGHT - 40))
    
    # Draw score
    score_text = font.render(f"Score: {score}", True, WHITE)
    surface.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 20, SCREEN_HEIGHT - 40))
    
    # Draw killed monsters count
    killed_text = font.render(f"Monsters: {killed_monsters}/200", True, WHITE)
    surface.blit(killed_text, (SCREEN_WIDTH // 2 - killed_text.get_width() // 2, SCREEN_HEIGHT - 40))

def draw_game_over(surface):
    font_large = pygame.font.Font(None, 72)
    font_small = pygame.font.Font(None, 36)
    
    # Draw game over text
    game_over_text = font_large.render("GAME OVER", True, RED)
    surface.blit(game_over_text, 
                (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                 SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2))
    
    # Draw final score
    score_text = font_small.render(f"Final Score: {score}", True, WHITE)
    surface.blit(score_text, 
                (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 
                 SCREEN_HEIGHT // 2 + game_over_text.get_height()))
    
    # Draw restart instruction
    restart_text = font_small.render("Press R to restart", True, WHITE)
    surface.blit(restart_text, 
                (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                 SCREEN_HEIGHT // 2 + game_over_text.get_height() + score_text.get_height() + 20))

def reset_game():
    global armor, score, killed_monsters, game_over
    global all_sprites, monsters, swords, player, upgrade_popup
    
    # Reset game variables
    armor = 100
    score = 0
    killed_monsters = 0
    game_over = False
    
    # Reset sprite groups
    all_sprites = pygame.sprite.Group()
    monsters = pygame.sprite.Group()
    swords = pygame.sprite.Group()
    
    # Create player
    player = Player()
    all_sprites.add(player)
    
    # Reset upgrade popup
    upgrade_popup = UpgradePopup()

# Import math module (needed for sword movement)
import math

# Create sprite groups
all_sprites = pygame.sprite.Group()
monsters = pygame.sprite.Group()
swords = pygame.sprite.Group()

# Create player
player = Player()
all_sprites.add(player)

# Create upgrade popup
upgrade_popup = UpgradePopup()

# Monster spawn timer
monster_spawn_timer = 0
monster_spawn_delay = 1000  # milliseconds

# Main game loop
running = True
while running:
    # Keep loop running at the right speed
    clock.tick(FPS)
    current_time = pygame.time.get_ticks()
    
    # Process input (events)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Check for restart on game over
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset_game()
        
        # Check for upgrade popup clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            upgrade_popup.handle_click(event.pos, player)
    
    # Update
    if not game_over and not upgrade_popup.active:
        # Spawn monsters
        if current_time - monster_spawn_timer > monster_spawn_delay:
            spawn_monster(all_sprites, monsters)
            monster_spawn_timer = current_time
        
        # Auto-shoot (修改这里，传入monsters参数)
        player.shoot(current_time, all_sprites, swords, monsters)
        
        # Update all sprites
        all_sprites.update()
        
        # Check collisions
        check_collisions(swords, monsters, upgrade_popup)
        
        # Check game over condition
        if armor <= 0:
            game_over = True
    
    # Draw / render
    screen.fill(BLACK)
    
    # Draw game areas
    draw_game_areas(screen)
    
    # Draw all sprites
    all_sprites.draw(screen)
    
    # Draw HUD
    draw_hud(screen)
    
    # Draw upgrade popup if active
    upgrade_popup.draw(screen)
    
    # Draw game over screen if game is over
    if game_over:
        draw_game_over(screen)
    
    # Flip the display
    pygame.display.flip()

# Quit the game
pygame.quit()
sys.exit()
