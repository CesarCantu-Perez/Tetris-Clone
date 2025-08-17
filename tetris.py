#!/usr/bin/env python3
"""
Tetris in Python (Pygame)
Controls:
  Left/Right: Move
  Down: Soft drop
  Up / X: Rotate clockwise
  Z: Rotate counter-clockwise
  Space: Hard drop
  C / Shift: Hold piece (once per drop)
  P: Pause
  R: Restart
  Q / Esc: Quit

Run:
  pip install pygame
  python tetris.py
"""

import sys
import os
import math
import random
import pygame
from pygame.locals import *

# ------------ Config ------------ #
GRID_W, GRID_H = 10, 20
BLOCK = 30  # pixel size of a cell
BORDER = 4
SIDE_PANEL = 220
TOP_MARGIN = 40
WIDTH = GRID_W * BLOCK + SIDE_PANEL + BORDER * 3
HEIGHT = GRID_H * BLOCK + TOP_MARGIN + BORDER * 2
FPS = 60

# Colors
BG = (18, 18, 24)
GRID_BG = (30, 30, 38)
GRID_LINE = (45, 45, 55)
TEXT = (230, 230, 240)
GHOST = (160, 160, 170)

# Piece colors (approx classic Tetris palette)
COLORS = {
    'I': (0, 240, 240),
    'J': (0, 0, 240),
    'L': (240, 160, 0),
    'O': (240, 240, 0),
    'S': (0, 240, 0),
    'T': (160, 0, 240),
    'Z': (240, 0, 0),
}

# Tetromino definitions using 4x4 matrices (SRS-like orientation order 0-3)
# Each shape is a list of rotation states; each rotation is a list of (x,y) cell coords
PIECES = {
    'I': [
        [(0,1), (1,1), (2,1), (3,1)],
        [(2,0), (2,1), (2,2), (2,3)],
        [(0,2), (1,2), (2,2), (3,2)],
        [(1,0), (1,1), (1,2), (1,3)],
    ],
    'J': [
        [(0,0), (0,1), (1,1), (2,1)],
        [(1,0), (2,0), (1,1), (1,2)],
        [(0,1), (1,1), (2,1), (2,2)],
        [(1,0), (1,1), (0,2), (1,2)],
    ],
    'L': [
        [(2,0), (0,1), (1,1), (2,1)],
        [(1,0), (1,1), (1,2), (2,2)],
        [(0,1), (1,1), (2,1), (0,2)],
        [(0,0), (1,0), (1,1), (1,2)],
    ],
    'O': [
        [(1,0), (2,0), (1,1), (2,1)],
        [(1,0), (2,0), (1,1), (2,1)],
        [(1,0), (2,0), (1,1), (2,1)],
        [(1,0), (2,0), (1,1), (2,1)],
    ],
    'S': [
        [(1,0), (2,0), (0,1), (1,1)],
        [(1,0), (1,1), (2,1), (2,2)],
        [(1,1), (2,1), (0,2), (1,2)],
        [(0,0), (0,1), (1,1), (1,2)],
    ],
    'T': [
        [(1,0), (0,1), (1,1), (2,1)],
        [(1,0), (1,1), (2,1), (1,2)],
        [(0,1), (1,1), (2,1), (1,2)],
        [(1,0), (0,1), (1,1), (1,2)],
    ],
    'Z': [
        [(0,0), (1,0), (1,1), (2,1)],
        [(2,0), (1,1), (2,1), (1,2)],
        [(0,1), (1,1), (1,2), (2,2)],
        [(1,0), (0,1), (1,1), (0,2)],
    ],
}

# SRS wall kick data (simplified). For O we don't kick; for I we use I-specific; others use JLSTZ.
KICKS_JLSTZ = {
    (0,1): [(0,0), (-1,0), (-1,-1), (0,2), (-1,2)],
    (1,0): [(0,0), (1,0), (1,1), (0,-2), (1,-2)],
    (1,2): [(0,0), (1,0), (1,1), (0,-2), (1,-2)],
    (2,1): [(0,0), (-1,0), (-1,-1), (0,2), (-1,2)],
    (2,3): [(0,0), (1,0), (1,-1), (0,2), (1,2)],
    (3,2): [(0,0), (-1,0), (-1,1), (0,-2), (-1,-2)],
    (3,0): [(0,0), (-1,0), (-1,1), (0,-2), (-1,-2)],
    (0,3): [(0,0), (1,0), (1,-1), (0,2), (1,2)],
}
KICKS_I = {
    (0,1): [(0,0), (-2,0), (1,0), (-2,1), (1,-2)],
    (1,0): [(0,0), (2,0), (-1,0), (2,-1), (-1,2)],
    (1,2): [(0,0), (-1,0), (2,0), (-1,-2), (2,1)],
    (2,1): [(0,0), (1,0), (-2,0), (1,2), (-2,-1)],
    (2,3): [(0,0), (2,0), (-1,0), (2,-1), (-1,2)],
    (3,2): [(0,0), (-2,0), (1,0), (-2,1), (1,-2)],
    (3,0): [(0,0), (1,0), (-2,0), (1,2), (-2,-1)],
    (0,3): [(0,0), (-1,0), (2,0), (-1,-2), (2,1)],
}

