"""Control de selección, turnos humanos y aplicación de jugadas de la IA."""

from app.ai.agent import (
    ALPHABETA_ALGORITHM,
    GREEDY_ALGORITHM,
    MINIMAX_ALGORITHM,
    AgentDecision,
)
from app.game.board import CENTER_X, ROW_COUNTS, Board, Cell
from app.game.moves import Move, get_piece_destinations
from app.game.pieces import Player
from app.game.rules import apply_move, get_winner

HUMAN_VS_HUMAN = "human_vs_human"
HUMAN_VS_AI = "human_vs_ai"
AI_VS_AI = "ai_vs_ai"
GAME_MODES = (HUMAN_VS_AI, HUMAN_VS_HUMAN, AI_VS_AI)
HUMAN_PLAYER = Player.BLUE
AI_PLAYER = Player.RED


def format_cell_label(cell: Cell) -> str:
    """Convierte una coordenada interna en fila y posición legibles."""
    fila, columna = cell
    primera_columna = CENTER_X - (ROW_COUNTS[fila] - 1)
    posicion_en_fila = (columna - primera_columna) // 2 + 1
    return f"F{fila + 1}·C{posicion_en_fila}"


class GameControls:
    """Mantiene selección y turnos; reglas y movimientos siguen en el motor."""

    def __init__(self, modo: str = HUMAN_VS_HUMAN) -> None:
        if modo not in GAME_MODES:
            raise ValueError(f"Modo de juego no reconocido: {modo}")
        self.modo = modo
        self.reset_game()

    def reset_game(self) -> None:
        """Empieza una partida nueva sin cambiar el modo seleccionado."""
        self.tablero = Board()
        self.celda_seleccionada: Cell | None = None
        self.destinos_legales: set[Cell] = set()
        self.ultimo_movimiento: tuple[Cell, Cell] | None = None

        if self.modo == HUMAN_VS_AI:
            self.mensaje = "Tú juegas AZUL. ROJO es la IA y empieza la partida."
        elif self.modo == AI_VS_AI:
            self.mensaje = "IA vs IA: pulsa Siguiente para avanzar una jugada o activa Automático."
        else:
            self.mensaje = "ROJO comienza. Selecciona una ficha roja para ver sus destinos."

    def set_mode(self, modo: str) -> None:
        """Cambia el modo y comienza una partida nueva."""
        if modo not in GAME_MODES:
            raise ValueError(f"Modo de juego no reconocido: {modo}")
        self.modo = modo
        self.reset_game()

    @property
    def winner(self) -> Player | None:
        """Ganador actual, si las diez piezas de un jugador llegaron a su meta."""
        return get_winner(self.tablero)

    @property
    def is_ai_turn(self) -> bool:
        """Indica si debe jugar la IA en el modo actual."""
        if self.winner is not None:
            return False
        if self.modo == AI_VS_AI:
            return True
        return self.modo == HUMAN_VS_AI and self.tablero.jugador_actual is AI_PLAYER

    def handle_board_click(self, cell: Cell | None) -> None:
        """Selecciona una pieza o ejecuta el destino legal que se haya pulsado."""
        if cell is None:
            return
        if self.winner is not None:
            self.mensaje = "La partida terminó. Pulsa Nueva partida para volver a jugar."
            return
        if self.is_ai_turn:
            self.mensaje = "Es turno de la IA. Avanza con Siguiente o activa el modo automático."
            return

        jugador_seleccionado = self.tablero.piece_at(cell)
        if self.celda_seleccionada is not None and cell in self.destinos_legales:
            self._apply_move(self.celda_seleccionada, cell)
            return

        if jugador_seleccionado is self.tablero.jugador_actual:
            if cell == self.celda_seleccionada:
                self.celda_seleccionada = None
                self.destinos_legales.clear()
                self.mensaje = "Selección cancelada. Elige una ficha del jugador actual."
                return

            self.celda_seleccionada = cell
            self.destinos_legales = set(
                get_piece_destinations(self.tablero, cell, self.tablero.jugador_actual)
            )
            if self.destinos_legales:
                self.mensaje = (
                    f"Ficha {self.tablero.jugador_actual.nombre_visible} seleccionada. "
                    "Elige uno de los destinos verdes."
                )
            else:
                self.mensaje = "Esa ficha no tiene destinos legales en este turno."
            return

        if self.celda_seleccionada is None:
            self.mensaje = f"Selecciona una ficha {self.tablero.jugador_actual.nombre_visible.lower()}."
        else:
            self.mensaje = "Destino no válido. Elige una de las celdas marcadas en verde."

    def finish_ai_turn(self, decision: AgentDecision | None) -> None:
        """Aplica la respuesta del agente y prepara el siguiente turno."""
        if not self.is_ai_turn:
            return

        if decision is None:
            self.tablero.jugador_actual = self.tablero.jugador_actual.oponente
            self.mensaje = "La IA no encontró jugadas legales. Se pasa el turno."
            return

        movimiento = decision.movimiento
        self._apply_move(movimiento.origen, movimiento.destino)
        if self.winner is None:
            metricas = decision.metricas
            nombres_algoritmo = {
                ALPHABETA_ALGORITHM: "Alfa-Beta",
                MINIMAX_ALGORITHM: "Minimax",
                GREEDY_ALGORITHM: "Heurística voraz",
            }
            nombre_algoritmo = nombres_algoritmo[decision.algoritmo]
            self.mensaje = (
                f"{nombre_algoritmo} con {decision.heuristica} eligió "
                f"{format_cell_label(movimiento.origen)} → "
                f"{format_cell_label(movimiento.destino)}; valor {decision.valor}, "
                f"{metricas.nodos_visitados} nodos explorados."
            )

    def _apply_move(self, origen: Cell, destino: Cell) -> None:
        """Entrega la validación final al motor y actualiza la presentación."""
        jugador_actual = self.tablero.jugador_actual
        apply_move(self.tablero, Move(origen, destino))
        self.ultimo_movimiento = (origen, destino)
        self.celda_seleccionada = None
        self.destinos_legales.clear()

        ganador = self.winner
        if ganador is not None:
            self.mensaje = f"¡{ganador.nombre_visible} llevó sus diez fichas a la zona objetivo!"
        elif self.modo == HUMAN_VS_AI and jugador_actual is AI_PLAYER:
            self.mensaje = "La IA movió una ficha. Ahora juega AZUL."
        elif self.modo == HUMAN_VS_AI:
            self.mensaje = "AZUL movió una ficha. La IA está preparando su respuesta."
        elif self.modo == AI_VS_AI:
            self.mensaje = f"{jugador_actual.nombre_visible} movió una ficha. La otra IA juega ahora."
        else:
            self.mensaje = (
                f"{jugador_actual.nombre_visible} movió una ficha. "
                f"Ahora juega {self.tablero.jugador_actual.nombre_visible}."
            )
