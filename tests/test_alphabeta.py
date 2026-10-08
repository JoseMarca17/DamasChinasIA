import unittest

from app.ai.alphabeta import alphabeta
from app.ai.minimax import SearchMetrics, minimax
from app.game.board import Board
from app.game.pieces import Player


class AlphaBetaTests(unittest.TestCase):
    def test_alpha_beta_matches_minimax_at_depths_zero_one_and_two(self):
        for depth in (0, 1, 2):
            with self.subTest(depth=depth):
                board = Board()

                self.assertEqual(
                    alphabeta(board, depth),
                    minimax(board, depth),
                )

    def test_alpha_beta_matches_minimax_when_blue_is_to_move(self):
        board = Board()
        board.jugador_actual = Player.BLUE

        self.assertEqual(alphabeta(board, profundidad=2), minimax(board, profundidad=2))

    def test_search_keeps_half_point_scores_from_e2(self):
        board = Board(configurar_posicion_inicial=False)
        board.place_piece((16, 12), Player.RED)
        board.place_piece((3, 9), Player.BLUE)

        self.assertEqual(minimax(board, profundidad=0, heuristica="E2"), 1.5)
        self.assertEqual(alphabeta(board, profundidad=0, heuristica="E2"), 1.5)

    def test_alpha_beta_prunes_branches_and_visits_fewer_nodes(self):
        board = Board()
        minimax_metrics = SearchMetrics()
        alphabeta_metrics = SearchMetrics()

        minimax_value = minimax(board, profundidad=2, metricas=minimax_metrics)
        alphabeta_value = alphabeta(board, profundidad=2, metricas=alphabeta_metrics)

        self.assertEqual(alphabeta_value, minimax_value)
        self.assertGreater(alphabeta_metrics.cortes, 0)
        self.assertGreater(alphabeta_metrics.movimientos_podados, 0)
        self.assertLess(alphabeta_metrics.nodos_visitados, minimax_metrics.nodos_visitados)

    def test_search_does_not_change_the_input_board(self):
        board = Board()
        original_occupants = board.ocupantes.copy()
        original_red_pieces = board.fichas_por_jugador[Player.RED].copy()
        original_blue_pieces = board.fichas_por_jugador[Player.BLUE].copy()

        alphabeta(board, profundidad=2)

        self.assertEqual(board.ocupantes, original_occupants)
        self.assertEqual(board.fichas_por_jugador[Player.RED], original_red_pieces)
        self.assertEqual(board.fichas_por_jugador[Player.BLUE], original_blue_pieces)
        self.assertEqual(board.jugador_actual, Player.RED)

    def test_negative_depth_is_rejected(self):
        with self.assertRaises(ValueError):
            alphabeta(Board(), profundidad=-1)


if __name__ == "__main__":
    unittest.main()
