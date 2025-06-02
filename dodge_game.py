import tkinter as tk
from tkinter import simpledialog, messagebox
import random
import os
import pygame

# Game constants
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 600
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 20
BLOCK_WIDTH = 40
BLOCK_HEIGHT = 20
BLOCK_SPEED = 5
UPDATE_DELAY = 50
LEADERBOARD_FILE = "leaderboard.txt"

# Initialize pygame mixer
pygame.mixer.init()

# Load sounds
try:
    SND_BLOCK_SPAWN = pygame.mixer.Sound("block_spawn.wav")
    SND_GAME_OVER = pygame.mixer.Sound("game_over.wav")
    SND_SCORE_TICK = pygame.mixer.Sound("score_tick.wav")
except Exception as e:
    SND_BLOCK_SPAWN = SND_GAME_OVER = SND_SCORE_TICK = None
    print("Warning: Could not load sound files:", e)

class DodgeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Dodge the Falling Blocks")
        self.main_menu()

    def main_menu(self):
        self.clear_widgets()

        self.menu_frame = tk.Frame(self.root, bg="black")
        self.menu_frame.pack(fill="both", expand=True)

        title = tk.Label(self.menu_frame, text="Dodge the Falling Blocks", font=("Arial", 24), fg="white", bg="black")
        title.pack(pady=40)

        start_button = tk.Button(self.menu_frame, text="Play Manually", font=("Arial", 16), command=self.start_game)
        start_button.pack(pady=10)

        ai_button = tk.Button(self.menu_frame, text="Watch AI Play", font=("Arial", 16), command=lambda: self.start_game(ai=True))
        ai_button.pack(pady=10)

        leaderboard_button = tk.Button(self.menu_frame, text="Leaderboard", font=("Arial", 16), command=self.show_leaderboard)
        leaderboard_button.pack(pady=10)

    def start_game(self, ai=False):
        self.use_ai = ai
        self.menu_frame.destroy()
        self.setup_game()

    def setup_game(self):
        self.score = 0
        self.running = True
        self.blocks = []

        self.canvas = tk.Canvas(self.root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg='black')
        self.canvas.pack()

        self.player = self.canvas.create_rectangle(
            WINDOW_WIDTH // 2 - PLAYER_WIDTH // 2,
            WINDOW_HEIGHT - PLAYER_HEIGHT - 10,
            WINDOW_WIDTH // 2 + PLAYER_WIDTH // 2,
            WINDOW_HEIGHT - 10,
            fill='blue'
        )

        self.score_text = self.canvas.create_text(10, 10, anchor='nw', fill='white', font=('Arial', 14), text='Score: 0')

        self.root.bind('<Left>', self.move_left)
        self.root.bind('<Right>', self.move_right)
        self.root.bind('<Escape>', lambda e: self.quit_game())

        self.update_game()

    def move_left(self, event):
        if self.running:
            x1, _, x2, _ = self.canvas.coords(self.player)
            if x1 <= 0:
                self.canvas.move(self.player, WINDOW_WIDTH, 0)
            else:
                self.canvas.move(self.player, -20, 0)

    def move_right(self, event):
        if self.running:
            x1, _, x2, _ = self.canvas.coords(self.player)
            if x2 >= WINDOW_WIDTH:
                self.canvas.move(self.player, -WINDOW_WIDTH, 0)
            else:
                self.canvas.move(self.player, 20, 0)

    def spawn_block(self):
        x = random.randint(0, WINDOW_WIDTH - BLOCK_WIDTH)
        block = self.canvas.create_rectangle(x, 0, x + BLOCK_WIDTH, BLOCK_HEIGHT, fill='red')
        self.blocks.append(block)
        if SND_BLOCK_SPAWN:
            SND_BLOCK_SPAWN.play()

    def update_blocks(self):
        for block in self.blocks:
            self.canvas.move(block, 0, BLOCK_SPEED)
        self.blocks = [b for b in self.blocks if self.canvas.coords(b)[1] < WINDOW_HEIGHT]

    def check_collision(self):
        player_coords = self.canvas.coords(self.player)
        for block in self.blocks:
            block_coords = self.canvas.coords(block)
            if self.overlaps(player_coords, block_coords):
                return True
        return False

    def overlaps(self, a, b):
        return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])

    def update_game(self):
        if not self.running:
            return

        if random.randint(1, 10) == 1:
            self.spawn_block()

        self.update_blocks()

        if self.check_collision():
            self.running = False
            if SND_GAME_OVER:
                SND_GAME_OVER.play()
            self.canvas.create_text(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, fill='white', font=('Arial', 24), text='GAME OVER')
            self.root.after(1000, self.prompt_name)
            return

        self.score += 1
        self.canvas.itemconfig(self.score_text, text=f'Score: {self.score}')
        if self.score % 10 == 0 and SND_SCORE_TICK:
            SND_SCORE_TICK.play()

        if self.use_ai:
            self.run_ai()

        self.root.after(UPDATE_DELAY, self.update_game)

    def run_ai(self):
        player_x1, _, player_x2, _ = self.canvas.coords(self.player)
        player_center = (player_x1 + player_x2) / 2

        future_threats = [0] * WINDOW_WIDTH

        for block in self.blocks:
            x1, y1, x2, y2 = self.canvas.coords(block)
            steps_to_player = (WINDOW_HEIGHT - y2) / BLOCK_SPEED
            if 0 <= steps_to_player <= 30:  # look ahead ~30 frames
                threat_pos = int((x1 + x2) / 2)
                for dx in range(-PLAYER_WIDTH//2, PLAYER_WIDTH//2):
                    pos = threat_pos + dx
                    if 0 <= pos < WINDOW_WIDTH:
                        future_threats[pos] += 1

        safe_zones = [(i, val) for i, val in enumerate(future_threats) if val == 0]
        if not safe_zones:
            return  # nowhere to go, stay still

        # Pick safe zone closest to center
        best = min(safe_zones, key=lambda x: abs(x[0] - player_center))

        if player_center < best[0]:
            self.move_right(None)
        elif player_center > best[0]:
            self.move_left(None)

    def prompt_name(self):
        name = simpledialog.askstring("Save Score", "Enter your 4-letter name:", parent=self.root)
        if name:
            name = name.strip().upper()[:4]
            if len(name) < 1:
                name = "ANON"
            self.save_score(name, self.score)
        self.back_to_menu()

    def save_score(self, name, score):
        try:
            with open(LEADERBOARD_FILE, "a") as f:
                f.write(f"{name} {score}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save score: {e}")

    def show_leaderboard(self):
        self.clear_widgets()

        frame = tk.Frame(self.root, bg="black")
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text="Leaderboard", font=("Arial", 24), fg="white", bg="black")
        title.pack(pady=20)

        scores = self.load_leaderboard()
        for entry in scores:
            label = tk.Label(frame, text=f"{entry[0]} - {entry[1]}", font=("Arial", 16), fg="white", bg="black")
            label.pack()

        back_btn = tk.Button(frame, text="Back to Menu", font=("Arial", 14), command=self.main_menu)
        back_btn.pack(pady=20)

    def load_leaderboard(self):
        scores = []
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 2 and parts[1].isdigit():
                        scores.append((parts[0], int(parts[1])))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:10]

    def back_to_menu(self):
        self.canvas.destroy()
        self.main_menu()

    def quit_game(self):
        self.running = False
        self.root.destroy()

    def clear_widgets(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    game = DodgeGame(root)
    root.mainloop()