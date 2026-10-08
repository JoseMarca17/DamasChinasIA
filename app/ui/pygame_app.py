"""Pantallas y partida de Damas Chinas con Pygame."""

from __future__ import annotations

import queue
import threading
import time

import pygame

from app.ai.agent import (
    ALPHABETA_ALGORITHM,
    GREEDY_ALGORITHM,
    MINIMAX_ALGORITHM,
    AdversarialAgent,
)
from app.ai.evaluation import HEURISTICAS_DISPONIBLES
from app.game.board import Board
from app.ui.board_renderer import BoardLayout, draw_board
from app.ui.controls import AI_VS_AI, HUMAN_VS_AI, HUMAN_VS_HUMAN, GameControls

ANCHO_VENTANA = 1180
ALTO_VENTANA = 800
ANCHO_TABLERO = 790

FONDO = (13, 32, 25)
PANEL = (24, 52, 39)
PANEL_CLARO = (34, 69, 49)
VERDE_OSCURO = (23, 49, 36)
VERDE_MEDIO = (54, 99, 62)
VERDE_BORDE = (91, 137, 82)
VERDE_RESALTE = (91, 143, 86)
AMARILLO = (240, 204, 105)
TEXTO = (244, 242, 213)
TEXTO_SUAVE = (183, 207, 178)

CODIGO_ALGORITMOS = {
    GREEDY_ALGORITHM: [
        "jugador = estado.jugador_actual",
        "movimientos = get_legal_moves(estado, jugador)",
        "for movimiento in movimientos:",
        "    hijo = estado.copy()",
        "    apply_move(hijo, movimiento)",
        "    valor = evaluar_estado(hijo, heuristica)",
        "MAX: mayor valor; MIN: menor",
    ],
    MINIMAX_ALGORITHM: [
        "if profundidad == 0:",
        "    return evaluar_estado(estado, heuristica)",
        "jugador = estado.jugador_actual",
        "movimientos = get_legal_moves(estado, jugador)",
        "for movimiento in movimientos:",
        "    valor = minimax(estado_hijo, profundidad - 1)",
        "MAX: mayor valor; MIN: menor",
    ],
    ALPHABETA_ALGORITHM: [
        "if profundidad == 0:",
        "    return evaluar_estado(estado, heuristica)",
        "jugador = estado.jugador_actual",
        "movimientos = get_legal_moves(estado, jugador)",
        "for movimiento in movimientos:",
        "    actualizar mejor_valor, alpha, beta",
        "    if beta <= alpha: break",
    ],
}

DESCRIPCIONES_ALGORITMOS = {
    GREEDY_ALGORITHM: "Prueba una jugada; no anticipa la respuesta rival.",
    MINIMAX_ALGORITHM: "Explora respuestas futuras hasta la profundidad elegida.",
    ALPHABETA_ALGORITHM: "Minimax que poda ramas que no cambian la decisión.",
}

NOMBRES_HEURISTICAS = {
    "E1": "Progreso hacia el objetivo",
    "E2": "Alineación con el eje central",
    "E3": "Evitar una ficha rezagada",
}

DESCRIPCIONES_HEURISTICAS = {
    "E1": "Compara las distancias totales de MAX y MIN a sus objetivos.",
    "E2": "Compara cuánto se alejan MAX y MIN del eje central; resta la mitad.",
    "E3": "A E1 le resta dos veces la distancia de la ficha MAX más atrasada.",
}

CODIGO_TURNO_HUMANO = [
    "leer casilla seleccionada",
    "destinos = movimientos_legales(ficha)",
    "si el destino es legal:",
    "    aplicar_movimiento(estado)",
    "    cambiar_turno(jugador)",
]


def _buscar_jugada_en_segundo_plano(
    estado: Board,
    algoritmo: str,
    profundidad: int,
    heuristica: str,
    identificador: int,
    cola_resultados: queue.Queue,
) -> None:
    """Calcula una jugada sin detener la ventana mientras piensa la IA."""
    try:
        agente = AdversarialAgent(
            algoritmo=algoritmo,
            profundidad=profundidad,
            heuristica=heuristica,
        )
        decision = agente.choose_move(estado)
        cola_resultados.put((identificador, decision, None))
    except Exception as error:
        cola_resultados.put((identificador, None, str(error)))


def _dibujar_texto(
    pantalla: pygame.Surface,
    fuente: pygame.font.Font,
    texto: str,
    color: tuple[int, int, int],
    posicion: tuple[int, int],
) -> None:
    pantalla.blit(fuente.render(texto, True, color), posicion)


