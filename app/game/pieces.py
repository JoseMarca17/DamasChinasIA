"""Definición de los jugadores y de sus metas."""

from enum import Enum


class Player(Enum):
    """Los dos bandos; ROJO es MAX y AZUL es MIN en los ejemplos de IA."""

    RED = "rojo"
    BLUE = "azul"

    @property
    def oponente(self) -> "Player":
        """Devuelve el jugador contrario."""
        if self is Player.RED:
            return Player.BLUE
        return Player.RED

    @property
    def nombre_visible(self) -> str:
        """Nombre legible para la interfaz y las explicaciones."""
        return self.value.upper()


MAX_PLAYER = Player.RED
MIN_PLAYER = Player.BLUE
