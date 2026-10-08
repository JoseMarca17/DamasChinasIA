"""
DAMAS CHINAS - Agente inteligente (Minimax, Poda Alfa-Beta y Función de Evaluación)
-----------------------------------------------------------------------------------
* Tablero estrella de 121 casillas (hexagonal), 10 fichas por jugador.
* Modos: Humano vs IA, Humano vs Humano e IA vs IA.
* Panel lateral que EXPLICA lo que hace el algoritmo (traza en vivo + teoría).
* Solo usa la librería estándar (tkinter). Ejecutar:  python damas_chinas.py
"""
import math
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

# =====================================================================
# 1. GEOMETRÍA DEL TABLERO (estrella de 6 puntas)
# =====================================================================
# Filas de arriba hacia abajo: 1,2,3,4,13,12,11,10,9,10,11,12,13,4,3,2,1  -> 121 casillas
ROW_COUNTS = [1, 2, 3, 4, 13, 12, 11, 10, 9, 10, 11, 12, 13, 4, 3, 2, 1]
CENTER_X = 12

CELLS = []      # índice -> (fila, x)   (x en "medias casillas" para el desfase hexagonal)
ROWPOS = []     # índice -> posición dentro de su fila (para etiquetas legibles)
INDEX = {}      # (fila, x) -> índice
for _r, _n in enumerate(ROW_COUNTS):
    for _k in range(_n):
        _x = CENTER_X - (_n - 1) + 2 * _k
        INDEX[(_r, _x)] = len(CELLS)
        CELLS.append((_r, _x))
        ROWPOS.append(_k)
N = len(CELLS)  # 121

# Vecinos (paso simple) y saltos (casilla intermedia, casilla de aterrizaje)
STEP_DIRS = [(0, -2), (0, 2), (-1, -1), (-1, 1), (1, -1), (1, 1)]
NEIGH = [[] for _ in range(N)]
JUMPS = [[] for _ in range(N)]
for _i, (_r, _x) in enumerate(CELLS):
    for _dr, _dx in STEP_DIRS:
        _j = INDEX.get((_r + _dr, _x + _dx))
        if _j is None:
            continue
        NEIGH[_i].append(_j)
        _l = INDEX.get((_r + 2 * _dr, _x + 2 * _dx))
        if _l is not None:
            JUMPS[_i].append((_j, _l))

MAXP, MINP = 1, 2                      # MAX = ROJO (arriba)  |  MIN = AZUL (abajo)
OTHER = {MAXP: MINP, MINP: MAXP}
NAMES = {MAXP: "ROJO", MINP: "AZUL"}

TOP_CELLS = [i for i, (r, _) in enumerate(CELLS) if r <= 3]       # 10 casillas
BOTTOM_CELLS = [i for i, (r, _) in enumerate(CELLS) if r >= 13]   # 10 casillas
GOAL_SET = {MAXP: frozenset(BOTTOM_CELLS), MINP: frozenset(TOP_CELLS)}
TIP = {MAXP: INDEX[(16, 12)], MINP: INDEX[(0, 12)]}               # vértice de la meta


