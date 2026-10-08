# AGENTS.md — Damas Chinas con agentes de IA

## Propósito

Aplicación académica de Damas Chinas para dos jugadores humanos o agentes de IA. Además de permitir jugar, el proyecto debe explicar de manera visible y entendible una heurística voraz, Minimax, poda Alfa-Beta, evaluación heurística, generación de movimientos, exploración de estados y selección de una jugada. El código se prepara para una exposición universitaria; la claridad tiene prioridad sobre la sofisticación.

## Tecnologías y entorno

- Juego: Python 3.x y Pygame.
- Visualizador independiente: HTML, CSS y JavaScript puro; no agregar React, Vue, Angular ni frameworks innecesarios.
- Entorno principal: Windows y el entorno virtual local `.venv/`. Ejecutar Python y pip desde ese entorno; no depender ni modificar el Python global.
- Dependencias externas mínimas. Minimax y Alfa-Beta se implementan a mano.

## Estructura esperada

```text
AGENTS.md, README.md, requirements.txt, .gitignore
app/main.py
app/game/{__init__.py,board.py,pieces.py,moves.py,rules.py}
app/ai/{__init__.py,minimax.py,alphabeta.py,evaluation.py,agent.py}
app/ui/{__init__.py,pygame_app.py,board_renderer.py,controls.py}
app/visualization/{__init__.py,export_tree.py}
visualizer/{index.html,style.css,script.js}
examples/{minimax_example.json,alphabeta_example.json}
tests/{test_board.py,test_moves.py,test_minimax.py,test_evaluation.py}
```

No concentrar la aplicación en `main.py`. Mantener la arquitectura aproximadamente así; se permiten módulos auxiliares pequeños cuando mejoren la claridad.

## Separación de responsabilidades

- `game/`: estado del tablero, jugadores/piezas, movimientos legales, aplicación de movimientos y detección de victoria. No importar ni usar Pygame.
- `ai/`: heurística voraz, Minimax, Alfa-Beta, evaluación y agente. No dibujar ni gestionar eventos de UI.
- `ui/`: ventana, dibujo, controles, turnos e interacción visual. La UI delega las reglas al motor y la decisión al agente.
- `visualizer/`: herramienta académica web independiente alimentada por ejemplos JSON pequeños. No depende de Pygame ni representa el árbol completo de una partida real.
- Flujo del juego: Pygame → motor → agente → búsqueda/evaluación → movimiento elegido → motor → Pygame.
- Flujo web: `examples/*.json` → HTML/CSS/JavaScript.

## Algoritmos y evaluación

### Minimax (`app/ai/minimax.py`)

Implementar de manera directa y cercana al pseudocódigo académico. Debe distinguir estado, profundidad, MAX, MIN, movimientos, estados hijos, hojas y propagación de valores. MAX elige el máximo y MIN el mínimo. Debe poder probarse sin abrir Pygame.

### Alfa-Beta (`app/ai/alphabeta.py`)

Mantener explícitos `alpha`, `beta` y `mejor_valor`, conservar la lógica de MAX/MIN y mostrar claramente el corte `if beta <= alpha: break` (o una condición equivalente documentada). No esconder la poda tras librerías ni abstracciones innecesarias. Con los mismos estados, debe devolver el mismo valor óptimo que Minimax.

### Heurística (`app/ai/evaluation.py`)

La evaluación devuelve un número: positivo favorece a MAX, negativo favorece a MIN y cero indica equilibrio. Basarla en características explicables de Damas Chinas: distancia/progreso a la zona objetivo, piezas adelantadas o piezas que ya alcanzaron posiciones favorables. Documentar cada componente y evitar complejidad difícil de exponer.

### Agente (`app/ai/agent.py`)

Recibe el estado, genera movimientos, ejecuta la heurística voraz, Minimax o Alfa-Beta, compara resultados y devuelve el mejor movimiento. No administra la interfaz.

