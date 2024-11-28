import pygame
import sys
import random
import os
from pathlib import Path
import asyncio

pygame.init()
pygame.mixer.init()

font = pygame.font.SysFont(None, 36)
large_font = pygame.font.SysFont(None, 72)
title_font = pygame.font.SysFont(None, 100)
clock = pygame.time.Clock()

SCREEN_WIDTH = 700
SCREEN_HEIGHT = 500
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Hungry Monkey - Addiction Edition')

platform_width = 128
platform_height = 10
platform_list = []
platform_img = pygame.image.load(f"hungry_monkey_sprites/7tree_top_sprite.png")
num_platforms = 12

floor = pygame.Rect(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50)

monkey_x = int(SCREEN_WIDTH / 2)
monkey_y = SCREEN_HEIGHT - 100
gravity = 1
velocity_y = 0
monkey_size = 50
jump_power = -17
monkey = pygame.Rect(monkey_x, monkey_y, monkey_size, monkey_size)
is_jumping = False
monkey_img = pygame.image.load(f"hungry_monkey_sprites/2monkey_f1.png")

bananas = []
num_bananas = 10
banana_img = pygame.image.load(f"hungry_monkey_sprites/1banana_sprite.png")
veggie_img = pygame.image.load(f"hungry_monkey_sprites/8veggie.png")

frame = 0
frames_left = 1000

score = 0
addiction_level = 0
max_addiction = 50
healing_rate = 0.5
banana_addiction = 10

top_score = 0
banana_x, banana_y = int(SCREEN_WIDTH / 2), 50
banana = pygame.Rect(banana_x, banana_y, 50, 50)

golden_banana_active = False
golden_banana_x = 0
golden_banana_y = 0
golden_banana = None
golden_banana_chance = 0.02
golden_banana_img = pygame.transform.scale(veggie_img, (50, 50))

DARK_GREEN = (0, 150, 0)
SKY_BLUE = (105, 186, 255)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GOLD = (255, 215, 0)

player_name = ""

try:
    jump_sound = pygame.mixer.Sound('sounds/jump.ogg')
    collect_sound = pygame.mixer.Sound('sounds/collect.ogg')
    game_over_sound = pygame.mixer.Sound('sounds/gameover.ogg')
    
    pygame.mixer.music.load('sounds/background.ogg')
    pygame.mixer.music.set_volume(0.5)
except:
    print("Warning: Sound files not found. Creating game without sound.")

animation_alpha = 255
game_over_y = -100

async def draw_addiction_meter():
    """Draws the addiction meter on screen"""
    meter_width = 200
    meter_height = 20
    x = SCREEN_WIDTH - meter_width - 10
    y = 10
    
    pygame.draw.rect(screen, WHITE, (x, y, meter_width, meter_height))
    
    fill_width = (addiction_level / max_addiction) * meter_width
    color = pygame.Color(0, 255, 0)
    if addiction_level > 30:
        color = pygame.Color(int(255 * (addiction_level/max_addiction)), 
                           int(255 * (1 - addiction_level/max_addiction)), 0)
    pygame.draw.rect(screen, color, (x, y, fill_width, meter_height))
    
    addiction_text = font.render(f"Banana Fever: {int(addiction_level)}%", True, WHITE)
    screen.blit(addiction_text, (x, y + meter_height + 5))

async def spawn_golden_banana():
    """Attempts to spawn a golden banana"""
    global golden_banana_active, golden_banana_x, golden_banana_y, golden_banana
    
    if not golden_banana_active and random.random() < golden_banana_chance:
        golden_banana_x = random.randint(0, SCREEN_WIDTH - 50)
        golden_banana_y = random.randint(100, SCREEN_HEIGHT - 150)
        golden_banana = pygame.Rect(golden_banana_x, golden_banana_y, 50, 50)
        golden_banana_active = True

async def generate_platforms():
    """Generate random platforms"""
    platform_list.clear()
    
    vertical_spacing = (SCREEN_HEIGHT - 130) // num_platforms
    
    for i in range(num_platforms):
        platform_x = random.randint(0, SCREEN_WIDTH - platform_width)
        platform_y = 80 + (i * vertical_spacing)
        platform_x += random.randint(-50, 50)
        platform_x = max(0, min(platform_x, SCREEN_WIDTH - platform_width))
        
        platform_list.append(pygame.Rect(platform_x, platform_y, platform_width, platform_height))

async def advance_timer():
    """Update and display timer"""
    global top_score, frames_left

    frames_left -= 1
    timer_txt = font.render(f"Time left: {frames_left}", True, WHITE)
    screen.blit(timer_txt, (10, 60))

    if frames_left <= 0:
        if score > top_score:
            top_score = score
        await game_over_display()