#high score file to display top 5 high scores
HIGHSCORE_FILE = "highscores.txt"

def load_highscores():
    if not os.path.exists(HIGHSCORE_FILE):
        return []
    with open(HIGHSCORE_FILE, "r") as f:
        scores = []
        for line in f.readlines():
            parts = line.strip().split(",")
            if len(parts) == 2:
                name, score = parts
                scores.append((name, int(score)))
        return scores

def save_highscore(initials, score):
    scores = load_highscores()
    scores.append((initials, score))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)[:5]  # Top 5
    with open(HIGHSCORE_FILE, "w") as f:
        for name, s in scores:
            f.write(f"{name},{s}\n")

def enter_initials(screen, clock, font, font_small, score):
    initials = ""
    entering = True

    while entering:
        screen.fill((0, 0, 0))
        prompt = font_small.render(f"New High Score! {score}", True, (255, 255, 0))
        screen.blit(prompt, (200, 150))

        entry_text = font_small.render("Enter your initials: " + initials, True, (255, 255, 255))
        screen.blit(entry_text, (200, 250))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and initials != "":
                    entering = False
                elif event.key == pygame.K_BACKSPACE:
                    initials = initials[:-1]
                elif len(initials) < 3 and event.unicode.isalpha():
                    initials += event.unicode.upper()

    return initials

def show_highscores(screen, clock, font_small):
    showing = True
    scores = load_highscores()

    while showing:
        screen.fill((0, 0, 0))
        title = font_small.render("High Scores - Press Enter to go back", True, (255, 255, 255))
        screen.blit(title, (50, 50))

        if not scores:
            no_score_text = font_small.render("No scores yet!", True, (200, 200, 210))
            screen.blit(no_score_text, (50, 120))
        else:
            for i, (name, score) in enumerate(scores):
                text = font_small.render(f"{i+1}. {name} - {score}", True, (200, 200, 210))
                screen.blit(text, (50, 120 + i*40))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    showing = False

def show_game_over_scores(screen, clock, font, font_small):
    showing = True
    scores = load_highscores()

    while showing:
        screen.fill((0, 0, 0))
        t = font.render("Game Over", True, TEXT)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - t.get_height()))
        t2 = font_small.render("Press R to restart, Q/Esc to quit", True, TEXT)
        screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2 + 10))
        #title = font_small.render("Game over! High Scores - Press R to restart or Q to quit", True, (255, 255, 255))
        #screen.blit(title, (50, 50))

        if not scores:
            no_score_text = font_small.render("No scores yet!", True, (200, 200, 210))
            screen.blit(no_score_text, (50, 120))
        else:
            for i, (name, score) in enumerate(scores):
                text = font_small.render(f"{i+1}. {name} - {score}", True, (200, 200, 210))
                screen.blit(text, (50, 120 + i*40))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_r:
                    main()

# 7-bag randomizer
def bag_generator():
    pieces = list(PIECES.keys())
    while True:
        random.shuffle(pieces)
        for p in pieces:
            yield p
# main menu            
def main_menu(screen, clock, font_large, font_small):
    menu_running = True
    selected = 0
    options = ["Start Game", "High Scores", "Controls", "Quit"]

    while menu_running:
        screen.fill((0, 0, 0))

        # Draw menu options
        for i, option in enumerate(options):
            color = (255, 255, 0) if i == selected else (255, 255, 255)
            text = font_large.render(option, True, color)
            rect = text.get_rect(center=(400, 200 + i*80))
            screen.blit(text, rect)

        pygame.display.flip()
        clock.tick(60)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if options[selected] == "Start Game":
                        menu_running = False
                    elif options[selected] == "Controls":
                        show_controls(screen, clock, font_small)
                    elif options[selected] =="High Scores":
                        show_highscores(screen, clock, font_small)
                    elif options[selected] == "Quit":
                        pygame.quit()
                        sys.exit()

