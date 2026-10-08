import json
import tempfile
import unittest
from pathlib import Path

from app.game.board import CELL_SET
from app.game.board import Board
from app.game.moves import Move, get_legal_moves
from app.game.pieces import Player
from app.game.rules import apply_move
from app.ai.evaluation import evaluar_estado
from app.visualization.export_tree import export_tree_example

EXAMPLES_DIRECTORY = Path(__file__).resolve().parents[1] / "examples"


def minimax_value(node):
    """Evalúa el pequeño árbol JSON para verificar sus valores declarados."""
    children = node.get("children", [])
    if not children:
        return node["value"]

    child_values = [minimax_value(child) for child in children]
    if node["player"] == "MAX":
        return max(child_values)
    return min(child_values)


def alphabeta_value(node, alpha=float("-inf"), beta=float("inf"), pruned=None):
    """Evalúa el árbol del ejemplo y anota hojas realmente podadas."""
    if pruned is None:
        pruned = []

    children = node.get("children", [])
    if not children:
        return node["value"]

    if node["player"] == "MAX":
        best_value = float("-inf")
        for child_index, child in enumerate(children):
            best_value = max(best_value, alphabeta_value(child, alpha, beta, pruned))
            alpha = max(alpha, best_value)
            if beta <= alpha:
                for skipped_child in children[child_index + 1:]:
                    pruned.extend(leaf["move"] for leaf in get_leaves(skipped_child))
                break
        return best_value

    best_value = float("inf")
    for child_index, child in enumerate(children):
        best_value = min(best_value, alphabeta_value(child, alpha, beta, pruned))
        beta = min(beta, best_value)
        if beta <= alpha:
            for skipped_child in children[child_index + 1:]:
                pruned.extend(leaf["move"] for leaf in get_leaves(skipped_child))
            break
    return best_value


def get_leaves(node):
    """Devuelve las hojas descendientes de un subárbol podado."""
    children = node.get("children", [])
    if not children:
        return [node]
    return [leaf for child in children for leaf in get_leaves(child)]


class ExampleTreeTests(unittest.TestCase):
    def load_example(self, filename):
        path = EXAMPLES_DIRECTORY / filename
        with path.open(encoding="utf-8") as example_file:
            return json.load(example_file)

    def test_minimax_example_has_the_expected_value_and_best_move(self):
        example = self.load_example("minimax_example.json")
        root = {"player": example["root_player"], "children": example["children"]}

        self.assertEqual(minimax_value(root), example["expected_value"])
        move_values = [minimax_value(child) for child in example["children"]]
        best_child = example["children"][move_values.index(max(move_values))]
        self.assertEqual(best_child["move"], example["best_move"])

    def test_alphabeta_example_picks_the_expected_move_and_prunes_b1(self):
        example = self.load_example("alphabeta_example.json")
        pruned_leaves = []

        # El agente Python busca cada jugada inicial por separado; alpha y beta
        # vuelven a sus valores iniciales para cada candidato de la raíz.
        valores_movimientos = [
            alphabeta_value(rama, pruned=pruned_leaves)
            for rama in example["children"]
        ]
        result = max(valores_movimientos)
        mejor_rama = example["children"][valores_movimientos.index(result)]

        self.assertEqual(result, example["expected_value"])
        self.assertEqual(mejor_rama["move"], example["best_move"])
        self.assertEqual(
            pruned_leaves,
            ["F4-C2 a F3-C2"],
        )

    def test_example_moves_are_legal_and_the_tree_has_three_plies(self):
        for filename in ("greedy_example.json", "minimax_example.json", "alphabeta_example.json"):
            with self.subTest(filename=filename):
                example = self.load_example(filename)
                estado_inicial = Board(configurar_posicion_inicial=False)
                for casilla in example["board_state"]["red"]:
                    estado_inicial.place_piece(tuple(casilla), Player.RED)
                for casilla in example["board_state"]["blue"]:
                    estado_inicial.place_piece(tuple(casilla), Player.BLUE)

                def revisar_movimientos(nodo, estado):
                    estado_hijo = estado.copy()
                    origen = tuple(nodo["piece_move"]["from"])
                    destino = tuple(nodo["piece_move"]["to"])
                    jugador = Player.RED if nodo["mover"] == "ROJO" else Player.BLUE
                    movimiento = Move(origen, destino)
                    self.assertIn(movimiento, get_legal_moves(estado_hijo, jugador))
                    apply_move(estado_hijo, movimiento)
                    hijos = nodo.get("children", [])
                    if not hijos:
                        self.assertEqual(nodo["value"], evaluar_estado(estado_hijo, "E1"))
                    for hijo in hijos:
                        revisar_movimientos(hijo, estado_hijo)

                for rama in example["children"]:
                    revisar_movimientos(rama, estado_inicial)

                if example["algorithm"] != "greedy":
                    self.assertTrue(example["children"][0]["children"][0]["children"])

    def test_greedy_example_selects_the_highest_immediate_evaluation(self):
        example = self.load_example("greedy_example.json")
        valores_movimientos = [hijo["value"] for hijo in example["children"]]
        mejor_hijo = example["children"][valores_movimientos.index(max(valores_movimientos))]

        self.assertEqual(max(valores_movimientos), example["expected_value"])
        self.assertEqual(mejor_hijo["move"], example["best_move"])

    def test_each_example_contains_a_valid_intermediate_board(self):
        for filename in ("minimax_example.json", "alphabeta_example.json", "greedy_example.json"):
            with self.subTest(filename=filename):
                board_state = self.load_example(filename)["board_state"]
                red_cells = [tuple(cell) for cell in board_state["red"]]
                blue_cells = [tuple(cell) for cell in board_state["blue"]]

                self.assertEqual(len(red_cells), 10)
                self.assertEqual(len(blue_cells), 10)
                self.assertEqual(len(set(red_cells + blue_cells)), 20)
                self.assertTrue(set(red_cells + blue_cells).issubset(CELL_SET))

    def test_example_export_round_trips_unicode_and_tree_data(self):
        example = self.load_example("alphabeta_example.json")
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "exported-example.json"

            returned_path = export_tree_example(example, output_path)

            self.assertEqual(returned_path, output_path)
            with output_path.open(encoding="utf-8") as output_file:
                self.assertEqual(json.load(output_file), example)

    def test_example_export_rejects_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "invalid.json"

            with self.assertRaises(ValueError):
                export_tree_example({}, output_path)

            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