async def draw_setting():
    """Draws background, platforms, floor, and bananas"""
    screen.fill(SKY_BLUE)

    for platform in platform_list:
        screen.blit(platform_img, platform)

    pygame.draw.rect(screen, DARK_GREEN, floor)

    for banana in bananas:
        screen.blit(banana_img, banana)
    
    if golden_banana_active and golden_banana is not None:
        golden_banana_surface = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.circle(golden_banana_surface, (*GOLD, 200), (25, 25), 25)
        screen.blit(golden_banana_surface, (golden_banana_x, golden_banana_y))
        screen.blit(golden_banana_img, (golden_banana_x, golden_banana_y))

    score_txt = font.render(f"Banana Score: {score}", True, WHITE)
    screen.blit(score_txt, (10, 10))
    
    await draw_addiction_meter()

async def generate_bananas():
    """Generate multiple bananas at random positions"""
    bananas.clear()
    for _ in range(num_bananas):
        banana_x = random.randint(0, SCREEN_WIDTH - 50)
        banana_y = random.randint(50, SCREEN_HEIGHT - 150)
        bananas.append(pygame.Rect(banana_x, banana_y, 50, 50))

async def load_high_scores():
    """Load high scores from file"""
    scores = []
    try:
        with open('highscore.txt', 'r') as file:
            lines = file.readlines()
            scores = [tuple(line.strip().split(',')) for line in lines]
    except FileNotFoundError:
        scores = []
    return sorted(scores, key=lambda x: int(x[1]), reverse=True)[:5]

async def save_high_score(new_score):
    """Save score to highscore.txt"""
    scores = await load_high_scores()
    scores.append((player_name, str(new_score)))
    scores = sorted(scores, key=lambda x: int(x[1]), reverse=True)[:5]
    
    with open('highscore.txt', 'w') as file:
        for name, score in scores:
            file.write(f"{name},{score}\n")

async def update_monkey():
    """Control monkey's movement and image, and detect collisions"""
    global monkey_x, monkey_y, velocity_y, monkey, monkey_img, platform_list, score, addiction_level
    global golden_banana_active, frames_left

    addiction_level = max(0, addiction_level - healing_rate)
    
    current_gravity = gravity * (1 + (addiction_level / 100))
    current_speed = 5 * (1 - (addiction_level / 200))
    
    velocity_y += current_gravity
    monkey_y += velocity_y

    key_pressed = pygame.key.get_pressed()
    if key_pressed[pygame.K_a]:
        monkey_x -= current_speed
    elif key_pressed[pygame.K_d]:
        monkey_x += current_speed
    
    monkey_x = max(0, min(monkey_x, SCREEN_WIDTH - monkey_size))
    
    monkey = pygame.Rect(monkey_x, monkey_y, monkey_size, monkey_size)

    for platform in platform_list:
        if monkey.colliderect(platform) and velocity_y > 0:
            monkey_y = platform[1] - monkey_size
            velocity_y = 0
            if key_pressed[pygame.K_SPACE]:
                velocity_y = jump_power * (1 - (addiction_level / 150))
                try:
                    jump_sound.play()
                except:
                    pass

    if monkey.colliderect(floor):
        monkey_y = floor[1] - monkey_size
        velocity_y = 0
        if key_pressed[pygame.K_SPACE]:
            velocity_y = jump_power * (1 - (addiction_level / 150))
            try:
                jump_sound.play()
            except:
                pass

    sprite_frame = int((frame / 5) % 4) + 1
    if addiction_level > 75:
        monkey_img = pygame.image.load(f"hungry_monkey_sprites/5monkey_happy.png")
    elif sprite_frame == 1:
        current_sprite = f"hungry_monkey_sprites/2monkey_f1.png"
    elif sprite_frame == 2:
        current_sprite = f"hungry_monkey_sprites/0monkey_f2.png"
    elif sprite_frame == 3:
        current_sprite = f"hungry_monkey_sprites/3monkey_f3.png"
    else:
        current_sprite = f"hungry_monkey_sprites/4monkey_f4.png"
        
    if addiction_level <= 75:
        monkey_img = pygame.image.load(current_sprite)
            
    if velocity_y < 0 and addiction_level <= 75:
        monkey_img = pygame.image.load(f"hungry_monkey_sprites/6monkey_jump_sprite.png")

    for banana in bananas[:]:
        if monkey.colliderect(banana):
            bananas.remove(banana)
            score += 1
            addiction_level = min(max_addiction, addiction_level + banana_addiction)
            try:
                collect_sound.play()
            except:
                pass
            
    if golden_banana_active and golden_banana and monkey.colliderect(golden_banana):
        golden_banana_active = False
        addiction_level = max(0, addiction_level - 30)
        frames_left += 100
        try:
            collect_sound.play()
        except:
            pass

    if not bananas:
        await generate_bananas()

    screen.blit(monkey_img, (monkey_x, monkey_y))
    
    if addiction_level >= max_addiction:
        await game_over_display("Banana Overdose!")

