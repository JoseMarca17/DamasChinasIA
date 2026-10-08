import unittest

from app.ai.evaluation import (
    DISTANCIAS_A_META,
    calcular_distancia_ficha,
    calcular_distancia_ficha_atrasada,
    calcular_distancia_total,
    calcular_penalizacion_eje,
    evaluar_e1,
    evaluar_e2,
    evaluar_e3,
    evaluar_estado,
)
from app.game.board import Board
from app.game.moves import get_legal_moves
from app.game.pieces import MAX_PLAYER, MIN_PLAYER, Player


class EvaluationTests(unittest.TestCase):
    def test_e1_is_balanced_at_the_start(self):
        self.assertEqual(evaluar_e1(Board()), 0)

    def test_goal_cells_have_zero_distance(self):
        estado = Board()

        for jugador in (MAX_PLAYER, MIN_PLAYER):
            for casilla_meta in estado.goal_cells_for(jugador):
                self.assertEqual(calcular_distancia_ficha(casilla_meta, jugador), 0)

    def test_e1_is_positive_when_max_is_closer_to_its_goal(self):
        estado = Board(configurar_posicion_inicial=False)
        estado.place_piece((16, 12), MAX_PLAYER)
        estado.place_piece((13, 9), MIN_PLAYER)

        self.assertGreater(evaluar_e1(estado), 0)

    def test_e1_is_negative_when_min_is_closer_to_its_goal(self):
        estado = Board(configurar_posicion_inicial=False)
        estado.place_piece((3, 9), MAX_PLAYER)
        estado.place_piece((0, 12), MIN_PLAYER)

        self.assertLess(evaluar_e1(estado), 0)

    def test_distance_total_adds_each_piece_distance(self):
        estado = Board(configurar_posicion_inicial=False)
        fichas_max = [(16, 12), (13, 9)]
        for casilla in fichas_max:
            estado.place_piece(casilla, MAX_PLAYER)

        distancia_esperada = sum(
            DISTANCIAS_A_META[MAX_PLAYER][casilla]
            for casilla in fichas_max
        )
        self.assertEqual(calcular_distancia_total(estado, MAX_PLAYER), distancia_esperada)

    def test_e2_applies_half_the_relative_central_axis_penalty(self):
        estado = Board(configurar_posicion_inicial=False)
        estado.place_piece((16, 12), MAX_PLAYER)
        estado.place_piece((3, 9), MIN_PLAYER)

        penalizacion_eje = calcular_penalizacion_eje(estado)

        self.assertEqual(evaluar_e1(estado), 0)
        self.assertEqual(penalizacion_eje, -3)
        self.assertEqual(evaluar_e2(estado), evaluar_e1(estado) - 0.5 * penalizacion_eje)
        self.assertEqual(evaluar_e2(estado), 1.5)

    def test_e3_applies_twice_the_farthest_max_piece_distance(self):
        estado = Board(configurar_posicion_inicial=False)
        estado.place_piece((0, 12), MAX_PLAYER)
        estado.place_piece((3, 9), MAX_PLAYER)
        estado.place_piece((3, 11), MIN_PLAYER)

        distancia_atrasada = calcular_distancia_ficha_atrasada(estado)

        self.assertEqual(
            distancia_atrasada,
            max(
                calcular_distancia_ficha(casilla, MAX_PLAYER)
                for casilla in estado.fichas_por_jugador[MAX_PLAYER]
            ),
        )
        self.assertEqual(evaluar_e3(estado), evaluar_e1(estado) - 2 * distancia_atrasada)

    def test_selected_heuristic_matches_its_function(self):
        estado = Board()

        self.assertEqual(evaluar_estado(estado), evaluar_e1(estado))
        self.assertEqual(evaluar_estado(estado, "E1"), evaluar_e1(estado))
        self.assertEqual(evaluar_estado(estado, "e2"), evaluar_e2(estado))
        self.assertEqual(evaluar_estado(estado, "E3"), evaluar_e3(estado))

    def test_unknown_heuristic_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluar_estado(Board(), "E4")

    def test_advancing_red_improves_e1(self):
        estado = Board()
        movimiento = next(
            jugada
            for jugada in get_legal_moves(estado, Player.RED)
            if jugada.destino[0] > jugada.origen[0]
        )

        estado.move_piece(movimiento.origen, movimiento.destino, Player.RED)

        self.assertGreater(evaluar_e1(estado), 0)


if __name__ == "__main__":
    unittest.main()
