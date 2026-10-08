"""Generación de pasos y saltos encadenados para una pieza."""

from __future__ import annotations

from dataclasses import dataclass

from app.game.board import (
    CELL_SET,
    STEP_DIRECTIONS,
    Board,
    Cell,
)
from app.game.pieces import Player


@dataclass(frozen=True)
class Move:
    """Movimiento de una pieza desde una celda hasta otra."""

    origen: Cell
    destino: Cell


def _jump_options(celda: Cell) -> tuple[tuple[Cell, Cell], ...]:
    """Para cada dirección devuelve (pieza_intermedia, casilla_de_aterrizaje)."""
    fila, columna = celda
    opciones = []
    for cambio_fila, cambio_columna in STEP_DIRECTIONS:
        celda_intermedia = (fila + cambio_fila, columna + cambio_columna)
        celda_de_salto = (fila + 2 * cambio_fila, columna + 2 * cambio_columna)
        if celda_intermedia in CELL_SET and celda_de_salto in CELL_SET:
            opciones.append((celda_intermedia, celda_de_salto))
    return tuple(opciones)


JUMP_OPTIONS = {celda: _jump_options(celda) for celda in CELL_SET}


def get_piece_destinations(tablero: Board, origen: Cell, jugador: Player) -> list[Cell]:
    """Genera casillas alcanzables por paso simple o una cadena de saltos.

    Cada salto debe pasar sobre una pieza propia o rival y aterrizar en una
    casilla vacía. En un turno se elige un paso simple o una secuencia de saltos.
    """
    if tablero.piece_at(origen) is not jugador:
        return []

    destinos = set()

    # Los seis vecinos vacíos son movimientos simples legales.
    fila, columna = origen
    for cambio_fila, cambio_columna in STEP_DIRECTIONS:
        vecina = (fila + cambio_fila, columna + cambio_columna)
        if vecina in CELL_SET and tablero.piece_at(vecina) is None:
            destinos.add(vecina)

    # Se libera el origen durante la búsqueda: la pieza ya salió de esa celda.
    # Las celdas visitadas evitan ciclos y que el origen aparezca como destino.
    visitadas = {origen}
    celdas_por_explorar = [origen]
    while celdas_por_explorar:
        celda_actual = celdas_por_explorar.pop()
        for celda_intermedia, celda_de_salto in JUMP_OPTIONS[celda_actual]:
            if tablero.piece_at(celda_intermedia) is None:
                continue
            if tablero.piece_at(celda_de_salto) is not None or celda_de_salto in visitadas:
                continue
            visitadas.add(celda_de_salto)
            destinos.add(celda_de_salto)
            celdas_por_explorar.append(celda_de_salto)

    return sorted(destinos)


def get_legal_moves(tablero: Board, jugador: Player) -> list[Move]:
    """Devuelve todos los movimientos de todas las piezas del jugador."""
    movimientos_legales = []
    for origen in sorted(tablero.fichas_por_jugador[jugador]):
        for destino in get_piece_destinations(tablero, origen, jugador):
            movimientos_legales.append(Move(origen, destino))
    return movimientos_legales
