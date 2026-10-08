# Damas Chinas: agentes de IA

Juego académico de Damas Chinas hecho con Python y Pygame. Permite jugar Humano vs Humano, Humano vs IA e IA vs IA. Incluye tres algoritmos de búsqueda —heurística voraz, Minimax y Alfa-Beta— y las evaluaciones E1, E2 y E3.

## Requisitos

- Python **3.10 o posterior**.
- Git para clonar el repositorio.
- Para jugar: una computadora con una ventana gráfica compatible con Pygame.
- Para el visualizador web: un navegador moderno. No necesita frameworks ni dependencias de JavaScript.

## 1. Clonar el proyecto

Abre una terminal y reemplaza `URL_DEL_REPOSITORIO` y `CARPETA_DEL_PROYECTO` por los datos de este repositorio:

```text
git clone URL_DEL_REPOSITORIO
cd CARPETA_DEL_PROYECTO
```

Los siguientes comandos se ejecutan desde la carpeta del proyecto, donde están `requirements.txt` y `app/`.

## 2. Instalar y ejecutar el juego

Se recomienda usar un entorno virtual para instalar las dependencias solo para este proyecto. La única dependencia externa es `pygame-ce`.

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.main
```

Si `py` no está disponible, usa `python` para crear el entorno:

```powershell
python -m venv .venv
```

### macOS o Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m app.main
```

La primera instalación necesita conexión a Internet para descargar Pygame. Después, ejecuta el juego desde la carpeta del proyecto con el Python del entorno virtual.

## 3. Ejecutar el visualizador web

El visualizador carga los ejemplos JSON con `fetch`, así que debe abrirse desde un servidor local y no directamente como archivo.

Abre una **segunda terminal** en la carpeta del proyecto y ejecuta:

### Windows

```powershell
.\.venv\Scripts\python.exe -m http.server 8000
```

### macOS o Linux

Ejecuta el servidor con el Python del entorno virtual:

```bash
.venv/bin/python -m http.server 8000
```

En el navegador, visita <http://localhost:8000/visualizer/>. Para detener el servidor, vuelve a esa terminal y pulsa **Ctrl+C**.

El visualizador permite elegir el algoritmo y E1, E2 o E3, y recorrer los pasos con **Anterior**, **Siguiente**, **Reiniciar** y **Reproducir**. Muestra una secuencia pequeña de movimientos legales, el árbol de búsqueda, los valores y las podas de Alfa-Beta. Las hojas se recalculan al cambiar la heurística.

## Controles del juego

- En los modos humanos, selecciona una ficha y después uno de sus destinos verdes.
- En IA vs IA, pulsa **Siguiente** o **S** para avanzar un movimiento a la vez. **Automático** hace que la partida continúe; **Pausar** vuelve al modo manual.
- **Reiniciar** empieza otra partida del modo actual. **Menú** permite elegir otro modo.
- **ESC** vuelve a la pantalla anterior; desde la pantalla inicial cierra el juego.

En la configuración de una partida con IA se eligen el algoritmo, la heurística y la profundidad. En IA vs IA ambos jugadores usan la misma configuración y la partida comienza en modo manual.

## Algoritmos y evaluaciones

- **Heurística voraz:** evalúa el resultado inmediato de cada jugada y no anticipa la respuesta del rival.
- **Minimax:** explora jugadas y respuestas hasta la profundidad elegida. MAX conserva el valor mayor y MIN el menor.
- **Alfa-Beta:** obtiene la decisión de Minimax y deja de explorar ramas cuando `beta <= alpha`.

Las evaluaciones miran el tablero desde MAX (ROJO): un valor positivo lo favorece y uno negativo favorece a MIN (AZUL).

```text
E1 = D_MIN - D_MAX
E2 = E1 - 0.5 × penalización_eje
E3 = E1 - 2 × distancia_ficha_más_atrasada
```

- **E1** compara la distancia total de las fichas de ambos jugadores a sus zonas objetivo.
- **E2** resta media desviación neta respecto al eje central: desviación de MAX menos desviación de MIN.
- **E3** resta dos veces la distancia de la ficha de MAX que está más lejos de su meta.

Las distancias usan las coordenadas y las zonas objetivo existentes en el tablero. Para seleccionar una heurística desde Python:

```python
from app.ai.agent import AdversarialAgent, ALPHABETA_ALGORITHM
from app.game.board import Board

estado = Board()
agente = AdversarialAgent(
    algoritmo=ALPHABETA_ALGORITHM,
    profundidad=2,
    heuristica="E2",  # "E1", "E2" o "E3"
)
decision = agente.choose_move(estado)
```

## Ejecutar las pruebas

Desde la carpeta del proyecto:

### Windows

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### macOS o Linux

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Estructura del proyecto

- `app/game/`: tablero, jugadores, movimientos y reglas.
- `app/ai/`: E1/E2/E3, agente, Minimax y Alfa-Beta.
- `app/ui/`: pantallas e interfaz de Pygame.
- `visualizer/`: visualizador web independiente.
- `examples/`: árboles pequeños de ejemplo.
- `tests/`: pruebas del motor, las evaluaciones, los agentes y los ejemplos.
