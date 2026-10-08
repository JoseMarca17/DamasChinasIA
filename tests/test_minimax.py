import unittest

from app.ai.evaluation import evaluar_estado
from app.ai.minimax import SearchMetrics, minimax
from app.game.board import Board
from app.game.moves import get_legal_moves
from app.game.pieces import Player
from app.game.rules import apply_move


class MinimaxTests(unittest.TestCase):
    def test_depth_zero_returns_the_heuristic_value(self):
        board = Board()

        self.assertEqual(minimax(board, profundidad=0), evaluar_estado(board))

    def test_red_maximizes_at_depth_one_and_counts_the_leaves(self):
        board = Board()
        possible_moves = get_legal_moves(board, Player.RED)
        child_values = []

        for move in possible_moves:
            child_state = board.copy()
            apply_move(child_state, move)
            child_values.append(evaluar_estado(child_state))

        metrics = SearchMetrics()
        result = minimax(board, profundidad=1, metricas=metrics)

        self.assertEqual(result, max(child_values))
        self.assertEqual(metrics.nodos_visitados, 1 + len(possible_moves))
        self.assertEqual(metrics.hojas_evaluadas, len(possible_moves))

    def test_blue_minimizes_at_depth_one(self):
        board = Board()
        board.jugador_actual = Player.BLUE
        possible_moves = get_legal_moves(board, Player.BLUE)
        child_values = []

        for move in possible_moves:
            child_state = board.copy()
            apply_move(child_state, move)
            child_values.append(evaluar_estado(child_state))

        self.assertEqual(minimax(board, profundidad=1), min(child_values))

    def test_depth_two_propagates_min_values_to_the_root_max(self):
        board = Board()
        root_values = []

        for red_move in get_legal_moves(board, Player.RED):
            after_red = board.copy()
            apply_move(after_red, red_move)
            blue_reply_values = []

            for blue_move in get_legal_moves(after_red, Player.BLUE):
                after_blue = after_red.copy()
                apply_move(after_blue, blue_move)
                blue_reply_values.append(evaluar_estado(after_blue))

            root_values.append(min(blue_reply_values))

        original_occupants = board.ocupantes.copy()
        result = minimax(board, profundidad=2)

        self.assertEqual(result, max(root_values))
        self.assertEqual(board.ocupantes, original_occupants)
        self.assertEqual(board.jugador_actual, Player.RED)

    def test_negative_depth_is_rejected(self):
        with self.assertRaises(ValueError):
            minimax(Board(), profundidad=-1)


if __name__ == "__main__":
    unittest.main()
