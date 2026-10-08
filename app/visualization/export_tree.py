"""Exporta ejemplos de árboles didácticos al formato JSON del visualizador."""

import json
from pathlib import Path
from typing import Mapping

REQUIRED_EXAMPLE_FIELDS = (
    "algorithm",
    "title",
    "root_player",
    "board_state",
    "children",
    "expected_value",
    "best_move",
)


def export_tree_example(example: Mapping[str, object], destination: str | Path) -> Path:
    """Valida y escribe un ejemplo JSON compatible con el visualizador web.

    El árbol debe ser pequeño y preparado para exposición; esta función no
    construye el árbol de búsqueda completo de una partida real.
    """
    missing_fields = [
        field_name
        for field_name in REQUIRED_EXAMPLE_FIELDS
        if field_name not in example
    ]
    if missing_fields:
        missing_names = ", ".join(missing_fields)
        raise ValueError(f"Faltan campos requeridos para el ejemplo: {missing_names}.")

    output_path = Path(destination)
    json_content = json.dumps(dict(example), ensure_ascii=False, indent=2)
    output_path.write_text(f"{json_content}\n", encoding="utf-8")
    return output_path