#show controls for main menu option
def show_controls(screen, clock, font_small):
    showing = True
    controls = [
        "Left / Right: Move",
        "Down: Soft Drop",
        "Up / X: Rotate Clockwise",
        "Z: Rotate Counter-Clockwise",
        "Space: Hard Drop",
        "C / Shift: Hold",
        "P: Pause, R: Restart",
        "Q / Esc: Quit"
    ]

    while showing:
        screen.fill((0, 0, 0))
        title = font_small.render("Controls - Press Enter to go back", True, (255, 255, 255))
        screen.blit(title, (50, 50))

        for i, line in enumerate(controls):
            text = font_small.render(line, True, (200, 200, 210))
            screen.blit(text, (50, 120 + i*40))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    showing = False

class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.rot = 0
        # spawn roughly centered; SRS spawn positions vary, but this is fine
        self.x = 3 if kind != 'I' else 3
        self.y = 0
        self.blocks = PIECES[kind]

    def cells(self, x=None, y=None, rot=None):
        x = self.x if x is None else x
        y = self.y if y is None else y
        rot = self.rot if rot is None else rot
        return [(x+cx, y+cy) for (cx,cy) in self.blocks[rot]]

class Board:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.grid = [[None for _ in range(w)] for _ in range(h)]

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def collides(self, cells):
        for x, y in cells:
            if x < 0 or x >= self.w or y >= self.h:
                return True
            if y >= 0 and self.grid[y][x] is not None:
                return True
        return False

    def lock(self, piece):
        for x, y in piece.cells():
            if 0 <= y < self.h:
                self.grid[y][x] = piece.kind
        # return lines cleared
        full = [i for i,row in enumerate(self.grid) if all(c is not None for c in row)]
        cleared = len(full)
        for i in full:
            del self.grid[i]
            self.grid.insert(0, [None for _ in range(self.w)])
        return cleared

    def top_out(self):
        # if any block is above the top after locking, game over
        for x in range(self.w):
            if self.grid[0][x] is not None and any(self.grid[y][x] is not None for y in range(0,2)):
                return True
        return False

class Game:
    def __init__(self):
        self.board = Board(GRID_W, GRID_H)
        self.bag = bag_generator()
        self.next_queue = [next(self.bag) for _ in range(5)]
        self.current = Piece(next(self.bag))
        self.hold = None
        self.hold_used = False
        self.score = 0
        self.level = 1
        self.lines = 0
        self.drop_cooldown = 0.5  # seconds initial
        self.gravity_timer = 0.0
        self.game_over = False
        self.paused = False
        self.spawn_new()

    def spawn_new(self):
        # move next piece into current, refill queue
        self.current = Piece(self.next_queue.pop(0) if self.next_queue else next(self.bag))
        self.next_queue.append(next(self.bag))
        self.hold_used = False
        # spawn adjustment if initial position collides
        if self.board.collides(self.current.cells()):
            # tiny nudge down or right if possible
            for dy in (0, -1, 1):
                for dx in (0, -1, 1):
                    if not self.board.collides(self.current.cells(self.current.x+dx, self.current.y+dy)):
                        self.current.x += dx
                        self.current.y += dy
                        return
            # if still colliding, game over
            self.game_over = True
            
            

    def soft_drop(self):
        if not self.try_move(0, 1):
            self.lock_and_clear()
        else:
            self.score += 1  # soft drop reward

    def hard_drop(self):
        dist = 0
        while self.try_move(0, 1):
            dist += 1
        self.score += 2 * dist
        self.lock_and_clear()

    def try_move(self, dx, dy):
        if self.game_over or self.paused:
            return False
        nx, ny = self.current.x + dx, self.current.y + dy
        if not self.board.collides(self.current.cells(nx, ny)):
            self.current.x, self.current.y = nx, ny
            return True
        return False

    def rotate(self, dir):
        if self.game_over or self.paused:
            return
        old_rot = self.current.rot
        new_rot = (old_rot + (1 if dir > 0 else -1)) % 4
        kicks = KICKS_I if self.current.kind == 'I' else KICKS_JLSTZ
        key = (old_rot, new_rot)
        candidates = kicks.get(key, [(0,0)])
        for dx, dy in candidates:
            cells = self.current.cells(self.current.x + dx, self.current.y + dy, new_rot)
            if not self.board.collides(cells):
                self.current.rot = new_rot
                self.current.x += dx
                self.current.y += dy
                return

    def hold_piece(self):
        if self.game_over or self.paused or self.hold_used:
            return
        self.hold_used = True
        if self.hold is None:
            self.hold = self.current.kind
            self.spawn_new()
        else:
            self.hold, self.current = self.current.kind, Piece(self.hold)
            # reset position/rotation
            self.current.x, self.current.y, self.current.rot = 3, 0, 0
            if self.board.collides(self.current.cells()):
                self.game_over = True

    def lock_and_clear(self):
        cleared = self.board.lock(self.current)
        if cleared:
            # basic Tetris scoring
            scores = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += scores.get(cleared, 0) * self.level
            self.lines += cleared
            # level up every 10 lines
            new_level = 1 + self.lines // 10
            if new_level != self.level:
                self.level = new_level
        if self.board.top_out():
            self.game_over = True
            return
        self.spawn_new()

    def fall_speed(self):
        # classic-like: speed increases with level, min clamp
        return max(0.10, 0.55 - (self.level - 1) * 0.05)

    def tick(self, dt, keys):
        if self.game_over or self.paused:
            return
        self.gravity_timer += dt
        if self.gravity_timer >= self.fall_speed():
            self.gravity_timer = 0
            if not self.try_move(0, 1):
                self.lock_and_clear()

    def ghost_y(self):
        # compute where the piece would land
        y = self.current.y
        while not self.board.collides(self.current.cells(self.current.x, y+1)):
            y += 1
        return y

