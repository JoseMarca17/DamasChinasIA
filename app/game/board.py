"""Representación de la geometría y el estado del tablero de Damas Chinas."""

from __future__ import annotations

from typing import TypeAlias

from app.game.pieces import Player

Cell: TypeAlias = tuple[int, int]

# Las filas describen una estrella de seis puntas con 121 posiciones.
ROW_COUNTS = (1, 2, 3, 4, 13, 12, 11, 10, 9, 10, 11, 12, 13, 4, 3, 2, 1)
CENTER_X = 12
STEP_DIRECTIONS = ((0, -2), (0, 2), (-1, -1), (-1, 1), (1, -1), (1, 1))


def _build_cells() -> tuple[Cell, ...]:
    """Construye las coordenadas válidas en orden de fila y columna."""
    celdas = []
    for fila, celdas_en_fila in enumerate(ROW_COUNTS):
        primera_columna = CENTER_X - (celdas_en_fila - 1)
        for posicion_en_fila in range(celdas_en_fila):
            columna = primera_columna + 2 * posicion_en_fila
            celdas.append((fila, columna))
    return tuple(celdas)


ALL_CELLS = _build_cells()
CELL_SET = frozenset(ALL_CELLS)
TOP_START_CELLS = frozenset(cell for cell in ALL_CELLS if cell[0] <= 3)
BOTTOM_START_CELLS = frozenset(cell for cell in ALL_CELLS if cell[0] >= 13)
GOAL_CELLS = {
    Player.RED: BOTTOM_START_CELLS,
    Player.BLUE: TOP_START_CELLS,
}


class Board:
    """Estado del tablero: ocupación, piezas de cada jugador y turno actual."""

    def __init__(self, configurar_posicion_inicial: bool = True) -> None:
        self.ocupantes: dict[Cell, Player] = {}
        self.fichas_por_jugador: dict[Player, set[Cell]] = {
            Player.RED: set(),
            Player.BLUE: set(),
        }
        self.jugador_actual = Player.RED

        if configurar_posicion_inicial:
            for celda in TOP_START_CELLS:
                self.place_piece(celda, Player.RED)
            for celda in BOTTOM_START_CELLS:
                self.place_piece(celda, Player.BLUE)

    @property
    def cells(self) -> tuple[Cell, ...]:
        """Todas las celdas válidas, en un orden estable."""
        return ALL_CELLS

    def copy(self) -> "Board":
        """Crea una copia independiente, útil para simulaciones de búsqueda."""
        tablero_copiado = Board(configurar_posicion_inicial=False)
        tablero_copiado.ocupantes = self.ocupantes.copy()
        tablero_copiado.fichas_por_jugador = {
            jugador: posiciones.copy()
            for jugador, posiciones in self.fichas_por_jugador.items()
        }
        tablero_copiado.jugador_actual = self.jugador_actual
        return tablero_copiado

    def piece_at(self, celda: Cell) -> Player | None:
        """Devuelve el dueño de la pieza en la celda, o None si está vacía."""
        return self.ocupantes.get(celda)

    def place_piece(self, celda: Cell, jugador: Player) -> None:
        """Coloca una pieza; se usa al configurar posiciones y en las pruebas."""
        if celda not in CELL_SET:
            raise ValueError(f"La celda {celda} no pertenece al tablero.")
        if celda in self.ocupantes:
            raise ValueError(f"La celda {celda} ya está ocupada.")
        self.ocupantes[celda] = jugador
        self.fichas_por_jugador[jugador].add(celda)

    def move_piece(self, origen: Cell, destino: Cell, jugador: Player) -> None:
        """Mueve una pieza ya validada y actualiza ambas representaciones."""
        if self.piece_at(origen) is not jugador:
            raise ValueError("La casilla de origen no contiene una pieza del jugador.")
        if destino not in CELL_SET:
            raise ValueError(f"La celda {destino} no pertenece al tablero.")
        if destino in self.ocupantes:
            raise ValueError("La casilla de destino debe estar vacía.")

        del self.ocupantes[origen]
        self.ocupantes[destino] = jugador
        self.fichas_por_jugador[jugador].remove(origen)
        self.fichas_por_jugador[jugador].add(destino)

    def goal_cells_for(self, jugador: Player) -> frozenset[Cell]:
        """Devuelve las diez celdas objetivo del jugador."""
        return GOAL_CELLS[jugador]
