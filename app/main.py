"""Punto de entrada de la aplicación de Damas Chinas."""


def main() -> None:
    """Inicia la partida Pygame sin importar la interfaz durante las pruebas."""
    from app.ui.pygame_app import run

    run()


if __name__ == "__main__":
    main()
