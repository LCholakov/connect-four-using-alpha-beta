import sys
import pygame
from typing import Optional

from constants import (
    ROWS, COLS, EMPTY, HUMAN, AI,
    CELL, PADDING, BOTTOM_MARGIN, WIDTH, HEIGHT, FPS,
    BG, GRID, HOLE, DISC_AI, DISC_HUMAN, WHITE, MUTED, WIN_HILITE, GHOST,
)
from board import Board
from ai import AIEngine

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Connect Four 10x10 — Human vs AI")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.font_big = pygame.font.SysFont("arial", 28, bold=True)

        self.board = Board()
        self.ai = AIEngine()
        self.current_player = HUMAN
        self.game_over = False
        self.winner: Optional[int] = None
        self.ai_stats = {"depth": 0, "nodes": 0, "nps": 0.0, "time": 0.0, "score": 0, "pv": []}
        self.ghost_col: Optional[int] = None

    def _draw_text(self, text: str, x: int, y: int, color, big: bool = False, align_right: bool = False):
        font = self.font_big if big else self.font
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if align_right:
            rect.topright = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)

    def draw(self):
        self.screen.fill(BG)
        status = ""
        if not self.game_over:
            status = "Your turn" if self.current_player == HUMAN else "AI thinking…"
        else:
            status = (
                "You win! Press R to restart." if self.winner == HUMAN else
                "AI wins! Press R to restart." if self.winner == AI else
                "Draw. Press R to restart."
            )
        self._draw_text(status, 12, 32, WHITE, big=True)

        stats_line = f"Depth {self.ai_stats['depth']} | Nodes {self.ai_stats['nodes']} | " \
                     f"NPS {self.ai_stats['nps']:.0f} | Time {self.ai_stats['time']:.2f}s"
        self._draw_text(stats_line, WIDTH - 12, 10, MUTED, align_right=True)
        pv_list = self.ai_stats.get("pv", [])
        if pv_list:
            pv_str = " → ".join(map(str, pv_list[:8]))
            self._draw_text(f"PV {pv_str}", WIDTH - 12, 42, MUTED, align_right=True)


        top = PADDING
        for r in range(ROWS):
            for c in range(COLS):
                x = c * CELL
                y = top + r * CELL
                pygame.draw.rect(self.screen, GRID, (x, y, CELL, CELL))
                cx = x + CELL // 2
                cy = y + CELL // 2
                radius = CELL // 2 - 6
                pygame.draw.circle(self.screen, HOLE, (cx, cy), radius)

        if not self.game_over and self.current_player == HUMAN and self.ghost_col is not None:
            if 0 <= self.ghost_col < COLS and self.board.heights[self.ghost_col] < ROWS:
                row_preview = ROWS - 1 - self.board.heights[self.ghost_col]
                cx = self.ghost_col * CELL + CELL // 2
                cy = PADDING + row_preview * CELL + CELL // 2
                pygame.draw.circle(self.screen, GHOST, (cx, cy), CELL // 2 - 10, width=3)

        for r in range(ROWS):
            for c in range(COLS):
                piece = self.board.grid[r][c]
                if piece != EMPTY:
                    cx = c * CELL + CELL // 2
                    cy = PADDING + r * CELL + CELL // 2
                    color = DISC_AI if piece == AI else DISC_HUMAN
                    pygame.draw.circle(self.screen, color, (cx, cy), CELL // 2 - 10)

        if self.board.winning_cells:
            for (r, c) in self.board.winning_cells:
                cx = c * CELL + CELL // 2
                cy = PADDING + r * CELL + CELL // 2
                pygame.draw.circle(self.screen, WIN_HILITE, (cx, cy), CELL // 2 - 22, width=6)

        pygame.display.flip()

    def _handle_move(self, col: int, player: int) -> bool:
        row = self.board.drop(col, player)

        # Check for win
        if self.board.check_win_from(row, col):
            self.winner = player
            self.board.winning_cells = self.board.check_win_from(row, col)
            self.game_over = True
            return True

        # Check for draw
        if self.board.is_full():
            self.winner = None
            self.game_over = True
            return True

        # Switch players
        self.current_player = AI if player == HUMAN else HUMAN
        return False

    def start_screen(self):
        selecting = True
        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key == pygame.K_h:
                        self.current_player = HUMAN
                        selecting = False
                    if event.key == pygame.K_a:
                        self.current_player = AI
                        selecting = False

            self.screen.fill(BG)
            title = "Connect Four 10x10"
            sub = "Press H — You start   |   Press A — AI starts"
            self._draw_text(title, WIDTH // 2 - 180, HEIGHT // 2 - 100, WHITE, big=True)
            self._draw_text(sub, WIDTH // 2 - 260, HEIGHT // 2 - 50, MUTED)
            self._draw_text("R to restart any time • ESC to quit", WIDTH // 2 - 210, HEIGHT // 2 + 10, MUTED)
            pygame.display.flip()
            self.clock.tick(FPS)

    def run_once_ai_move_if_starts(self):
        if self.current_player == AI and not self.game_over:
            self.draw()
            move, stats = self.ai.choose_move(self.board, AI)
            self.ai_stats = stats
            self._handle_move(move, AI)

    def reset_game(self):
        """Reset the game state to start a new game."""
        self.board = Board()
        self.game_over = False
        self.winner = None
        self.ai_stats = {"depth": 0, "nodes": 0, "nps": 0.0, "time": 0.0, "score": 0}

    def handle_events(self):
        """Handle pygame events and return True if the game should restart."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_r:
                    return True
            if event.type == pygame.MOUSEMOTION:
                x, _ = event.pos
                self.ghost_col = min(COLS - 1, max(0, x // CELL))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.game_over and self.current_player == HUMAN:
                    x, _ = event.pos
                    col = x // CELL
                    if 0 <= col < COLS and self.board.heights[col] < ROWS:
                        self._handle_move(col, HUMAN)
        return False

    def play_turn(self):
        """Process the current player's turn if it's AI."""
        if not self.game_over and self.current_player == AI:
            self.draw()
            move, stats = self.ai.choose_move(self.board, AI)
            self.ai_stats = stats
            self._handle_move(move, AI)

    def run(self):
        """Main game loop."""
        while True:
            self.reset_game()
            self.start_screen()
            self.run_once_ai_move_if_starts()

            while True:
                if self.handle_events():
                    break

                self.play_turn()
                self.draw()
                self.clock.tick(FPS)