"""Agente que compara las jugadas usando búsqueda o evaluación heurística."""

from dataclasses import dataclass
from math import inf

from app.ai.alphabeta import alphabeta
from app.ai.evaluation import evaluar_estado, normalizar_heuristica
from app.ai.minimax import SearchMetrics, minimax
from app.game.board import Board
from app.game.moves import Move, get_legal_moves
from app.game.pieces import MAX_PLAYER
from app.game.rules import apply_move, get_winner

MINIMAX_ALGORITHM = "minimax"
ALPHABETA_ALGORITHM = "alphabeta"
GREEDY_ALGORITHM = "greedy"
SUPPORTED_ALGORITHMS = (MINIMAX_ALGORITHM, ALPHABETA_ALGORITHM, GREEDY_ALGORITHM)


@dataclass(frozen=True)
class AgentDecision:
    """Jugada elegida, valor obtenido y datos que explican el análisis."""

    movimiento: Move
    valor: int | float
    metricas: SearchMetrics
    algoritmo: str
    heuristica: str
    profundidad: int


class AdversarialAgent:
    """Elige una jugada buscando respuestas o evaluando solo el siguiente estado."""

    def __init__(
        self,
        algoritmo: str = ALPHABETA_ALGORITHM,
        profundidad: int = 2,
        heuristica: str = "E1",
    ) -> None:
        if algoritmo not in SUPPORTED_ALGORITHMS:
            nombres_disponibles = ", ".join(SUPPORTED_ALGORITHMS)
            raise ValueError(f"Algoritmo no reconocido. Usa: {nombres_disponibles}.")
        if profundidad < 1:
            raise ValueError("La profundidad del agente debe ser al menos 1.")

        self.algoritmo = algoritmo
        self.profundidad = profundidad
        self.heuristica = normalizar_heuristica(heuristica)

    def choose_move(self, estado: Board) -> AgentDecision | None:
        """Devuelve la mejor jugada sin cambiar el tablero recibido.

        El algoritmo voraz mira solo el resultado inmediato de cada jugada.
        Minimax y Alfa-Beta también analizan las respuestas siguientes.
        """
        if get_winner(estado) is not None:
            return None

        movimientos_posibles = get_legal_moves(estado, estado.jugador_actual)
        if not movimientos_posibles:
            return None

        jugador_actual = estado.jugador_actual
        if self.algoritmo == MINIMAX_ALGORITHM:
            buscar = minimax
        elif self.algoritmo == ALPHABETA_ALGORITHM:
            buscar = alphabeta
        else:
            buscar = None

        metricas_totales = SearchMetrics(nodos_visitados=1)
        mejor_movimiento = None
        mejor_valor = -inf if jugador_actual is MAX_PLAYER else inf

        for movimiento in movimientos_posibles:
            estado_hijo = estado.copy()
            apply_move(estado_hijo, movimiento)
            metricas_de_rama = SearchMetrics()

            if buscar is None:
                # Voraz: aplicar una jugada y medir su estado con la heurística.
                valor_movimiento = evaluar_estado(estado_hijo, self.heuristica)
                metricas_de_rama.nodos_visitados = 1
                metricas_de_rama.hojas_evaluadas = 1
            else:
                valor_movimiento = buscar(
                    estado_hijo,
                    self.profundidad - 1,
                    metricas_de_rama,
                    heuristica=self.heuristica,
                )

            self._sumar_metricas(metricas_totales, metricas_de_rama)
            if jugador_actual is MAX_PLAYER:
                es_mejor_movimiento = valor_movimiento > mejor_valor
            else:
                es_mejor_movimiento = valor_movimiento < mejor_valor

            if mejor_movimiento is None or es_mejor_movimiento:
                mejor_movimiento = movimiento
                mejor_valor = valor_movimiento

        return AgentDecision(
            movimiento=mejor_movimiento,
            valor=mejor_valor,
            metricas=metricas_totales,
            algoritmo=self.algoritmo,
            heuristica=self.heuristica,
            profundidad=1 if self.algoritmo == GREEDY_ALGORITHM else self.profundidad,
        )

    @staticmethod
    def _sumar_metricas(totales: SearchMetrics, rama: SearchMetrics) -> None:
        """Suma las métricas de cada alternativa de la raíz."""
        totales.nodos_visitados += rama.nodos_visitados
        totales.hojas_evaluadas += rama.hojas_evaluadas
        totales.cortes += rama.cortes
        totales.movimientos_podados += rama.movimientos_podados
