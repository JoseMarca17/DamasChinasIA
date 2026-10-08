import unittest

from app.game.board import ALL_CELLS, BOTTOM_START_CELLS, TOP_START_CELLS, Board
from app.game.pieces import Player


class BoardTests(unittest.TestCase):
    def test_initial_board_has_121_cells_and_ten_pieces_per_player(self):
        board = Board()

        self.assertEqual(len(ALL_CELLS), 121)
        self.assertEqual(len(board.fichas_por_jugador[Player.RED]), 10)
        self.assertEqual(len(board.fichas_por_jugador[Player.BLUE]), 10)
        self.assertEqual(board.fichas_por_jugador[Player.RED], set(TOP_START_CELLS))
        self.assertEqual(board.fichas_por_jugador[Player.BLUE], set(BOTTOM_START_CELLS))
        self.assertEqual(board.jugador_actual, Player.RED)

    def test_copy_has_independent_piece_positions(self):
        board = Board()
        copied_board = board.copy()

        copied_board.fichas_por_jugador[Player.RED].clear()

        self.assertEqual(len(board.fichas_por_jugador[Player.RED]), 10)
        self.assertEqual(len(copied_board.fichas_por_jugador[Player.RED]), 0)


if __name__ == "__main__":
    unittest.main()
