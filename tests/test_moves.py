import unittest

from app.game.board import Board
from app.game.moves import Move, get_legal_moves, get_piece_destinations
from app.game.pieces import Player
from app.game.rules import apply_move, get_winner


class MoveTests(unittest.TestCase):
    def test_piece_can_step_to_an_empty_neighbor(self):
        board = Board(configurar_posicion_inicial=False)
        origin = (8, 12)
        destination = (8, 14)
        board.place_piece(origin, Player.RED)

        self.assertIn(destination, get_piece_destinations(board, origin, Player.RED))

    def test_piece_can_jump_over_an_opponent_piece(self):
        board = Board(configurar_posicion_inicial=False)
        origin = (8, 12)
        landing = (8, 16)
        board.place_piece(origin, Player.RED)
        board.place_piece((8, 14), Player.BLUE)

        self.assertIn(landing, get_piece_destinations(board, origin, Player.RED))

    def test_piece_can_make_a_chain_of_jumps(self):
        board = Board(configurar_posicion_inicial=False)
        origin = (8, 12)
        board.place_piece(origin, Player.RED)
        board.place_piece((8, 14), Player.BLUE)
        board.place_piece((8, 18), Player.BLUE)

        self.assertIn((8, 20), get_piece_destinations(board, origin, Player.RED))

    def test_applying_a_legal_move_updates_positions_and_turn(self):
        board = Board()
        move = get_legal_moves(board, Player.RED)[0]
        origin_player = board.jugador_actual

        apply_move(board, move)

        self.assertIsNone(board.piece_at(move.origen))
        self.assertEqual(board.piece_at(move.destino), origin_player)
        self.assertEqual(board.jugador_actual, Player.BLUE)

    def test_illegal_move_is_rejected_without_changing_the_board(self):
        board = Board()
        initial_positions = board.fichas_por_jugador[Player.RED].copy()

        with self.assertRaises(ValueError):
            apply_move(board, Move((0, 12), (8, 12)))

        self.assertEqual(board.fichas_por_jugador[Player.RED], initial_positions)

    def test_player_wins_when_all_ten_pieces_reach_the_opposite_triangle(self):
        board = Board(configurar_posicion_inicial=False)
        for goal_cell in board.goal_cells_for(Player.RED):
            board.place_piece(goal_cell, Player.RED)

        self.assertEqual(get_winner(board), Player.RED)


if __name__ == "__main__":
    unittest.main()
