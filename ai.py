import math
import time
from typing import List, Optional, Tuple
from constants import AI_TIME_LIMIT_S, AI_MAX_DEPTH, WIN_SCORE, AI
from board import Board

class TimeUp(Exception):
    pass

class AIEngine:
    def __init__(self, time_limit_s: float = AI_TIME_LIMIT_S, max_depth: int = AI_MAX_DEPTH):
        self.time_limit_s = time_limit_s
        self.max_depth = max_depth
        self.nodes = 0
        self.start_time = 0.0
        self.best_move: Optional[int] = None
        self.best_score: float = -math.inf
        self.depth_reached = 0
        self.pv_line: List[int] = []

    def choose_move(self, board: Board, player: int = AI):
        self.nodes = 0
        self.start_time = time.perf_counter()
        self.best_move = None
        self.best_score = -math.inf
        self.depth_reached = 0
        self.pv_line = []

        valid = board.valid_moves()
        if not valid:
            return 0, {"depth": 0, "nodes": 0, "nps": 0.0, "time": 0.0, "score": 0, "pv": []}

        ordered_seed = valid[:]

        try:
            for depth in range(1, self.max_depth + 1):
                score, move, line = self._negamax(board, depth, -math.inf, math.inf, AI, 0, ordered_seed)
                self.best_score, self.best_move, self.pv_line = score, move, line
                self.depth_reached = depth
        except TimeUp:
            pass

        elapsed = max(1e-9, time.perf_counter() - self.start_time)
        stats = {
            "depth": self.depth_reached,
            "nodes": self.nodes,
            "nps": self.nodes / elapsed,
            "time": elapsed,
            "score": self.best_score,
            "pv": self.pv_line,
        }
        move = self.best_move if self.best_move is not None else ordered_seed[0]
        return move, stats

    def _negamax(self, board: Board, depth: int, alpha: float, beta: float,
                 player: int, ply: int, order_hint: List[int]) -> Tuple[float, Optional[int], List[int]]:
        if (time.perf_counter() - self.start_time) > self.time_limit_s:
            raise TimeUp()

        # Count every node visited (internal + leaf)
        self.nodes += 1

        if depth == 0 or board.is_full():
            return board.evaluate() * player, None, []

        best_score = -math.inf
        best_move = None
        best_line: List[int] = []

        moves = board.valid_moves()
        if order_hint:
            hint_set = set(order_hint)
            moves = [m for m in order_hint if m in moves] + [m for m in moves if m not in hint_set]

        for col in moves:
            row = board.drop(col, player)
            try:
                winner_cells = board.check_win_from(row, col)
                if winner_cells:
                    score = (WIN_SCORE - ply)
                    child_line: List[int] = []
                else:
                    child_score, _, child_line = self._negamax(board, depth - 1, -beta, -alpha, -player, ply + 1, order_hint)
                    score = -child_score
            finally:
                # Always undo, even if we time out mid-search.
                board.undo()

            if score > best_score:
                best_score = score
                best_move = col
                best_line = [col] + child_line
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                break

        return best_score, best_move, best_line