async def game_over_display(reason="Time's Up!"):
    """Displays animated game over screen with high scores"""
    global score, game_over_y, animation_alpha
    
    try:
        game_over_sound.play()
    except:
        pass

    save_high_score(score)
    high_scores = await load_high_scores()

    animation_frames = 60
    for i in range(animation_frames):
        screen.fill(SKY_BLUE)
        
        game_over_y = min(-100 + (i * 5), SCREEN_HEIGHT // 4)
        times_up_txt = large_font.render(reason, True, RED)
        times_up_rect = times_up_txt.get_rect(center=(SCREEN_WIDTH // 2, game_over_y))
        screen.blit(times_up_txt, times_up_rect)

        if i > 20:
            alpha = min(255, (i - 20) * 12)
            
            score_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            
            y_offset = SCREEN_HEIGHT // 2 - 50
            score_txt = font.render(f"Your score: {score}", True, (*WHITE, alpha))
            score_surface.blit(score_txt, (SCREEN_WIDTH // 2 - score_txt.get_width() // 2, y_offset))
            
            y_offset += 50
            rank_txt = font.render("High Scores:", True, (*WHITE, alpha))
            score_surface.blit(rank_txt, (SCREEN_WIDTH // 2 - rank_txt.get_width() // 2, y_offset))
            
            for idx, (name, high_score) in enumerate(high_scores, 1):
                y_offset += 30
                hs_txt = font.render(f"{idx}. {name}: {high_score}", True, (*WHITE, alpha))
                score_surface.blit(hs_txt, (SCREEN_WIDTH // 2 - hs_txt.get_width() // 2, y_offset))
            
            screen.blit(score_surface, (0, 0))

        restart_txt = font.render("Press R to restart, or Q to quit", True, WHITE)
        screen.blit(restart_txt, (SCREEN_WIDTH // 2 - restart_txt.get_width() // 2, SCREEN_HEIGHT - 100))
        
        pygame.display.update()
        await asyncio.sleep(1/30)

    input_waiting = True
    while input_waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    input_waiting = False
                    await game_loop()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
        await asyncio.sleep(0)

async def reset_variables():
    """Reset game variables"""
    global frames_left, score, platform_list, monkey_x, monkey_y, game_over_y
    global animation_alpha, velocity_y, addiction_level, golden_banana_active

    frames_left = 1000
    score = 0
    addiction_level = 0
    platform_list = []
    golden_banana_active = False
    await generate_platforms()
    monkey_x = int(SCREEN_WIDTH / 2)
    monkey_y = SCREEN_HEIGHT - 100
    velocity_y = 0
    game_over_y = -100
    animation_alpha = 255

async def draw_title_screen():
    """Displays animated title screen and gets player name"""
    global player_name
    
    title_y = -100
    monkey_scale = 0
    name_alpha = 0
    input_active = False
    
    monkey_title = pygame.image.load(f"hungry_monkey_sprites/2monkey_f1.png")
    monkey_title = pygame.transform.scale(monkey_title, (200, 200))
    
    while True:
        screen.fill(SKY_BLUE)
        
        if title_y < SCREEN_HEIGHT // 4:
            title_y += 5
        
        if monkey_scale < 1:
            monkey_scale += 0.02
        
        if name_alpha < 255 and title_y >= SCREEN_HEIGHT // 4:
            name_alpha += 5
        
        title_text = title_font.render("Hungry Monkey", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        screen.blit(title_text, title_rect)
        
        scaled_size = int(200 * monkey_scale)
        if scaled_size > 0:
            scaled_monkey = pygame.transform.scale(monkey_title, (scaled_size, scaled_size))
            monkey_rect = scaled_monkey.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(scaled_monkey, monkey_rect)
        
        if name_alpha > 0:
            name_surface = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)
            prompt_text = font.render("Enter your name:", True, (*WHITE, name_alpha))
            name_text = font.render(player_name + ("_" if input_active else ""), True, (*WHITE, name_alpha))
            
            name_surface.blit(prompt_text, (SCREEN_WIDTH // 2 - prompt_text.get_width() // 2, 0))
            name_surface.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, 40))
            
            if name_alpha >= 255:
                input_active = True
                start_text = font.render("Press ENTER to start", True, WHITE)
                name_surface.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, 80))
            
            screen.blit(name_surface, (0, SCREEN_HEIGHT - 150))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if input_active and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and player_name.strip():
                    return
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.key <= 127 and len(player_name) < 15:
                    if event.unicode.isalnum() or event.unicode.isspace():
                        player_name += event.unicode
        
        pygame.display.update()
        await asyncio.sleep(1/60)

async def game_loop():
    """Main game loop"""
    global frame

    await draw_title_screen()
    await reset_variables()
    
    try:
        pygame.mixer.music.play(-1)
    except:
        pass

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

        await draw_setting()
        await update_monkey()
        await advance_timer()
        await spawn_golden_banana()

        pygame.display.update()
        await asyncio.sleep(1/30)
        frame += 1

async def main():
    """Main async function to run the game"""
    await game_loop()

if __name__ == "__main__":
    asyncio.run(main())

