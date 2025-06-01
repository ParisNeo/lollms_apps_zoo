import pygame
import sys
import math
import random
import json
from pygame import gfxdraw
from datetime import datetime

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Screen dimensions
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Kingdom: Evolutionary Battle")

# Colors
BACKGROUND = (15, 20, 30)
GRID_COLOR = (30, 40, 60)
PLAYER_COLOR = (0, 200, 255)
AI_COLORS = [
    (255, 50, 100),
    (180, 70, 255),
    (255, 150, 50),
    (50, 200, 100),
    (200, 100, 255)
]
KING_COLOR = (255, 215, 0)
FOOD_COLOR = (255, 100, 100)
MAGNET_COLOR = (100, 200, 255)
TEXT_COLOR = (220, 220, 220)
UI_COLOR = (40, 50, 80)
UI_HIGHLIGHT = (70, 130, 180)
BUTTON_COLOR = (60, 80, 120)
BUTTON_HOVER = (90, 120, 180)

# Game constants
CELL_SIZE = 20
GRID_WIDTH = WIDTH // CELL_SIZE
GRID_HEIGHT = HEIGHT // CELL_SIZE
ARENA_MARGIN = 50
ARENA_WIDTH = WIDTH - 2 * ARENA_MARGIN
ARENA_HEIGHT = HEIGHT - 2 * ARENA_MARGIN
GRID_COLS = ARENA_WIDTH // CELL_SIZE
GRID_ROWS = ARENA_HEIGHT // CELL_SIZE

# Game variables
FPS = 60
INITIAL_SNAKE_LENGTH = 5
FOOD_SPAWN_CHANCE = 0.03
MAGNET_SPAWN_CHANCE = 0.005
MAGNET_DURATION = 5 * FPS  # 5 seconds
GAME_DURATION = 120 * FPS  # 2 minutes
MAX_LEVEL = 5

# Create game fonts
font_large = pygame.font.SysFont("Arial", 48, bold=True)
font_medium = pygame.font.SysFont("Arial", 28)
font_small = pygame.font.SysFont("Arial", 20)