### Búsqueda voraz

Para cada movimiento legal, crea el estado hijo, lo evalúa con la heurística y escoge el mayor valor para MAX o el menor para MIN. Solo mira una jugada y no calcula respuestas futuras del rival; mantener esta diferencia visible en el código.

## Motor y reglas

La lógica debe poder usarse en pruebas sin abrir ventanas. Representar de forma explícita jugadores, celdas y movimientos. Mantener generación de destinos, saltos encadenados, validación/aplicación de jugadas y detección de victoria en el motor. La generación de movimientos debe ser determinista cuando sea práctico para facilitar la explicación y las pruebas.

## Visualizador académico

- Mantener árboles deliberadamente pequeños y controlados, preferentemente con una posición intermedia preparada manualmente.
- Incluir controles `Anterior`, `Siguiente`, `Reiniciar` y `Reproducir`.
- Mostrar el tablero ilustrativo a un lado, el árbol pequeño al centro y el pseudocódigo del algoritmo seleccionado al otro lado.
- Permitir observar estado inicial, generación de movimientos, expansión, evaluación, propagación, decisión y podas Alfa-Beta.
- Mostrar pseudocódigo junto al árbol y resaltar la línea del paso actual.
- Mostrar valores de evaluación y las ramas podadas; no intentar desplegar el árbol completo de una partida.

## Estilo para exposición

- Usar nombres descriptivos en español cuando ayuden (`estado_actual`, `mejor_movimiento`, `movimientos_posibles`, `jugador_actual`, `valor_heuristico`). `alpha` y `beta` son nombres estándar permitidos.
- Preferir funciones pequeñas, comentarios que expliquen el porqué y código fácil de seguir oralmente.
- Evitar código compacto, dependencias innecesarias, metaprogramación, patrones complejos, lambdas que resten claridad y abstracciones empresariales.
- No añadir comentarios obvios. No mover reglas a la interfaz ni algoritmos a `main.py`.

## Pruebas

Crear y mantener pruebas básicas para creación del tablero y piezas, movimientos válidos, aplicación de jugadas y victoria, evaluación heurística, algoritmo voraz y Minimax/Alfa-Beta sobre árboles pequeños. Las pruebas de motor y algoritmos no deben requerir Pygame ni una ventana.

## Fases de implementación

1. Motor: tablero, jugadores, movimientos, reglas y victoria.
2. Interfaz Pygame: ventana, tablero, selección de movimientos y turnos.
3. Heurística explicada y probada.
4. Minimax explicado, probado e integrado.
5. Alfa-Beta probado y comparado con Minimax.
6. Agente humano vs IA.
7. Visualizador independiente con escenario intermedio, pasos, pseudocódigo, evaluación y podas.
8. Presentación, ejemplos y README.

Avanzar por fases. No implementar todo de golpe ni declarar completa una fase que siga pendiente.

## Git y mantenimiento

- Ignorar `.venv/`, `__pycache__/`, `*.pyc`, `.vscode/`, temporales y logs.
- No borrar ni sobrescribir código existente sin necesidad. Antes de un cambio importante, revisar la estructura y reutilizar lo que corresponda sin romper la separación modular.
- No crear copias duplicadas de módulos ni modificar la arquitectura sin justificarlo.
- Mantener cambios pequeños y commits descriptivos (`feat: implementar tablero`, `feat: agregar movimientos válidos`, etc.). No crear commits salvo que se solicite.

## Criterio de finalización

El proyecto completo debe permitir partidas Humano vs Humano, Humano vs IA e IA vs IA, validar movimientos y victoria, jugar contra agentes con una heurística explicable, y demostrar mediante el visualizador HTML un árbol pequeño paso a paso con pseudocódigo resaltado, valores y poda. Los nombres descriptivos de variables se escriben en español; se conservan términos estándar como Minimax, MAX/MIN, `alpha` y `beta`.