# ------------ Drawing helpers ------------ #
def draw_cell(surf, x, y, color, inset=2, alpha=None):
    rect = pygame.Rect(BORDER + x*BLOCK, TOP_MARGIN + y*BLOCK, BLOCK, BLOCK)
    if alpha is not None:
        s = pygame.Surface((BLOCK, BLOCK), pygame.SRCALPHA)
        c = (*color, alpha)
        pygame.draw.rect(s, c, (inset, inset, BLOCK-2*inset, BLOCK-2*inset), border_radius=6)
        surf.blit(s, rect.topleft)
    else:
        pygame.draw.rect(surf, (12,12,16), rect, border_radius=6)
        inner = rect.inflate(-inset*2, -inset*2)
        pygame.draw.rect(surf, color, inner, border_radius=6)

def draw_board(screen, game, font_small):
    # board background
    board_rect = pygame.Rect(BORDER, TOP_MARGIN, GRID_W*BLOCK, GRID_H*BLOCK)
    pygame.draw.rect(screen, GRID_BG, board_rect, border_radius=8)
    # grid lines
    for x in range(GRID_W+1):
        pygame.draw.line(screen, GRID_LINE,
            (BORDER + x*BLOCK, TOP_MARGIN),
            (BORDER + x*BLOCK, TOP_MARGIN + GRID_H*BLOCK))
    for y in range(GRID_H+1):
        pygame.draw.line(screen, GRID_LINE,
            (BORDER, TOP_MARGIN + y*BLOCK),
            (BORDER + GRID_W*BLOCK, TOP_MARGIN + y*BLOCK))

    # locked blocks
    for y in range(GRID_H):
        for x in range(GRID_W):
            k = game.board.grid[y][x]
            if k:
                draw_cell(screen, x, y, COLORS[k])

    # ghost piece
    gy = game.ghost_y()
    for (cx, cy) in game.current.cells(game.current.x, gy):
        if cy >= 0:
            draw_cell(screen, cx, cy, GHOST, alpha=70)

    # current piece
    for (cx, cy) in game.current.cells():
        if cy >= 0:
            draw_cell(screen, cx, cy, COLORS[game.current.kind])

    # border
    pygame.draw.rect(screen, (80,80,95), board_rect, 2, border_radius=8)

