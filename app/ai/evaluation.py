"""Tres evaluaciones explicables del avance de las piezas."""

from collections import deque

from app.game.board import ALL_CELLS, CELL_SET, CENTER_X, GOAL_CELLS, STEP_DIRECTIONS, Board, Cell
from app.game.pieces import MAX_PLAYER, MIN_PLAYER, Player

HEURISTICAS_DISPONIBLES = ("E1", "E2", "E3")


def _obtener_vecinas(celda: Cell) -> list[Cell]:
    """Devuelve las casillas a las que se llega con un paso sencillo."""
    fila, columna = celda
    vecinas = []

    for cambio_fila, cambio_columna in STEP_DIRECTIONS:
        casilla_vecina = (fila + cambio_fila, columna + cambio_columna)
        if casilla_vecina in CELL_SET:
            vecinas.append(casilla_vecina)

    return vecinas


def _calcular_distancias_a_meta(jugador: Player) -> dict[Cell, int]:
    """Calcula la distancia en pasos desde cada casilla hasta la meta más cercana."""
    distancias = {}
    casillas_por_visitar = deque()

    for casilla_meta in GOAL_CELLS[jugador]:
        distancias[casilla_meta] = 0
        casillas_por_visitar.append(casilla_meta)

    while casillas_por_visitar:
        casilla_actual = casillas_por_visitar.popleft()
        distancia_siguiente = distancias[casilla_actual] + 1

        for casilla_vecina in _obtener_vecinas(casilla_actual):
            if casilla_vecina not in distancias:
                distancias[casilla_vecina] = distancia_siguiente
                casillas_por_visitar.append(casilla_vecina)

    if len(distancias) != len(ALL_CELLS):
        raise ValueError("No se pudieron calcular las distancias de todas las casillas.")

    return distancias


# La distancia de una casilla depende de la forma del tablero, no de las piezas.
DISTANCIAS_A_META = {
    MAX_PLAYER: _calcular_distancias_a_meta(MAX_PLAYER),
    MIN_PLAYER: _calcular_distancias_a_meta(MIN_PLAYER),
}


def normalizar_heuristica(heuristica: str) -> str:
    """Comprueba el nombre de la heurística y acepta e1, e2 o e3 en minúsculas."""
    nombre = heuristica.upper()
    if nombre not in HEURISTICAS_DISPONIBLES:
        opciones = ", ".join(HEURISTICAS_DISPONIBLES)
        raise ValueError(f"Heurística no reconocida. Usa: {opciones}.")
    return nombre


def calcular_distancia_ficha(celda: Cell, jugador: Player) -> int:
    """Devuelve la distancia de una ficha a la zona objetivo de su jugador."""
    return DISTANCIAS_A_META[jugador][celda]


def calcular_distancia_total(estado: Board, jugador: Player) -> int:
    """Suma las distancias de todas las fichas del jugador a su meta."""
    distancia_total = 0

    for celda in estado.fichas_por_jugador[jugador]:
        distancia_total += calcular_distancia_ficha(celda, jugador)

    return distancia_total


def calcular_penalizacion_eje(estado: Board) -> int:
    """Compara cuánto se alejan MAX y MIN del eje central vertical.

    Se usa la columna existente del tablero y su centro ``CENTER_X``. La
    penalización es la desviación total de MAX menos la de MIN, para que ambas
    partes se comparen con la misma escala.
    """
    desviacion_max = 0
    desviacion_min = 0

    for fila, columna in estado.fichas_por_jugador[MAX_PLAYER]:
        desviacion_max += abs(columna - CENTER_X)

    for fila, columna in estado.fichas_por_jugador[MIN_PLAYER]:
        desviacion_min += abs(columna - CENTER_X)

    return desviacion_max - desviacion_min


def calcular_distancia_ficha_atrasada(estado: Board) -> int:
    """Devuelve la distancia a meta de la ficha de MAX que está más atrás."""
    distancia_mayor = 0

    for celda in estado.fichas_por_jugador[MAX_PLAYER]:
        distancia = calcular_distancia_ficha(celda, MAX_PLAYER)
        if distancia > distancia_mayor:
            distancia_mayor = distancia

    return distancia_mayor


def evaluar_e1(estado: Board) -> int:
    """E1 mide el progreso total de MIN menos el progreso total de MAX."""
    distancia_max = calcular_distancia_total(estado, MAX_PLAYER)
    distancia_min = calcular_distancia_total(estado, MIN_PLAYER)
    return distancia_min - distancia_max


def evaluar_e2(estado: Board) -> float:
    """E2 usa E1 y resta media penalización por alejarse del eje central."""
    return evaluar_e1(estado) - 0.5 * calcular_penalizacion_eje(estado)


def evaluar_e3(estado: Board) -> int:
    """E3 usa E1 y penaliza que la ficha más atrasada de MAX quede rezagada."""
    distancia_atrasada = calcular_distancia_ficha_atrasada(estado)
    return evaluar_e1(estado) - 2 * distancia_atrasada


def evaluar_estado(estado: Board, heuristica: str = "E1") -> int | float:
    """Evalúa el estado con E1, E2 o E3; los valores positivos favorecen a MAX."""
    nombre_heuristica = normalizar_heuristica(heuristica)

    if nombre_heuristica == "E1":
        return evaluar_e1(estado)
    if nombre_heuristica == "E2":
        return evaluar_e2(estado)
    return evaluar_e3(estado)
