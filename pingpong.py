"""
BCI-Controlled Pong Game
========================
A Pong game designed for Brain-Computer Interface control using motor imagery.
Features customizable difficulty, score tracking, and JSON export.

Controls:
- Keyboard: LEFT/RIGHT arrow keys (for testing)
- BCI: Will be integrated via simulate_bci_input() function

Author: BCI Research Project
Date: November 2025
"""

import pygame
import json
import time
from datetime import datetime
import sys

# =============================================================================
# GAME CONFIGURATION (Easy to customize!)
# =============================================================================

class GameConfig:
    """Centralized configuration for easy customization"""
    
    # Window settings
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    FPS = 60
    
    # Ball settings
    BALL_SPEED_X = 5  # ← CUSTOMIZE: Ball horizontal speed (1-10)
    BALL_SPEED_Y = 5  # ← CUSTOMIZE: Ball vertical speed (1-10)
    BALL_SIZE = 15
    BALL_SPEED_INCREASE = 1.05  # Speed multiplier per paddle hit
    
    # Paddle settings
    PADDLE_WIDTH = 100
    PADDLE_HEIGHT = 15
    PADDLE_SPEED = 8  # ← CUSTOMIZE: Paddle movement speed (5-15)
    PADDLE_Y_POSITION = 550  # Distance from top
    
    # Colors (RGB)
    COLOR_BACKGROUND = (20, 20, 40)
    COLOR_PADDLE = (100, 200, 255)
    COLOR_BALL = (255, 100, 100)
    COLOR_TEXT = (255, 255, 255)
    COLOR_BRICKS = (255, 215, 0)
    
    # Bricks (optional - set to 0 for pure Pong)
    BRICKS_ENABLED = True  # ← CUSTOMIZE: True for brick breaker, False for pure pong
    BRICK_ROWS = 5  # ← CUSTOMIZE: Number of brick rows (0-10)
    BRICK_COLS = 10  # ← CUSTOMIZE: Number of brick columns
    BRICK_WIDTH = 70
    BRICK_HEIGHT = 20
    BRICK_PADDING = 5
    
    # Game mechanics
    LIVES = 3  # ← CUSTOMIZE: Number of lives (1-10)
    
    # File settings
    SCORE_FILE = "pong_scores.json"  # ← CUSTOMIZE: Output filename


# =============================================================================
# GAME CLASSES
# =============================================================================

class Ball:
    """Ball object with physics"""
    
    def __init__(self, x, y, config):
        self.x = x
        self.y = y
        self.size = config.BALL_SIZE
        self.speed_x = config.BALL_SPEED_X
        self.speed_y = -config.BALL_SPEED_Y  # Start moving upward
        self.config = config
    
    def move(self):
        """Update ball position"""
        self.x += self.speed_x
        self.y += self.speed_y
    
    def bounce_x(self):
        """Reverse horizontal direction"""
        self.speed_x *= -1
    
    def bounce_y(self):
        """Reverse vertical direction"""
        self.speed_y *= -1
    
    def check_wall_collision(self, window_width, window_height):
        """Check and handle wall collisions"""
        # Left/right walls
        if self.x - self.size <= 0 or self.x + self.size >= window_width:
            self.bounce_x()
        
        # Top wall
        if self.y - self.size <= 0:
            self.bounce_y()
        
        # Bottom (ball lost)
        if self.y - self.size > window_height:
            return True  # Ball lost
        
        return False
    
    def increase_speed(self):
        """Increase ball speed after paddle hit"""
        self.speed_x *= self.config.BALL_SPEED_INCREASE
        self.speed_y *= self.config.BALL_SPEED_INCREASE
    
    def draw(self, screen):
        """Draw ball on screen"""
        pygame.draw.circle(screen, self.config.COLOR_BALL, 
                          (int(self.x), int(self.y)), self.size)