class Snake:
    def __init__(self, start_pos, color, player_id, is_player=False, level=1):
        self.body = [start_pos]
        self.direction = (1, 0)
        self.color = color
        self.player_id = player_id
        self.grow_pending = INITIAL_SNAKE_LENGTH - 1
        self.alive = True
        self.score = 0
        self.speed = 4 + level // 2
        self.last_move_time = 0
        self.move_delay = 1000 // self.speed
        self.is_player = is_player
        self.magnet_active = False
        self.magnet_timer = 0
        self.magnet_strength = 0
        self.is_king = False
        self.king_timer = 0
        self.ai_direction_change_timer = 0
        
    def move(self, current_time, food_positions, other_snakes):
        if not self.alive:
            return
            
        # Handle movement delay based on speed
        if current_time - self.last_move_time < self.move_delay:
            return
            
        self.last_move_time = current_time
        
        # For AI snakes, periodically consider changing direction
        if not self.is_player and self.ai_direction_change_timer <= 0:
            self.ai_direction_change_timer = random.randint(10, 30)
            self.consider_direction_change(food_positions, other_snakes)
        else:
            self.ai_direction_change_timer -= 1
        
        # Calculate new head position
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = (
            (head_x + dx) % GRID_COLS,
            (head_y + dy) % GRID_ROWS
        )
        
        # Check for collision with food
        ate_food = False
        for food in food_positions[:]:
            if new_head == food:
                self.grow(1)
                food_positions.remove(food)
                ate_food = True
                self.score += 10
                break
                
        # Check for collision with other snakes
        collision_snake = None
        collision_index = -1
        
        for snake in other_snakes:
            if not snake.alive:
                continue
                
            for i, segment in enumerate(snake.body):
                if new_head == segment:
                    collision_snake = snake
                    collision_index = i
                    break
                    
            if collision_snake:
                break
                
        # Handle snake collisions
        if collision_snake:
            # Big snake eating smaller snake
            if len(self.body) > len(collision_snake.body) and collision_index > 0:
                # Truncate the smaller snake
                tail_segment = collision_snake.body[collision_index:]
                collision_snake.body = collision_snake.body[:collision_index]
                
                # Add the tail segment as food
                for segment in tail_segment:
                    food_positions.append(segment)
                    
                # Grow the bigger snake by the number of segments eaten
                self.grow(len(tail_segment))
                self.score += len(tail_segment) * 5
                
                # Play crunch sound effect
                crunch_sound.play()
            elif self == collision_snake and collision_index == 0:
                # Collision with own head (only possible with wrap-around)
                pass
            else:
                # Collision with head of another snake or bigger snake
                if new_head == collision_snake.body[0]:
                    # Head-to-head collision
                    if len(self.body) > len(collision_snake.body):
                        # This snake wins
                        collision_snake.die()
                        self.grow(len(collision_snake.body) // 2)
                        self.score += len(collision_snake.body) * 10
                    elif len(self.body) < len(collision_snake.body):
                        # This snake loses
                        self.die()
                        collision_snake.grow(len(self.body) // 2)
                        collision_snake.score += len(self.body) * 10
                    else:
                        # Equal size - both die
                        self.die()
                        collision_snake.die()
                else:
                    # Body collision - only die if hitting a bigger snake's body
                    if len(self.body) < len(collision_snake.body):
                        self.die()
        
        # Move the snake
        if self.alive:
            self.body.insert(0, new_head)
            
            if not ate_food and self.grow_pending <= 0:
                self.body.pop()
            elif self.grow_pending > 0:
                self.grow_pending -= 1
    
    def consider_direction_change(self, food_positions, other_snakes):
        # Simple AI: move toward food if possible, avoid collisions
        
        head_x, head_y = self.body[0]
        possible_directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        # Remove opposite direction to prevent 180-degree turns
        opposite_direction = (-self.direction[0], -self.direction[1])
        possible_directions = [d for d in possible_directions if d != opposite_direction]
        
        # Score each possible direction
        direction_scores = []
        
        for dx, dy in possible_directions:
            new_head = ((head_x + dx) % GRID_COLS, (head_y + dy) % GRID_ROWS)
            score = 0
            
            # Check for immediate collision
            collision = False
            for snake in other_snakes:
                if not snake.alive:
                    continue
                    
                if new_head in snake.body:
                    # Avoid bigger snakes
                    if len(snake.body) > len(self.body) and snake.body[0] != new_head:
                        collision = True
                        break
                    # Don't avoid smaller snakes (we can eat them)
            
            if collision:
                direction_scores.append(-100)
                continue
                
            # Attract to food
            for food_x, food_y in food_positions:
                dist = abs(new_head[0] - food_x) + abs(new_head[1] - food_y)
                score += max(0, (GRID_COLS + GRID_ROWS - dist) // 5)
                
            # Avoid going toward walls if no food
            if score == 0:
                # Prefer to stay away from walls
                wall_dist_x = min(new_head[0], GRID_COLS - new_head[0])
                wall_dist_y = min(new_head[1], GRID_ROWS - new_head[1])
                score = min(wall_dist_x, wall_dist_y)
                
            direction_scores.append(score)
        
        # Choose best direction
        if direction_scores:
            best_score = max(direction_scores)
            if best_score > 0:
                best_index = direction_scores.index(best_score)
                self.direction = possible_directions[best_index]
    
    def change_direction(self, new_direction):
        # Prevent 180-degree turns
        current_dx, current_dy = self.direction
        new_dx, new_dy = new_direction
        
        if (current_dx, current_dy) != (-new_dx, -new_dy):
            self.direction = new_direction
    
    def grow(self, amount=1):
        self.grow_pending += amount
    
    def activate_magnet(self, strength=10):
        self.magnet_active = True
        self.magnet_timer = MAGNET_DURATION
        self.magnet_strength = strength
    
    def update_effects(self):
        # Update magnet effect
        if self.magnet_active:
            self.magnet_timer -= 1
            if self.magnet_timer <= 0:
                self.magnet_active = False
                
        # Update king highlight
        if self.is_king:
            self.king_timer -= 1
            if self.king_timer <= 0:
                self.is_king = False
    
    def die(self):
        self.alive = False
        death_sound.play()
    
    def draw(self, surface):
        if not self.alive:
            return
            
        # Draw crown for king
        if self.is_king:
            head_x, head_y = self.body[0]
            px = ARENA_MARGIN + head_x * CELL_SIZE + CELL_SIZE//2
            py = ARENA_MARGIN + head_y * CELL_SIZE - CELL_SIZE//2
            
            # Draw crown
            pygame.draw.polygon(surface, KING_COLOR, [
                (px - CELL_SIZE//2, py),
                (px - CELL_SIZE//4, py - CELL_SIZE//3),
                (px, py - CELL_SIZE//2),
                (px + CELL_SIZE//4, py - CELL_SIZE//3),
                (px + CELL_SIZE//2, py),
            ])
            
            # Draw jewels
            pygame.draw.circle(surface, (255, 50, 100), (px - CELL_SIZE//3, py - CELL_SIZE//6), CELL_SIZE//6)
            pygame.draw.circle(surface, (50, 200, 100), (px, py - CELL_SIZE//4), CELL_SIZE//5)
            pygame.draw.circle(surface, (100, 150, 255), (px + CELL_SIZE//3, py - CELL_SIZE//6), CELL_SIZE//6)
            
        # Draw magnet effect if active
        if self.magnet_active:
            head_x, head_y = self.body[0]
            px = ARENA_MARGIN + head_x * CELL_SIZE + CELL_SIZE//2
            py = ARENA_MARGIN + head_y * CELL_SIZE + CELL_SIZE//2
            
            # Draw pulsing magnetic field
            field_size = CELL_SIZE * 2 + math.sin(pygame.time.get_ticks() / 200) * 5
            pygame.draw.circle(surface, (*MAGNET_COLOR, 50), 
                             (px, py), field_size, 2)
            
            # Draw magnetic poles
            pole_size = CELL_SIZE // 3
            pygame.draw.circle(surface, (255, 100, 100), 
                             (px - pole_size, py), pole_size//2)
            pygame.draw.circle(surface, (100, 100, 255), 
                             (px + pole_size, py), pole_size//2)
        
        # Draw snake body
        for i, (x, y) in enumerate(self.body):
            # Calculate position in pixels
            px = ARENA_MARGIN + x * CELL_SIZE
            py = ARENA_MARGIN + y * CELL_SIZE
            
            # Draw snake segment with gradient effect
            color_factor = 1.0 - (i / len(self.body)) * 0.7
            segment_color = (
                max(0, min(255, int(self.color[0] * color_factor))),
                max(0, min(255, int(self.color[1] * color_factor))),
                max(0, min(255, int(self.color[2] * color_factor)))
            )
            
            # Draw rounded segment
            pygame.draw.rect(surface, segment_color, 
                            (px, py, CELL_SIZE, CELL_SIZE), 
                            border_radius=8)
            
            # Draw highlight on head
            if i == 0:
                pygame.draw.circle(surface, (255, 255, 255), 
                                  (px + CELL_SIZE//2, py + CELL_SIZE//2), 
                                  CELL_SIZE//3)
                
                # Draw eyes
                eye_size = CELL_SIZE // 5
                eye_offset = CELL_SIZE // 3
                
                # Determine eye positions based on direction
                dx, dy = self.direction
                if dx == 1:  # Right
                    left_eye = (px + CELL_SIZE - eye_offset, py + eye_offset)
                    right_eye = (px + CELL_SIZE - eye_offset, py + CELL_SIZE - eye_offset)
                elif dx == -1:  # Left
                    left_eye = (px + eye_offset, py + eye_offset)
                    right_eye = (px + eye_offset, py + CELL_SIZE - eye_offset)
                elif dy == 1:  # Down
                    left_eye = (px + eye_offset, py + CELL_SIZE - eye_offset)
                    right_eye = (px + CELL_SIZE - eye_offset, py + CELL_SIZE - eye_offset)
                else:  # Up
                    left_eye = (px + eye_offset, py + eye_offset)
                    right_eye = (px + CELL_SIZE - eye_offset, py + eye_offset)
                
                pygame.draw.circle(surface, (0, 0, 0), left_eye, eye_size)
                pygame.draw.circle(surface, (0, 0, 0), right_eye, eye_size)

class MagnetPowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = MAGNET_COLOR
        self.size = CELL_SIZE // 2
        self.collected = False
        self.spawn_time = pygame.time.get_ticks()
        self.pulse_phase = 0
        
    def update(self):
        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)
        
    def draw(self, surface):
        if self.collected:
            return
            
        px = ARENA_MARGIN + self.x * CELL_SIZE + CELL_SIZE//2
        py = ARENA_MARGIN + self.y * CELL_SIZE + CELL_SIZE//2
        
        # Draw pulsing effect
        pulse_size = self.size + math.sin(self.pulse_phase) * 3
        
        # Draw outer glow
        pygame.draw.circle(surface, 
                          (self.color[0], self.color[1], self.color[2], 100),
                          (px, py), 
                          pulse_size + 2)
        
        # Draw main power-up circle
        pygame.draw.circle(surface, self.color, (px, py), pulse_size)
        
        # Draw magnet icon
        pygame.draw.rect(surface, BACKGROUND, 
                        (px - pulse_size//2, py - pulse_size//3, 
                         pulse_size, pulse_size//1.5),
                        border_radius=3)
        
        # Draw magnetic field lines
        for i in range(3):
            angle = self.pulse_phase + i * math.pi/3
            start_x = px + math.cos(angle) * pulse_size * 0.8
            start_y = py + math.sin(angle) * pulse_size * 0.8
            end_x = px + math.cos(angle) * pulse_size * 1.5
            end_y = py + math.sin(angle) * pulse_size * 1.5
            
            pygame.draw.line(surface, BACKGROUND, (start_x, start_y), (end_x, end_y), 2)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.lifetime = random.randint(20, 40)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)
        
    def draw(self, surface):
        alpha = min(255, self.lifetime * 6)
        pygame.draw.circle(surface, 
                          (*self.color, alpha),
                          (int(self.x), int(self.y)), 
                          int(self.size))

class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        
    def draw(self, surface):
        color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, UI_HIGHLIGHT, self.rect, 2, border_radius=10)
        
        text_surf = font_medium.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.action:
                self.action()
                return True
        return False

class Game:
    def __init__(self, level=1):
        self.level = min(level, MAX_LEVEL)
        self.player = Snake(
            start_pos=(GRID_COLS//4, GRID_ROWS//2),
            color=PLAYER_COLOR,
            player_id=0,
            is_player=True,
            level=self.level
        )
        
        # Create AI snakes
        self.ai_snakes = []
        num_ai = 3 + self.level  # More AI snakes at higher levels
        
        for i in range(num_ai):
            # Position AI snakes away from player
            start_x = GRID_COLS * 3 // 4 + random.randint(-5, 5)
            start_y = GRID_ROWS//2 + random.randint(-10, 10) % GRID_ROWS
            
            ai_snake = Snake(
                start_pos=(start_x, start_y),
                color=AI_COLORS[i % len(AI_COLORS)],
                player_id=i+1,
                level=self.level
            )
            # Set random initial direction
            ai_snake.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            self.ai_snakes.append(ai_snake)
        
        self.all_snakes = [self.player] + self.ai_snakes
        self.food_positions = []
        self.magnets = []
        self.particles = []
        self.game_over = False
        self.game_won = False
        self.time_remaining = GAME_DURATION
        self.king_snake = None
        self.update_king()
        
        # Generate initial food
        for _ in range(10 + self.level * 2):
            self.spawn_food()
        
        # Start background music
        if level == 1:
            pygame.mixer.music.play(-1)
    
    def spawn_food(self):
        # Find an empty position
        while True:
            x = random.randint(1, GRID_COLS - 2)
            y = random.randint(1, GRID_ROWS - 2)
            pos = (x, y)
            
            # Check if position is free
            occupied = False
            for snake in self.all_snakes:
                if pos in snake.body:
                    occupied = True
                    break
                    
            if pos in self.food_positions:
                occupied = True
                
            if not occupied:
                break
                
        self.food_positions.append(pos)
    
    def spawn_magnet(self):
        # Only spawn if there are less than 2 magnets
        if len(self.magnets) >= 2:
            return
            
        # Find an empty position
        while True:
            x = random.randint(1, GRID_COLS - 2)
            y = random.randint(1, GRID_ROWS - 2)
            pos = (x, y)
            
            # Check if position is free
            occupied = False
            for snake in self.all_snakes:
                if pos in snake.body:
                    occupied = True
                    break
                    
            if pos in self.food_positions:
                occupied = True
                
            if any(magnet.x == x and magnet.y == y for magnet in self.magnets):
                occupied = True
                
            if not occupied:
                break
                
        self.magnets.append(MagnetPowerUp(x, y))
    
    def handle_magnet_collision(self, snake):
        for magnet in self.magnets[:]:
            if snake.body[0] == (magnet.x, magnet.y) and not magnet.collected:
                magnet.collected = True
                snake.activate_magnet(10 + self.level * 2)
                self.magnets.remove(magnet)
                powerup_sound.play()
    
    def update_king(self):
        # Find the largest living snake
        largest_snake = None
        max_length = 0
        
        for snake in self.all_snakes:
            if snake.alive and len(snake.body) > max_length:
                max_length = len(snake.body)
                largest_snake = snake
        
        if largest_snake:
            # Update king status
            if self.king_snake != largest_snake:
                if self.king_snake:
                    self.king_snake.is_king = False
                largest_snake.is_king = True
                largest_snake.king_timer = 30  # Blink effect
                self.king_snake = largest_snake
    
    def update(self):
        if self.game_over:
            return
            
        current_time = pygame.time.get_ticks()
        
        # Update game timer
        self.time_remaining -= 1
        if self.time_remaining <= 0:
            self.game_over = True
            self.determine_winner()
            return
            
        # Apply magnet effects
        for snake in self.all_snakes:
            if snake.magnet_active and snake.alive:
                head_x, head_y = snake.body[0]
                
                # Attract nearby food
                for food_pos in self.food_positions[:]:
                    fx, fy = food_pos
                    dist = math.sqrt((head_x - fx)**2 + (head_y - fy)**2)
                    
                    if dist < snake.magnet_strength:
                        # Move food toward snake
                        dx = head_x - fx
                        dy = head_y - fy
                        
                        # Normalize direction
                        if dx != 0 or dy != 0:
                            length = math.sqrt(dx*dx + dy*dy)
                            dx, dy = dx/length, dy/length
                            
                            # Move food
                            new_fx = round(fx + dx * 0.7)
                            new_fy = round(fy + dy * 0.7)
                            new_pos = (new_fx, new_fy)
                            
                            # Check if new position is valid
                            valid_pos = True
                            for s in self.all_snakes:
                                if new_pos in s.body:
                                    valid_pos = False
                                    break
                            
                            if valid_pos and 0 <= new_fx < GRID_COLS and 0 <= new_fy < GRID_ROWS:
                                self.food_positions.remove(food_pos)
                                self.food_positions.append(new_pos)
        
        # Update player
        self.player.move(current_time, self.food_positions, self.all_snakes)
        
        # Update AI snakes
        for ai_snake in self.ai_snakes:
            if ai_snake.alive:
                ai_snake.move(current_time, self.food_positions, self.all_snakes)
        
        # Update effects
        for snake in self.all_snakes:
            snake.update_effects()
        
        # Check for magnet collisions
        self.handle_magnet_collision(self.player)
        for ai_snake in self.ai_snakes:
            self.handle_magnet_collision(ai_snake)
        
        # Randomly spawn food
        if random.random() < FOOD_SPAWN_CHANCE:
            self.spawn_food()
            
        # Randomly spawn magnets
        if random.random() < MAGNET_SPAWN_CHANCE:
            self.spawn_magnet()
            
        # Update magnets
        for magnet in self.magnets:
            magnet.update()
            
        # Update particles
        for particle in self.particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                self.particles.remove(particle)
        
        # Update king status
        self.update_king()
        
        # Check if player is dead
        if not self.player.alive:
            self.game_over = True
            self.game_won = False
    
    def determine_winner(self):
        # Find the snake with the highest score
        highest_score = -1
        winner = None
        
        for snake in self.all_snakes:
            if snake.alive and snake.score > highest_score:
                highest_score = snake.score
                winner = snake
                
        self.game_won = winner and winner.is_player
        
        # Add to leaderboard
        if self.game_won:
            self.add_to_leaderboard(self.player.score, self.level)
    
    def add_to_leaderboard(self, score, level):
        try:
            with open("leaderboard.json", "r") as f:
                leaderboard = json.load(f)
        except:
            leaderboard = []
            
        # Add new entry
        new_entry = {
            "score": score,
            "level": level,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        leaderboard.append(new_entry)
        
        # Sort and keep top 10
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        leaderboard = leaderboard[:10]
        
        with open("leaderboard.json", "w") as f:
            json.dump(leaderboard, f)
    
    def draw(self, surface):
        # Draw background
        surface.fill(BACKGROUND)
        
        # Draw arena border
        pygame.draw.rect(surface, UI_HIGHLIGHT, 
                        (ARENA_MARGIN - 5, ARENA_MARGIN - 5, 
                         ARENA_WIDTH + 10, ARENA_HEIGHT + 10), 
                        5, border_radius=15)
        
        # Draw grid
        for x in range(GRID_COLS):
            for y in range(GRID_ROWS):
                # Draw grid dots
                dot_size = 1
                dot_x = ARENA_MARGIN + x * CELL_SIZE + CELL_SIZE//2
                dot_y = ARENA_MARGIN + y * CELL_SIZE + CELL_SIZE//2
                pygame.draw.circle(surface, GRID_COLOR, (dot_x, dot_y), dot_size)
        
        # Draw food
        for food_x, food_y in self.food_positions:
            px = ARENA_MARGIN + food_x * CELL_SIZE + CELL_SIZE//2
            py = ARENA_MARGIN + food_y * CELL_SIZE + CELL_SIZE//2
            pygame.draw.circle(surface, FOOD_COLOR, (px, py), CELL_SIZE//3)
            
            # Draw shine effect
            pygame.draw.circle(surface, (255, 200, 200), 
                             (px - CELL_SIZE//8, py - CELL_SIZE//8), 
                             CELL_SIZE//8)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(surface)
            
        # Draw magnets
        for magnet in self.magnets:
            magnet.draw(surface)
        
        # Draw snakes
        for snake in self.all_snakes:
            snake.draw(surface)
        
        # Draw HUD
        self.draw_hud(surface)
        
        # Draw game over screen
        if self.game_over:
            self.draw_game_over(surface)
    
    def draw_hud(self, surface):
        # Player stats
        pygame.draw.rect(surface, UI_COLOR, (20, 20, 300, 100), border_radius=10)
        pygame.draw.rect(surface, UI_HIGHLIGHT, (20, 20, 300, 100), 2, border_radius=10)
        
        # Level
        level_text = font_small.render(f"Level: {self.level}", True, TEXT_COLOR)
        surface.blit(level_text, (40, 30))
        
        # Score
        score_text = font_medium.render(f"Score: {self.player.score}", True, TEXT_COLOR)
        surface.blit(score_text, (40, 55))
        
        # Size
        size_text = font_small.render(f"Size: {len(self.player.body)}", True, TEXT_COLOR)
        surface.blit(size_text, (40, 85))
        
        # Time remaining
        minutes = self.time_remaining // (FPS * 60)
        seconds = (self.time_remaining // FPS) % 60
        time_text = font_medium.render(f"Time: {minutes:02d}:{seconds:02d}", True, TEXT_COLOR)
        time_rect = time_text.get_rect(center=(WIDTH//2, 40))
        surface.blit(time_text, time_rect)
        
        # King indicator
        if self.king_snake and self.king_snake.is_player:
            king_text = font_medium.render("YOU ARE THE KING!", True, KING_COLOR)
            king_rect = king_text.get_rect(center=(WIDTH//2, 80))
            surface.blit(king_text, king_rect)
        elif self.king_snake:
            king_text = font_medium.render("KING SNAKE!", True, KING_COLOR)
            king_rect = king_text.get_rect(center=(WIDTH//2, 80))
            surface.blit(king_text, king_rect)
        
        # Magnet status
        if self.player.magnet_active:
            magnet_text = font_small.render(f"MAGNET: {self.player.magnet_timer//FPS + 1}s", True, MAGNET_COLOR)
            magnet_rect = magnet_text.get_rect(midright=(WIDTH - 40, 40))
            surface.blit(magnet_text, magnet_rect)
    
    def draw_game_over(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Draw game over box
        pygame.draw.rect(surface, UI_COLOR, 
                        (WIDTH//2 - 200, HEIGHT//2 - 150, 400, 300), 
                        border_radius=20)
        pygame.draw.rect(surface, UI_HIGHLIGHT, 
                        (WIDTH//2 - 200, HEIGHT//2 - 150, 400, 300), 
                        3, border_radius=20)
        
        # Draw result text
        if self.game_won:
            result_text = font_large.render("VICTORY!", True, (100, 255, 100))
        else:
            result_text = font_large.render("GAME OVER", True, (255, 100, 100))
            
        surface.blit(result_text, (WIDTH//2 - result_text.get_width()//2, HEIGHT//2 - 120))
        
        # Draw scores
        score_text = font_medium.render(f"Final Score: {self.player.score}", True, TEXT_COLOR)
        surface.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 - 50))
        
        # Draw level
        level_text = font_medium.render(f"Level: {self.level}", True, TEXT_COLOR)
        surface.blit(level_text, (WIDTH//2 - level_text.get_width()//2, HEIGHT//2 - 10))
        
        # Draw restart instructions
        restart_text = font_medium.render("Press SPACE to continue", True, (150, 200, 255))
        surface.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))
        
        # Draw menu instructions
        menu_text = font_small.render("Press M for Main Menu", True, TEXT_COLOR)
        surface.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, HEIGHT//2 + 100))

class Menu:
    def __init__(self):
        self.buttons = []
        self.leaderboard = []
        self.current_screen = "main"  # "main", "credits", "leaderboard"
        self.level = 1
        
        # Load leaderboard
        self.load_leaderboard()
        
        # Create buttons
        button_width, button_height = 300, 60
        center_x = WIDTH // 2 - button_width // 2
        start_y = HEIGHT // 2 - button_height
        
        self.buttons.append(Button(center_x, start_y, button_width, button_height, "Start Game", self.start_game))
        self.buttons.append(Button(center_x, start_y + 80, button_width, button_height, "Leaderboard", self.show_leaderboard))
        self.buttons.append(Button(center_x, start_y + 160, button_width, button_height, "Credits", self.show_credits))
        self.buttons.append(Button(center_x, start_y + 240, button_width, button_height, "Quit", self.quit_game))
        
        # Level selection buttons
        self.level_buttons = []
        for i in range(MAX_LEVEL):
            self.level_buttons.append(Button(
                center_x - 150 + i * 70, 
                start_y + 100, 
                60, 40, 
                str(i+1), 
                lambda lvl=i+1: self.select_level(lvl)
            ))
        
        # Back button for sub-screens
        self.back_button = Button(WIDTH//2 - 100, HEIGHT - 100, 200, 50, "Back", self.show_main_menu)
    
    def load_leaderboard(self):
        try:
            with open("leaderboard.json", "r") as f:
                self.leaderboard = json.load(f)
        except:
            self.leaderboard = []
    
    def select_level(self, level):
        self.level = level
        self.start_game()
    
    def start_game(self):
        global game_state
        game_state = Game(self.level)
    
    def show_leaderboard(self):
        self.current_screen = "leaderboard"
    
    def show_credits(self):
        self.current_screen = "credits"
    
    def show_main_menu(self):
        self.current_screen = "main"
    
    def quit_game(self):
        pygame.quit()
        sys.exit()
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.current_screen != "main":
                self.show_main_menu()
                return True
                
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.check_hover(mouse_pos)
            for button in self.level_buttons:
                button.check_hover(mouse_pos)
            self.back_button.check_hover(mouse_pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button.handle_event(event):
                    return True
                    
            for button in self.level_buttons:
                if button.handle_event(event):
                    return True
                    
            if self.back_button.handle_event(event):
                return True
                
        return False
    
    def draw(self, surface):
        surface.fill(BACKGROUND)
        
        # Draw title
        title_text = font_large.render("SNAKE KINGDOM", True, UI_HIGHLIGHT)
        title_rect = title_text.get_rect(center=(WIDTH//2, 100))
        surface.blit(title_text, title_rect)
        
        subtitle_text = font_medium.render("Evolutionary Battle", True, (150, 200, 255))
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH//2, 150))
        surface.blit(subtitle_text, subtitle_rect)
        
        if self.current_screen == "main":
            # Draw buttons
            for button in self.buttons:
                button.draw(surface)
            
            # Draw level selection
            level_text = font_medium.render(f"Level: {self.level}", True, TEXT_COLOR)
            level_rect = level_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            surface.blit(level_text, level_rect)
            
            # Draw level buttons
            for button in self.level_buttons:
                button.draw(surface)
                
        elif self.current_screen == "leaderboard":
            self.draw_leaderboard(surface)
        elif self.current_screen == "credits":
            self.draw_credits(surface)
    
    def draw_leaderboard(self, surface):
        # Draw title
        title_text = font_large.render("LEADERBOARD", True, UI_HIGHLIGHT)
        title_rect = title_text.get_rect(center=(WIDTH//2, 100))
        surface.blit(title_text, title_rect)
        
        # Draw table headers
        pygame.draw.rect(surface, UI_COLOR, (WIDTH//2 - 300, 150, 600, 40), border_radius=5)
        headers = ["Rank", "Score", "Level", "Date"]
        for i, header in enumerate(headers):
            header_text = font_medium.render(header, True, TEXT_COLOR)
            header_x = WIDTH//2 - 300 + 150 * i + 75 - header_text.get_width()//2
            surface.blit(header_text, (header_x, 160))
        
        # Draw leaderboard entries
        if not self.leaderboard:
            no_data_text = font_medium.render("No records yet!", True, TEXT_COLOR)
            no_data_rect = no_data_text.get_rect(center=(WIDTH//2, 250))
            surface.blit(no_data_text, no_data_rect)
        else:
            for i, entry in enumerate(self.leaderboard[:10]):
                y_pos = 200 + i * 40
                bg_color = (50, 60, 90) if i % 2 == 0 else (40, 50, 80)
                pygame.draw.rect(surface, bg_color, (WIDTH//2 - 300, y_pos, 600, 40))
                
                # Rank
                rank_text = font_medium.render(str(i+1), True, TEXT_COLOR)
                surface.blit(rank_text, (WIDTH//2 - 280, y_pos + 10))
                
                # Score
                score_text = font_medium.render(str(entry["score"]), True, TEXT_COLOR)
                surface.blit(score_text, (WIDTH//2 - 130, y_pos + 10))
                
                # Level
                level_text = font_medium.render(str(entry["level"]), True, TEXT_COLOR)
                surface.blit(level_text, (WIDTH//2 + 20, y_pos + 10))
                
                # Date
                date_text = font_medium.render(entry["date"], True, TEXT_COLOR)
                surface.blit(date_text, (WIDTH//2 + 170, y_pos + 10))
        
        # Draw back button
        self.back_button.draw(surface)
    
    def draw_credits(self, surface):
        # Draw title
        title_text = font_large.render("CREDITS", True, UI_HIGHLIGHT)
        title_rect = title_text.get_rect(center=(WIDTH//2, 100))
        surface.blit(title_text, title_rect)
        
        # Draw credits content
        credits = [
            "Game Design & Programming: DeepSeek Assistant",
            "Concept: Snake Kingdom Evolutionary Battle",
            "Special Thanks:",
            "- PyGame Community",
            "- Snake Game Pioneers",
            "- Creative AI Development",
            "Version: 1.0"
        ]
        
        for i, line in enumerate(credits):
            text = font_medium.render(line, True, TEXT_COLOR)
            text_rect = text.get_rect(center=(WIDTH//2, 200 + i * 50))
            surface.blit(text, text_rect)
        
        # Draw back button
        self.back_button.draw(surface)

# Load sounds
try:
    crunch_sound = pygame.mixer.Sound("crunch.wav")  # Placeholder
    death_sound = pygame.mixer.Sound("death.wav")    # Placeholder
    powerup_sound = pygame.mixer.Sound("powerup.wav") # Placeholder
    
    # Background music
    pygame.mixer.music.load("background.mp3")  # Placeholder
    pygame.mixer.music.set_volume(0.5)
except:
    # Create silent sounds if files not found
    crunch_sound = pygame.mixer.Sound(buffer=bytearray([]))
    death_sound = pygame.mixer.Sound(buffer=bytearray([]))
    powerup_sound = pygame.mixer.Sound(buffer=bytearray([]))

# Initialize game state
game_state = None
menu = Menu()
clock = pygame.time.Clock()

# Main game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game_state and not game_state.game_over:
                # Player controls
                if event.key == pygame.K_UP:
                    game_state.player.change_direction((0, -1))
                elif event.key == pygame.K_DOWN:
                    game_state.player.change_direction((0, 1))
                elif event.key == pygame.K_LEFT:
                    game_state.player.change_direction((-1, 0))
                elif event.key == pygame.K_RIGHT:
                    game_state.player.change_direction((1, 0))
                elif event.key == pygame.K_m:
                    pygame.mixer.music.stop()
                    menu = Menu()
            elif game_state and game_state.game_over:
                if event.key == pygame.K_SPACE:
                    # Continue to next level or restart
                    if game_state.game_won and game_state.level < MAX_LEVEL:
                        game_state = Game(game_state.level + 1)
                    else:
                        game_state = Game(game_state.level)
                elif event.key == pygame.K_m:
                    pygame.mixer.music.stop()
                    menu = Menu()
            elif event.key == pygame.K_ESCAPE:
                running = False
        else:
            # Handle menu events
            menu.handle_event(event)
    
    # Update game state
    if game_state:
        game_state.update()
    else:
        # We're in the menu
        pass
    
    # Draw everything
    if game_state:
        game_state.draw(screen)
    else:
        menu.draw(screen)
    
    # Update display
    pygame.display.flip()
    
    # Control game speed
    clock.tick(FPS)

pygame.quit()
sys.exit()
