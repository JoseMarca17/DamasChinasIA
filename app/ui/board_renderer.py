"""Dibuja el tablero de Damas Chinas y permite detectar clics en casillas."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, sqrt

import pygame

from app.game.board import (
    ALL_CELLS,
    BOTTOM_START_CELLS,
    CENTER_X,
    TOP_START_CELLS,
    Board,
    Cell,
)
from app.game.pieces import Player

COLOR_CONTORNO = (96, 67, 43)
COLOR_TABLERO = (155, 108, 63)
COLOR_CASILLA = (203, 157, 99)
COLOR_META_ROJA = (184, 116, 103)
COLOR_META_AZUL = (103, 139, 175)
COLOR_FICHA_ROJA = (220, 72, 65)
COLOR_FICHA_AZUL = (58, 145, 221)
COLOR_DESTINO = (73, 211, 139)
COLOR_SELECCION = (255, 213, 94)

# Puntos del borde de la estrella, usando las coordenadas del motor.
CONTORNO_ESTRELLA = (
    (0, 12), (4, 16), (4, 24), (8, 20), (12, 24), (12, 16),
    (16, 12), (12, 8), (12, 0), (8, 4), (4, 0), (4, 8),
)


@dataclass(frozen=True)
class BoardLayout:
    """Convierte las casillas del motor en posiciones de pantalla."""

    centro_x: float
    centro_y: float
    unidad_columna: float
    espacio_filas: float
    radio_clic: float

    @classmethod
    def fit_to_rect(cls, area: pygame.Rect) -> "BoardLayout":
        """Calcula el tamaño de tablero que cabe en el área indicada."""
        unidad_columna = min(
            (area.width - 64) / 24,
            (area.height - 72) / (16 * sqrt(3)),
        )
        espacio_filas = unidad_columna * sqrt(3)
        return cls(
            centro_x=area.centerx,
            centro_y=area.centery,
            unidad_columna=unidad_columna,
            espacio_filas=espacio_filas,
            radio_clic=unidad_columna * 0.86,
        )

    def cell_to_pixel(self, celda: Cell) -> tuple[int, int]:
        """Devuelve el centro de una casilla en píxeles."""
        fila, columna = celda
        x = self.centro_x + (columna - CENTER_X) * self.unidad_columna
        y = self.centro_y + (fila - 8) * self.espacio_filas
        return round(x), round(y)

    def hit_test(self, posicion: tuple[int, int]) -> Cell | None:
        """Devuelve la casilla más cercana al clic, si está suficientemente cerca."""
        raton_x, raton_y = posicion
        casilla_cercana = None
        distancia_cercana = self.radio_clic

        for celda in ALL_CELLS:
            x, y = self.cell_to_pixel(celda)
            distancia = hypot(raton_x - x, raton_y - y)
            if distancia <= distancia_cercana:
                casilla_cercana = celda
                distancia_cercana = distancia

        return casilla_cercana


def draw_board(
    pantalla: pygame.Surface,
    estado: Board,
    distribucion: BoardLayout,
    celda_seleccionada: Cell | None = None,
    destinos_legales: set[Cell] | None = None,
    ultimo_movimiento: tuple[Cell, Cell] | None = None,
) -> None:
    """Dibuja la estrella, sus casillas, las piezas y las pistas del turno."""
    if destinos_legales is None:
        destinos_legales = set()

    puntos = [distribucion.cell_to_pixel(celda) for celda in CONTORNO_ESTRELLA]
    pygame.draw.polygon(pantalla, COLOR_CONTORNO, puntos)

    puntos_internos = [
        (
            round(distribucion.centro_x + (columna - CENTER_X) * distribucion.unidad_columna * 0.97),
            round(distribucion.centro_y + (fila - 8) * distribucion.espacio_filas * 0.97),
        )
        for fila, columna in CONTORNO_ESTRELLA
    ]
    pygame.draw.polygon(pantalla, COLOR_TABLERO, puntos_internos)

    if ultimo_movimiento is not None:
        origen = distribucion.cell_to_pixel(ultimo_movimiento[0])
        destino = distribucion.cell_to_pixel(ultimo_movimiento[1])
        pygame.draw.line(pantalla, (239, 243, 249), origen, destino, 3)

    for celda in ALL_CELLS:
        centro = distribucion.cell_to_pixel(celda)
        if celda in TOP_START_CELLS:
            color_casilla = COLOR_META_ROJA
        elif celda in BOTTOM_START_CELLS:
            color_casilla = COLOR_META_AZUL
        else:
            color_casilla = COLOR_CASILLA

        radio = max(7, round(distribucion.unidad_columna * 0.67))
        pygame.draw.circle(pantalla, (91, 62, 39), centro, radio + 2)
        pygame.draw.circle(pantalla, color_casilla, centro, radio)

        if celda in destinos_legales:
            pygame.draw.circle(pantalla, COLOR_DESTINO, centro, radio + 5, 3)
            pygame.draw.circle(pantalla, COLOR_DESTINO, centro, 4)
        if celda == celda_seleccionada:
            pygame.draw.circle(pantalla, COLOR_SELECCION, centro, radio + 8, 3)

    radio_ficha = max(8, round(distribucion.unidad_columna * 0.57))
    colores = ((Player.RED, COLOR_FICHA_ROJA), (Player.BLUE, COLOR_FICHA_AZUL))
    for jugador, color in colores:
        for celda in sorted(estado.fichas_por_jugador[jugador]):
            centro = distribucion.cell_to_pixel(celda)
            sombra = (centro[0] + 2, centro[1] + 3)
            pygame.draw.circle(pantalla, (55, 42, 35), sombra, radio_ficha + 1)
            pygame.draw.circle(pantalla, color, centro, radio_ficha)
            pygame.draw.circle(pantalla, (255, 255, 255), centro, radio_ficha, 2)
