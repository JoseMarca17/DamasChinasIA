import unittest

from app.game.moves import get_legal_moves
from app.game.pieces import Player
from app.ui.controls import AI_VS_AI, HUMAN_VS_AI, GameControls, format_cell_label
from app.ai.agent import AdversarialAgent, GREEDY_ALGORITHM


class GameControlsTests(unittest.TestCase):
    def test_cell_label_uses_human_row_and_position_not_internal_column(self):
        self.assertEqual(format_cell_label((3, 9)), "F4·C1")
        self.assertEqual(format_cell_label((3, 15)), "F4·C4")

    def test_selecting_a_piece_and_destination_applies_a_turn(self):
        controls = GameControls()
        move = get_legal_moves(controls.tablero, Player.RED)[0]

        controls.handle_board_click(move.origen)
        self.assertEqual(controls.celda_seleccionada, move.origen)
        self.assertIn(move.destino, controls.destinos_legales)

        controls.handle_board_click(move.destino)

        self.assertIsNone(controls.celda_seleccionada)
        self.assertEqual(controls.tablero.piece_at(move.destino), Player.RED)
        self.assertEqual(controls.tablero.jugador_actual, Player.BLUE)
        self.assertEqual(controls.ultimo_movimiento, (move.origen, move.destino))

    def test_new_game_resets_turn_and_selection(self):
        controls = GameControls()
        first_move = get_legal_moves(controls.tablero, Player.RED)[0]
        controls.handle_board_click(first_move.origen)

        controls.reset_game()

        self.assertEqual(controls.tablero.jugador_actual, Player.RED)
        self.assertIsNone(controls.celda_seleccionada)
        self.assertEqual(controls.destinos_legales, set())
        self.assertIsNone(controls.ultimo_movimiento)

    def test_human_cannot_move_during_the_ai_turn(self):
        controls = GameControls(modo=HUMAN_VS_AI)
        original_positions = controls.tablero.fichas_por_jugador[Player.RED].copy()
        red_piece = sorted(original_positions)[0]

        self.assertTrue(controls.is_ai_turn)
        controls.handle_board_click(red_piece)

        self.assertIsNone(controls.celda_seleccionada)
        self.assertEqual(controls.tablero.fichas_por_jugador[Player.RED], original_positions)

    def test_ai_decision_is_applied_and_turn_passes_to_the_human(self):
        controls = GameControls(modo=HUMAN_VS_AI)
        decision = AdversarialAgent(profundidad=1).choose_move(controls.tablero.copy())

        controls.finish_ai_turn(decision)

        self.assertEqual(controls.tablero.jugador_actual, Player.BLUE)
        self.assertFalse(controls.is_ai_turn)
        self.assertEqual(controls.tablero.piece_at(decision.movimiento.destino), Player.RED)
        self.assertIn("Alfa-Beta", controls.mensaje)
        self.assertIn("F", controls.mensaje)

    def test_ai_vs_ai_allows_both_players_to_take_turns(self):
        controls = GameControls(modo=AI_VS_AI)
        agente = AdversarialAgent(algoritmo=GREEDY_ALGORITHM)
        fichas_rojas_iniciales = controls.tablero.fichas_por_jugador[Player.RED].copy()
        fichas_azules_iniciales = controls.tablero.fichas_por_jugador[Player.BLUE].copy()

        self.assertTrue(controls.is_ai_turn)
        decision_roja = agente.choose_move(controls.tablero.copy())
        controls.finish_ai_turn(decision_roja)
        self.assertEqual(controls.tablero.jugador_actual, Player.BLUE)
        self.assertTrue(controls.is_ai_turn)
        self.assertNotEqual(controls.tablero.fichas_por_jugador[Player.RED], fichas_rojas_iniciales)
        self.assertEqual(controls.tablero.fichas_por_jugador[Player.BLUE], fichas_azules_iniciales)

        decision_azul = agente.choose_move(controls.tablero.copy())
        controls.finish_ai_turn(decision_azul)
        self.assertEqual(controls.tablero.jugador_actual, Player.RED)
        self.assertTrue(controls.is_ai_turn)
        self.assertNotEqual(controls.tablero.fichas_por_jugador[Player.BLUE], fichas_azules_iniciales)


if __name__ == "__main__":
    unittest.main()