class Paddle:
    """Player-controlled paddle"""
    
    def __init__(self, x, y, config):
        self.x = x
        self.y = y
        self.width = config.PADDLE_WIDTH
        self.height = config.PADDLE_HEIGHT
        self.speed = config.PADDLE_SPEED
        self.config = config
    
    def move_left(self, window_width):
        """Move paddle left"""
        self.x -= self.speed
        if self.x < 0:
            self.x = 0
    
    def move_right(self, window_width):
        """Move paddle right"""
        self.x += self.speed
        if self.x + self.width > window_width:
            self.x = window_width - self.width
    
    def check_ball_collision(self, ball):
        """Check if ball hits paddle"""
        if (ball.y + ball.size >= self.y and 
            ball.y - ball.size <= self.y + self.height and
            ball.x >= self.x and 
            ball.x <= self.x + self.width):
            return True
        return False
    
    def draw(self, screen):
        """Draw paddle on screen"""
        pygame.draw.rect(screen, self.config.COLOR_PADDLE, 
                        (self.x, self.y, self.width, self.height))


class Brick:
    """Brick object for brick breaker mode"""
    
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.destroyed = False
    
    def check_collision(self, ball):
        """Check if ball hits brick"""
        if self.destroyed:
            return False
        
        if (ball.x + ball.size >= self.x and 
            ball.x - ball.size <= self.x + self.width and
            ball.y + ball.size >= self.y and 
            ball.y - ball.size <= self.y + self.height):
            self.destroyed = True
            return True
        return False
    
    def draw(self, screen):
        """Draw brick on screen"""
        if not self.destroyed:
            pygame.draw.rect(screen, self.color, 
                           (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, (0, 0, 0), 
                           (self.x, self.y, self.width, self.height), 2)


# =============================================================================
# SCORE TRACKING
# =============================================================================

class ScoreTracker:
    """Track and save game statistics"""
    
    def __init__(self, config):
        self.config = config
        self.session_start = datetime.now()
        self.reset()
    
    def reset(self):
        """Reset score for new game"""
        self.paddle_hits = 0
        self.brick_hits = 0
        self.walls_hit = 0
        self.lives_lost = 0
        self.max_rally = 0
        self.current_rally = 0
        self.game_duration = 0
    
    def record_paddle_hit(self):
        """Record paddle hit"""
        self.paddle_hits += 1
        self.current_rally += 1
        if self.current_rally > self.max_rally:
            self.max_rally = self.current_rally

    def record_brick_hit(self):
        """Record brick destroyed"""
        self.brick_hits += 1
    
    def record_wall_hit(self):
        """Record wall bounce"""
        self.walls_hit += 1
    
    def record_life_lost(self):
        """Record life lost"""
        self.lives_lost += 1
        self.current_rally = 0
    
    def calculate_score(self):
        """Calculate total score"""
        score = (
            self.paddle_hits * 10 +      # 10 points per paddle hit
            self.brick_hits * 50 +        # 50 points per brick
            self.max_rally * 20           # 20 points per max rally
        )
        return score
    
    def save_to_json(self):
        """Save game statistics to JSON file"""
        self.game_duration = (datetime.now() - self.session_start).total_seconds()
        
        data = {
            "session_timestamp": self.session_start.strftime("%Y-%m-%d %H:%M:%S"),
            "game_duration_seconds": round(self.game_duration, 2),
            "statistics": {
                "paddle_hits": self.paddle_hits,
                "brick_hits": self.brick_hits,
                "walls_hit": self.walls_hit,
                "lives_lost": self.lives_lost,
                "max_rally": self.max_rally,
                "total_score": self.calculate_score()
            },
            "game_settings": {
                "ball_speed": self.config.BALL_SPEED_X,
                "paddle_speed": self.config.PADDLE_SPEED,
                "bricks_enabled": self.config.BRICKS_ENABLED,
                "lives": self.config.LIVES
            }
        }
        
        # Append to existing file or create new
        try:
            with open(self.config.SCORE_FILE, 'r') as f:
                all_scores = json.load(f)
        except FileNotFoundError:
            all_scores = []
        
        all_scores.append(data)
        
        with open(self.config.SCORE_FILE, 'w') as f:
            json.dump(all_scores, f, indent=4)
        
        print(f"\n✅ Scores saved to {self.config.SCORE_FILE}")
        print(f"   Total Score: {self.calculate_score()}")
        print(f"   Paddle Hits: {self.paddle_hits}")
        print(f"   Brick Hits: {self.brick_hits}")
        print(f"   Max Rally: {self.max_rally}")


# =============================================================================
# MAIN GAME CLASS
# =============================================================================

class PongGame:
    """Main game controller"""
    
    def __init__(self, config):
        pygame.init()
        self.config = config
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        pygame.display.set_caption("BCI Pong - Motor Imagery Controlled")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        self.score_tracker = ScoreTracker(config)
        self.reset_game()
    
    def reset_game(self):
        """Reset game state"""
        # Create ball
        self.ball = Ball(
            self.config.WINDOW_WIDTH // 2,
            self.config.WINDOW_HEIGHT // 2,
            self.config
        )
        
        # Create paddle
        self.paddle = Paddle(
            self.config.WINDOW_WIDTH // 2 - self.config.PADDLE_WIDTH // 2,
            self.config.PADDLE_Y_POSITION,
            self.config
        )
        
        # Create bricks
        self.bricks = []
        if self.config.BRICKS_ENABLED:
            self.create_bricks()
        
        self.lives = self.config.LIVES
        self.game_over = False
        self.won = False
    
    def create_bricks(self):
        """Create brick layout"""
        colors = [
            (255, 0, 0),    # Red
            (255, 127, 0),  # Orange
            (255, 255, 0),  # Yellow
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
        ]
        
        start_y = 50
        for row in range(self.config.BRICK_ROWS):
            for col in range(self.config.BRICK_COLS):
                x = col * (self.config.BRICK_WIDTH + self.config.BRICK_PADDING) + 35
                y = row * (self.config.BRICK_HEIGHT + self.config.BRICK_PADDING) + start_y
                color = colors[row % len(colors)]
                self.bricks.append(Brick(x, y, self.config.BRICK_WIDTH, 
                                        self.config.BRICK_HEIGHT, color))
    
    def simulate_bci_input(self):
        """
        PLACEHOLDER for BCI integration
        
        Replace this function with actual BCI predictions!
        Currently uses keyboard for testing.
        
        Returns:
            'left', 'right', or 'idle'
        """
        keys = pygame.key.get_pressed()
        # print(keys)
        
        if keys[pygame.K_LEFT]:
            return 'left'
        elif keys[pygame.K_RIGHT]:
            return 'right'
        else:
            return 'idle'
        
        # TODO: Replace with:
        # prediction, confidence = bci_model.predict(eeg_window)
        # if confidence > 0.75:
        #     return 'left' if prediction == 0 else 'right'
        # else:
        #     return 'idle'
    
    def handle_input(self):
        """Handle paddle control"""
        bci_command = self.simulate_bci_input()
        
        if bci_command == 'left':
            self.paddle.move_left(self.config.WINDOW_WIDTH)
        elif bci_command == 'right':
            self.paddle.move_right(self.config.WINDOW_WIDTH)
        # 'idle' = do nothing
    
    def update(self):
        """Update game state"""
        if self.game_over:
            return
        
        # Move ball
        self.ball.move()
        
        # Check wall collisions
        ball_lost = self.ball.check_wall_collision(
            self.config.WINDOW_WIDTH, 
            self.config.WINDOW_HEIGHT
        )
        
        if ball_lost:
            self.lives -= 1
            self.score_tracker.record_life_lost()
            
            if self.lives <= 0:
                self.game_over = True
            else:
                # Reset ball position
                self.ball.x = self.config.WINDOW_WIDTH // 2
                self.ball.y = self.config.WINDOW_HEIGHT // 2
                self.ball.speed_y = -abs(self.ball.speed_y)
        
        # Check paddle collision
        if self.paddle.check_ball_collision(self.ball):
            self.ball.bounce_y()
            self.ball.increase_speed()
            self.score_tracker.record_paddle_hit()
        
        # Check brick collisions
        all_bricks_destroyed = True
        for brick in self.bricks:
            if not brick.destroyed:
                all_bricks_destroyed = False
                if brick.check_collision(self.ball):
                    self.ball.bounce_y()
                    self.score_tracker.record_brick_hit()
        
        # Check win condition
        if self.config.BRICKS_ENABLED and all_bricks_destroyed:
            self.game_over = True
            self.won = True
    
    def draw(self):
        """Draw everything"""
        self.screen.fill(self.config.COLOR_BACKGROUND)
        
        # Draw bricks
        for brick in self.bricks:
            brick.draw(self.screen)
        
        # Draw paddle and ball
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        
        # Draw HUD
        score_text = self.font.render(
            f"Score: {self.score_tracker.calculate_score()}", 
            True, self.config.COLOR_TEXT
        )
        lives_text = self.font.render(
            f"Lives: {self.lives}", 
            True, self.config.COLOR_TEXT
        )
        hits_text = self.font.render(
            f"Paddle Hits: {self.score_tracker.paddle_hits}", 
            True, self.config.COLOR_TEXT
        )
        
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (self.config.WINDOW_WIDTH - 150, 10))
        self.screen.blit(hits_text, (10, self.config.WINDOW_HEIGHT - 40))
        
        # Draw game over screen
        if self.game_over:
            overlay = pygame.Surface((self.config.WINDOW_WIDTH, self.config.WINDOW_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            if self.won:
                end_text = self.font.render("YOU WON!", True, (0, 255, 0))
            else:
                end_text = self.font.render("GAME OVER", True, (255, 0, 0))
            
            final_score = self.font.render(
                f"Final Score: {self.score_tracker.calculate_score()}", 
                True, self.config.COLOR_TEXT
            )
            restart_text = self.font.render(
                "Press R to Restart or Q to Quit", 
                True, self.config.COLOR_TEXT
            )
            
            self.screen.blit(end_text, 
                           (self.config.WINDOW_WIDTH // 2 - end_text.get_width() // 2, 200))
            self.screen.blit(final_score, 
                           (self.config.WINDOW_WIDTH // 2 - final_score.get_width() // 2, 270))
            self.screen.blit(restart_text, 
                           (self.config.WINDOW_WIDTH // 2 - restart_text.get_width() // 2, 350))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        running = True
        
        print("\n" + "="*60)
        print("BCI PONG GAME STARTED")
        print("="*60)
        print("Controls:")
        print("  LEFT Arrow  = Move paddle left (simulates left fist MI)")
        print("  RIGHT Arrow = Move paddle right (simulates right fist MI)")
        print("  Q           = Quit game")
        print("="*60 + "\n")
        
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    
                    if self.game_over:
                        if event.key == pygame.K_r:
                            self.reset_game()
                            self.score_tracker.reset()
                            self.score_tracker.session_start = datetime.now()
            
            # Game logic
            self.handle_input()
            self.update()
            self.draw()
            
            self.clock.tick(self.config.FPS)
        
        # Save scores before quitting
        self.score_tracker.save_to_json()
        pygame.quit()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧠 BCI PONG GAME - Motor Imagery Controlled")
    print("="*60)
    print("\nInitializing game...")
    
    # Create configuration
    config = GameConfig()
    
    # Print configuration
    print(f"\n📊 Game Settings:")
    print(f"   Ball Speed: {config.BALL_SPEED_X}")
    print(f"   Paddle Speed: {config.PADDLE_SPEED}")
    print(f"   Lives: {config.LIVES}")
    print(f"   Bricks Enabled: {config.BRICKS_ENABLED}")
    print(f"   Score File: {config.SCORE_FILE}")
    
    # Run game
    game = PongGame(config)
    game.run()
    
    print("\n✅ Game closed. Thank you for playing!")
