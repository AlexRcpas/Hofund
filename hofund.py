import pygame
import random
import sys
import os
from pygame.locals import *

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
FPS = 60

# Area dimensions
WORMHOLE_HEIGHT = SCREEN_HEIGHT * 0.18  # Top 20% for wormhole area
DEFENSE_HEIGHT = SCREEN_HEIGHT * 0.3    # Bottom 30% for defense area
ATTACK_HEIGHT = SCREEN_HEIGHT * 0.52     # Middle 50% for attack area

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# Game variables
armor = 600
score = 0
killed_monsters = 0  # 击杀怪物计数器，用于确保前两只怪物必然掉落升级
game_over = False

# Sword types
NORMAL_SWORD = 0
ICE_SWORD = 1
FIRE_SWORD = 2
SWORD_RAIN = 3  # 新增剑雨类型

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
pic_dir = os.path.join(current_dir, "pic")

# Create the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hofund - Tower Defense")
clock = pygame.time.Clock()

# Load images
try:
    player_img = pygame.image.load(os.path.join(pic_dir, "Heimdall00.jpeg")).convert_alpha()
    player_img = pygame.transform.scale(player_img, (100, 100))
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
        
        # 跟踪已获取的剑类型（初始只有普通剑）
        self.unlocked_sword_types = [NORMAL_SWORD]
        # 限制最多可获取的额外剑类型数量
        self.max_extra_sword_types = 3
        
        # 为每种剑类型创建独立的属性
        self.sword_attributes = {
            NORMAL_SWORD: {
                "count": 1,          # 剑的数量
                "fire_rate": 2.0,    # 发射频率
                "damage": 8,        # 伤害值
                "range": 20,         # 伤害范围
                "upgrades": 0,       # 升级次数
                "last_shot": 0       # 上次发射时间
            },
            ICE_SWORD: {
                "count": 0,
                "fire_rate": 2.0,
                "damage": 10,
                "range": 20,
                "upgrades": 0,
                "last_shot": 0
            },
            FIRE_SWORD: {
                "count": 0,
                "fire_rate": 2.0,
                "damage": 15,
                "range": 20,
                "upgrades": 0,
                "last_shot": 0
            },
            SWORD_RAIN: {
                "damage": 0,         # 每次伤害值（0表示未解锁）
                "radius": 60,        # 影响范围
                "duration": 5000,    # 持续时间(毫秒)
                "cooldown": 15000,   # 冷却时间(毫秒)
                "upgrades": 0,       # 升级次数
                "last_used": 0       # 上次使用时间
            }
        }
        
        # 剑雨技能是否激活
        self.sword_rain_active = False
        
    def can_unlock_new_sword_type(self):
        """检查是否还能解锁新的剑类型"""
        # 计算已解锁的额外剑类型数量（不包括NORMAL_SWORD）
        extra_types_count = len([t for t in self.unlocked_sword_types if t != NORMAL_SWORD])
        return extra_types_count < self.max_extra_sword_types
    
    def unlock_sword_type(self, sword_type):
        """解锁新的剑类型"""
        if sword_type not in self.unlocked_sword_types and self.can_unlock_new_sword_type():
            self.unlocked_sword_types.append(sword_type)
            # 如果是剑雨，设置初始伤害值
            if sword_type == SWORD_RAIN:
                self.sword_attributes[SWORD_RAIN]["damage"] = 3
            # 其他剑类型设置初始数量为1
            else:
                self.sword_attributes[sword_type]["count"] = 1
            return True
        return False
    
    def update(self):
        # Player doesn't move, but could add movement controls here
        pass
    
    def find_nearest_monster(self, monsters):
        nearest_monster = None
        min_distance = float('inf')
        defense_line = SCREEN_HEIGHT - DEFENSE_HEIGHT
        attack_line = SCREEN_HEIGHT - DEFENSE_HEIGHT - ATTACK_HEIGHT
        
        # 首先检查是否有怪物已经到达防线
        attacking_monsters = []
        for monster in monsters:
            if monster.attacking:
                attacking_monsters.append(monster)
        
        # 如果有正在攻击的怪物，优先攻击它们中距离玩家最近的
        if attacking_monsters:
            for monster in attacking_monsters:
                dx = monster.rect.centerx - self.rect.centerx
                dy = monster.rect.centery - self.rect.centery
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_monster = monster
        
        # 如果没有正在攻击的怪物，则选择距离防线最近的怪物
        else:
            for monster in monsters:
                # 只考虑已经进入攻防区域的怪物
                if monster.rect.bottom >= attack_line and not monster.attacking:
                    # 计算怪物到防线的距离
                    distance_to_defense = defense_line - monster.rect.bottom
                    
                    if distance_to_defense < min_distance:
                        min_distance = distance_to_defense
                        nearest_monster = monster
        
        if nearest_monster:
            if nearest_monster.attacking:
                print(f"Targeting attacking monster at: {nearest_monster.rect.topleft}")
            else:
                print(f"Targeting monster at: {nearest_monster.rect.topleft}, Distance to defense: {min_distance}")
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
        nearest_monster = self.find_nearest_monster(monsters)
        if not nearest_monster:
            return

        # 对每种已解锁的剑类型分别检查是否可以发射
        for sword_type in self.unlocked_sword_types:
            # 跳过剑雨类型，它有单独的触发机制
            if sword_type == SWORD_RAIN:
                continue
                
            attrs = self.sword_attributes[sword_type]
            # 确保剑的数量大于0
            if attrs["count"] <= 0:
                continue
                
            time_since_last_shot = current_time - attrs["last_shot"]
            
            if time_since_last_shot > 1000 / attrs["fire_rate"]:
                attrs["last_shot"] = current_time
                base_angle = self.calculate_angle_to_target(nearest_monster)
                
                # 根据怪物是否正在攻击调整飞剑的分布
                if nearest_monster.attacking:
                    # 如果怪物正在攻击防线，所有飞剑都瞄准它
                    for i in range(attrs["count"]):
                        new_sword = Sword(self.rect.centerx, self.rect.centery, 
                                        sword_type, attrs["damage"], attrs["range"],
                                        base_angle)
                        all_sprites.add(new_sword)
                        swords.add(new_sword)
                else:
                    # 如果怪物还未到达防线，飞剑可以有一定的扇形分布
                    for i in range(attrs["count"]):
                        angle_offset = 0
                        if attrs["count"] > 1:
                            angle_offset = (i - (attrs["count"] - 1) / 2) * 15
                        
                        new_sword = Sword(self.rect.centerx, self.rect.centery, 
                                        sword_type, attrs["damage"], attrs["range"],
                                        base_angle + angle_offset)
                        all_sprites.add(new_sword)
                        swords.add(new_sword)

    def get_cooldown_percentage(self, current_time, sword_type):
        """获取指定剑类型的冷却百分比（0-1）"""
        attrs = self.sword_attributes[sword_type]
        time_since_last_shot = current_time - attrs["last_shot"]
        cooldown_time = 1000 / attrs["fire_rate"]
        return min(time_since_last_shot / cooldown_time, 1.0)

    def auto_use_sword_rain(self, current_time, all_sprites):
        """自动触发剑雨技能，不检查冷却时间"""
        # 找到最接近防线的怪物
        nearest_monster = self.find_nearest_monster(monsters)
        if not nearest_monster:
            # 如果没有怪物，则在防线中央创建剑雨
            defense_line_y = SCREEN_HEIGHT - DEFENSE_HEIGHT
            dummy_target = pygame.sprite.Sprite()
            dummy_target.rect = pygame.Rect(SCREEN_WIDTH // 2, defense_line_y, 1, 1)
            nearest_monster = dummy_target
        
        # 创建剑雨效果
        attrs = self.sword_attributes[SWORD_RAIN]
        sword_rain = SwordRain(
            nearest_monster, 
            attrs["damage"],
            attrs["radius"],
            attrs["duration"]
        )
        
        all_sprites.add(sword_rain)
        attrs["last_used"] = current_time
        self.sword_rain_active = True
        return True
    
    def use_sword_rain(self, current_time, all_sprites):
        """检查冷却时间后触发剑雨技能"""
        # 检查冷却时间
        attrs = self.sword_attributes[SWORD_RAIN]
        if current_time - attrs["last_used"] < attrs["cooldown"]:
            return False
        
        # 检查剑雨是否已解锁（伤害值大于0）
        if attrs["damage"] <= 0:
            return False
            
        return self.auto_use_sword_rain(current_time, all_sprites)

    def get_sword_rain_cooldown_percentage(self, current_time):
        """获取剑雨技能的冷却百分比（0-1）"""
        attrs = self.sword_attributes[SWORD_RAIN]
        time_since_last_used = current_time - attrs["last_used"]
        return min(time_since_last_used / attrs["cooldown"], 1.0)

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

# SwordRain class
class SwordRain(pygame.sprite.Sprite):
    def __init__(self, target_monster, damage, radius, duration):
        super().__init__()
        self.target = target_monster
        self.damage = damage  # 每次伤害值
        self.radius = radius  # 影响范围
        self.duration = duration  # 持续时间(毫秒)
        self.created_time = pygame.time.get_ticks()
        
        # 创建剑雨的视觉效果
        self.image = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        
        # 绘制剑雨效果
        self.draw_rain_effect()
        
        # 伤害计时器
        self.last_damage_time = 0
        self.damage_interval = 200  # 每200毫秒造成一次伤害
    
    def draw_rain_effect(self):
        # 清空图像
        self.image.fill((0,0,0,0))
        
        # 绘制范围指示圈
        pygame.draw.circle(self.image, (255,255,255,50), 
                          (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, (255,255,255,100), 
                          (self.radius, self.radius), self.radius, 2)
        
        # 绘制随机的"剑"效果
        for _ in range(20):
            x = random.randint(0, self.radius*2)
            y = random.randint(0, self.radius*2)
            length = random.randint(5, 15)
            angle = random.randint(0, 360)
            end_x = x + length * math.cos(math.radians(angle))
            end_y = y + length * math.sin(math.radians(angle))
            
            # 只在圆形区域内绘制
            dist = ((x - self.radius)**2 + (y - self.radius)**2)**0.5
            if dist <= self.radius:
                pygame.draw.line(self.image, (200,200,255,200), 
                                (x, y), (end_x, end_y), 2)
    
    def update(self):
        current_time = pygame.time.get_ticks()
        
        # 检查是否已经超过持续时间
        if current_time - self.created_time > self.duration:
            self.kill()
            return
        
        # 如果目标怪物还存在，跟随它移动
        if hasattr(self.target, 'alive') and self.target.alive():
            self.rect.center = self.target.rect.center
        elif hasattr(self.target, 'rect'):
            # 如果目标不是怪物或已死亡，但有rect属性，保持位置不变
            if not hasattr(self, 'fixed_position'):
                self.fixed_position = self.target.rect.center
                self.rect.center = self.fixed_position
        
        # 定期重绘效果以产生动画
        if current_time % 100 < 20:  # 每100ms更新一次动画
            self.draw_rain_effect()
        
        # 定期对范围内的怪物造成伤害
        if current_time - self.last_damage_time > self.damage_interval:
            self.apply_damage()
            self.last_damage_time = current_time
    
    def apply_damage(self):
        # 获取所有在范围内的怪物
        for monster in monsters:
            # 计算与中心点的距离
            dx = monster.rect.centerx - self.rect.centerx
            dy = monster.rect.centery - self.rect.centery
            distance = (dx**2 + dy**2)**0.5
            
            # 如果在范围内，造成伤害
            if distance <= self.radius:
                monster.health -= self.damage
                
                # 检查怪物是否被击败
                if monster.health <= 0:
                    global score, killed_monsters, upgrade_popup
                    score += 10
                    
                    # 如果是正在攻击的怪物被击杀，给予额外分数
                    if monster.attacking:
                        score += 5
                    
                    # 前两只怪物被击杀时必然弹出升级窗口
                    if killed_monsters < 2 or monster.drops_upgrade:
                        upgrade_popup.active = True
                        upgrade_popup.popup_count += 1  # 增加弹出计数
                        upgrade_popup.randomize_upgrades()  # 每次激活时随机选择新的升级选项
                    
                    killed_monsters += 1
                    monster.kill()

# Monster class
class Monster(pygame.sprite.Sprite):
    def __init__(self, monster_type):
        super().__init__()
        self.monster_type = monster_type
        
        # Different monster types
        if monster_type == 0:  # Basic monster
            self.image = pygame.Surface((40, 40))
            self.image.fill(RED)
            self.health = 40
            self.speed = 0.5
            self.damage = 5
        elif monster_type == 1:  # Fast monster
            self.image = pygame.Surface((30, 30))
            self.image.fill(GREEN)
            self.health = 30
            self.speed = 0.8
            self.damage = 3
        elif monster_type == 2:  # Tank monster
            self.image = pygame.Surface((50, 50))
            self.image.fill(BLUE)
            self.health = 80
            self.speed = 0.3
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
            armor -= self.damage * 0.02  # Adjust the rate of damage as needed
            armor = float("{:.2f}".format(armor))
            if armor < 0:
                armor = 0
            return
        
        # Move monster down
        self.y_float += self.speed
        self.rect.y = int(self.y_float)
        
        # Check if monster reached defense line
        if self.rect.bottom >= SCREEN_HEIGHT - DEFENSE_HEIGHT:
            self.attacking = True
            # Stop the monster exactly at the defense line
            self.rect.bottom = SCREEN_HEIGHT - DEFENSE_HEIGHT
            self.y_float = float(self.rect.y)

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
        
        # 记录弹出次数，用于前三次必然包含剑雨选项
        self.popup_count = 0
        
        # 所有可能的升级选项
        self.all_upgrades = [
            {"text": "Add Normal Sword", "action": lambda: self.add_sword(NORMAL_SWORD), "sword_type": NORMAL_SWORD},
            {"text": "Speed Up Normal", "action": lambda: self.increase_fire_rate(NORMAL_SWORD), "sword_type": NORMAL_SWORD},
            {"text": "Power Up Normal", "action": lambda: self.increase_damage(NORMAL_SWORD), "sword_type": NORMAL_SWORD}
        ]
        
        # 可解锁的新剑类型
        self.unlock_options = [
            {"text": "Unlock Ice Sword", "action": lambda: self.unlock_sword_type(ICE_SWORD), "sword_type": ICE_SWORD},
            {"text": "Unlock Fire Sword", "action": lambda: self.unlock_sword_type(FIRE_SWORD), "sword_type": FIRE_SWORD},
            {"text": "Unlock Sword Rain", "action": lambda: self.unlock_sword_type(SWORD_RAIN), "sword_type": SWORD_RAIN}
        ]
        
        # 已解锁剑类型的升级选项（会动态生成）
        self.unlocked_upgrades = []
        
        # 当前显示的升级选项
        self.current_upgrades = []
        
        # 刷新按钮
        self.refresh_button = {
            "rect": pygame.Rect(self.rect.centerx - button_width // 2, 
                               self.rect.y + self.rect.height - button_height - button_margin, 
                               button_width, button_height),
            "text": "Refresh Options"
        }
        
        self.font = pygame.font.Font(None, 28)
        
        # 初始化随机选项
        self.randomize_upgrades()
    
    def update_unlocked_upgrades(self):
        """更新已解锁剑类型的升级选项"""
        self.unlocked_upgrades = []
        
        # 检查ICE_SWORD是否已解锁
        if ICE_SWORD in player.unlocked_sword_types:
            self.unlocked_upgrades.extend([
                {"text": "Add Ice Sword", "action": lambda: self.add_sword(ICE_SWORD), "sword_type": ICE_SWORD},
                {"text": "Speed Up Ice", "action": lambda: self.increase_fire_rate(ICE_SWORD), "sword_type": ICE_SWORD},
                {"text": "Power Up Ice", "action": lambda: self.increase_damage(ICE_SWORD), "sword_type": ICE_SWORD}
            ])
        
        # 检查FIRE_SWORD是否已解锁
        if FIRE_SWORD in player.unlocked_sword_types:
            self.unlocked_upgrades.extend([
                {"text": "Add Fire Sword", "action": lambda: self.add_sword(FIRE_SWORD), "sword_type": FIRE_SWORD},
                {"text": "Speed Up Fire", "action": lambda: self.increase_fire_rate(FIRE_SWORD), "sword_type": FIRE_SWORD},
                {"text": "Power Up Fire", "action": lambda: self.increase_damage(FIRE_SWORD), "sword_type": FIRE_SWORD}
            ])
        
        # 检查SWORD_RAIN是否已解锁
        if SWORD_RAIN in player.unlocked_sword_types:
            self.unlocked_upgrades.extend([
                {"text": "Rain Damage Up", "action": lambda: self.upgrade_sword_rain_damage(), "sword_type": SWORD_RAIN},
                {"text": "Rain Radius Up", "action": lambda: self.upgrade_sword_rain_radius(), "sword_type": SWORD_RAIN},
                {"text": "Rain Duration Up", "action": lambda: self.upgrade_sword_rain_duration(), "sword_type": SWORD_RAIN},
                {"text": "Rain Cooldown Down", "action": lambda: self.upgrade_sword_rain_cooldown(), "sword_type": SWORD_RAIN}
            ])
    
    def randomize_upgrades(self):
        """随机选择3个升级选项"""
        # 更新已解锁剑类型的升级选项
        self.update_unlocked_upgrades()
        
        # 获取所有可用的升级选项
        available_upgrades = []
        
        # 添加普通剑的升级选项
        for upgrade in self.all_upgrades:
            if player.sword_attributes[upgrade["sword_type"]]["upgrades"] < 10:
                available_upgrades.append(upgrade)
        
        # 添加已解锁剑类型的升级选项
        for upgrade in self.unlocked_upgrades:
            if player.sword_attributes[upgrade["sword_type"]]["upgrades"] < 10:
                available_upgrades.append(upgrade)
        
        # 添加可解锁的新剑类型选项
        if player.can_unlock_new_sword_type():
            for option in self.unlock_options:
                if option["sword_type"] not in player.unlocked_sword_types:
                    available_upgrades.append(option)
        
        # 如果没有可用升级，返回
        if not available_upgrades:
            self.current_upgrades = []
            return
        
        # 随机选择3个或更少的升级选项
        num_options = min(3, len(available_upgrades))
        selected_upgrades = random.sample(available_upgrades, num_options)
        
        # 设置按钮位置
        button_width = 180
        button_height = 40
        button_margin = 20
        
        self.current_upgrades = []
        for i, upgrade in enumerate(selected_upgrades):
            button = upgrade.copy()
            button["rect"] = pygame.Rect(
                self.rect.centerx - button_width // 2, 
                self.rect.y + button_margin * (i+1) + button_height * i, 
                button_width, button_height
            )
            self.current_upgrades.append(button)
    
    def unlock_sword_type(self, sword_type):
        """解锁新的剑类型"""
        global player
        if player.unlock_sword_type(sword_type):
            print(f"Unlocked new sword type: {sword_type}")
            # 如果是剑雨，直接调用原有的解锁方法
            if sword_type == SWORD_RAIN:
                self.unlock_sword_rain()
            return True
        return False
    
    def draw(self, surface):
        if not self.active:
            return
            
        # Draw popup background
        pygame.draw.rect(surface, (50, 50, 50), self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 2)
        
        # Draw title
        title = self.font.render("Choose Upgrade", True, WHITE)
        surface.blit(title, (self.rect.centerx - title.get_width() // 2, self.rect.y + 10))
        
        # Draw upgrade buttons
        for button in self.current_upgrades:
            # 检查是否达到升级上限
            sword_type = button["sword_type"]
            is_maxed = player.sword_attributes[sword_type]["upgrades"] >= 10
            
            # 设置按钮颜色
            button_color = (100, 100, 100, 128) if is_maxed else (100, 100, 100)
            pygame.draw.rect(surface, button_color, button["rect"])
            pygame.draw.rect(surface, WHITE, button["rect"], 2)
            
            # 设置文本颜色
            text_color = (150, 150, 150) if is_maxed else WHITE
            text = self.font.render(button["text"], True, text_color)
            text_pos = (button["rect"].centerx - text.get_width() // 2, 
                        button["rect"].centery - text.get_height() // 2)
            surface.blit(text, text_pos)
        
        # Draw refresh button
        pygame.draw.rect(surface, (80, 80, 120), self.refresh_button["rect"])
        pygame.draw.rect(surface, WHITE, self.refresh_button["rect"], 2)
        refresh_text = self.font.render(self.refresh_button["text"], True, WHITE)
        refresh_pos = (self.refresh_button["rect"].centerx - refresh_text.get_width() // 2, 
                      self.refresh_button["rect"].centery - refresh_text.get_height() // 2)
        surface.blit(refresh_text, refresh_pos)
    
    def handle_click(self, pos, player):
        if not self.active:
            return False
        
        # 检查是否点击了刷新按钮
        if self.refresh_button["rect"].collidepoint(pos):
            self.randomize_upgrades()
            return True
            
        # 检查是否点击了升级按钮
        for button in self.current_upgrades:
            if button["rect"].collidepoint(pos):
                # 检查对应的剑类型
                sword_type = button["sword_type"]
                
                # 检查是否达到升级上限
                if player.sword_attributes[sword_type]["upgrades"] >= 10:
                    print(f"Cannot upgrade further - max level reached")
                    return True
                
                button["action"]()
                self.active = False
                return True
                
        return False
    
    def add_sword(self, sword_type):
        global player
        attrs = player.sword_attributes[sword_type]
        attrs["count"] += 1
        attrs["upgrades"] += 1
        print(f"Added sword - type: {sword_type}, count: {attrs['count']}, upgrades: {attrs['upgrades']}/10")
    
    def increase_fire_rate(self, sword_type):
        global player
        attrs = player.sword_attributes[sword_type]
        attrs["fire_rate"] *= 1.2
        attrs["upgrades"] += 1
        print(f"Increased fire rate - type: {sword_type}, rate: {attrs['fire_rate']:.2f}, upgrades: {attrs['upgrades']}/10")
    
    def increase_damage(self, sword_type):
        global player
        attrs = player.sword_attributes[sword_type]
        attrs["damage"] += 5
        attrs["upgrades"] += 1
        print(f"Increased damage - type: {sword_type}, damage: {attrs['damage']}, upgrades: {attrs['upgrades']}/10")
    
    def upgrade_sword_rain_damage(self):
        global player
        attrs = player.sword_attributes[SWORD_RAIN]
        attrs["damage"] += 2
        attrs["upgrades"] += 1
        print(f"Increased sword rain damage - damage: {attrs['damage']}, upgrades: {attrs['upgrades']}/10")
    
    def upgrade_sword_rain_radius(self):
        global player
        attrs = player.sword_attributes[SWORD_RAIN]
        attrs["radius"] += 10
        attrs["upgrades"] += 1
        print(f"Increased sword rain radius - radius: {attrs['radius']}, upgrades: {attrs['upgrades']}/10")
    
    def upgrade_sword_rain_duration(self):
        global player
        attrs = player.sword_attributes[SWORD_RAIN]
        attrs["duration"] += 1000  # 增加1秒
        attrs["upgrades"] += 1
        print(f"Increased sword rain duration - duration: {attrs['duration']/1000}s, upgrades: {attrs['upgrades']}/10")
    
    def upgrade_sword_rain_cooldown(self):
        global player
        attrs = player.sword_attributes[SWORD_RAIN]
        attrs["cooldown"] = max(5000, attrs["cooldown"] - 1000)  # 减少1秒，最低5秒
        attrs["upgrades"] += 1
        print(f"Decreased sword rain cooldown - cooldown: {attrs['cooldown']/1000}s, upgrades: {attrs['upgrades']}/10")
    
    def unlock_sword_rain(self):
        """解锁剑雨技能"""
        global player
        attrs = player.sword_attributes[SWORD_RAIN]
        attrs["upgrades"] += 1
        print(f"Unlocked Sword Rain! Initial damage: {attrs['damage']}")
        
        # 解锁后自动触发一次剑雨效果
        current_time = pygame.time.get_ticks()
        player.auto_use_sword_rain(current_time, all_sprites)

# Game functions
def spawn_monster(all_sprites, monsters):
    # Determine monster type based on probabilities
    monster_type = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
    
    # Create monster
    new_monster = Monster(monster_type)
    
    # 确保前两只怪物必然掉落升级
    global killed_monsters
    if killed_monsters < 2:
        new_monster.drops_upgrade = True
    # 其他怪物正常概率掉落
    elif killed_monsters < 2000 and random.random() < 0.015:  # 1.5% chance for first 2000
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
                
                # 如果是正在攻击的怪物被击杀，给予额外分数
                if monster.attacking:
                    score += 5
                
                # 前两只怪物被击杀时必然弹出升级窗口
                if killed_monsters < 2 or monster.drops_upgrade:
                    upgrade_popup.active = True
                    upgrade_popup.popup_count += 1  # 增加弹出计数
                    upgrade_popup.randomize_upgrades()  # 每次激活时随机选择新的升级选项
                
                killed_monsters += 1
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
    font = pygame.font.Font(None, 30)
    
    # Draw armor
    armor_text = font.render(f"Armor: {armor}", True, WHITE)
    surface.blit(armor_text, (15, SCREEN_HEIGHT - 40))
    
    # Draw score
    score_text = font.render(f"Score: {score}", True, WHITE)
    surface.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 10, SCREEN_HEIGHT - 40))
    
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

def draw_sword_hud(surface, player, current_time):
    # HUD位置和大小设置
    hud_width = 80
    hud_x = SCREEN_WIDTH - hud_width - 10
    hud_y = 10
    item_height = 60
    padding = 10
    
    # 字体设置
    font = pygame.font.Font(None, 24)
    
    # 剑类型颜色映射
    sword_colors = {
        NORMAL_SWORD: WHITE,
        ICE_SWORD: CYAN,
        FIRE_SWORD: ORANGE,
        SWORD_RAIN: (180, 180, 255)  # 淡蓝紫色
    }
    
    sword_names = {
        NORMAL_SWORD: "Normal",
        ICE_SWORD: "Ice",
        FIRE_SWORD: "Fire",
        SWORD_RAIN: "Rain"
    }
    
    # 获取已解锁的剑类型（不包括NORMAL_SWORD）
    unlocked_types = [t for t in player.unlocked_sword_types if t != NORMAL_SWORD]
    
    # 绘制每种已解锁剑的状态
    for i, sword_type in enumerate(unlocked_types):
        attrs = player.sword_attributes[sword_type]
        y = hud_y + (item_height + padding) * i
        
        # 创建半透明背景
        bg_surface = pygame.Surface((hud_width, item_height), pygame.SRCALPHA)
        bg_surface.fill((50, 50, 50, 150))  # 半透明背景
        surface.blit(bg_surface, (hud_x, y))
        
        # 绘制边框
        pygame.draw.rect(surface, sword_colors[sword_type], 
                        (hud_x, y, hud_width, item_height), 2)
        
        # 绘制剑类型名称和等级
        name_text = font.render(f"{sword_names[sword_type]} Lv.{attrs['upgrades']}", True, sword_colors[sword_type])
        surface.blit(name_text, (hud_x + 5, y + 5))
        
        # 绘制CD倒计时圆盘
        cd_radius = 15
        cd_x = hud_x + hud_width // 2
        cd_y = y + item_height - cd_radius - 5
        
        # 绘制底层圆
        pygame.draw.circle(surface, (30, 30, 30, 150), (cd_x, cd_y), cd_radius)
        
        # 计算并绘制CD进度
        if sword_type == SWORD_RAIN:
            cooldown = player.get_sword_rain_cooldown_percentage(current_time)
        else:
            cooldown = player.get_cooldown_percentage(current_time, sword_type)
            
        if cooldown < 1:
            angle = (1 - cooldown) * 360  # 转换为角度
            # 绘制扇形
            pygame.draw.arc(surface, sword_colors[sword_type],
                          (cd_x - cd_radius, cd_y - cd_radius,
                           cd_radius * 2, cd_radius * 2),
                          math.radians(270), math.radians(270 + angle), cd_radius)
        
        # 绘制圆形边框
        pygame.draw.circle(surface, sword_colors[sword_type], (cd_x, cd_y), cd_radius, 2)

def reset_game():
    global armor, score, killed_monsters, game_over
    global all_sprites, monsters, swords, player, upgrade_popup
    
    # Reset game variables
    armor = 1000
    score = 0
    killed_monsters = 0
    game_over = False
    
    # Reset sprite groups
    all_sprites = pygame.sprite.Group()
    monsters = pygame.sprite.Group()
    swords = pygame.sprite.Group()
    
    # Create player with reset sword attributes
    player = Player()
    # 确保初始只有普通剑可用
    player.unlocked_sword_types = [NORMAL_SWORD]
    all_sprites.add(player)
    
    # Reset upgrade popup
    upgrade_popup = UpgradePopup()
    upgrade_popup.popup_count = 0  # 重置弹出计数器
    upgrade_popup.randomize_upgrades()  # 确保重置时随机选择新的升级选项

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
monster_spawn_delay = 600  # milliseconds

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
        
        # Auto-shoot
        player.shoot(current_time, all_sprites, swords, monsters)
        
        # 自动触发剑雨技能（如果已解锁且冷却完成）
        if player.sword_attributes[SWORD_RAIN]["damage"] > 0:
            player.use_sword_rain(current_time, all_sprites)
        
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
    
    # Draw sword status HUD
    draw_sword_hud(screen, player, current_time)
    
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