def _dibujar_texto_centrado(
    pantalla: pygame.Surface,
    fuente: pygame.font.Font,
    texto: str,
    color: tuple[int, int, int],
    centro: tuple[int, int],
) -> None:
    imagen = fuente.render(texto, True, color)
    pantalla.blit(imagen, imagen.get_rect(center=centro))


def _dibujar_boton(
    pantalla: pygame.Surface,
    rectangulo: pygame.Rect,
    texto: str,
    fuente: pygame.font.Font,
    raton: tuple[int, int],
    seleccionado: bool = False,
) -> None:
    color = VERDE_MEDIO if seleccionado else VERDE_OSCURO
    color_borde = AMARILLO if seleccionado else VERDE_BORDE
    if rectangulo.collidepoint(raton):
        color = VERDE_RESALTE
        color_borde = AMARILLO
    pygame.draw.rect(pantalla, color, rectangulo, border_radius=10)
    pygame.draw.rect(pantalla, color_borde, rectangulo, 2, border_radius=10)
    _dibujar_texto_centrado(pantalla, fuente, texto, TEXTO, rectangulo.center)


def _dibujar_fondo_retro(pantalla: pygame.Surface) -> None:
    """Agrega una cuadrícula tenue para dar a los menús un aire retro."""
    pantalla.fill(FONDO)
    for x in range(0, ANCHO_VENTANA, 48):
        pygame.draw.line(pantalla, (19, 41, 31), (x, 0), (x, ALTO_VENTANA), 1)
    for y in range(0, ALTO_VENTANA, 48):
        pygame.draw.line(pantalla, (19, 41, 31), (0, y), (ANCHO_VENTANA, y), 1)

    pygame.draw.rect(pantalla, (17, 39, 29), (0, 704, ANCHO_VENTANA, 96))
    for x in range(0, ANCHO_VENTANA, 48):
        pygame.draw.rect(pantalla, (22, 47, 34), (x, 704, 24, 24))


def _dibujar_marco_retro(pantalla: pygame.Surface, rectangulo: pygame.Rect) -> None:
    """Dibuja un marco doble como una tarjeta de juego retro."""
    pygame.draw.rect(pantalla, VERDE_OSCURO, rectangulo, border_radius=14)
    pygame.draw.rect(pantalla, VERDE_BORDE, rectangulo, 3, border_radius=14)
    marco_interno = rectangulo.inflate(-14, -14)
    pygame.draw.rect(pantalla, PANEL_CLARO, marco_interno, 1, border_radius=10)


