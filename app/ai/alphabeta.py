"""Búsqueda Minimax con poda Alfa-Beta aplicada al motor del juego."""

from math import inf

from app.ai.evaluation import evaluar_estado, normalizar_heuristica
from app.ai.minimax import SearchMetrics
from app.game.board import Board
from app.game.moves import get_legal_moves
from app.game.pieces import MAX_PLAYER
from app.game.rules import apply_move, get_winner


def alphabeta(
    estado: Board,
    profundidad: int,
    metricas: SearchMetrics | None = None,
    heuristica: str = "E1",
) -> int | float:
    """Devuelve el valor Minimax, omitiendo ramas que no pueden cambiarlo.

    `alpha` es el mejor valor que MAX ya puede garantizar y `beta` el mejor
    valor que MIN puede garantizar. Cuando `beta <= alpha`, la búsqueda deja
    de visitar los movimientos hermanos que ya no pueden afectar la decisión.
    Los nodos se visitan en el orden determinista generado por el motor.
    """
    if profundidad < 0:
        raise ValueError("La profundidad de búsqueda no puede ser negativa.")
    heuristica = normalizar_heuristica(heuristica)

    if metricas is None:
        metricas = SearchMetrics()
    else:
        metricas.reset()

    return _alphabeta(estado, profundidad, -inf, inf, metricas, heuristica)


def _alphabeta(
    estado: Board,
    profundidad: int,
    alpha: float,
    beta: float,
    metricas: SearchMetrics,
    heuristica: str,
) -> int | float:
    """Versión recursiva que conserva explícitamente MAX, MIN, alpha y beta."""
    metricas.nodos_visitados += 1

    if profundidad == 0 or get_winner(estado) is not None:
        metricas.hojas_evaluadas += 1
        return evaluar_estado(estado, heuristica)

    jugador_actual = estado.jugador_actual
    movimientos_posibles = get_legal_moves(estado, jugador_actual)

    if not movimientos_posibles:
        estado_pasado = estado.copy()
        estado_pasado.jugador_actual = jugador_actual.oponente
        return _alphabeta(estado_pasado, profundidad - 1, alpha, beta, metricas, heuristica)

    if jugador_actual is MAX_PLAYER:
        mejor_valor = -inf

        for indice_movimiento, movimiento in enumerate(movimientos_posibles):
            estado_hijo = estado.copy()
            apply_move(estado_hijo, movimiento)
            valor_hijo = _alphabeta(estado_hijo, profundidad - 1, alpha, beta, metricas, heuristica)

            if valor_hijo > mejor_valor:
                mejor_valor = valor_hijo

            if mejor_valor > alpha:
                alpha = mejor_valor

            movimientos_restantes = len(movimientos_posibles) - indice_movimiento - 1
            if beta <= alpha:
                if movimientos_restantes > 0:
                    metricas.cortes += 1
                    metricas.movimientos_podados += movimientos_restantes
                break

        return mejor_valor

    mejor_valor = inf

    for indice_movimiento, movimiento in enumerate(movimientos_posibles):
        estado_hijo = estado.copy()
        apply_move(estado_hijo, movimiento)
        valor_hijo = _alphabeta(estado_hijo, profundidad - 1, alpha, beta, metricas, heuristica)

        if valor_hijo < mejor_valor:
            mejor_valor = valor_hijo

        if mejor_valor < beta:
            beta = mejor_valor

        movimientos_restantes = len(movimientos_posibles) - indice_movimiento - 1
        if beta <= alpha:
            if movimientos_restantes > 0:
                metricas.cortes += 1
                metricas.movimientos_podados += movimientos_restantes
            break

    return mejor_valor
