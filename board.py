from typing import List, Optional, Tuple
from constants import (ROWS, COLS, CONNECT_N, EMPTY, HUMAN, AI, CENTER_COL,
    W_WINDOW_AI_4, W_WINDOW_HUMAN_4, W_WINDOW_AI_3E1, W_WINDOW_HUMAN_3E1,
    W_WINDOW_AI_2E2, W_WINDOW_HUMAN_2E2, W_WINDOW_AI_1E3, W_WINDOW_HUMAN_1E3,
    CENTER_COL_BONUS_BASE, CENTER_ROW_BONUS_BASE, CENTER_ROW_BONUS_DIV
)

class Board:
    def __init__(self):
        self.grid: List[List[int]] = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        self.heights: List[int] = [0 for _ in range(COLS)]
        self.last_move: Optional[Tuple[int, int]] = None
        self.winning_cells: Optional[List[Tuple[int, int]]] = None
        self.move_stack: List[int] = []

    def clone(self):
        b = Board()
        for r in range(ROWS):
            b.grid[r] = self.grid[r][:]
        b.heights = self.heights[:]
        b.last_move = self.last_move
        b.winning_cells = None
        b.move_stack = self.move_stack[:]
        return b

    def valid_moves(self) -> List[int]:
        return [c for c in range(COLS) if self.heights[c] < ROWS]

    def is_full(self) -> bool:
        return all(h >= ROWS for h in self.heights)

    def drop(self, col: int, player: int) -> Optional[int]:
        if col < 0 or col >= COLS:
            return None
        if self.heights[col] >= ROWS:
            return None
        row = ROWS - 1 - self.heights[col]
        self.grid[row][col] = player
        self.heights[col] += 1
        self.last_move = (row, col)
        self.move_stack.append(col)
        return row

    def undo(self) -> None:
        if not self.move_stack:
            return
        col = self.move_stack.pop()
        self.heights[col] -= 1
        row = ROWS - 1 - self.heights[col]
        self.grid[row][col] = EMPTY
        self.last_move = None
        self.winning_cells = None

    def check_win_from(self, row: int, col: int):
        player = self.grid[row][col]
        if player == EMPTY:
            return None
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            cells = [(row, col)]
            r, c = row + dy, col + dx
            while 0 <= r < ROWS and 0 <= c < COLS and self.grid[r][c] == player:
                cells.append((r, c))
                r += dy
                c += dx
            r, c = row - dy, col - dx
            while 0 <= r < ROWS and 0 <= c < COLS and self.grid[r][c] == player:
                cells.insert(0, (r, c))
                r -= dy
                c -= dx
            if len(cells) >= CONNECT_N:
                return cells[:CONNECT_N]
        return None

    def has_winner(self) -> Optional[int]:
        if not self.last_move:
            return None
        r, c = self.last_move
        cells = self.check_win_from(r, c)
        if cells:
            self.winning_cells = cells
            return self.grid[r][c]
        return None

    def evaluate(self) -> int:
        score = 0
        # modest center preference
        for r in range(ROWS):
            for c in range(COLS):
                piece = self.grid[r][c]
                if piece == EMPTY:
                    continue
                col_bonus = CENTER_COL_BONUS_BASE - abs(c - CENTER_COL)
                row_bonus = CENTER_ROW_BONUS_BASE - abs((r - (ROWS - 1) / 2.0)) / CENTER_ROW_BONUS_DIV
                score += (1 if piece == AI else -1) * int(col_bonus + row_bonus)

        def window_score(window: List[int]) -> int:
            count_ai = window.count(AI)
            count_human = window.count(HUMAN)
            count_empty = window.count(EMPTY)
            if count_ai > 0 and count_human > 0:
                return 0
            if count_ai == 4:
                return W_WINDOW_AI_4
            if count_human == 4:
                return W_WINDOW_HUMAN_4
            if count_ai == 3 and count_empty == 1:
                return W_WINDOW_AI_3E1
            if count_human == 3 and count_empty == 1:
                return W_WINDOW_HUMAN_3E1
            if count_ai == 2 and count_empty == 2:
                return W_WINDOW_AI_2E2
            if count_human == 2 and count_empty == 2:
                return W_WINDOW_HUMAN_2E2
            if count_ai == 1 and count_empty == 3:
                return W_WINDOW_AI_1E3
            if count_human == 1 and count_empty == 3:
                return W_WINDOW_HUMAN_1E3
            return 0

        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                win = [self.grid[r][c + i] for i in range(4)]
                score += window_score(win)
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                win = [self.grid[r + i][c] for i in range(4)]
                score += window_score(win)
        # Diagonal down-right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                win = [self.grid[r + i][c + i] for i in range(4)]
                score += window_score(win)
        # Diagonal up-right
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                win = [self.grid[r - i][c + i] for i in range(4)]
                score += window_score(win)
        return score