def draw_panel(screen, game, font, font_small):
    x0 = BORDER*2 + GRID_W*BLOCK
    y0 = TOP_MARGIN
    panel = pygame.Rect(x0, y0, SIDE_PANEL, GRID_H*BLOCK)
    pygame.draw.rect(screen, GRID_BG, panel, border_radius=8)
    pygame.draw.rect(screen, (80,80,95), panel, 2, border_radius=8)

    def text(label, val, y):
        surf = font_small.render(f"{label}: {val}", True, TEXT)
        screen.blit(surf, (x0 + 14, y))

    title = font.render("TETRIS", True, TEXT)
    screen.blit(title, (x0 + 14, y0 + 10))

    text("Score", game.score, y0 + 60)
    text("Level", game.level, y0 + 88)
    text("Lines", game.lines, y0 + 116)

    # Next queue
    nq = font_small.render("Next", True, TEXT)
    screen.blit(nq, (x0 + 14, y0 + 150))

    def draw_mini(shape, px, py):
        blocks = PIECES[shape][0]
        # center mini previews
        xs = [c[0] for c in blocks]
        ys = [c[1] for c in blocks]
        w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        ox = px - (w*BLOCK)//2 + 15
        oy = py - (h*BLOCK)//2 + 15
        for (cx, cy) in blocks:
            rx = (cx - min(xs)) * BLOCK + ox
            ry = (cy - min(ys)) * BLOCK + oy
            rect = pygame.Rect(rx, ry, BLOCK-8, BLOCK-8)
            pygame.draw.rect(screen, COLORS[shape], rect, border_radius=6)

    ny = y0 + 180
    for i, s in enumerate(game.next_queue[:3]):
        draw_mini(s, x0 + SIDE_PANEL//2, ny + i*60)

    # Hold
    hold_label = font_small.render("Hold", True, TEXT)
    screen.blit(hold_label, (x0 + 14, y0 + 340))#480
    if game.hold:
        draw_mini(game.hold, x0 + SIDE_PANEL//2, y0 + 390)#520

    # Help
    help_lines = [
        "Arrows: move/drop",
        "Z/X or Up: rotate",
        "Space: hard drop",
        "C/Shift: hold",
        "P: pause, R: restart",
        "Q/Esc: quit",
    ]
    for i, line in enumerate(help_lines):
        s = font_small.render(line, True, (200,200,210))
        screen.blit(s, (x0 + 14, y0 + 440 + i*20))

def draw_header(screen, font_small):
    hdr = font_small.render("Python + Pygame — Tetris", True, (180, 180, 195))
    screen.blit(hdr, (BORDER, 10))

def reset_game():
    return Game()

def main():
    pygame.init()
    pygame.mixer.init()

    #set display
    pygame.display.set_caption("Tetris (Pygame)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arialrounded", 28, bold=True)
    font_small = pygame.font.SysFont("arial", 18)
    font_large = pygame.font.SysFont("arial", 50)
    main_menu(screen, clock, font_large, font_small)

    #load bgm
    pygame.mixer.music.load("Tetris 99 - Main Theme.ogg")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
    
    #start game
    game = Game()

    # Repeat left/right movement with key hold
    move_delay = 0.12
    move_timer = 0.0
    move_dir = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key in (K_ESCAPE, K_q):
                    running = False
                elif event.key == K_p:
                    game.paused = not game.paused
                elif event.key == K_r:
                    game = reset_game()
                elif not game.paused and not game.game_over:
                    if event.key == K_LEFT:
                        game.try_move(-1, 0)
                        move_dir = -1
                        move_timer = 0
                    elif event.key == K_RIGHT:
                        game.try_move(1, 0)
                        move_dir = 1
                        move_timer = 0
                    elif event.key == K_DOWN:
                        game.soft_drop()
                    elif event.key in (K_UP, K_x):
                        game.rotate(+1)
                    elif event.key == K_z:
                        game.rotate(-1)
                    elif event.key == K_SPACE:
                        game.hard_drop()
                    elif event.key in (K_c, K_LSHIFT, K_RSHIFT):
                        game.hold_piece()
            elif event.type == KEYUP:
                if event.key in (K_LEFT, K_RIGHT):
                    move_dir = 0
                    move_timer = 0

        # Auto repeat for horizontal movement
        if move_dir != 0 and not game.paused and not game.game_over:
            move_timer += dt
            if move_timer >= move_delay:
                if game.try_move(move_dir, 0):
                    move_timer -= move_delay  # keep it smooth
                else:
                    move_timer = 0.0

        # Tick gravity
        game.tick(dt, pygame.key.get_pressed())

        # Draw
        screen.fill(BG)
        draw_header(screen, font_small)
        draw_board(screen, game, font_small)
        draw_panel(screen, game, font, font_small)

        # Overlays
        if game.paused:
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0,0,0,120))
            screen.blit(s, (0,0))
            t = font.render("Paused", True, TEXT)
            screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - t.get_height()//2))
        if game.game_over:
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0,0,0,140))
            screen.blit(s, (0,0))

            # --- High score logic ---
            scores = load_highscores()
            # Check if qualifies for leaderboard
            if len(scores) < 5 or game.score > scores[-1][1]:
                initials = enter_initials(screen, clock, font, font_small, game.score)
                save_highscore(initials, game.score)
                game.score = 0
            
            show_game_over_scores(screen, clock, font, font_small)



        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
