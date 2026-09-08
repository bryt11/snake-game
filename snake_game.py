#!/usr/bin/env python3
"""
Classic Snake Arcade Game
Built with Python 3 and Tkinter (Standard Library - Zero Dependencies).

Features:
- Smooth grid movement with input buffering (prevents self-collision on rapid turns)
- Dual controls: Arrow Keys and WASD
- Sound effects using native system audio with Mute toggle (press 'M')
- Regular food (Apples) and Golden Bonus Food with countdown timer
- Dynamic speed progression as score increases
- Persistent High Score saved to JSON
- Pause / Resume ('P' or Spacebar) and Quick Restart ('R')
- Sleek dark neon arcade aesthetics with eye animations
"""

import json
import os
import random
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import font

# --- Configuration Constants ---
GRID_WIDTH = 25
GRID_HEIGHT = 25
CELL_SIZE = 24  # pixels per cell (600x600 board)

CANVAS_WIDTH = GRID_WIDTH * CELL_SIZE
CANVAS_HEIGHT = GRID_HEIGHT * CELL_SIZE

HEADER_HEIGHT = 70
WINDOW_WIDTH = CANVAS_WIDTH
WINDOW_HEIGHT = CANVAS_HEIGHT + HEADER_HEIGHT

INITIAL_SPEED_MS = 125
MIN_SPEED_MS = 55
SPEED_INCREMENT = 2  # ms faster every food item

HIGH_SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.json")

# Color Palette
COLOR_BG_HEADER = "#161b22"
COLOR_BG_BOARD = "#0d1117"
COLOR_GRID = "#1f242c"
COLOR_SNAKE_HEAD = "#39d353"
COLOR_SNAKE_BODY_1 = "#26a641"
COLOR_SNAKE_BODY_2 = "#198835"
COLOR_SNAKE_EYE = "#ffffff"
COLOR_SNAKE_PUPIL = "#000000"
COLOR_FOOD = "#ff4d6d"
COLOR_FOOD_STEM = "#00e676"
COLOR_BONUS_FOOD = "#ffd700"
COLOR_TEXT_PRIMARY = "#f0f6fc"
COLOR_TEXT_MUTED = "#8b949e"
COLOR_ACCENT = "#58a6ff"
COLOR_OVERLAY = "#000000"


