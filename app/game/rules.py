"""Reglas de aplicación de jugadas y detección de victoria."""

from app.game.board import Board, TOP_START_CELLS
from app.game.moves import Move, get_legal_moves
from app.game.pieces import Player


def apply_move(tablero: Board, movimiento: Move) -> None:
    """Valida y aplica la jugada del turno actual, luego cambia el turno.

    La función modifica el estado recibido. Para explorar una alternativa sin
    afectar la partida, primero se puede crear una copia con ``tablero.copy()``.
    """
    jugador_actual = tablero.jugador_actual
    if movimiento not in get_legal_moves(tablero, jugador_actual):
        raise ValueError(f"Movimiento ilegal para {jugador_actual.nombre_visible}: {movimiento}")

    tablero.move_piece(movimiento.origen, movimiento.destino, jugador_actual)
    if get_winner(tablero) is None:
        tablero.jugador_actual = jugador_actual.oponente


def get_winner(tablero: Board) -> Player | None:
    """Devuelve el jugador ganador cuando todas sus piezas están en su meta."""
    for jugador in Player:
        fichas_del_jugador = tablero.fichas_por_jugador[jugador]
        if (
            len(fichas_del_jugador) == len(TOP_START_CELLS)
            and fichas_del_jugador.issubset(tablero.goal_cells_for(jugador))
        ):
            return jugador
    return None


def is_game_over(tablero: Board) -> bool:
    """Indica si la partida ya tiene un ganador."""
    return get_winner(tablero) is not None
