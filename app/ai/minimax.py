"""Búsqueda Minimax aplicada a estados reales del motor del juego."""

from dataclasses import dataclass
from math import inf

from app.ai.evaluation import evaluar_estado, normalizar_heuristica
from app.game.board import Board
from app.game.moves import get_legal_moves
from app.game.pieces import MAX_PLAYER
from app.game.rules import apply_move, get_winner


@dataclass
class SearchMetrics:
    """Contadores para explicar cuánto del árbol exploró cada algoritmo."""

    nodos_visitados: int = 0
    hojas_evaluadas: int = 0
    cortes: int = 0
    movimientos_podados: int = 0

    def reset(self) -> None:
        """Prepara los contadores para una búsqueda nueva."""
        self.nodos_visitados = 0
        self.hojas_evaluadas = 0
        self.cortes = 0
        self.movimientos_podados = 0


def minimax(
    estado: Board,
    profundidad: int,
    metricas: SearchMetrics | None = None,
    heuristica: str = "E1",
) -> int | float:
    """Devuelve el valor Minimax de ``estado`` hasta la profundidad indicada.

    ``profundidad`` cuenta medias jugadas (plies): cada movimiento de un jugador
    consume un nivel. ROJO es MAX y busca valores altos; AZUL es MIN y busca
    valores bajos. Los hijos se construyen sobre copias, así el estado recibido
    no cambia durante la búsqueda.

    Si un jugador no tiene movimientos legales, se considera que pasa el turno.
    Ese pase consume un nivel, igual que una jugada. ``metricas`` es opcional y
    acumula la cantidad de nodos visitados y hojas evaluadas en esta búsqueda.
    """
    if profundidad < 0:
        raise ValueError("La profundidad de búsqueda no puede ser negativa.")
    heuristica = normalizar_heuristica(heuristica)

    if metricas is None:
        metricas = SearchMetrics()
    else:
        metricas.reset()

    return _minimax(estado, profundidad, metricas, heuristica)


def _minimax(
    estado: Board,
    profundidad: int,
    metricas: SearchMetrics,
    heuristica: str,
) -> int | float:
    """Versión recursiva que muestra explícitamente MAX y MIN."""
    metricas.nodos_visitados += 1

    if profundidad == 0 or get_winner(estado) is not None:
        metricas.hojas_evaluadas += 1
        return evaluar_estado(estado, heuristica)

    jugador_actual = estado.jugador_actual
    movimientos_posibles = get_legal_moves(estado, jugador_actual)

    if not movimientos_posibles:
        # Un pase también entrega el turno al rival. Copiamos antes de cambiarlo
        # para que esta rama no modifique el tablero que recibió la función.
        estado_pasado = estado.copy()
        estado_pasado.jugador_actual = jugador_actual.oponente
        return _minimax(estado_pasado, profundidad - 1, metricas, heuristica)

    if jugador_actual is MAX_PLAYER:
        mejor_valor = -inf

        for movimiento in movimientos_posibles:
            estado_hijo = estado.copy()
            apply_move(estado_hijo, movimiento)
            valor_hijo = _minimax(estado_hijo, profundidad - 1, metricas, heuristica)

            # MAX conserva el valor más alto encontrado hasta ahora.
            if valor_hijo > mejor_valor:
                mejor_valor = valor_hijo

        return mejor_valor

    mejor_valor = inf

    for movimiento in movimientos_posibles:
        estado_hijo = estado.copy()
        apply_move(estado_hijo, movimiento)
        valor_hijo = _minimax(estado_hijo, profundidad - 1, metricas, heuristica)

        # MIN conserva el valor más bajo encontrado hasta ahora.
        if valor_hijo < mejor_valor:
            mejor_valor = valor_hijo

    return mejor_valor
