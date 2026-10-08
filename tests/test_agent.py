import unittest

from app.ai.agent import (
    ALPHABETA_ALGORITHM,
    GREEDY_ALGORITHM,
    MINIMAX_ALGORITHM,
    AdversarialAgent,
)
from app.ai.evaluation import evaluar_estado
from app.game.board import Board
from app.game.moves import get_legal_moves
from app.game.pieces import Player
from app.game.rules import apply_move


class AdversarialAgentTests(unittest.TestCase):
    def test_agent_returns_a_legal_move_without_changing_the_position(self):
        board = Board()
        original_occupants = board.ocupantes.copy()
        agent = AdversarialAgent(algoritmo=ALPHABETA_ALGORITHM, profundidad=1)

        decision = agent.choose_move(board)

        self.assertIsNotNone(decision)
        self.assertIn(decision.movimiento, get_legal_moves(board, Player.RED))
        self.assertEqual(board.ocupantes, original_occupants)
        self.assertEqual(board.jugador_actual, Player.RED)
        self.assertEqual(decision.algoritmo, ALPHABETA_ALGORITHM)
        self.assertGreater(decision.metricas.nodos_visitados, 1)

    def test_agent_selects_the_best_child_value_for_red(self):
        board = Board()
        child_values = []

        for move in get_legal_moves(board, Player.RED):
            child_state = board.copy()
            apply_move(child_state, move)
            child_values.append(evaluar_estado(child_state))

        decision = AdversarialAgent(MINIMAX_ALGORITHM, profundidad=1).choose_move(board)

        self.assertEqual(decision.valor, max(child_values))

    def test_agent_selects_the_best_child_value_for_blue(self):
        board = Board()
        board.jugador_actual = Player.BLUE
        child_values = []

        for move in get_legal_moves(board, Player.BLUE):
            child_state = board.copy()
            apply_move(child_state, move)
            child_values.append(evaluar_estado(child_state))

        decision = AdversarialAgent(ALPHABETA_ALGORITHM, profundidad=1).choose_move(board)

        self.assertEqual(decision.valor, min(child_values))

    def test_minimax_and_alpha_beta_produce_the_same_decision_value(self):
        board = Board()
        minimax_decision = AdversarialAgent(MINIMAX_ALGORITHM, profundidad=2).choose_move(board)
        alphabeta_decision = AdversarialAgent(ALPHABETA_ALGORITHM, profundidad=2).choose_move(board)

        self.assertEqual(alphabeta_decision.valor, minimax_decision.valor)

    def test_agent_returns_none_when_no_move_is_available(self):
        board = Board(configurar_posicion_inicial=False)
        board.jugador_actual = Player.BLUE

        decision = AdversarialAgent().choose_move(board)

        self.assertIsNone(decision)

    def test_unknown_algorithm_and_zero_depth_are_rejected(self):
        with self.assertRaises(ValueError):
            AdversarialAgent(algoritmo="otro")
        with self.assertRaises(ValueError):
            AdversarialAgent(profundidad=0)
        with self.assertRaises(ValueError):
            AdversarialAgent(heuristica="E4")

    def test_agent_can_select_each_heuristic(self):
        for heuristica in ("E1", "E2", "E3"):
            with self.subTest(heuristica=heuristica):
                decision = AdversarialAgent(
                    GREEDY_ALGORITHM,
                    heuristica=heuristica,
                ).choose_move(Board())

                self.assertEqual(decision.heuristica, heuristica)

    def test_greedy_agent_chooses_the_best_immediate_evaluation(self):
        board = Board()
        ocupantes_originales = board.ocupantes.copy()
        valores_movimientos = []
        for movimiento in get_legal_moves(board, Player.RED):
            estado_hijo = board.copy()
            apply_move(estado_hijo, movimiento)
            valores_movimientos.append(evaluar_estado(estado_hijo))

        decision = AdversarialAgent(GREEDY_ALGORITHM).choose_move(board)

        self.assertEqual(decision.valor, max(valores_movimientos))
        self.assertEqual(decision.profundidad, 1)
        self.assertIn(decision.movimiento, get_legal_moves(board, Player.RED))
        self.assertEqual(board.ocupantes, ocupantes_originales)

    def test_greedy_agent_minimizes_for_blue(self):
        board = Board()
        board.jugador_actual = Player.BLUE
        valores_movimientos = []
        for movimiento in get_legal_moves(board, Player.BLUE):
            estado_hijo = board.copy()
            apply_move(estado_hijo, movimiento)
            valores_movimientos.append(evaluar_estado(estado_hijo))

        decision = AdversarialAgent(GREEDY_ALGORITHM).choose_move(board)

        self.assertEqual(decision.valor, min(valores_movimientos))
        self.assertIn(decision.movimiento, get_legal_moves(board, Player.BLUE))

    def test_minimax_and_alpha_beta_work_with_all_heuristics(self):
        for heuristica in ("E1", "E2", "E3"):
            with self.subTest(heuristica=heuristica):
                board = Board()
                decision_minimax = AdversarialAgent(
                    MINIMAX_ALGORITHM,
                    profundidad=2,
                    heuristica=heuristica,
                ).choose_move(board)
                decision_alphabeta = AdversarialAgent(
                    ALPHABETA_ALGORITHM,
                    profundidad=2,
                    heuristica=heuristica,
                ).choose_move(board)

                self.assertEqual(decision_minimax.valor, decision_alphabeta.valor)
                self.assertEqual(decision_minimax.heuristica, heuristica)
                self.assertEqual(decision_alphabeta.heuristica, heuristica)


if __name__ == "__main__":
    unittest.main()