def _dibujar_fichas_decorativas(
    pantalla: pygame.Surface,
    centro: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    """Dibuja unas fichas decorativas en forma de pequeño triángulo."""
    centro_x, centro_y = centro
    posiciones = ((0, 0), (-16, 23), (16, 23), (-32, 46), (0, 46), (32, 46))
    for cambio_x, cambio_y in posiciones:
        pygame.draw.circle(pantalla, (13, 32, 25), (centro_x + cambio_x + 2, centro_y + cambio_y + 3), 8)
        pygame.draw.circle(pantalla, color, (centro_x + cambio_x, centro_y + cambio_y), 8)
        pygame.draw.circle(pantalla, TEXTO, (centro_x + cambio_x, centro_y + cambio_y), 8, 1)


def _dibujar_texto_en_caja(
    pantalla: pygame.Surface,
    texto: str,
    fuente: pygame.font.Font,
    color: tuple[int, int, int],
    caja: pygame.Rect,
) -> None:
    """Divide un mensaje en líneas para que quepa en el panel."""
    linea_actual = ""
    lineas = []

    for palabra in texto.split():
        linea_candidata = f"{linea_actual} {palabra}".strip()
        if linea_actual and fuente.size(linea_candidata)[0] > caja.width:
            lineas.append(linea_actual)
            linea_actual = palabra
        else:
            linea_actual = linea_candidata

    if linea_actual:
        lineas.append(linea_actual)

    for numero, linea in enumerate(lineas):
        y = caja.y + numero * fuente.get_linesize()
        if y + fuente.get_linesize() > caja.bottom:
            break
        _dibujar_texto(pantalla, fuente, linea, color, (caja.x, y))


def _dibujar_pantalla_inicio(
    pantalla: pygame.Surface,
    raton: tuple[int, int],
    fuentes: dict[str, pygame.font.Font],
) -> pygame.Rect:
    _dibujar_fondo_retro(pantalla)
    marco = pygame.Rect(150, 145, 880, 500)
    _dibujar_marco_retro(pantalla, marco)
    _dibujar_fichas_decorativas(pantalla, (245, 300), AMARILLO)
    _dibujar_fichas_decorativas(pantalla, (935, 300), VERDE_RESALTE)

    titulo_sombra = fuentes["titulo"].render("DAMAS CHINAS", True, (16, 38, 28))
    pantalla.blit(titulo_sombra, titulo_sombra.get_rect(center=(594, 286)))
    _dibujar_texto_centrado(
        pantalla,
        fuentes["titulo"],
        "DAMAS CHINAS",
        AMARILLO,
        (590, 280),
    )
    _dibujar_texto_centrado(
        pantalla,
        fuentes["cuerpo"],
        "Juega y descubre cómo piensa una IA",
        TEXTO_SUAVE,
        (590, 365),
    )

    boton_jugar = pygame.Rect(450, 455, 280, 72)
    _dibujar_boton(pantalla, boton_jugar, ">  JUGAR  <", fuentes["boton"], raton, True)
    creditos = fuentes["pequena"].render(
        "Desarrollado por Ángeles Gutiérrez, Paola Mancilla y Jose Marca",
        True,
        (112, 145, 115),
    )
    pantalla.blit(creditos, (ANCHO_VENTANA - creditos.get_width() - 18, ALTO_VENTANA - 28))
    return boton_jugar


def _dibujar_pantalla_modos(
    pantalla: pygame.Surface,
    raton: tuple[int, int],
    fuentes: dict[str, pygame.font.Font],
) -> dict[str, pygame.Rect]:
    _dibujar_fondo_retro(pantalla)
    _dibujar_marco_retro(pantalla, pygame.Rect(175, 110, 830, 560))
    _dibujar_texto_centrado(pantalla, fuentes["titulo_pantalla"], "ELIGE TU MODO", AMARILLO, (590, 155))
    _dibujar_texto_centrado(
        pantalla,
        fuentes["cuerpo"],
        "Selecciona una forma de jugar",
        TEXTO_SUAVE,
        (590, 202),
    )

    botones = {
        HUMAN_VS_HUMAN: pygame.Rect(270, 260, 640, 96),
        HUMAN_VS_AI: pygame.Rect(270, 380, 640, 96),
        AI_VS_AI: pygame.Rect(270, 500, 640, 96),
        "volver": pygame.Rect(30, 735, 150, 44),
    }
    etiquetas = {
        HUMAN_VS_HUMAN: ("01", "HUMANO VS HUMANO", "Dos jugadores · turnos alternados"),
        HUMAN_VS_AI: ("02", "HUMANO VS IA", "Juega contra el agente"),
        AI_VS_AI: ("03", "IA VS IA", "Observa las decisiones de los agentes"),
    }
    for modo, (numero, titulo, detalle) in etiquetas.items():
        tarjeta = botones[modo]
        color_tarjeta = VERDE_MEDIO if tarjeta.collidepoint(raton) else VERDE_OSCURO
        pygame.draw.rect(pantalla, color_tarjeta, tarjeta, border_radius=12)
        pygame.draw.rect(
            pantalla,
            AMARILLO if tarjeta.collidepoint(raton) else VERDE_BORDE,
            tarjeta,
            2,
            border_radius=12,
        )
        _dibujar_texto(pantalla, fuentes["titulo_panel"], numero, AMARILLO, (tarjeta.x + 22, tarjeta.y + 25))
        _dibujar_texto(pantalla, fuentes["boton"], titulo, TEXTO, (tarjeta.x + 92, tarjeta.y + 17))
        _dibujar_texto(pantalla, fuentes["pequena"], detalle, TEXTO_SUAVE, (tarjeta.x + 92, tarjeta.y + 57))
    _dibujar_boton(pantalla, botones["volver"], "Volver", fuentes["normal"], raton)
    return botones


def _dibujar_pantalla_algoritmo(
    pantalla: pygame.Surface,
    raton: tuple[int, int],
    fuentes: dict[str, pygame.font.Font],
    algoritmo: str,
    profundidad: int,
    heuristica: str,
    heuristicas_abiertas: bool,
    profundidad_abierta: bool,
) -> tuple[dict[str, pygame.Rect], pygame.Rect, tuple[pygame.Rect, ...], pygame.Rect, tuple[pygame.Rect, ...]]:
    _dibujar_fondo_retro(pantalla)
    _dibujar_marco_retro(pantalla, pygame.Rect(28, 90, 1124, 596))
    _dibujar_texto_centrado(pantalla, fuentes["titulo_pantalla"], "ELIGE TU ESTRATEGIA", AMARILLO, (590, 125))

    nombres = {
        GREEDY_ALGORITHM: "Heurística voraz",
        MINIMAX_ALGORITHM: "Minimax",
        ALPHABETA_ALGORITHM: "Alfa-Beta",
    }
    _dibujar_texto(pantalla, fuentes["normal"], "1 · ALGORITMO", TEXTO_SUAVE, (62, 168))
    botones = {"volver": pygame.Rect(30, 735, 150, 44), "comenzar": pygame.Rect(900, 725, 250, 54)}
    alturas = (200, 305, 410)
    for algoritmo_opcion, y in zip(nombres, alturas):
        rectangulo = pygame.Rect(62, y, 520, 82)
        botones[algoritmo_opcion] = rectangulo
        esta_seleccionado = algoritmo_opcion == algoritmo
        color = VERDE_MEDIO if esta_seleccionado else VERDE_OSCURO
        borde = AMARILLO if esta_seleccionado else VERDE_BORDE
        if rectangulo.collidepoint(raton):
            color = VERDE_RESALTE
            borde = AMARILLO
        pygame.draw.rect(pantalla, color, rectangulo, border_radius=10)
        pygame.draw.rect(pantalla, borde, rectangulo, 2, border_radius=10)
        _dibujar_texto(pantalla, fuentes["boton"], nombres[algoritmo_opcion], TEXTO, (rectangulo.x + 18, y + 10))
        _dibujar_texto_en_caja(
            pantalla,
            DESCRIPCIONES_ALGORITMOS[algoritmo_opcion],
            fuentes["pequena"],
            TEXTO_SUAVE,
            pygame.Rect(rectangulo.x + 18, y + 47, rectangulo.width - 36, 30),
        )

    if algoritmo == GREEDY_ALGORITHM:
        _dibujar_texto_en_caja(
            pantalla,
            "La voraz solo evalúa el siguiente movimiento.",
            fuentes["pequena"],
            AMARILLO,
            pygame.Rect(78, 525, 480, 45),
        )

    _dibujar_texto(pantalla, fuentes["normal"], "2 · FUNCIÓN DE EVALUACIÓN", TEXTO_SUAVE, (625, 168))
    boton_heuristica = pygame.Rect(625, 200, 500, 54)
    texto_heuristica = f"{heuristica}  ·  {NOMBRES_HEURISTICAS[heuristica]}     ▼"
    _dibujar_boton(pantalla, boton_heuristica, texto_heuristica, fuentes["normal"], raton, True)

    botones_heuristicas = ()
    if heuristicas_abiertas:
        botones_heuristicas = tuple(
            pygame.Rect(625, 261 + indice * 47, 500, 43)
            for indice in range(len(HEURISTICAS_DISPONIBLES))
        )
        for opcion, rectangulo in zip(HEURISTICAS_DISPONIBLES, botones_heuristicas):
            color_opcion = VERDE_MEDIO if opcion == heuristica else VERDE_OSCURO
            pygame.draw.rect(pantalla, color_opcion, rectangulo, border_radius=8)
            pygame.draw.rect(
                pantalla,
                AMARILLO if opcion == heuristica else VERDE_BORDE,
                rectangulo,
                1,
                border_radius=8,
            )
            _dibujar_texto(pantalla, fuentes["pequena"], opcion, AMARILLO, (rectangulo.x + 12, rectangulo.y + 4))
            _dibujar_texto(pantalla, fuentes["pequena"], NOMBRES_HEURISTICAS[opcion], TEXTO, (rectangulo.x + 70, rectangulo.y + 4))
    else:
        _dibujar_texto_en_caja(
            pantalla,
            DESCRIPCIONES_HEURISTICAS[heuristica],
            fuentes["pequena"],
            TEXTO_SUAVE,
            pygame.Rect(637, 266, 474, 52),
        )

    _dibujar_texto(pantalla, fuentes["normal"], "3 · PROFUNDIDAD DE BÚSQUEDA", TEXTO_SUAVE, (625, 405))
    boton_profundidad = pygame.Rect(625, 438, 500, 54)
    nombres_profundidad = {1: "RÁPIDA", 2: "EQUILIBRADA", 3: "PROFUNDA"}
    _dibujar_boton(
        pantalla,
        boton_profundidad,
        f"NIVEL {profundidad}  ·  {nombres_profundidad[profundidad]}     ▼",
        fuentes["normal"],
        raton,
        True,
    )

    botones_profundidad = ()
    if profundidad_abierta:
        botones_profundidad = tuple(
            pygame.Rect(625 + indice * 168, 500, 158, 78)
            for indice in range(3)
        )
        for nivel, rectangulo in enumerate(botones_profundidad, start=1):
            color_nivel = VERDE_MEDIO if nivel == profundidad else VERDE_OSCURO
            pygame.draw.rect(pantalla, color_nivel, rectangulo, border_radius=9)
            pygame.draw.rect(
                pantalla,
                AMARILLO if nivel == profundidad else VERDE_BORDE,
                rectangulo,
                2,
                border_radius=9,
            )
            _dibujar_texto_centrado(pantalla, fuentes["boton"], str(nivel), AMARILLO, (rectangulo.centerx, rectangulo.y + 25))
            _dibujar_texto_centrado(pantalla, fuentes["pequena"], nombres_profundidad[nivel].title(), TEXTO, (rectangulo.centerx, rectangulo.y + 55))
    else:
        _dibujar_texto_en_caja(
            pantalla,
            "El nivel 1 piensa rápido; un nivel mayor revisa más respuestas.",
            fuentes["pequena"],
            TEXTO_SUAVE,
            pygame.Rect(637, 503, 474, 45),
        )

    _dibujar_boton(pantalla, botones["volver"], "Volver", fuentes["normal"], raton)
    _dibujar_boton(pantalla, botones["comenzar"], "Comenzar partida", fuentes["normal"], raton, True)
    return botones, boton_heuristica, botones_heuristicas, boton_profundidad, botones_profundidad


def _dibujar_panel_partida(
    pantalla: pygame.Surface,
    tablero: Board,
    controles: GameControls,
    algoritmo: str,
    heuristica: str,
    profundidad: int,
    pensando: bool,
    juego_automatico: bool,
    mensaje: str,
    fuentes: dict[str, pygame.font.Font],
    raton: tuple[int, int],
) -> dict[str, pygame.Rect]:
    panel = pygame.Rect(ANCHO_TABLERO, 0, ANCHO_VENTANA - ANCHO_TABLERO, ALTO_VENTANA)
    pygame.draw.rect(pantalla, PANEL, panel)
    pygame.draw.line(pantalla, (58, 91, 64), panel.topleft, panel.bottomleft, 2)

    margen = panel.x + 22
    ancho_texto = panel.width - 44
    _dibujar_texto(pantalla, fuentes["titulo_panel"], "PARTIDA", TEXTO, (margen, 20))
    _dibujar_texto(pantalla, fuentes["pequena"], "DAMAS CHINAS · AGENTES DE IA", (157, 191, 155), (margen, 55))

    nombres_modo = {
        HUMAN_VS_HUMAN: "Humano vs Humano",
        HUMAN_VS_AI: "Humano vs IA",
        AI_VS_AI: "IA vs IA",
    }
    nombres_algoritmo = {
        GREEDY_ALGORITHM: "Heurística voraz",
        MINIMAX_ALGORITHM: "Minimax",
        ALPHABETA_ALGORITHM: "Alfa-Beta",
    }
    _dibujar_texto(pantalla, fuentes["normal"], nombres_modo[controles.modo], TEXTO, (margen, 88))
    if controles.modo == HUMAN_VS_HUMAN:
        etiqueta_algoritmo = "Reglas del turno humano"
    else:
        etiqueta_algoritmo = f"{nombres_algoritmo[algoritmo]} · {heuristica} · nivel {profundidad}"
    _dibujar_texto(
        pantalla,
        fuentes["pequena"],
        etiqueta_algoritmo,
        TEXTO_SUAVE,
        (margen, 119),
    )

    ganador = controles.winner
    if ganador is None:
        nombre_turno = tablero.jugador_actual.nombre_visible
        estado_turno = "IA analizando" if pensando else "Turno"
        if controles.modo == HUMAN_VS_AI and tablero.jugador_actual.value == "azul":
            estado_turno = "Tu turno"
        if controles.modo == HUMAN_VS_HUMAN:
            estado_turno = "Turno de"
        texto_turno = f"{estado_turno}: {nombre_turno}"
    else:
        texto_turno = f"¡Gana {ganador.nombre_visible}!"

    tarjeta_turno = pygame.Rect(margen, 155, ancho_texto, 45)
    pygame.draw.rect(pantalla, (34, 66, 47), tarjeta_turno, border_radius=9)
    _dibujar_texto(pantalla, fuentes["normal"], texto_turno, TEXTO, (tarjeta_turno.x + 12, tarjeta_turno.y + 10))

    caja_mensaje = pygame.Rect(margen, 210, ancho_texto, 76)
    pygame.draw.rect(pantalla, (17, 39, 29), caja_mensaje, border_radius=9)
    _dibujar_texto_en_caja(
        pantalla,
        mensaje,
        fuentes["pequena"],
        TEXTO_SUAVE,
        pygame.Rect(caja_mensaje.x + 11, caja_mensaje.y + 9, caja_mensaje.width - 22, caja_mensaje.height - 15),
    )

    pygame.draw.line(pantalla, (58, 91, 64), (margen, 306), (panel.right - 22, 306), 1)
    if controles.modo == HUMAN_VS_HUMAN:
        descripcion_codigo = "El motor comprueba cada selección y aplica solo movimientos legales."
        lineas_codigo = CODIGO_TURNO_HUMANO
    else:
        descripcion_codigo = DESCRIPCIONES_HEURISTICAS[heuristica]
        lineas_codigo = CODIGO_ALGORITMOS[algoritmo]
    _dibujar_texto(pantalla, fuentes["normal"], "Código que guía la jugada", TEXTO, (margen, 320))
    _dibujar_texto_en_caja(
        pantalla,
        descripcion_codigo,
        fuentes["pequena"],
        TEXTO_SUAVE,
        pygame.Rect(margen, 350, ancho_texto, 43),
    )

    caja_codigo = pygame.Rect(margen, 402, ancho_texto, 224)
    pygame.draw.rect(pantalla, (16, 34, 25), caja_codigo, border_radius=8)
    indice_destacado = 3 if pensando and len(lineas_codigo) > 3 else len(lineas_codigo) - 1
    for numero_linea, linea in enumerate(lineas_codigo):
        y = caja_codigo.y + 15 + numero_linea * 31
        if numero_linea == indice_destacado:
            pygame.draw.rect(
                pantalla,
                (70, 82, 53),
                pygame.Rect(caja_codigo.x + 7, y - 2, caja_codigo.width - 14, 27),
                border_radius=4,
            )
        _dibujar_texto(
            pantalla,
            fuentes["codigo"],
            linea,
            (248, 218, 139) if numero_linea == indice_destacado else (195, 211, 229),
            (caja_codigo.x + 12, y),
        )

    if controles.modo != HUMAN_VS_HUMAN:
        formulas_heuristicas = {
            "E1": "E1 = D_MIN - D_MAX",
            "E2": "E2 = E1 - 0.5 × penalización eje",
            "E3": "E3 = E1 - 2 × ficha MAX atrasada",
        }
        _dibujar_texto(
            pantalla,
            fuentes["pequena"],
            formulas_heuristicas[heuristica],
            (205, 223, 196),
            (margen, 643),
        )

    botones = {
        "menu": pygame.Rect(margen, 720, 150, 48),
        "nueva": pygame.Rect(margen + 165, 720, 150, 48),
    }
    _dibujar_boton(pantalla, botones["menu"], "Menú", fuentes["pequena"], raton)
    _dibujar_boton(pantalla, botones["nueva"], "Reiniciar", fuentes["pequena"], raton)

    if controles.modo == AI_VS_AI:
        botones["siguiente"] = pygame.Rect(margen, 665, 150, 42)
        botones["automatico"] = pygame.Rect(margen + 165, 665, 150, 42)
        if juego_automatico:
            texto_siguiente = "En automático"
        elif pensando:
            texto_siguiente = "Pensando…"
        else:
            texto_siguiente = "Siguiente"
        _dibujar_boton(
            pantalla,
            botones["siguiente"],
            texto_siguiente,
            fuentes["pequena"],
            raton,
            not pensando and not juego_automatico,
        )
        texto_automatico = "Pausar" if juego_automatico else "Automático"
        _dibujar_boton(
            pantalla,
            botones["automatico"],
            texto_automatico,
            fuentes["pequena"],
            raton,
        )

    return botones


def run() -> None:
    """Inicia el menú y coordina las jugadas de las personas y de la IA."""
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("Damas Chinas — Algoritmos de IA")
    reloj = pygame.time.Clock()

    fuentes = {
        "titulo": pygame.font.SysFont("consolas", 68, bold=True),
        "titulo_pantalla": pygame.font.SysFont("consolas", 42, bold=True),
        "titulo_panel": pygame.font.Font(None, 37),
        "boton": pygame.font.SysFont("consolas", 26, bold=True),
        "cuerpo": pygame.font.Font(None, 25),
        "normal": pygame.font.Font(None, 23),
        "pequena": pygame.font.Font(None, 19),
        "codigo": pygame.font.SysFont("consolas", 13),
    }

    area_tablero = pygame.Rect(0, 0, ANCHO_TABLERO, ALTO_VENTANA)
    distribucion_tablero = BoardLayout.fit_to_rect(area_tablero)
    controles = GameControls(modo=HUMAN_VS_HUMAN)
    modo_elegido = HUMAN_VS_AI
    algoritmo = ALPHABETA_ALGORITHM
    heuristica = "E1"
    profundidad = 2
    desplegable_heuristicas_abierto = False
    desplegable_profundidad_abierto = False
    pantalla_actual = "inicio"
    cola_resultados: queue.Queue = queue.Queue()
    identificador_busqueda = 0
    pensando = False
    error_busqueda = False
    juego_automatico = False
    paso_solicitado = False
    siguiente_turno_ia = 0.0
    mensaje = ""

    def cancelar_busqueda() -> None:
        nonlocal identificador_busqueda, pensando, error_busqueda
        identificador_busqueda += 1
        pensando = False
        error_busqueda = False

    def iniciar_partida() -> None:
        nonlocal pantalla_actual, juego_automatico, paso_solicitado, siguiente_turno_ia, mensaje
        controles.set_mode(modo_elegido)
        cancelar_busqueda()
        pantalla_actual = "partida"
        juego_automatico = False
        paso_solicitado = False
        siguiente_turno_ia = time.monotonic() + 0.25
        mensaje = controles.mensaje

    def reiniciar_partida() -> None:
        nonlocal juego_automatico, paso_solicitado, siguiente_turno_ia, mensaje
        controles.reset_game()
        cancelar_busqueda()
        juego_automatico = False
        paso_solicitado = False
        siguiente_turno_ia = time.monotonic() + 0.25
        mensaje = controles.mensaje

    ejecutar = True
    while ejecutar:
        posicion_raton = pygame.mouse.get_pos()
        pantalla_mostrada = pantalla_actual
        botones_modos = {}
        botones_algoritmo = {}
        boton_heuristica = pygame.Rect(0, 0, 0, 0)
        botones_heuristicas = ()
        boton_profundidad = pygame.Rect(0, 0, 0, 0)
        botones_profundidad = ()
        botones_partida = {}

        if pantalla_actual == "inicio":
            boton_jugar = _dibujar_pantalla_inicio(pantalla, posicion_raton, fuentes)
        elif pantalla_actual == "modos":
            botones_modos = _dibujar_pantalla_modos(pantalla, posicion_raton, fuentes)
        elif pantalla_actual == "algoritmo":
            (
                botones_algoritmo,
                boton_heuristica,
                botones_heuristicas,
                boton_profundidad,
                botones_profundidad,
            ) = _dibujar_pantalla_algoritmo(
                pantalla,
                posicion_raton,
                fuentes,
                algoritmo,
                profundidad,
                heuristica,
                desplegable_heuristicas_abierto,
                desplegable_profundidad_abierto,
            )
        else:
            pantalla.fill(FONDO)
            draw_board(
                pantalla,
                controles.tablero,
                distribucion_tablero,
                celda_seleccionada=controles.celda_seleccionada,
                destinos_legales=controles.destinos_legales,
                ultimo_movimiento=controles.ultimo_movimiento,
            )
            botones_partida = _dibujar_panel_partida(
                pantalla,
                controles.tablero,
                controles,
                algoritmo,
                heuristica,
                profundidad,
                pensando,
                juego_automatico,
                mensaje,
                fuentes,
                posicion_raton,
            )

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutar = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    if pantalla_actual == "inicio":
                        ejecutar = False
                    elif pantalla_actual == "partida":
                        cancelar_busqueda()
                        pantalla_actual = "modos"
                    elif pantalla_actual == "algoritmo":
                        desplegable_heuristicas_abierto = False
                        desplegable_profundidad_abierto = False
                        pantalla_actual = "modos"
                    else:
                        pantalla_actual = "inicio"
                elif evento.key == pygame.K_s and pantalla_actual == "partida" and controles.modo == AI_VS_AI:
                    if not pensando and not juego_automatico:
                        paso_solicitado = True
                elif evento.key == pygame.K_n and pantalla_actual == "partida":
                    reiniciar_partida()

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if pantalla_actual == "inicio" and boton_jugar.collidepoint(evento.pos):
                    pantalla_actual = "modos"
                elif pantalla_actual == "modos":
                    if botones_modos["volver"].collidepoint(evento.pos):
                        pantalla_actual = "inicio"
                    else:
                        for modo in (HUMAN_VS_HUMAN, HUMAN_VS_AI, AI_VS_AI):
                            if botones_modos[modo].collidepoint(evento.pos):
                                modo_elegido = modo
                                if modo == HUMAN_VS_HUMAN:
                                    iniciar_partida()
                                else:
                                    desplegable_heuristicas_abierto = False
                                    desplegable_profundidad_abierto = False
                                    pantalla_actual = "algoritmo"
                                break
                elif pantalla_actual == "algoritmo":
                    if botones_algoritmo["volver"].collidepoint(evento.pos):
                        desplegable_heuristicas_abierto = False
                        desplegable_profundidad_abierto = False
                        pantalla_actual = "modos"
                    elif botones_algoritmo["comenzar"].collidepoint(evento.pos):
                        desplegable_heuristicas_abierto = False
                        desplegable_profundidad_abierto = False
                        iniciar_partida()
                    elif boton_heuristica.collidepoint(evento.pos):
                        desplegable_heuristicas_abierto = not desplegable_heuristicas_abierto
                        desplegable_profundidad_abierto = False
                    elif desplegable_heuristicas_abierto and any(
                        rectangulo.collidepoint(evento.pos) for rectangulo in botones_heuristicas
                    ):
                        for nombre_heuristica, rectangulo in zip(
                            HEURISTICAS_DISPONIBLES,
                            botones_heuristicas,
                        ):
                            if rectangulo.collidepoint(evento.pos):
                                heuristica = nombre_heuristica
                                desplegable_heuristicas_abierto = False
                                break
                    elif boton_profundidad.collidepoint(evento.pos):
                        desplegable_profundidad_abierto = not desplegable_profundidad_abierto
                        desplegable_heuristicas_abierto = False
                    elif desplegable_profundidad_abierto and any(
                        rectangulo.collidepoint(evento.pos) for rectangulo in botones_profundidad
                    ):
                        for nivel, rectangulo in enumerate(botones_profundidad, start=1):
                            if rectangulo.collidepoint(evento.pos):
                                profundidad = nivel
                                desplegable_profundidad_abierto = False
                                break
                    else:
                        desplegable_heuristicas_abierto = False
                        desplegable_profundidad_abierto = False
                        for algoritmo_opcion, rectangulo in botones_algoritmo.items():
                            if algoritmo_opcion not in ("volver", "comenzar") and rectangulo.collidepoint(evento.pos):
                                algoritmo = algoritmo_opcion
                                break
                elif pantalla_actual == "partida":
                    if botones_partida["menu"].collidepoint(evento.pos):
                        cancelar_busqueda()
                        pantalla_actual = "modos"
                    elif botones_partida["nueva"].collidepoint(evento.pos):
                        reiniciar_partida()
                    elif controles.modo == AI_VS_AI and botones_partida["siguiente"].collidepoint(evento.pos):
                        if not pensando and not juego_automatico:
                            paso_solicitado = True
                    elif controles.modo == AI_VS_AI and botones_partida["automatico"].collidepoint(evento.pos):
                        juego_automatico = not juego_automatico
                        if juego_automatico:
                            siguiente_turno_ia = time.monotonic()
                    elif evento.pos[0] < ANCHO_TABLERO:
                        controles.handle_board_click(distribucion_tablero.hit_test(evento.pos))
                        mensaje = controles.mensaje

            if pantalla_actual != pantalla_mostrada:
                break

        while True:
            try:
                id_completado, decision, error = cola_resultados.get_nowait()
            except queue.Empty:
                break

            if id_completado != identificador_busqueda:
                continue

            pensando = False
            if error is not None:
                error_busqueda = True
                mensaje = f"La búsqueda de la IA falló: {error}"
            else:
                controles.finish_ai_turn(decision)
                mensaje = controles.mensaje
                if juego_automatico:
                    siguiente_turno_ia = time.monotonic() + 0.4

        turno_automatico = controles.modo != AI_VS_AI or juego_automatico or paso_solicitado
        if (
            pantalla_actual == "partida"
            and controles.is_ai_turn
            and turno_automatico
            and time.monotonic() >= siguiente_turno_ia
            and not pensando
            and not error_busqueda
        ):
            pensando = True
            paso_solicitado = False
            estado_copia = controles.tablero.copy()
            identificador_actual = identificador_busqueda
            hilo_busqueda = threading.Thread(
                target=_buscar_jugada_en_segundo_plano,
                args=(estado_copia, algoritmo, profundidad, heuristica, identificador_actual, cola_resultados),
                name="busqueda-ia-damas-chinas",
                daemon=True,
            )
            hilo_busqueda.start()

        pygame.display.flip()
        reloj.tick(60)

    pygame.quit()
