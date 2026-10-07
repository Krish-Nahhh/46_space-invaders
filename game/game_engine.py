import os
import random
import pygame
from .player import Player
from .enemy import EnemyGrid
from .bullet import Bullet

# Game Engine

WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (220, 60, 60)
YELLOW = (240, 200, 40)

# fire_chance = chance PER FRAME that ONE enemy in the grid fires (at 60 FPS)
DIFFICULTIES = {
    "Easy":   {"enemy_speed": 1.0, "fire_chance": 0.01},
    "Medium": {"enemy_speed": 1.5, "fire_chance": 0.02},
    "Hard":   {"enemy_speed": 2.5, "fire_chance": 0.04},
}

SOUND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sounds")


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 60)

        self.shoot_sound = self._load_sound("shoot.wav")
        self.explosion_sound = self._load_sound("explosion.wav")
        self.game_over_sound = self._load_sound("game_over.wav")

        self.reset("Medium")

    # ---------- setup / helpers ----------
    def reset(self, difficulty):
        settings = DIFFICULTIES[difficulty]
        self.player = Player(self.width // 2 - 20, self.height - 50, 40, 20)
        self.enemy_grid = EnemyGrid(self.width, speed=settings["enemy_speed"])
        self.player_bullets = []
        self.enemy_bullets = []
        self._shoot_cooldown = 0
        self.enemy_fire_chance = settings["fire_chance"]
        self.score = 0
        self.game_over = False

    def _load_sound(self, name):
        try:
            return pygame.mixer.Sound(os.path.join(SOUND_DIR, name))
        except (pygame.error, FileNotFoundError):
            return None

    def _play(self, sound):
        if sound:
            sound.play()

    def _end_game(self):
        if self.game_over:
            return  # already over, don't replay the sound
        self.game_over = True
        self._play(self.game_over_sound)

    def _draw_centered(self, screen, text, font, color, y):
        surf = font.render(text, True, color)
        screen.blit(surf, (self.width // 2 - surf.get_width() // 2, y))

    # ---------- input ----------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.game_over:
            choices = {pygame.K_1: "Easy", pygame.K_2: "Medium", pygame.K_3: "Hard"}
            if event.key in choices:
                self.reset(choices[event.key])
            elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if event.key == pygame.K_SPACE and self._shoot_cooldown <= 0:
            bullet_x = self.player.center_x() - 2
            self.player_bullets.append(Bullet(bullet_x, self.player.y, direction=-1))
            self._shoot_cooldown = 15
            self._play(self.shoot_sound)

    def handle_input(self):
        if self.game_over:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move(-self.player.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move(self.player.speed, self.width)

    # ---------- update ----------
    def update(self):
        if self.game_over:
            return

        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= 1

        self.enemy_grid.move()

        # One roll per frame; a random living enemy fires
        alive = self.enemy_grid.alive_enemies()
        if alive and random.random() < self.enemy_fire_chance:
            shooter = random.choice(alive)
            bullet_x = shooter.x + shooter.width // 2
            self.enemy_bullets.append(Bullet(bullet_x, shooter.y + shooter.height, direction=1))

        for bullet in self.player_bullets:
            bullet.move()
        for bullet in self.enemy_bullets:
            bullet.move()

        self.player_bullets = [b for b in self.player_bullets if not b.off_screen(self.height)]
        self.enemy_bullets = [b for b in self.enemy_bullets if not b.off_screen(self.height)]

        # Task 1 fix: collect hits, remove after the loop
        bullets_to_remove = []
        for bullet in self.player_bullets:
            bullet_rect = bullet.rect()
            for enemy in self.enemy_grid.alive_enemies():
                if bullet_rect.colliderect(enemy.rect()):
                    enemy.alive = False
                    bullets_to_remove.append(bullet)
                    self.score += 1
                    self._play(self.explosion_sound)
                    break  # one bullet kills at most one enemy
        self.player_bullets = [b for b in self.player_bullets if b not in bullets_to_remove]

        for bullet in self.enemy_bullets:
            if bullet.rect().colliderect(self.player.rect()):
                self._end_game()
                break

        if self.enemy_grid.reached_bottom(self.player.y):
            self._end_game()

    # ---------- render ----------
    def render(self, screen):
        pygame.draw.rect(screen, GREEN, self.player.rect())

        for enemy in self.enemy_grid.alive_enemies():
            pygame.draw.rect(screen, WHITE, enemy.rect())

        for bullet in self.player_bullets:
            pygame.draw.rect(screen, WHITE, bullet.rect())
        for bullet in self.enemy_bullets:
            pygame.draw.rect(screen, RED, bullet.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            mid = self.height // 2
            self._draw_centered(screen, "GAME OVER", self.big_font, RED, mid - 120)
            self._draw_centered(screen, f"Final Score: {self.score}", self.font, WHITE, mid - 40)
            self._draw_centered(screen, "Play again:  1 = Easy   2 = Medium   3 = Hard", self.font, YELLOW, mid + 20)
            self._draw_centered(screen, "Q / Esc = Quit", self.font, WHITE, mid + 70)
            