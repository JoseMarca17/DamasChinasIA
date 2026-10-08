"""Motor independiente de la interfaz para Damas Chinas."""

from app.game.board import Board
from app.game.moves import Move, get_legal_moves, get_piece_destinations
from app.game.pieces import Player
from app.game.rules import apply_move, get_winner, is_game_over

__all__ = [
    "Board",
    "Move",
    "Player",
    "apply_move",
    "get_legal_moves",
    "get_piece_destinations",
    "get_winner",
    "is_game_over",
]