def hex_dist(a: int, b: int) -> int:
    (r1, x1), (r2, x2) = CELLS[a], CELLS[b]
    dr, dx = abs(r1 - r2), abs(x1 - x2)
    return dr + max(0, (dx - dr) // 2)


# Distancia (en pasos) de cada casilla al vértice de la meta de cada jugador
DIST = {p: [hex_dist(i, TIP[p]) for i in range(N)] for p in (MAXP, MINP)}


def label(i: int) -> str:
    return f"F{CELLS[i][0] + 1}·C{ROWPOS[i] + 1}"


# =====================================================================
# 2. ESTADO DEL JUEGO
# =====================================================================
class Board:
    __slots__ = ("occ", "pieces", "goal_count")

    def __init__(self):
        self.occ = [0] * N
        self.pieces = {MAXP: set(TOP_CELLS), MINP: set(BOTTOM_CELLS)}
        self.goal_count = {MAXP: 0, MINP: 0}
        for i in TOP_CELLS:
            self.occ[i] = MAXP
        for i in BOTTOM_CELLS:
            self.occ[i] = MINP

    def copy(self) -> "Board":
        b = Board.__new__(Board)
        b.occ = self.occ[:]
        b.pieces = {MAXP: set(self.pieces[MAXP]), MINP: set(self.pieces[MINP])}
        b.goal_count = dict(self.goal_count)
        return b

    def dests(self, s: int):
        """Destinos de la ficha en s: pasos a vecinas libres + saltos encadenados."""
        occ = self.occ
        out = [n for n in NEIGH[s] if occ[n] == 0]
        saved = occ[s]
        occ[s] = 0                       # la ficha ya "salió" de su casilla
        seen = {s}
        stack = [s]
        while stack:
            cur = stack.pop()
            for over, land in JUMPS[cur]:
                if occ[over] and occ[land] == 0 and land not in seen:
                    seen.add(land)
                    out.append(land)
                    stack.append(land)
        occ[s] = saved
        return out

    def moves(self, player: int):
        res = []
        for s in self.pieces[player]:
            for d in self.dests(s):
                res.append((s, d))
        return res

    def do(self, move, p: int):
        s, d = move
        self.occ[s] = 0
        self.occ[d] = p
        pcs = self.pieces[p]
        pcs.remove(s)
        pcs.add(d)
        g = GOAL_SET[p]
        if s in g:
            self.goal_count[p] -= 1
        if d in g:
            self.goal_count[p] += 1

    def undo(self, move, p: int):
        s, d = move
        self.occ[d] = 0
        self.occ[s] = p
        pcs = self.pieces[p]
        pcs.remove(d)
        pcs.add(s)
        g = GOAL_SET[p]
        if d in g:
            self.goal_count[p] -= 1
        if s in g:
            self.goal_count[p] += 1


# =====================================================================
# 3. FUNCIÓN DE EVALUACIÓN HEURÍSTICA
# =====================================================================
W_SUM, W_LAG, W_GOAL = 2.0, 1.0, 3.0
WIN = 100000


def player_score(b: Board, p: int):
    """Puntaje de un jugador: cuanto más cerca de su meta, mejor (menos negativo)."""
    d = DIST[p]
    total = 0
    worst = 0
    for i in b.pieces[p]:
        v = d[i]
        total += v
        if v > worst:
            worst = v
    score = -(W_SUM * total + W_LAG * worst) + W_GOAL * b.goal_count[p]
    return score, total, worst


def evaluate(b: Board) -> float:
    """f(estado) = puntaje(ROJO) - puntaje(AZUL).  Positivo => ventaja ROJO (MAX)."""
    return player_score(b, MAXP)[0] - player_score(b, MINP)[0]


# =====================================================================
# 4. BÚSQUEDA: MINIMAX, ALFA-BETA y VORAZ (solo evaluación)
# =====================================================================
class Cancelled(Exception):
    pass


def fmt(v: float) -> str:
    if v == float("inf"):
        return "+∞"
    if v == -float("inf"):
        return "-∞"
    return f"{v:+.1f}"


ALGO_NAMES = {
    "MINIMAX": "Minimax puro",
    "ALFABETA": "Minimax con poda Alfa-Beta",
    "EVAL": "Solo función de evaluación (voraz)",
}


class Searcher:
    def __init__(self, board: Board, player: int, depth: int, algo: str, emit, cancel):
        self.b = board
        self.player = player
        self.depth = depth
        self.algo = algo
        self.emit = emit
        self.cancel = cancel
        self.nodes = 0
        self.leaves = 0
        self.prunes = 0
        self.pruned_moves = 0
        self.prune_logged = 0

    # ---------- utilidades ----------
    def check(self):
        if self.cancel.is_set():
            raise Cancelled()

    def ordered(self, player):
        """Ordena jugadas por avance hacia la meta (mejores primero => más podas)."""
        moves = self.b.moves(player)
        d = DIST[player]
        moves.sort(key=lambda m: d[m[1]] - d[m[0]])
        return moves

    def terminal(self, depth):
        gc = self.b.goal_count
        if gc[MAXP] == 10:
            return WIN + depth
        if gc[MINP] == 10:
            return -(WIN + depth)
        return None

    # ---------- Minimax puro ----------
    def minimax(self, depth, player):
        self.nodes += 1
        if self.nodes % 2000 == 0:
            self.check()
        t = self.terminal(depth)
        if t is not None:
            return t
        if depth == 0:
            self.leaves += 1
            return evaluate(self.b)
        moves = self.b.moves(player)
        if not moves:
            self.leaves += 1
            return evaluate(self.b)
        if player == MAXP:
            v = -float("inf")
            for m in moves:
                self.b.do(m, player)
                c = self.minimax(depth - 1, MINP)
                self.b.undo(m, player)
                if c > v:
                    v = c
            return v
        v = float("inf")
        for m in moves:
            self.b.do(m, player)
            c = self.minimax(depth - 1, MAXP)
            self.b.undo(m, player)
            if c < v:
                v = c
        return v

    # ---------- Alfa-Beta ----------
    def ab(self, depth, player, alpha, beta, level):
        self.nodes += 1
        if self.nodes % 2000 == 0:
            self.check()
        t = self.terminal(depth)
        if t is not None:
            return t
        if depth == 0:
            self.leaves += 1
            return evaluate(self.b)
        moves = self.ordered(player)
        if not moves:
            self.leaves += 1
            return evaluate(self.b)
        n = len(moves)
        if player == MAXP:
            v = -float("inf")
            for idx, m in enumerate(moves):
                self.b.do(m, player)
                c = self.ab(depth - 1, MINP, alpha, beta, level + 1)
                self.b.undo(m, player)
                if c > v:
                    v = c
                if v > alpha:
                    alpha = v
                if v >= beta:
                    self._prune("β", "MAX", level, v, alpha, beta, n - idx - 1)
                    break
            return v
        v = float("inf")
        for idx, m in enumerate(moves):
            self.b.do(m, player)
            c = self.ab(depth - 1, MAXP, alpha, beta, level + 1)
            self.b.undo(m, player)
            if c < v:
                v = c
            if v < beta:
                beta = v
            if v <= alpha:
                self._prune("α", "MIN", level, v, alpha, beta, n - idx - 1)
                break
        return v

    def _prune(self, kind, role, level, v, alpha, beta, remaining):
        self.prunes += 1
        self.pruned_moves += remaining
        if remaining <= 0 or self.prune_logged >= 5:
            return
        self.prune_logged += 1
        if kind == "β":
            txt = (f"  ✂ PODA β (nivel {level}, nodo MAX): valor {fmt(v)} ≥ β={fmt(beta)}. "
                   f"MIN ya tiene una opción mejor arriba y nunca dejaría llegar aquí → "
                   f"descarto {remaining} jugada(s) sin evaluarlas.")
        else:
            txt = (f"  ✂ PODA α (nivel {level}, nodo MIN): valor {fmt(v)} ≤ α={fmt(alpha)}. "
                   f"MAX ya tiene una opción mejor arriba y no elegiría esta rama → "
                   f"descarto {remaining} jugada(s) sin evaluarlas.")
        self.emit("log", txt, "prune")

    # ---------- Ejecución desde la raíz ----------
    def run(self):
        t0 = time.time()
        p = self.player
        b = self.b
        maximizing = (p == MAXP)
        role = "MAX (maximiza)" if maximizing else "MIN (minimiza)"
        depth = 1 if self.algo == "EVAL" else self.depth

        self.emit("log", f"▶ Turno de {NAMES[p]} — {ALGO_NAMES[self.algo]}"
                         + ("" if self.algo == "EVAL" else f", profundidad {depth}"), "title")

        moves = self.ordered(p) if self.algo == "ALFABETA" else b.moves(p)
        if not moves:
            self.emit("log", "No hay jugadas legales.", "warn")
            return None
        self.emit("log", f"Nivel 0 · {role}: {len(moves)} jugadas legales "
                         f"(pasos + saltos encadenados).", "info")
        if self.algo == "ALFABETA":
            self.emit("log", "Ordeno las jugadas por avance hacia la meta: probar primero "
                             "las buenas hace que las podas ocurran antes.", "info")
        elif self.algo == "MINIMAX":
            self.emit("log", "Sin poda: se visita TODO el árbol hasta la profundidad pedida.", "info")
        else:
            self.emit("log", "Sin mirar al futuro: pruebo cada jugada y me quedo con la que "
                             "deja la mejor evaluación inmediata.", "info")

        best_move = None
        best_val = -float("inf") if maximizing else float("inf")
        alpha, beta = -float("inf"), float("inf")
        ranking = []
        total = len(moves)

        for idx, m in enumerate(moves):
            self.check()
            self.emit("progress", idx + 1, total)
            b.do(m, p)
            if self.algo == "EVAL":
                self.nodes += 1
                self.leaves += 1
                t = self.terminal(0)
                val = t if t is not None else evaluate(b)
            elif self.algo == "MINIMAX":
                val = self.minimax(depth - 1, OTHER[p])
            else:
                val = self.ab(depth - 1, OTHER[p], alpha, beta, 1)
            b.undo(m, p)
            ranking.append((val, m))

            better = val > best_val if maximizing else val < best_val
            if better or best_move is None:
                best_val, best_move = val, m
                self.emit("log", f"  ★ Nueva mejor jugada: {label(m[0])} → {label(m[1])}  "
                                 f"valor {fmt(val)}", "good")
                if self.algo == "ALFABETA":
                    if maximizing:
                        alpha = max(alpha, val)
                    else:
                        beta = min(beta, val)
                    self.emit("log", f"    ventana actualizada: α={fmt(alpha)}  β={fmt(beta)}", "dim")

        dt = time.time() - t0
        if self.algo != "ALFABETA":
            top = sorted(ranking, key=lambda t: t[0], reverse=maximizing)[:3]
            self.emit("log", "Top 3 jugadas de la raíz:", "info")
            for k, (v, m) in enumerate(top, 1):
                self.emit("log", f"   {k}. {label(m[0])} → {label(m[1])}   valor {fmt(v)}", "dim")

        self.emit("log", f"✔ ELEGIDA: {label(best_move[0])} → {label(best_move[1])}  "
                         f"(valor {fmt(best_val)})", "good")
        self.emit("log", f"📊 Nodos visitados: {self.nodes:,} · hojas evaluadas: {self.leaves:,} "
                         f"· tiempo: {dt:.2f}s", "info")
        if self.algo == "ALFABETA":
            self.emit("log", f"✂ Podas realizadas: {self.prunes:,} · jugadas descartadas sin "
                             f"explorar: {self.pruned_moves:,}", "prune")
        side = "ROJO" if best_val > 0 else "AZUL" if best_val < 0 else "nadie"
        if abs(best_val) >= WIN:
            self.emit("log", f"🏁 ¡{NAMES[p]} encuentra una victoria forzada!", "good")
        else:
            self.emit("log", f"Lectura: si ambos juegan lo mejor posible durante {depth} jugada(s), "
                             f"la posición queda a favor de {side} (valor positivo = ROJO, "
                             f"negativo = AZUL).", "dim")
        self.emit("log", "─" * 46, "dim")
        return {"move": best_move, "value": best_val}


# =====================================================================
# 5. TEXTO TEÓRICO PARA EL PANEL "¿CÓMO FUNCIONA?"
# =====================================================================
THEORY = """## Objetivo
Llevar tus 10 fichas al triángulo opuesto antes que el rival. ROJO (MAX) empieza arriba, AZUL (MIN) abajo.

## Movimientos
• Paso: a una casilla vecina libre (6 direcciones).
• Salto: sobre una ficha (propia o ajena) hacia la casilla libre justo detrás.
• Saltos encadenados: si desde donde aterrizas puedes volver a saltar, lo haces en el mismo turno.

## Función de evaluación (heurística)
Mide "qué tan buena" es una posición sin seguir jugando:
   puntaje(jugador) = −(2·Σdistancias + 1·ficha_más_atrasada) + 3·fichas_en_meta
   f(estado) = puntaje(ROJO) − puntaje(AZUL)
• Σdistancias: suma de pasos de cada ficha hasta el vértice de la meta.
• Ficha más atrasada: castiga dejar fichas rezagadas (en damas chinas, la última ficha decide).
• Valor positivo = ventaja de ROJO. Negativo = ventaja de AZUL.

## Minimax
ROJO (MAX) busca el valor más ALTO; AZUL (MIN) el más BAJO. La IA simula sus jugadas, las respuestas del rival, sus respuestas a eso... hasta la profundidad elegida, evalúa las hojas con f(estado) y sube los valores: MAX toma el máximo de sus hijos, MIN el mínimo. Así elige la jugada que es mejor suponiendo que el rival responde lo mejor posible.
Coste: b^d nodos (b≈40-70 jugadas) → crece muy rápido.

## Poda Alfa-Beta
Mismo resultado que Minimax, pero sin explorar ramas inútiles:
• α = lo mejor que MAX tiene asegurado hasta ahora.
• β = lo mejor que MIN tiene asegurado hasta ahora.
• Si en un nodo α ≥ β, el resto de hermanos no puede cambiar la decisión → se PODAN.
Ordenar las jugadas (las que más avanzan primero) hace que se pode muchísimo más.

## Solo función de evaluación (voraz)
No mira al futuro: prueba cada jugada propia y elige la de mejor f(estado). Es rápida pero "miope": cae en trampas que Minimax ve.

## Cómo leer la traza
▶ inicio del turno · ★ nueva mejor jugada · ✂ poda · ✔ jugada elegida · 📊 estadísticas.
Compara el número de NODOS entre Minimax y Alfa-Beta con la misma profundidad: el resultado es igual, pero Alfa-Beta explora muchísimos menos nodos.

## Consejos
• Minimax puro: profundidad 1-3 (la 3 puede tardar unos segundos).
• Alfa-Beta: profundidad 1-4.
• 💡 Sugerir jugada: la IA te recomienda movimiento y te explica por qué.
"""


# =====================================================================
# 6. INTERFAZ GRÁFICA
# =====================================================================
BG = "#17212b"
PANEL = "#1f2d3a"
TEXT = "#ecf0f1"
ACCENT = "#f5b041"
RED = "#e74c3c"
RED_D = "#922b21"
BLUE = "#3498db"
BLUE_D = "#1b4f72"

DX, DY = 17, 30
MX, MY = 46, 52
CANVAS_W = 24 * DX + 2 * MX
CANVAS_H = 16 * DY + 2 * MY
HOLE_R, PIECE_R = 11, 13
MAX_PLIES = 600


def pxy(r, x):
    return MX + x * DX, MY + r * DY


def cell_xy(i):
    r, x = CELLS[i]
    return pxy(r, x)


STAR_POINTS = [(0, 12), (4, 16), (4, 24), (8, 20), (12, 24), (12, 16),
               (16, 12), (12, 8), (12, 0), (8, 4), (4, 0), (4, 8)]


class App:
    def __init__(self, root):
        self.root = root
        root.title("Damas Chinas · Agente con Minimax y Poda Alfa-Beta")
        root.configure(bg=BG)
        root.geometry(f"{CANVAS_W + 560}x{CANVAS_H + 20}")
        root.minsize(CANVAS_W + 520, CANVAS_H)

        self.mode = tk.StringVar(value="IAvIA")
        self.algo = tk.StringVar(value="ALFABETA")
        self.depth = tk.IntVar(value=3)
        self.step_by_step = tk.BooleanVar(value=True)

        self.q = queue.Queue()
        self.token = 0
        self.thinking = False
        self.cancel = threading.Event()
        self.next_ai = 0.0

        self._build_ui()
        self.new_game(first=True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(40, self.tick)

    # ---------- construcción de la interfaz ----------
    def _build_ui(self):
        self.canvas = tk.Canvas(self.root, width=CANVAS_W, height=CANVAS_H, bg=BG, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(10, 0), pady=10)
        self.canvas.bind("<Button-1>", self.on_click)

        side = tk.Frame(self.root, bg=PANEL)
        side.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(side, text="⬡  DAMAS CHINAS · AGENTE IA", font=("Segoe UI", 14, "bold"),
                 fg=ACCENT, bg=PANEL).pack(pady=(10, 4))

        cfg = tk.Frame(side, bg=PANEL)
        cfg.pack(fill=tk.X, padx=14)

        def group(title, var, options, col):
            f = tk.LabelFrame(cfg, text=title, fg=TEXT, bg=PANEL, font=("Segoe UI", 9, "bold"),
                              bd=1, relief=tk.GROOVE)
            f.grid(row=0, column=col, sticky="nsew", padx=3, pady=4)
            for text, val in options:
                tk.Radiobutton(f, text=text, variable=var, value=val, fg=TEXT, bg=PANEL,
                               selectcolor=BG, activebackground=PANEL, activeforeground=ACCENT,
                               font=("Segoe UI", 9), anchor="w",
                               command=self.on_config_change).pack(fill=tk.X, padx=6)

        group("MODO", self.mode, [("Humano vs IA", "HvIA"), ("Humano vs Humano", "HvH"),
                                  ("IA vs IA", "IAvIA")], 0)
        group("ALGORITMO", self.algo, [("Minimax", "MINIMAX"), ("Poda Alfa-Beta", "ALFABETA"),
                                       ("Solo evaluación", "EVAL")], 1)
        cfg.grid_columnconfigure(0, weight=1)
        cfg.grid_columnconfigure(1, weight=1)

        row = tk.Frame(side, bg=PANEL)
        row.pack(fill=tk.X, padx=14, pady=2)
        tk.Label(row, text="Profundidad:", fg=TEXT, bg=PANEL, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Spinbox(row, from_=1, to=4, width=3, textvariable=self.depth, font=("Segoe UI", 10),
                   state="readonly", readonlybackground="#34495e", fg="white").pack(side=tk.LEFT, padx=6)
        
        tk.Checkbutton(row, text="Paso a paso", variable=self.step_by_step, bg=PANEL, fg=TEXT,
                       selectcolor=BG, activebackground=PANEL, activeforeground=ACCENT,
                       font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=6)

        self.lbl_warn = tk.Label(row, text="", fg="#e67e22", bg=PANEL, font=("Segoe UI", 8))
        self.lbl_warn.pack(side=tk.LEFT, padx=4)

        btns = tk.Frame(side, bg=PANEL)
        btns.pack(fill=tk.X, padx=14, pady=6)
        for text, cmd in [("🔄 Nueva", self.new_game), ("💡 Sugerir", self.hint_request),
                          ("⏭ Paso IA", self.force_ai_move), ("🧹 Limpiar", self.clear_log)]:
            tk.Button(btns, text=text, command=cmd, bg="#34495e", fg="white", relief=tk.FLAT,
                      activebackground="#4a6278", activeforeground="white", font=("Segoe UI", 9),
                      padx=5, pady=3).pack(side=tk.LEFT, padx=3)

        self.lbl_turn = tk.Label(side, text="", font=("Segoe UI", 12, "bold"), fg=TEXT, bg=PANEL, anchor="w")
        self.lbl_turn.pack(fill=tk.X, padx=16, pady=(6, 0))

        self.lbl_eval = tk.Label(side, text="", font=("Consolas", 9), fg=TEXT, bg=PANEL, anchor="w", justify="left")
        self.lbl_eval.pack(fill=tk.X, padx=16)
        self.bar = tk.Canvas(side, height=14, bg=PANEL, highlightthickness=0)
        self.bar.pack(fill=tk.X, padx=16, pady=(2, 4))

        self.lbl_prog = tk.Label(side, text="", fg="#2ecc71", bg=PANEL, font=("Segoe UI", 9), anchor="w")
        self.lbl_prog.pack(fill=tk.X, padx=16)
        self.pbar = ttk.Progressbar(side, mode="determinate")
        self.pbar.pack(fill=tk.X, padx=16, pady=(0, 6))

        nb = ttk.Notebook(side)
        nb.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        tab_log = tk.Frame(nb, bg="#101820")
        tab_th = tk.Frame(nb, bg="#101820")
        nb.add(tab_log, text="  🧠 Traza de la IA  ")
        nb.add(tab_th, text="  📘 ¿Cómo funciona?  ")

        self.logbox = self._make_text(tab_log, "Consolas", 9)
        for tag, color in [("title", ACCENT), ("info", "#d5dbdb"), ("good", "#58d68d"), ("prune", "#f0b27a"),
                           ("dim", "#7f8c8d"), ("warn", "#ec7063"), ("human", "#5dade2"), ("ai", "#ec7063")]:
            self.logbox.tag_config(tag, foreground=color,
                                   font=("Consolas", 9, "bold") if tag == "title" else ("Consolas", 9))

        th = self._make_text(tab_th, "Segoe UI", 10)
        th.tag_config("h", foreground=ACCENT, font=("Segoe UI", 11, "bold"), spacing1=8, spacing3=2)
        th.tag_config("p", foreground="#d5dbdb")
        th.config(state=tk.NORMAL)
        for line in THEORY.splitlines():
            if line.startswith("## "):
                th.insert(tk.END, line[3:] + "\n", "h")
            else:
                th.insert(tk.END, line + "\n", "p")
        th.config(state=tk.DISABLED)

    def _make_text(self, parent, font, size):
        sb = tk.Scrollbar(parent)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        t = tk.Text(parent, bg="#101820", fg="#d5dbdb", font=(font, size), wrap=tk.WORD, bd=0,
                    padx=8, pady=6, yscrollcommand=sb.set, state=tk.DISABLED)
        t.pack(fill=tk.BOTH, expand=True)
        sb.config(command=t.yview)
        return t

    # ---------- registro ----------
    def log(self, text, tag="info"):
        self.logbox.config(state=tk.NORMAL)
        self.logbox.insert(tk.END, text + "\n", tag)
        if int(self.logbox.index("end-1c").split(".")[0]) > 900:
            self.logbox.delete("1.0", "200.0")
        self.logbox.see(tk.END)
        self.logbox.config(state=tk.DISABLED)

    def clear_log(self):
        self.logbox.config(state=tk.NORMAL)
        self.logbox.delete("1.0", tk.END)
        self.logbox.config(state=tk.DISABLED)

    # ---------- control de partida ----------
    def new_game(self, first=False):
        self.token += 1
        self.cancel.set()
        self.cancel = threading.Event()
        self.thinking = False
        self.board = Board()
        self.turn = MINP                       # empieza AZUL (el humano en Humano vs IA)
        self.selected = None
        self.possible = []
        self.hint = None
        self.last_move = None
        self.winner = None
        self.ply = 0
        self.next_ai = time.time() + 0.6
        self.lbl_prog.config(text="")
        self.pbar["value"] = 0
        self.on_config_change()
        self.clear_log()
        self.log("¡Partida lista! Tablero de 121 casillas, 10 fichas por jugador.", "title")
        if self.mode.get() == "HvIA":
            self.log("Tú eres AZUL (abajo). Selecciona una ficha y haz clic en un punto verde.", "info")
        self.update_status()
        self.draw_board()

    def on_config_change(self):
        a, d = self.algo.get(), self.depth.get()
        if a == "MINIMAX" and d > 3:
            self.depth.set(3)
            d = 3
        if a == "MINIMAX" and d == 3:
            self.lbl_warn.config(text="⚠ puede tardar unos segundos")
        elif a == "ALFABETA" and d == 4:
            self.lbl_warn.config(text="⚠ puede tardar")
        else:
            self.lbl_warn.config(text="")
        if hasattr(self, "board"):
            self.update_status()

    def human_controls(self, p):
        m = self.mode.get()
        return m == "HvH" or (m == "HvIA" and p == MINP)

    def who(self, p):
        m = self.mode.get()
        if m == "HvH":
            return f"Jugador {1 if p == MINP else 2}"
        if m == "HvIA":
            return "Humano" if p == MINP else "IA"
        return "IA"

    def update_status(self):
        if self.winner:
            txt = f"🏆 ¡Gana {NAMES[self.winner]} ({self.who(self.winner)})!"
            col = BLUE if self.winner == MINP else RED
        elif self.winner is None and self.ply >= MAX_PLIES:
            txt, col = "🤝 Empate por límite de jugadas", TEXT
        else:
            dot = "🔵" if self.turn == MINP else "🔴"
            extra = "  ⏳ pensando…" if self.thinking else ""
            txt = f"Turno: {dot} {NAMES[self.turn]} ({self.who(self.turn)}){extra}"
            col = BLUE if self.turn == MINP else RED
        self.lbl_turn.config(text=txt, fg=col)
        self.update_eval()

    def update_eval(self):
        e = evaluate(self.board)
        _, sr, wr = player_score(self.board, MAXP)
        _, sb, wb = player_score(self.board, MINP)
        _, sr_, wr_ = player_score(self.board, MAXP)
        self.lbl_eval.config(
            text=f"f(estado) = {e:+.1f}   (+ favorece ROJO · − favorece AZUL)\n"
                 f"ROJO: Σdist={sr:>3}  atrasada={wr:>2}  en meta={self.board.goal_count[MAXP]}/10\n"
                 f"AZUL: Σdist={sb:>3}  atrasada={wb:>2}  en meta={self.board.goal_count[MINP]}/10")
        self.bar.update_idletasks()
        w = max(self.bar.winfo_width(), 200)
        frac = 1 / (1 + math.exp(-e / 40.0))
        self.bar.delete("all")
        self.bar.create_rectangle(0, 0, w, 14, fill=BLUE_D, outline="")
        self.bar.create_rectangle(0, 0, w * frac, 14, fill=RED_D, outline="")
        self.bar.create_line(w / 2, 0, w / 2, 14, fill="#bdc3c7")

    # ---------- aplicar jugadas ----------
    def apply_move(self, player, move, source):
        self.board.do(move, player)
        self.last_move = (player, move)
        self.selected, self.possible, self.hint = None, [], None
        self.ply += 1
        icon = "👤" if source == "human" else "🤖"
        self.log(f"{icon} {NAMES[player]} movió {label(move[0])} → {label(move[1])}",
                 "human" if player == MINP else "ai")
        if self.board.goal_count[player] == 10:
            self.winner = player
            self.log(f"🏆 ¡{NAMES[player]} llevó sus 10 fichas a la meta y GANA!", "good")
        else:
            self.turn = OTHER[player]
            self.next_ai = time.time() + (0.5 if self.mode.get() == "IAvIA" else 0.3)
            if self.ply >= MAX_PLIES:
                self.log("Se alcanzó el límite de jugadas: empate.", "warn")
        self.update_status()
        self.draw_board()

    # ---------- IA en hilo aparte ----------
    def force_ai_move(self):
        """Obliga a la IA a jugar su turno si estamos en modo manual."""
        if self.winner or self.thinking or self.ply >= MAX_PLIES:
            return
        if not self.human_controls(self.turn):
            self.start_search("play")
"""
DAMAS CHINAS - Agente inteligente (Minimax, Poda Alfa-Beta y Función de Evaluación)
-----------------------------------------------------------------------------------
* Tablero estrella de 121 casillas (hexagonal), 10 fichas por jugador.
* Modos: Humano vs IA, Humano vs Humano e IA vs IA (con avance paso a paso manual).
* Panel lateral que EXPLICA lo que hace el algoritmo (traza en vivo + teoría).
* Solo usa la librería estándar (tkinter). Ejecutar: python damas_chinas.py
"""
import math
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

# =====================================================================
# 1. GEOMETRÍA DEL TABLERO (estrella de 6 puntas)
# =====================================================================
ROW_COUNTS = [1, 2, 3, 4, 13, 12, 11, 10, 9, 10, 11, 12, 13, 4, 3, 2, 1]
CENTER_X = 12

CELLS = []      # índice -> (fila, x)
ROWPOS = []     # índice -> posición dentro de su fila
INDEX = {}      # (fila, x) -> índice
for _r, _n in enumerate(ROW_COUNTS):
    for _k in range(_n):
        _x = CENTER_X - (_n - 1) + 2 * _k
        INDEX[(_r, _x)] = len(CELLS)
        CELLS.append((_r, _x))
        ROWPOS.append(_k)
N = len(CELLS)  # 121

STEP_DIRS = [(0, -2), (0, 2), (-1, -1), (-1, 1), (1, -1), (1, 1)]
NEIGH = [[] for _ in range(N)]
JUMPS = [[] for _ in range(N)]
for _i, (_r, _x) in enumerate(CELLS):
    for _dr, _dx in STEP_DIRS:
        _j = INDEX.get((_r + _dr, _x + _dx))
        if _j is None:
            continue
        NEIGH[_i].append(_j)
        _l = INDEX.get((_r + 2 * _dr, _x + 2 * _dx))
        if _l is not None:
            JUMPS[_i].append((_j, _l))

MAXP, MINP = 1, 2                      # MAX = ROJO (arriba)  |  MIN = AZUL (abajo)
OTHER = {MAXP: MINP, MINP: MAXP}
NAMES = {MAXP: "ROJO", MINP: "AZUL"}

TOP_CELLS = [i for i, (r, _) in enumerate(CELLS) if r <= 3]       # 10 casillas
BOTTOM_CELLS = [i for i, (r, _) in enumerate(CELLS) if r >= 13]   # 10 casillas
GOAL_SET = {MAXP: frozenset(BOTTOM_CELLS), MINP: frozenset(TOP_CELLS)}
TIP = {MAXP: INDEX[(16, 12)], MINP: INDEX[(0, 12)]}               # vértice de la meta


def hex_dist(a: int, b: int) -> int:
    (r1, x1), (r2, x2) = CELLS[a], CELLS[b]
    dr, dx = abs(r1 - r2), abs(x1 - x2)
    return dr + max(0, (dx - dr) // 2)


DIST = {p: [hex_dist(i, TIP[p]) for i in range(N)] for p in (MAXP, MINP)}


def label(i: int) -> str:
    return f"F{CELLS[i][0] + 1}·C{ROWPOS[i] + 1}"


# =====================================================================
# 2. ESTADO DEL JUEGO
# =====================================================================
class Board:
    __slots__ = ("occ", "pieces", "goal_count")

    def __init__(self):
        self.occ = [0] * N
        self.pieces = {MAXP: set(TOP_CELLS), MINP: set(BOTTOM_CELLS)}
        self.goal_count = {MAXP: 0, MINP: 0}
        for i in TOP_CELLS:
            self.occ[i] = MAXP
        for i in BOTTOM_CELLS:
            self.occ[i] = MINP

    def copy(self) -> "Board":
        b = Board.__new__(Board)
        b.occ = self.occ[:]
        b.pieces = {MAXP: set(self.pieces[MAXP]), MINP: set(self.pieces[MINP])}
        b.goal_count = dict(self.goal_count)
        return b

    def dests(self, s: int):
        occ = self.occ
        out = [n for n in NEIGH[s] if occ[n] == 0]
        saved = occ[s]
        occ[s] = 0
        seen = {s}
        stack = [s]
        while stack:
            cur = stack.pop()
            for over, land in JUMPS[cur]:
                if occ[over] and occ[land] == 0 and land not in seen:
                    seen.add(land)
                    out.append(land)
                    stack.append(land)
        occ[s] = saved
        return out

    def moves(self, player: int):
        res = []
        for s in self.pieces[player]:
            for d in self.dests(s):
                res.append((s, d))
        return res

    def do(self, move, p: int):
        s, d = move
        self.occ[s] = 0
        self.occ[d] = p
        pcs = self.pieces[p]
        pcs.remove(s)
        pcs.add(d)
        g = GOAL_SET[p]
        if s in g:
            self.goal_count[p] -= 1
        if d in g:
            self.goal_count[p] += 1

    def undo(self, move, p: int):
        s, d = move
        self.occ[d] = 0
        self.occ[s] = p
        pcs = self.pieces[p]
        pcs.remove(d)
        pcs.add(s)
        g = GOAL_SET[p]
        if d in g:
            self.goal_count[p] -= 1
        if s in g:
            self.goal_count[p] += 1


# =====================================================================
# 3. FUNCIÓN DE EVALUACIÓN HEURÍSTICA
# =====================================================================
W_SUM, W_LAG, W_GOAL = 2.0, 1.0, 3.0
WIN = 100000


def player_score(b: Board, p: int):
    d = DIST[p]
    total = 0
    worst = 0
    for i in b.pieces[p]:
        v = d[i]
        total += v
        if v > worst:
            worst = v
    score = -(W_SUM * total + W_LAG * worst) + W_GOAL * b.goal_count[p]
    return score, total, worst


def evaluate(b: Board) -> float:
    return player_score(b, MAXP)[0] - player_score(b, MINP)[0]


# =====================================================================
# 4. BÚSQUEDA: MINIMAX, ALFA-BETA y VORAZ (solo evaluación)
# =====================================================================
class Cancelled(Exception):
    pass


def fmt(v: float) -> str:
    if v == float("inf"):
        return "+∞"
    if v == -float("inf"):
        return "-∞"
    return f"{v:+.1f}"


ALGO_NAMES = {
    "MINIMAX": "Minimax puro",
    "ALFABETA": "Minimax con poda Alfa-Beta",
    "EVAL": "Solo función de evaluación (voraz)",
}


class Searcher:
    def __init__(self, board: Board, player: int, depth: int, algo: str, emit, cancel):
        self.b = board
        self.player = player
        self.depth = depth
        self.algo = algo
        self.emit = emit
        self.cancel = cancel
        self.nodes = 0
        self.leaves = 0
        self.prunes = 0
        self.pruned_moves = 0
        self.prune_logged = 0

    def check(self):
        if self.cancel.is_set():
            raise Cancelled()

    def ordered(self, player):
        moves = self.b.moves(player)
        d = DIST[player]
        moves.sort(key=lambda m: d[m[1]] - d[m[0]])
        return moves

    def terminal(self, depth):
        gc = self.b.goal_count
        if gc[MAXP] == 10:
            return WIN + depth
        if gc[MINP] == 10:
            return -(WIN + depth)
        return None

    def minimax(self, depth, player):
        self.nodes += 1
        if self.nodes % 2000 == 0:
            self.check()
        t = self.terminal(depth)
        if t is not None:
            return t
        if depth == 0:
            self.leaves += 1
            return evaluate(self.b)
        moves = self.b.moves(player)
        if not moves:
            self.leaves += 1
            return evaluate(self.b)
        if player == MAXP:
            v = -float("inf")
            for m in moves:
                self.b.do(m, player)
                c = self.minimax(depth - 1, MINP)
                self.b.undo(m, player)
                if c > v:
                    v = c
            return v
        v = float("inf")
        for m in moves:
            self.b.do(m, player)
            c = self.minimax(depth - 1, MAXP)
            self.b.undo(m, player)
            if c < v:
                v = c
        return v

    def ab(self, depth, player, alpha, beta, level):
        self.nodes += 1
        if self.nodes % 2000 == 0:
            self.check()
        t = self.terminal(depth)
        if t is not None:
            return t
        if depth == 0:
            self.leaves += 1
            return evaluate(self.b)
        moves = self.ordered(player)
        if not moves:
            self.leaves += 1
            return evaluate(self.b)
        n = len(moves)
        if player == MAXP:
            v = -float("inf")
            for idx, m in enumerate(moves):
                self.b.do(m, player)
                c = self.ab(depth - 1, MINP, alpha, beta, level + 1)
                self.b.undo(m, player)
                if c > v:
                    v = c
                if v > alpha:
                    alpha = v
                if v >= beta:
                    self._prune("β", "MAX", level, v, alpha, beta, n - idx - 1)
                    break
            return v
        v = float("inf")
        for idx, m in enumerate(moves):
            self.b.do(m, player)
            c = self.ab(depth - 1, MAXP, alpha, beta, level + 1)
            self.b.undo(m, player)
            if c < v:
                v = c
            if v < beta:
                beta = v
            if v <= alpha:
                self._prune("α", "MIN", level, v, alpha, beta, n - idx - 1)
                break
        return v

    def _prune(self, kind, role, level, v, alpha, beta, remaining):
        self.prunes += 1
        self.pruned_moves += remaining
        if remaining <= 0 or self.prune_logged >= 5:
            return
        self.prune_logged += 1
        if kind == "β":
            txt = (f"  ✂ PODA β (nivel {level}, nodo MAX): valor {fmt(v)} ≥ β={fmt(beta)}. "
                   f"MIN ya tiene una opción mejor arriba y nunca dejaría llegar aquí → "
                   f"descarto {remaining} jugada(s) sin evaluarlas.")
        else:
            txt = (f"  ✂ PODA α (nivel {level}, nodo MIN): valor {fmt(v)} ≤ α={fmt(alpha)}. "
                   f"MAX ya tiene una opción mejor arriba y no elegiría esta rama → "
                   f"descarto {remaining} jugada(s) sin evaluarlas.")
        self.emit("log", txt, "prune")

    def run(self):
        t0 = time.time()
        p = self.player
        b = self.b
        maximizing = (p == MAXP)
        role = "MAX (maximiza)" if maximizing else "MIN (minimiza)"
        depth = 1 if self.algo == "EVAL" else self.depth

        self.emit("log", f"▶ Turno de {NAMES[p]} — {ALGO_NAMES[self.algo]}"
                         + ("" if self.algo == "EVAL" else f", profundidad {depth}"), "title")

        moves = self.ordered(p) if self.algo == "ALFABETA" else b.moves(p)
        if not moves:
            self.emit("log", "No hay jugadas legales.", "warn")
            return None
        self.emit("log", f"Nivel 0 · {role}: {len(moves)} jugadas legales "
                         f"(pasos + saltos encadenados).", "info")
        if self.algo == "ALFABETA":
            self.emit("log", "Ordeno las jugadas por avance hacia la meta: probar primero "
                             "las buenas hace que las podas ocurran antes.", "info")
        elif self.algo == "MINIMAX":
            self.emit("log", "Sin poda: se visita TODO el árbol hasta la profundidad pedida.", "info")
        else:
            self.emit("log", "Sin mirar al futuro: pruebo cada jugada y me quedo con la que "
                             "deja la mejor evaluación inmediata.", "info")

        best_move = None
        best_val = -float("inf") if maximizing else float("inf")
        alpha, beta = -float("inf"), float("inf")
        ranking = []
        total = len(moves)

        for idx, m in enumerate(moves):
            self.check()
            self.emit("progress", idx + 1, total)
            b.do(m, p)
            if self.algo == "EVAL":
                self.nodes += 1
                self.leaves += 1
                t = self.terminal(0)
                val = t if t is not None else evaluate(b)
            elif self.algo == "MINIMAX":
                val = self.minimax(depth - 1, OTHER[p])
            else:
                val = self.ab(depth - 1, OTHER[p], alpha, beta, 1)
            b.undo(m, p)
            ranking.append((val, m))

            better = val > best_val if maximizing else val < best_val
            if better or best_move is None:
                best_val, best_move = val, m
                self.emit("log", f"  ★ Nueva mejor jugada: {label(m[0])} → {label(m[1])}  "
                                 f"valor {fmt(val)}", "good")
                if self.algo == "ALFABETA":
                    if maximizing:
                        alpha = max(alpha, val)
                    else:
                        beta = min(beta, val)
                    self.emit("log", f"    ventana actualizada: α={fmt(alpha)}  β={fmt(beta)}", "dim")

        dt = time.time() - t0
        if self.algo != "ALFABETA":
            top = sorted(ranking, key=lambda t: t[0], reverse=maximizing)[:3]
            self.emit("log", "Top 3 jugadas de la raíz:", "info")
            for k, (v, m) in enumerate(top, 1):
                self.emit("log", f"   {k}. {label(m[0])} → {label(m[1])}   valor {fmt(v)}", "dim")

        self.emit("log", f"✔ ELEGIDA: {label(best_move[0])} → {label(best_move[1])}  "
                         f"(valor {fmt(best_val)})", "good")
        self.emit("log", f"📊 Nodos visitados: {self.nodes:,} · hojas evaluadas: {self.leaves:,} "
                         f"· tiempo: {dt:.2f}s", "info")
        if self.algo == "ALFABETA":
            self.emit("log", f"✂ Podas realizadas: {self.prunes:,} · jugadas descartadas sin "
                             f"explorar: {self.pruned_moves:,}", "prune")
        side = "ROJO" if best_val > 0 else "AZUL" if best_val < 0 else "nadie"
        if abs(best_val) >= WIN:
            self.emit("log", f"🏁 ¡{NAMES[p]} encuentra una victoria forzada!", "good")
        else:
            self.emit("log", f"Lectura: si ambos juegan lo mejor posible durante {depth} jugada(s), "
                             f"la posición queda a favor de {side} (valor positivo = ROJO, "
                             f"negativo = AZUL).", "dim")
        self.emit("log", "─" * 46, "dim")
        return {"move": best_move, "value": best_val}


# =====================================================================
# 5. TEXTO TEÓRICO PARA EL PANEL "¿CÓMO FUNCIONA?"
# =====================================================================
THEORY = """## Objetivo
Llevar tus 10 fichas al triángulo opuesto antes que el rival. ROJO (MAX) empieza arriba, AZUL (MIN) abajo.

## Movimientos
• Paso: a una casilla vecina libre (6 direcciones).
• Salto: sobre una ficha (propia o ajena) hacia la casilla libre justo detrás.
• Saltos encadenados: si desde donde aterrizas puedes volver a saltar, lo haces en el mismo turno.

## Función de evaluación (heurística)
Mide "qué tan buena" es una posición sin seguir jugando:
   puntaje(jugador) = −(2·Σdistancias + 1·ficha_más_atrasada) + 3·fichas_en_meta
   f(estado) = puntaje(ROJO) − puntaje(AZUL)
• Σdistancias: suma de pasos de cada ficha hasta el vértice de la meta.
• Ficha más atrasada: castiga dejar fichas rezagadas (en damas chinas, la última ficha decide).
• Valor positivo = ventaja de ROJO. Negativo = ventaja de AZUL.

## Minimax
ROJO (MAX) busca el valor más ALTO; AZUL (MIN) el más BAJO. La IA simula sus jugadas, las respuestas del rival, sus respuestas a eso... hasta la profundidad elegida, evalúa las hojas con f(estado) y sube los valores: MAX toma el máximo de sus hijos, MIN el mínimo. Así elige la jugada que es mejor suponiendo que el rival responde lo mejor posible.
Coste: b^d nodos (b≈40-70 jugadas) → crece muy rápido.

## Poda Alfa-Beta
Mismo resultado que Minimax, pero sin explorar ramas inútiles:
• α = lo mejor que MAX tiene asegurado hasta ahora.
• β = lo mejor que MIN tiene asegurado hasta ahora.
• Si en un nodo α ≥ β, el resto de hermanos no puede cambiar la decisión → se PODAN.
Ordenar las jugadas (las que más avanzan primero) hace que se pode muchísimo más.

## Solo función de evaluación (voraz)
No mira al futuro: prueba cada jugada propia y elige la de mejor f(estado). Es rápida pero "miope": cae en trampas que Minimax ve.

## Cómo leer la traza
▶ inicio del turno · ★ nueva mejor jugada · ✂ poda · ✔ jugada elegida · 📊 estadísticas.
Compara el número de NODOS entre Minimax y Alfa-Beta con la misma profundidad: el resultado es igual, pero Alfa-Beta explora muchísimos menos nodos.

## Consejos
• Minimax puro: profundidad 1-3.
• Alfa-Beta: profundidad 1-4.
• Modo Paso a paso: Usa el botón 'Siguiente Jugada' para pausar y explicar cada decisión.
"""


# =====================================================================
# 6. INTERFAZ GRÁFICA
# =====================================================================
BG = "#17212b"
PANEL = "#1f2d3a"
TEXT = "#ecf0f1"
ACCENT = "#f5b041"
RED = "#e74c3c"
RED_D = "#922b21"
BLUE = "#3498db"
BLUE_D = "#1b4f72"

DX, DY = 17, 30
MX, MY = 46, 52
CANVAS_W = 24 * DX + 2 * MX
CANVAS_H = 16 * DY + 2 * MY
HOLE_R, PIECE_R = 11, 13
MAX_PLIES = 600


def pxy(r, x):
    return MX + x * DX, MY + r * DY


def cell_xy(i):
    r, x = CELLS[i]
    return pxy(r, x)


STAR_POINTS = [(0, 12), (4, 16), (4, 24), (8, 20), (12, 24), (12, 16),
               (16, 12), (12, 8), (12, 0), (8, 4), (4, 0), (4, 8)]


class App:
    def __init__(self, root):
        self.root = root
        root.title("Damas Chinas · Agente con Minimax y Poda Alfa-Beta")
        root.configure(bg=BG)
        root.geometry(f"{CANVAS_W + 560}x{CANVAS_H + 30}")
        root.minsize(CANVAS_W + 520, CANVAS_H)

        self.mode = tk.StringVar(value="IAvIA")
        self.algo = tk.StringVar(value="ALFABETA")
        self.depth = tk.IntVar(value=3)
        self.manual_step = tk.BooleanVar(value=True)

        self.q = queue.Queue()
        self.token = 0
        self.thinking = False
        self.cancel = threading.Event()
        self.next_ai = 0.0

        self._build_ui()
        self.new_game(first=True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(40, self.tick)

    def _build_ui(self):
        self.canvas = tk.Canvas(self.root, width=CANVAS_W, height=CANVAS_H, bg=BG, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(10, 0), pady=10)
        self.canvas.bind("<Button-1>", self.on_click)

        side = tk.Frame(self.root, bg=PANEL)
        side.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(side, text="⬡  DAMAS CHINAS · AGENTE IA", font=("Segoe UI", 14, "bold"),
                 fg=ACCENT, bg=PANEL).pack(pady=(10, 4))

        cfg = tk.Frame(side, bg=PANEL)
        cfg.pack(fill=tk.X, padx=14)

        def group(title, var, options, col):
            f = tk.LabelFrame(cfg, text=title, fg=TEXT, bg=PANEL, font=("Segoe UI", 9, "bold"),
                              bd=1, relief=tk.GROOVE)
            f.grid(row=0, column=col, sticky="nsew", padx=3, pady=4)
            for text, val in options:
                tk.Radiobutton(f, text=text, variable=var, value=val, fg=TEXT, bg=PANEL,
                               selectcolor=BG, activebackground=PANEL, activeforeground=ACCENT,
                               font=("Segoe UI", 9), anchor="w",
                               command=self.on_config_change).pack(fill=tk.X, padx=6)

        group("MODO", self.mode, [("Humano vs IA", "HvIA"), ("Humano vs Humano", "HvH"),
                                  ("IA vs IA", "IAvIA")], 0)
        group("ALGORITMO", self.algo, [("Minimax", "MINIMAX"), ("Poda Alfa-Beta", "ALFABETA"),
                                       ("Solo evaluación", "EVAL")], 1)
        cfg.grid_columnconfigure(0, weight=1)
        cfg.grid_columnconfigure(1, weight=1)

        row = tk.Frame(side, bg=PANEL)
        row.pack(fill=tk.X, padx=14, pady=2)
        tk.Label(row, text="Profundidad:", fg=TEXT, bg=PANEL, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Spinbox(row, from_=1, to=4, width=3, textvariable=self.depth, font=("Segoe UI", 10),
                   state="readonly", readonlybackground="#34495e", fg="white").pack(side=tk.LEFT, padx=6)

        tk.Checkbutton(row, text="Paso a paso (Manual)", variable=self.manual_step, bg=PANEL, fg=TEXT,
                       selectcolor=BG, activebackground=PANEL, activeforeground=ACCENT,
                       font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10)

        self.lbl_warn = tk.Label(row, text="", fg="#e67e22", bg=PANEL, font=("Segoe UI", 8))
        self.lbl_warn.pack(side=tk.LEFT, padx=4)

        # Botón dedicado para avanzar paso a paso
        step_btn_frame = tk.Frame(side, bg=PANEL)
        step_btn_frame.pack(fill=tk.X, padx=14, pady=(6, 2))
        self.btn_next = tk.Button(step_btn_frame, text="▶ Siguiente Jugada (IA)", command=self.step_ai,
                                  bg="#d35400", fg="white", activebackground="#e67e22", activeforeground="white",
                                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, pady=5)
        self.btn_next.pack(fill=tk.X)

        btns = tk.Frame(side, bg=PANEL)
        btns.pack(fill=tk.X, padx=14, pady=4)
        for text, cmd in [("🔄 Nueva", self.new_game), ("💡 Sugerir", self.hint_request),
                          ("🧹 Limpiar traza", self.clear_log)]:
            tk.Button(btns, text=text, command=cmd, bg="#34495e", fg="white", relief=tk.FLAT,
                      activebackground="#4a6278", activeforeground="white", font=("Segoe UI", 9),
                      padx=6, pady=3).pack(side=tk.LEFT, padx=2)

        self.lbl_turn = tk.Label(side, text="", font=("Segoe UI", 12, "bold"), fg=TEXT, bg=PANEL, anchor="w")
        self.lbl_turn.pack(fill=tk.X, padx=16, pady=(6, 0))

        self.lbl_eval = tk.Label(side, text="", font=("Consolas", 9), fg=TEXT, bg=PANEL, anchor="w", justify="left")
        self.lbl_eval.pack(fill=tk.X, padx=16)
        self.bar = tk.Canvas(side, height=14, bg=PANEL, highlightthickness=0)
        self.bar.pack(fill=tk.X, padx=16, pady=(2, 4))

        self.lbl_prog = tk.Label(side, text="", fg="#2ecc71", bg=PANEL, font=("Segoe UI", 9), anchor="w")
        self.lbl_prog.pack(fill=tk.X, padx=16)
        self.pbar = ttk.Progressbar(side, mode="determinate")
        self.pbar.pack(fill=tk.X, padx=16, pady=(0, 6))

        nb = ttk.Notebook(side)
        nb.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        tab_log = tk.Frame(nb, bg="#101820")
        tab_th = tk.Frame(nb, bg="#101820")
        nb.add(tab_log, text="  🧠 Traza de la IA  ")
        nb.add(tab_th, text="  📘 ¿Cómo funciona?  ")

        self.logbox = self._make_text(tab_log, "Consolas", 9)
        for tag, color in [("title", ACCENT), ("info", "#d5dbdb"), ("good", "#58d68d"), ("prune", "#f0b27a"),
                           ("dim", "#7f8c8d"), ("warn", "#ec7063"), ("human", "#5dade2"), ("ai", "#ec7063")]:
            self.logbox.tag_config(tag, foreground=color,
                                   font=("Consolas", 9, "bold") if tag == "title" else ("Consolas", 9))

        th = self._make_text(tab_th, "Segoe UI", 10)
        th.tag_config("h", foreground=ACCENT, font=("Segoe UI", 11, "bold"), spacing1=8, spacing3=2)
        th.tag_config("p", foreground="#d5dbdb")
        th.config(state=tk.NORMAL)
        for line in THEORY.splitlines():
            if line.startswith("## "):
                th.insert(tk.END, line[3:] + "\n", "h")
            else:
                th.insert(tk.END, line + "\n", "p")
        th.config(state=tk.DISABLED)

    def _make_text(self, parent, font, size):
        sb = tk.Scrollbar(parent)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        t = tk.Text(parent, bg="#101820", fg="#d5dbdb", font=(font, size), wrap=tk.WORD, bd=0,
                    padx=8, pady=6, yscrollcommand=sb.set, state=tk.DISABLED)
        t.pack(fill=tk.BOTH, expand=True)
        sb.config(command=t.yview)
        return t

    def log(self, text, tag="info"):
        self.logbox.config(state=tk.NORMAL)
        self.logbox.insert(tk.END, text + "\n", tag)
        if int(self.logbox.index("end-1c").split(".")[0]) > 900:
            self.logbox.delete("1.0", "200.0")
        self.logbox.see(tk.END)
        self.logbox.config(state=tk.DISABLED)

    def clear_log(self):
        self.logbox.config(state=tk.NORMAL)
        self.logbox.delete("1.0", tk.END)
        self.logbox.config(state=tk.DISABLED)

    def new_game(self, first=False):
        self.token += 1
        self.cancel.set()
        self.cancel = threading.Event()
        self.thinking = False
        self.board = Board()
        self.turn = MINP                       # Empieza AZUL
        self.selected = None
        self.possible = []
        self.hint = None
        self.last_move = None
        self.winner = None
        self.ply = 0
        self.next_ai = time.time() + 0.6
        self.lbl_prog.config(text="")
        self.pbar["value"] = 0
        self.on_config_change()
        self.clear_log()
        self.log("¡Partida lista! Tablero de 121 casillas, 10 fichas por jugador.", "title")
        if self.mode.get() == "IAvIA":
            self.log("Modo IA vs IA activado. Haz clic en '▶ Siguiente Jugada (IA)' para ejecutar cada turno.", "info")
        elif self.mode.get() == "HvIA":
            self.log("Tú eres AZUL (abajo). Selecciona una ficha y haz clic en un punto verde.", "info")
        self.update_status()
        self.draw_board()

    def on_config_change(self):
        a, d = self.algo.get(), self.depth.get()
        if a == "MINIMAX" and d > 3:
            self.depth.set(3)
            d = 3
        if a == "MINIMAX" and d == 3:
            self.lbl_warn.config(text="⚠ puede tardar unos segundos")
        elif a == "ALFABETA" and d == 4:
            self.lbl_warn.config(text="⚠ puede tardar")
        else:
            self.lbl_warn.config(text="")
        if hasattr(self, "board"):
            self.update_status()

    def human_controls(self, p):
        m = self.mode.get()
        return m == "HvH" or (m == "HvIA" and p == MINP)

    def who(self, p):
        m = self.mode.get()
        if m == "HvH":
            return f"Jugador {1 if p == MINP else 2}"
        if m == "HvIA":
            return "Humano" if p == MINP else "IA"
        return "IA"

    def update_status(self):
        if self.winner:
            txt = f"🏆 ¡Gana {NAMES[self.winner]} ({self.who(self.winner)})!"
            col = BLUE if self.winner == MINP else RED
        elif self.winner is None and self.ply >= MAX_PLIES:
            txt, col = "🤝 Empate por límite de jugadas", TEXT
        else:
            dot = "🔵" if self.turn == MINP else "🔴"
            extra = "  ⏳ calculando árbol…" if self.thinking else ""
            txt = f"Turno: {dot} {NAMES[self.turn]} ({self.who(self.turn)}){extra}"
            col = BLUE if self.turn == MINP else RED
        self.lbl_turn.config(text=txt, fg=col)
        self.update_eval()

    def update_eval(self):
        e = evaluate(self.board)
        _, sr, wr = player_score(self.board, MAXP)
        _, sb, wb = player_score(self.board, MINP)
        self.lbl_eval.config(
            text=f"f(estado) = {e:+.1f}   (+ favorece ROJO · − favorece AZUL)\n"
                 f"ROJO: Σdist={sr:>3}  atrasada={wr:>2}  en meta={self.board.goal_count[MAXP]}/10\n"
                 f"AZUL: Σdist={sb:>3}  atrasada={wb:>2}  en meta={self.board.goal_count[MINP]}/10")
        self.bar.update_idletasks()
        w = max(self.bar.winfo_width(), 200)
        frac = 1 / (1 + math.exp(-e / 40.0))
        self.bar.delete("all")
        self.bar.create_rectangle(0, 0, w, 14, fill=BLUE_D, outline="")
        self.bar.create_rectangle(0, 0, w * frac, 14, fill=RED_D, outline="")
        self.bar.create_line(w / 2, 0, w / 2, 14, fill="#bdc3c7")

    def apply_move(self, player, move, source):
        self.board.do(move, player)
        self.last_move = (player, move)
        self.selected, self.possible, self.hint = None, [], None
        self.ply += 1
        icon = "👤" if source == "human" else "🤖"
        self.log(f"{icon} {NAMES[player]} movió {label(move[0])} → {label(move[1])}",
                 "human" if player == MINP else "ai")
        if self.board.goal_count[player] == 10:
            self.winner = player
            self.log(f"🏆 ¡{NAMES[player]} llevó sus 10 fichas a la meta y GANA!", "good")
        else:
            self.turn = OTHER[player]
            self.next_ai = time.time() + (0.5 if self.mode.get() == "IAvIA" else 0.3)
            if self.ply >= MAX_PLIES:
                self.log("Se alcanzó el límite de jugadas: empate.", "warn")
        self.update_status()
        self.draw_board()

    def step_ai(self):
        """Ejecuta una sola jugada de la IA si es su turno."""
        if self.thinking or self.winner or self.ply >= MAX_PLIES:
            return
        if not self.human_controls(self.turn):
            self.start_search("play")

    def start_search(self, purpose):
        if self.thinking or self.winner or self.ply >= MAX_PLIES:
            return
        self.thinking = True
        token = self.token
        board = self.board.copy()
        player = self.turn
        algo, depth = self.algo.get(), self.depth.get()
        if algo == "MINIMAX" and depth > 3:
            depth = 3
        cancel = self.cancel

        def emit(kind, *payload):
            self.q.put((kind, token) + payload)

        searcher = Searcher(board, player, depth, algo, emit, cancel)
        if purpose == "hint":
            emit("log", "💡 Calculando una sugerencia para ti…", "info")

        def work():
            try:
                res = searcher.run()
                self.q.put(("done", token, purpose, player, res))
            except Cancelled:
                self.q.put(("cancelled", token))
            except Exception as ex:
                self.q.put(("error", token, str(ex)))

        threading.Thread(target=work, daemon=True).start()
        self.update_status()

    def tick(self):
        try:
            while True:
                self.handle(self.q.get_nowait())
        except queue.Empty:
            pass

        # Disparo automático: SÓLO si 'Paso a paso' está DESACTIVADO
        if (not self.thinking and not self.winner and self.ply < MAX_PLIES
                and not self.human_controls(self.turn) and time.time() >= self.next_ai):
            if not self.manual_step.get():
                self.start_search("play")

        self.root.after(40, self.tick)

    def handle(self, msg):
        kind, token = msg[0], msg[1]
        if token != self.token:
            return
        if kind == "log":
            self.log(msg[2], msg[3])
        elif kind == "progress":
            i, n = msg[2], msg[3]
            self.lbl_prog.config(text=f"Evaluando jugada raíz {i}/{n}…")
            self.pbar["maximum"] = n
            self.pbar["value"] = i
        elif kind == "done":
            self.thinking = False
            self.lbl_prog.config(text="")
            self.pbar["value"] = 0
            purpose, player, res = msg[2], msg[3], msg[4]
            if res is None:
                if purpose == "play":
                    self.log(f"{NAMES[player]} no tiene jugadas: pasa el turno.", "warn")
                    self.turn = OTHER[player]
                self.update_status()
                return
            if purpose == "hint":
                self.hint = res["move"]
                self.log(f"💡 Sugerencia: {label(self.hint[0])} → {label(self.hint[1])} (marcada en dorado)", "good")
                self.update_status()
                self.draw_board()
            else:
                self.apply_move(player, res["move"], "ai")
        elif kind == "cancelled":
            pass
        elif kind == "error":
            self.thinking = False
            self.log(f"Error en la IA: {msg[2]}", "warn")
            self.update_status()

    def hint_request(self):
        if self.winner or self.thinking:
            return
        if self.mode.get() == "IAvIA":
            self.log("En IA vs IA usa el botón de siguiente paso para ver el análisis.", "dim")
            return
        if not self.human_controls(self.turn):
            return
        self.start_search("hint")

    def cell_at(self, x, y):
        best, bd = None, 18 * 18
        for i in range(N):
            cx, cy = cell_xy(i)
            d = (cx - x) ** 2 + (cy - y) ** 2
            if d < bd:
                best, bd = i, d
        return best

    def on_click(self, e):
        if self.winner or self.thinking or not self.human_controls(self.turn):
            return
        i = self.cell_at(e.x, e.y)
        if i is None:
            return
        b = self.board
        if b.occ[i] == self.turn:
            self.selected = i
            self.possible = b.dests(i)
            self.hint = None
            self.log(f"Seleccionaste {label(i)} → {len(self.possible)} destinos posibles.", "dim")
        elif self.selected is not None and i in self.possible:
            self.apply_move(self.turn, (self.selected, i), "human")
            return
        self.draw_board()

    def draw_board(self):
        c = self.canvas
        c.delete("all")
        pts = []
        for r, x in STAR_POINTS:
            pts.extend(pxy(r, x))
        c.create_polygon(pts, fill="#5b3a1a", outline="#5b3a1a", width=44, joinstyle=tk.ROUND)
        c.create_polygon(pts, fill="#d8a45f", outline="#d8a45f", width=36, joinstyle=tk.ROUND)

        top, bottom = set(TOP_CELLS), set(BOTTOM_CELLS)
        for i in range(N):
            cx, cy = cell_xy(i)
            fill = "#e8a29b" if i in top else "#9fc4e8" if i in bottom else "#b07a42"
            c.create_oval(cx - HOLE_R, cy - HOLE_R, cx + HOLE_R, cy + HOLE_R, fill=fill, outline="#7a4e22", width=2)

        if self.last_move:
            p, (s, d) = self.last_move
            x1, y1 = cell_xy(s)
            x2, y2 = cell_xy(d)
            c.create_line(x1, y1, x2, y2, fill="#ffffff", width=2, dash=(5, 4), arrow=tk.LAST)
            c.create_oval(x1 - 16, y1 - 16, x1 + 16, y1 + 16, outline="#ffffff", width=2, dash=(3, 3))

        if self.hint:
            s, d = self.hint
            x1, y1 = cell_xy(s)
            x2, y2 = cell_xy(d)
            c.create_line(x1, y1, x2, y2, fill="#f1c40f", width=3, dash=(6, 3), arrow=tk.LAST)
            for (x, y) in ((x1, y1), (x2, y2)):
                c.create_oval(x - 17, y - 17, x + 17, y + 17, outline="#f1c40f", width=3)

        for p, fill, dark, light in ((MAXP, RED, RED_D, "#f5b7b1"), (MINP, BLUE, BLUE_D, "#aed6f1")):
            for i in self.board.pieces[p]:
                cx, cy = cell_xy(i)
                c.create_oval(cx - PIECE_R + 2, cy - PIECE_R + 3, cx + PIECE_R + 2, cy + PIECE_R + 3,
                              fill="#6b4a24", outline="")
                c.create_oval(cx - PIECE_R, cy - PIECE_R, cx + PIECE_R, cy + PIECE_R,
                              fill=fill, outline=dark, width=2)
                c.create_oval(cx - 7, cy - 8, cx - 1, cy - 3, fill=light, outline="")

        if self.selected is not None:
            cx, cy = cell_xy(self.selected)
            c.create_oval(cx - 18, cy - 18, cx + 18, cy + 18, outline="#f1c40f", width=3)
            for d in self.possible:
                x, y = cell_xy(d)
                c.create_oval(x - 6, y - 6, x + 6, y + 6, fill="#2ecc71", outline="#1e8449", width=2)

        if self.winner:
            col = BLUE if self.winner == MINP else RED
            c.create_rectangle(40, CANVAS_H // 2 - 36, CANVAS_W - 40, CANVAS_H // 2 + 36,
                               fill="#101820", outline=col, width=3)
            c.create_text(CANVAS_W // 2, CANVAS_H // 2, text=f"🏆 ¡GANA {NAMES[self.winner]}!",
                          fill=col, font=("Segoe UI", 24, "bold"))

    def on_close(self):
        self.cancel.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
    def start_search(self, purpose):
        if self.thinking or self.winner or self.ply >= MAX_PLIES:
            return
        self.thinking = True
        token = self.token
        board = self.board.copy()
        player = self.turn
        algo, depth = self.algo.get(), self.depth.get()
        if algo == "MINIMAX" and depth > 3:
            depth = 3
        cancel = self.cancel

        def emit(kind, *payload):
            self.q.put((kind, token) + payload)

        searcher = Searcher(board, player, depth, algo, emit, cancel)
        if purpose == "hint":
            emit("log", "💡 Calculando una sugerencia para ti…", "info")

        def work():
            try:
                res = searcher.run()
                self.q.put(("done", token, purpose, player, res))
            except Cancelled:
                self.q.put(("cancelled", token))
            except Exception as ex:                      # nunca dejar la UI colgada
                self.q.put(("error", token, str(ex)))

        threading.Thread(target=work, daemon=True).start()
        self.update_status()

    def tick(self):
        try:
            while True:
                self.handle(self.q.get_nowait())
        except queue.Empty:
            pass
        if (not self.thinking and not self.winner and self.ply < MAX_PLIES
                and not self.human_controls(self.turn) and time.time() >= self.next_ai):
            if not self.step_by_step.get():
                self.start_search("play")
        self.root.after(40, self.tick)

    def handle(self, msg):
        kind, token = msg[0], msg[1]
        if token != self.token:
            return
        if kind == "log":
            self.log(msg[2], msg[3])
        elif kind == "progress":
            i, n = msg[2], msg[3]
            self.lbl_prog.config(text=f"Evaluando jugada raíz {i}/{n}…")
            self.pbar["maximum"] = n
            self.pbar["value"] = i
        elif kind == "done":
            self.thinking = False
            self.lbl_prog.config(text="")
            self.pbar["value"] = 0
            purpose, player, res = msg[2], msg[3], msg[4]
            if res is None:
                if purpose == "play":
                    self.log(f"{NAMES[player]} no tiene jugadas: pasa el turno.", "warn")
                    self.turn = OTHER[player]
                self.update_status()
                return
            if purpose == "hint":
                self.hint = res["move"]
                self.log(f"💡 Sugerencia: {label(self.hint[0])} → {label(self.hint[1])} (marcada en dorado)", "good")
                self.update_status()
                self.draw_board()
            else:
                self.apply_move(player, res["move"], "ai")
        elif kind == "cancelled":
            pass
        elif kind == "error":
            self.thinking = False
            self.log(f"Error en la IA: {msg[2]}", "warn")
            self.update_status()

    def hint_request(self):
        if self.winner or self.thinking:
            return
        if self.mode.get() == "IAvIA":
            self.log("En IA vs IA la IA ya juega sola.", "dim")
            return
        if not self.human_controls(self.turn):
            return
        self.start_search("hint")

    # ---------- entrada del humano ----------
    def cell_at(self, x, y):
        best, bd = None, 18 * 18
        for i in range(N):
            cx, cy = cell_xy(i)
            d = (cx - x) ** 2 + (cy - y) ** 2
            if d < bd:
                best, bd = i, d
        return best

    def on_click(self, e):
        if self.winner or self.thinking or not self.human_controls(self.turn):
            return
        i = self.cell_at(e.x, e.y)
        if i is None:
            return
        b = self.board
        if b.occ[i] == self.turn:
            self.selected = i
            self.possible = b.dests(i)
            self.hint = None
            self.log(f"Seleccionaste {label(i)} → {len(self.possible)} destinos posibles.", "dim")
        elif self.selected is not None and i in self.possible:
            self.apply_move(self.turn, (self.selected, i), "human")
            return
        self.draw_board()

    # ---------- dibujo ----------
    def draw_board(self):
        c = self.canvas
        c.delete("all")
        pts = []
        for r, x in STAR_POINTS:
            pts.extend(pxy(r, x))
        c.create_polygon(pts, fill="#5b3a1a", outline="#5b3a1a", width=44, joinstyle=tk.ROUND)
        c.create_polygon(pts, fill="#d8a45f", outline="#d8a45f", width=36, joinstyle=tk.ROUND)

        top, bottom = set(TOP_CELLS), set(BOTTOM_CELLS)
        for i in range(N):
            cx, cy = cell_xy(i)
            fill = "#e8a29b" if i in top else "#9fc4e8" if i in bottom else "#b07a42"
            c.create_oval(cx - HOLE_R, cy - HOLE_R, cx + HOLE_R, cy + HOLE_R, fill=fill, outline="#7a4e22", width=2)

        if self.last_move:
            p, (s, d) = self.last_move
            x1, y1 = cell_xy(s)
            x2, y2 = cell_xy(d)
            c.create_line(x1, y1, x2, y2, fill="#ffffff", width=2, dash=(5, 4), arrow=tk.LAST)
            c.create_oval(x1 - 16, y1 - 16, x1 + 16, y1 + 16, outline="#ffffff", width=2, dash=(3, 3))

        if self.hint:
            s, d = self.hint
            x1, y1 = cell_xy(s)
            x2, y2 = cell_xy(d)
            c.create_line(x1, y1, x2, y2, fill="#f1c40f", width=3, dash=(6, 3), arrow=tk.LAST)
            for (x, y) in ((x1, y1), (x2, y2)):
                c.create_oval(x - 17, y - 17, x + 17, y + 17, outline="#f1c40f", width=3)

        for p, fill, dark, light in ((MAXP, RED, RED_D, "#f5b7b1"), (MINP, BLUE, BLUE_D, "#aed6f1")):
            for i in self.board.pieces[p]:
                cx, cy = cell_xy(i)
                c.create_oval(cx - PIECE_R + 2, cy - PIECE_R + 3, cx + PIECE_R + 2, cy + PIECE_R + 3,
                              fill="#6b4a24", outline="")
                c.create_oval(cx - PIECE_R, cy - PIECE_R, cx + PIECE_R, cy + PIECE_R,
                              fill=fill, outline=dark, width=2)
                c.create_oval(cx - 7, cy - 8, cx - 1, cy - 3, fill=light, outline="")

        if self.selected is not None:
            cx, cy = cell_xy(self.selected)
            c.create_oval(cx - 18, cy - 18, cx + 18, cy + 18, outline="#f1c40f", width=3)
            for d in self.possible:
                x, y = cell_xy(d)
                c.create_oval(x - 6, y - 6, x + 6, y + 6, fill="#2ecc71", outline="#1e8449", width=2)

        if self.winner:
            col = BLUE if self.winner == MINP else RED
            c.create_rectangle(40, CANVAS_H // 2 - 36, CANVAS_W - 40, CANVAS_H // 2 + 36,
                               fill="#101820", outline=col, width=3)
            c.create_text(CANVAS_W // 2, CANVAS_H // 2, text=f"🏆 ¡GANA {NAMES[self.winner]}!",
                          fill=col, font=("Segoe UI", 24, "bold"))

    def on_close(self):
        self.cancel.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()