class SoundManager:
    """Handles sound effects without freezing the UI."""
    def __init__(self):
        self.enabled = True
        self.is_mac = sys.platform == "darwin"
        self.sounds = {
            "eat": "/System/Library/Sounds/Pop.aiff",
            "bonus": "/System/Library/Sounds/Hero.aiff",
            "die": "/System/Library/Sounds/Basso.aiff",
            "start": "/System/Library/Sounds/Tink.aiff"
        }

    def play(self, sound_key):
        if not self.enabled or not self.is_mac:
            return
        sound_path = self.sounds.get(sound_key)
        if sound_path and os.path.exists(sound_path):
            threading.Thread(
                target=lambda: subprocess.run(
                    ["afplay", sound_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                ),
                daemon=True
            ).start()

    def toggle_mute(self):
        self.enabled = not self.enabled
        return self.enabled


class SnakeGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Snake Arcade")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG_HEADER)

        # Center the game window on screen
        self.center_window()

        self.sound = SoundManager()
        self.high_score = self.load_high_score()

        # Custom Fonts
        self.font_title = font.Font(family="Helvetica", size=14, weight="bold")
        self.font_score = font.Font(family="Helvetica", size=12, weight="bold")
        self.font_sub = font.Font(family="Helvetica", size=10)
        self.font_banner = font.Font(family="Helvetica", size=24, weight="bold")
        self.font_banner_sub = font.Font(family="Helvetica", size=13)

        # Build UI layout
        self.create_widgets()

        # Bind User Inputs
        self.bind_events()

        # Initialize Game State
        self.reset_game(is_initial_start=True)

    def center_window(self):
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = max(0, (screen_w - WINDOW_WIDTH) // 2)
        pos_y = max(0, (screen_h - WINDOW_HEIGHT) // 2)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{pos_x}+{pos_y}")

    def load_high_score(self) -> int:
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, "r") as f:
                    data = json.load(f)
                    return int(data.get("high_score", 0))
            except Exception:
                return 0
        return 0

    def save_high_score(self):
        try:
            with open(HIGH_SCORE_FILE, "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except Exception:
            pass

    def create_widgets(self):
        # Header frame
        self.header_frame = tk.Frame(
            self.root,
            width=WINDOW_WIDTH,
            height=HEADER_HEIGHT,
            bg=COLOR_BG_HEADER,
            padx=16,
            pady=8
        )
        self.header_frame.pack(fill=tk.X)

        # Left: Score & High Score
        self.score_frame = tk.Frame(self.header_frame, bg=COLOR_BG_HEADER)
        self.score_frame.pack(side=tk.LEFT)

        self.score_label = tk.Label(
            self.score_frame,
            text="SCORE: 0",
            font=self.font_title,
            fg=COLOR_SNAKE_HEAD,
            bg=COLOR_BG_HEADER
        )
        self.score_label.pack(anchor=tk.W)

        self.high_score_label = tk.Label(
            self.score_frame,
            text=f"BEST: {self.high_score}",
            font=self.font_sub,
            fg=COLOR_BONUS_FOOD,
            bg=COLOR_BG_HEADER
        )
        self.high_score_label.pack(anchor=tk.W)

        # Center: Game Status badge
        self.status_label = tk.Label(
            self.header_frame,
            text="PRESS ANY KEY TO START",
            font=self.font_sub,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_HEADER
        )
        self.status_label.pack(side=tk.LEFT, expand=True)

        # Right: Controls info / Audio status
        self.info_frame = tk.Frame(self.header_frame, bg=COLOR_BG_HEADER)
        self.info_frame.pack(side=tk.RIGHT)

        self.sound_label = tk.Label(
            self.info_frame,
            text="SOUND: ON [M]",
            font=self.font_sub,
            fg=COLOR_ACCENT,
            bg=COLOR_BG_HEADER
        )
        self.sound_label.pack(anchor=tk.E)

        self.speed_label = tk.Label(
            self.info_frame,
            text="SPEED: 1x",
            font=self.font_sub,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_HEADER
        )
        self.speed_label.pack(anchor=tk.E)

        # Canvas for Game Board
        self.canvas = tk.Canvas(
            self.root,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=COLOR_BG_BOARD,
            highlightthickness=0
        )
        self.canvas.pack()

    def bind_events(self):
        # Key presses
        self.root.bind("<KeyPress>", self.handle_keypress)

    def reset_game(self, is_initial_start=False):
        # Snake initial positions (Head at index 0)
        mid_x = GRID_WIDTH // 2
        mid_y = GRID_HEIGHT // 2
        self.snake = [
            (mid_x, mid_y),
            (mid_x - 1, mid_y),
            (mid_x - 2, mid_y)
        ]
        self.direction = (1, 0)  # Facing right
        self.direction_queue = []  # Buffer for fast turns

        self.score = 0
        self.food_eaten_count = 0
        self.speed_ms = INITIAL_SPEED_MS

        self.bonus_food = None
        self.bonus_timer = 0  # Steps remaining for bonus food
        self.bonus_max_timer = 40

        self.game_over = False
        self.paused = False
        self.started = not is_initial_start
        self.loop_id = None

        self.spawn_food()

        self.update_header_labels()
        self.render()

        if self.started:
            self.sound.play("start")
            self.run_loop()

    def update_header_labels(self):
        self.score_label.config(text=f"SCORE: {self.score}")
        self.high_score_label.config(text=f"BEST: {self.high_score}")

        speed_factor = round(INITIAL_SPEED_MS / self.speed_ms, 1)
        self.speed_label.config(text=f"SPEED: {speed_factor}x")

        if not self.started:
            self.status_label.config(text="READY - PRESS ARROWS OR WASD", fg=COLOR_ACCENT)
        elif self.game_over:
            self.status_label.config(text="GAME OVER - PRESS [R] TO RETRY", fg=COLOR_FOOD)
        elif self.paused:
            self.status_label.config(text="PAUSED - PRESS [SPACE] TO RESUME", fg=COLOR_BONUS_FOOD)
        else:
            if self.bonus_food:
                self.status_label.config(text=f"GOLDEN APPLE ACTIVE! ({self.bonus_timer})", fg=COLOR_BONUS_FOOD)
            else:
                self.status_label.config(text="PLAYING", fg=COLOR_SNAKE_HEAD)

    def spawn_food(self):
        available_cells = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in self.snake and (x, y) != self.bonus_food
        ]
        if available_cells:
            self.food = random.choice(available_cells)
        else:
            self.food = None  # Victory / Board Full

    def spawn_bonus_food(self):
        available_cells = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in self.snake and (x, y) != self.food
        ]
        if available_cells:
            self.bonus_food = random.choice(available_cells)
            self.bonus_timer = self.bonus_max_timer

    def handle_keypress(self, event):
        key = event.keysym.lower()

        # Quit
        if key in ("escape", "q"):
            self.root.quit()
            return

        # Toggle Mute
        if key == "m":
            sound_on = self.sound.toggle_mute()
            self.sound_label.config(
                text=f"SOUND: {'ON' if sound_on else 'OFF'} [M]",
                fg=COLOR_ACCENT if sound_on else COLOR_TEXT_MUTED
            )
            return

        # Restart
        if key == "r":
            if self.loop_id:
                self.root.after_cancel(self.loop_id)
                self.loop_id = None
            self.reset_game(is_initial_start=False)
            return

        # Pause / Resume
        if key in ("space", "p"):
            if not self.started:
                self.started = True
                self.sound.play("start")
                self.run_loop()
                return
            if not self.game_over:
                self.paused = not self.paused
                self.update_header_labels()
                if not self.paused:
                    self.run_loop()
                else:
                    self.render()
            return

        # Movement keys mapping
        direction_map = {
            "up": (0, -1),
            "w": (0, -1),
            "down": (0, 1),
            "s": (0, 1),
            "left": (-1, 0),
            "a": (-1, 0),
            "right": (1, 0),
            "d": (1, 0)
        }

        if key in direction_map:
            new_dir = direction_map[key]

            # Start game if waiting
            if not self.started:
                self.started = True
                self.direction = new_dir
                self.sound.play("start")
                self.run_loop()
                return

            if self.paused or self.game_over:
                return

            # Determine the baseline direction to compare against
            reference_dir = self.direction_queue[-1] if self.direction_queue else self.direction

            # Prevent 180-degree instant reversal into own neck
            if (new_dir[0] + reference_dir[0] != 0 or new_dir[1] + reference_dir[1] != 0):
                # Queue up to 2 future turns for ultra-responsive control
                if len(self.direction_queue) < 2:
                    self.direction_queue.append(new_dir)

    def tick(self):
        if self.paused or self.game_over or not self.started:
            return

        # Process buffered input
        if self.direction_queue:
            self.direction = self.direction_queue.pop(0)

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # 1. Check Wall Collision
        if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
                new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
            self.trigger_game_over("Wall Crash!")
            return

        # 2. Check Self Collision (excluding the tail if the snake won't grow)
        will_grow = (new_head == self.food) or (new_head == self.bonus_food)
        body_to_check = self.snake if will_grow else self.snake[:-1]
        if new_head in body_to_check:
            self.trigger_game_over("Self Collision!")
            return

        # Move head forward
        self.snake.insert(0, new_head)

        # 3. Check Food Consumed
        if new_head == self.food:
            self.score += 10
            self.food_eaten_count += 1
            self.sound.play("eat")

            # Progressive speedup
            if self.speed_ms > MIN_SPEED_MS:
                self.speed_ms = max(MIN_SPEED_MS, self.speed_ms - SPEED_INCREMENT)

            # High Score check
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()

            self.spawn_food()

            # Spawn bonus food every 5 food items if not already active
            if self.food_eaten_count % 5 == 0 and not self.bonus_food:
                self.spawn_bonus_food()

        elif self.bonus_food and new_head == self.bonus_food:
            # Bonus score proportional to remaining timer
            bonus_points = 30 + (self.bonus_timer * 2)
            self.score += bonus_points
            self.sound.play("bonus")

            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()

            self.bonus_food = None
            self.bonus_timer = 0

        else:
            # Normal move: remove tail
            self.snake.pop()

        # Tick bonus timer
        if self.bonus_food:
            self.bonus_timer -= 1
            if self.bonus_timer <= 0:
                self.bonus_food = None

        self.update_header_labels()
        self.render()

    def run_loop(self):
        self.tick()
        if not self.game_over and not self.paused and self.started:
            self.loop_id = self.root.after(self.speed_ms, self.run_loop)

    def trigger_game_over(self, reason):
        self.game_over = True
        self.sound.play("die")
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
        self.update_header_labels()
        self.render()

    # --- Rendering Methods ---
    def render(self):
        self.canvas.delete("all")
        self.draw_grid()

        if self.bonus_food:
            self.draw_bonus_food()

        if self.food:
            self.draw_food()

        self.draw_snake()

        # Render overlays
        if not self.started:
            self.draw_start_overlay()
        elif self.paused:
            self.draw_pause_overlay()
        elif self.game_over:
            self.draw_game_over_overlay()

    def draw_grid(self):
        # Draw clean grid lines
        for x in range(0, CANVAS_WIDTH, CELL_SIZE):
            self.canvas.create_line(x, 0, x, CANVAS_HEIGHT, fill=COLOR_GRID, width=1)
        for y in range(0, CANVAS_HEIGHT, CELL_SIZE):
            self.canvas.create_line(0, y, CANVAS_WIDTH, y, fill=COLOR_GRID, width=1)

    def draw_food(self):
        gx, gy = self.food
        px = gx * CELL_SIZE
        py = gy * CELL_SIZE
        padding = 3

        # Apple body (vibrant circle)
        self.canvas.create_oval(
            px + padding, py + padding + 1,
            px + CELL_SIZE - padding, py + CELL_SIZE - padding + 1,
            fill=COLOR_FOOD,
            outline="#ff758f",
            width=1
        )
        # Small highlight reflection
        self.canvas.create_oval(
            px + padding + 3, py + padding + 3,
            px + padding + 7, py + padding + 7,
            fill="#ffffff",
            outline=""
        )
        # Little green leaf stem
        self.canvas.create_line(
            px + CELL_SIZE // 2, py + padding + 2,
            px + CELL_SIZE // 2 + 3, py + 1,
            fill=COLOR_FOOD_STEM,
            width=2
        )

    def draw_bonus_food(self):
        gx, gy = self.bonus_food
        px = gx * CELL_SIZE
        py = gy * CELL_SIZE

        # Outer glowing ring based on timer ratio
        timer_ratio = self.bonus_timer / self.bonus_max_timer
        pad = 2

        self.canvas.create_oval(
            px + pad, py + pad,
            px + CELL_SIZE - pad, py + CELL_SIZE - pad,
            fill=COLOR_BONUS_FOOD,
            outline="#fff275",
            width=2
        )

        # Star / Diamond inside
        mid_x = px + CELL_SIZE // 2
        mid_y = py + CELL_SIZE // 2
        r = 5
        self.canvas.create_polygon(
            mid_x, mid_y - r,
            mid_x + r, mid_y,
            mid_x, mid_y + r,
            mid_x - r, mid_y,
            fill="#ffffff",
            outline=""
        )

        # Mini timer bar beneath bonus food
        bar_w = (CELL_SIZE - 4) * timer_ratio
        self.canvas.create_line(
            px + 2, py + CELL_SIZE - 2,
            px + 2 + bar_w, py + CELL_SIZE - 2,
            fill=COLOR_BONUS_FOOD,
            width=2
        )

    def draw_snake(self):
        # Draw body segments first (tail to neck)
        for i in range(len(self.snake) - 1, 0, -1):
            gx, gy = self.snake[i]
            px = gx * CELL_SIZE
            py = gy * CELL_SIZE
            color = COLOR_SNAKE_BODY_1 if (i % 2 == 0) else COLOR_SNAKE_BODY_2

            pad = 2
            self.canvas.create_rectangle(
                px + pad, py + pad,
                px + CELL_SIZE - pad, py + CELL_SIZE - pad,
                fill=color,
                outline="",
                width=0
            )

        # Draw Head with rounded appearance
        hx, hy = self.snake[0]
        px = hx * CELL_SIZE
        py = hy * CELL_SIZE
        pad = 1

        self.canvas.create_rectangle(
            px + pad, py + pad,
            px + CELL_SIZE - pad, py + CELL_SIZE - pad,
            fill=COLOR_SNAKE_HEAD,
            outline="",
            width=0
        )

        # Eyes facing the direction of movement
        dx, dy = self.direction
        eye_radius = 2.5
        pupil_radius = 1.2

        if dx == 1:  # Facing Right
            e1 = (px + CELL_SIZE - 6, py + 6)
            e2 = (px + CELL_SIZE - 6, py + CELL_SIZE - 6)
            pupil_offset = (1, 0)
        elif dx == -1:  # Facing Left
            e1 = (px + 6, py + 6)
            e2 = (px + 6, py + CELL_SIZE - 6)
            pupil_offset = (-1, 0)
        elif dy == -1:  # Facing Up
            e1 = (px + 6, py + 6)
            e2 = (px + CELL_SIZE - 6, py + 6)
            pupil_offset = (0, -1)
        else:  # Facing Down
            e1 = (px + 6, py + CELL_SIZE - 6)
            e2 = (px + CELL_SIZE - 6, py + CELL_SIZE - 6)
            pupil_offset = (0, 1)

        for ex, ey in (e1, e2):
            self.canvas.create_oval(
                ex - eye_radius, ey - eye_radius,
                ex + eye_radius, ey + eye_radius,
                fill=COLOR_SNAKE_EYE, outline=""
            )
            self.canvas.create_oval(
                ex - pupil_radius + pupil_offset[0],
                ey - pupil_radius + pupil_offset[1],
                ex + pupil_radius + pupil_offset[0],
                ey + pupil_radius + pupil_offset[1],
                fill=COLOR_SNAKE_PUPIL, outline=""
            )

    def draw_start_overlay(self):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2

        # Dimmed backdrop card
        card_w, card_h = 420, 260
        self.canvas.create_rectangle(
            cx - card_w // 2, cy - card_h // 2,
            cx + card_w // 2, cy + card_h // 2,
            fill="#161b22",
            outline=COLOR_SNAKE_HEAD,
            width=2
        )

        self.canvas.create_text(
            cx, cy - 80,
            text="🐍 SNAKE ARCADE",
            font=self.font_banner,
            fill=COLOR_SNAKE_HEAD
        )

        instructions = [
            "Use ARROW KEYS or WASD to navigate",
            "Collect Apples [🍎] for +10 points",
            "Catch Golden Stars [⭐] for bonus points!",
            "Press [P] or [SPACE] to pause",
            "Press [M] to toggle sound effects"
        ]

        start_y = cy - 35
        for i, text in enumerate(instructions):
            self.canvas.create_text(
                cx, start_y + (i * 22),
                text=text,
                font=self.font_sub,
                fill=COLOR_TEXT_PRIMARY
            )

        self.canvas.create_text(
            cx, cy + 95,
            text="▶ Press ANY ARROW KEY or WASD to Play",
            font=self.font_score,
            fill=COLOR_BONUS_FOOD
        )

    def draw_pause_overlay(self):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2

        card_w, card_h = 320, 140
        self.canvas.create_rectangle(
            cx - card_w // 2, cy - card_h // 2,
            cx + card_w // 2, cy + card_h // 2,
            fill="#161b22",
            outline=COLOR_BONUS_FOOD,
            width=2
        )

        self.canvas.create_text(
            cx, cy - 25,
            text="GAME PAUSED",
            font=self.font_banner,
            fill=COLOR_BONUS_FOOD
        )
        self.canvas.create_text(
            cx, cy + 25,
            text="Press [SPACE] or [P] to Resume",
            font=self.font_banner_sub,
            fill=COLOR_TEXT_PRIMARY
        )

    def draw_game_over_overlay(self):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2

        card_w, card_h = 360, 220
        self.canvas.create_rectangle(
            cx - card_w // 2, cy - card_h // 2,
            cx + card_w // 2, cy + card_h // 2,
            fill="#161b22",
            outline=COLOR_FOOD,
            width=2
        )

        self.canvas.create_text(
            cx, cy - 65,
            text="GAME OVER",
            font=self.font_banner,
            fill=COLOR_FOOD
        )

        self.canvas.create_text(
            cx, cy - 20,
            text=f"Final Score: {self.score}",
            font=self.font_score,
            fill=COLOR_TEXT_PRIMARY
        )

        is_new_high = (self.score >= self.high_score and self.score > 0)
        best_msg = "⭐ NEW HIGH SCORE! ⭐" if is_new_high else f"High Score: {self.high_score}"
        self.canvas.create_text(
            cx, cy + 10,
            text=best_msg,
            font=self.font_sub,
            fill=COLOR_BONUS_FOOD if is_new_high else COLOR_TEXT_MUTED
        )

        self.canvas.create_text(
            cx, cy + 60,
            text="Press [R] to Play Again",
            font=self.font_score,
            fill=COLOR_SNAKE_HEAD
        )


def main():
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
