"use strict";

const CANTIDAD_FILAS = [1, 2, 3, 4, 13, 12, 11, 10, 9, 10, 11, 12, 13, 4, 3, 2, 1];
const ESPACIO_SVG = "http://www.w3.org/2000/svg";
const ARCHIVOS_EJEMPLO = {
  greedy: "../examples/greedy_example.json",
  minimax: "../examples/minimax_example.json",
  alphabeta: "../examples/alphabeta_example.json",
};

const elementos = {
  algoritmo: document.getElementById("algoritmo"),
  heuristica: document.getElementById("heuristica"),
  tituloEjemplo: document.getElementById("tituloEjemplo"),
  anterior: document.getElementById("anterior"),
  siguiente: document.getElementById("siguiente"),
  reiniciar: document.getElementById("reiniciar"),
  reproducir: document.getElementById("reproducir"),
  contadorPaso: document.getElementById("contadorPaso"),
  tablero: document.getElementById("tablero"),
  movimientoActual: document.getElementById("movimientoActual"),
  notaTablero: document.getElementById("notaTablero"),
  arbol: document.getElementById("arbol"),
  tituloPaso: document.getElementById("tituloPaso"),
  explicacionPaso: document.getElementById("explicacionPaso"),
  nodosVisitados: document.getElementById("nodosVisitados"),
  hojasEvaluadas: document.getElementById("hojasEvaluadas"),
  estadisticaPodas: document.getElementById("estadisticaPodas"),
  podas: document.getElementById("podas"),
  mejorJugada: document.getElementById("mejorJugada"),
  valorRaiz: document.getElementById("valorRaiz"),
  resumenAlgoritmo: document.getElementById("resumenAlgoritmo"),
  formulaHeuristica: document.getElementById("formulaHeuristica"),
  pseudocodigo: document.getElementById("pseudocodigo"),
  notaAlgoritmo: document.getElementById("notaAlgoritmo"),
  errorCarga: document.getElementById("errorCarga"),
};

const PSEUDOCODIGO = {
  greedy: [
    ["movimientos", "movimientos = get_legal_moves(estado, estado.jugador_actual)"],
    ["movimiento", "para cada movimiento:"],
    ["copiar", "    estado_hijo = estado.copy()"],
    ["aplicar", "    apply_move(estado_hijo, movimiento)"],
    ["evaluar", "    valor = evaluar_estado(estado_hijo, \"{heuristica}\")"],
    ["comparar", "MAX conserva el mayor; MIN, el menor"],
    ["devolver", "devolver el mejor movimiento"],
  ],
  minimax: [
    ["inicio", "minimax(estado, profundidad, heuristica)"],
    ["terminal", "si profundidad == 0 o hay ganador:"],
    ["evaluar", "    devolver evaluar_estado(estado, \"{heuristica}\")"],
    ["movimientos", "movimientos = get_legal_moves(estado, estado.jugador_actual)"],
    ["pase", "si no hay movimientos: pasar turno"],
    ["max", "si juega MAX: mejor = −∞"],
    ["min", "si juega MIN: mejor = +∞"],
    ["explorar", "copiar el estado y aplicar el movimiento"],
    ["llamar", "valor = minimax(hijo, profundidad - 1, heuristica)"],
    ["propagarMax", "    MAX conserva el valor mayor"],
    ["propagarMin", "    MIN conserva el valor menor"],
    ["devolver", "devolver mejor valor"],
  ],
  alphabeta: [
    ["inicio", "alphabeta(estado, profundidad, alpha, beta, heuristica)"],
    ["terminal", "si profundidad == 0 o hay ganador:"],
    ["evaluar", "    devolver evaluar_estado(estado, \"{heuristica}\")"],
    ["movimientos", "movimientos = get_legal_moves(estado, estado.jugador_actual)"],
    ["pase", "si no hay movimientos: pasar turno"],
    ["max", "si juega MAX: mejor = −∞"],
    ["min", "si juega MIN: mejor = +∞"],
    ["explorar", "copiar el estado y aplicar el movimiento"],
    ["llamar", "valor = alphabeta(hijo, prof. - 1, alpha, beta, heuristica)"],
    ["propagarMax", "    MAX conserva el valor mayor"],
    ["alpha", "    alpha = max(alpha, mejor)"],
    ["propagarMin", "    MIN conserva el valor menor"],
    ["beta", "    beta = min(beta, mejor)"],
    ["corte", "    si beta <= alpha: break"],
    ["devolver", "devolver mejor valor"],
  ],
};

const EXPLICACIONES = {
  greedy: "El agente puntúa cada hijo inmediato y escoge el mejor para quien mueve. No anticipa la respuesta rival.",
  minimax: "Explora movimientos legales y respuestas hasta la profundidad elegida. MAX maximiza y MIN minimiza.",
  alphabeta: "El agente prueba cada jugada raíz. Alfa-Beta poda respuestas dentro de cada búsqueda.",
};

const FORMULAS_HEURISTICAS = {
  E1: "E1 = D_MIN - D_MAX",
  E2: "E2 = E1 - 0.5 × (desviación MAX - desviación MIN)",
  E3: "E3 = E1 - 2 × distancia de la ficha MAX más atrasada",
};

const EXPLICACIONES_HEURISTICAS = {
  E1: "Compara el progreso total de MAX y MIN hacia sus zonas objetivo.",
  E2: "Compara la distancia horizontal de ambos lados al eje central del tablero.",
  E3: "Evita que MAX deje muy atrás su ficha más distante de la meta.",
};

const DIRECCIONES_PASO = [[0, -2], [0, 2], [-1, -1], [-1, 1], [1, -1], [1, 1]];
const CELDAS_TABLERO = [];
const CODIGOS_CELDA = new Set();

CANTIDAD_FILAS.forEach((cantidad, fila) => {
  const primeraColumna = 12 - (cantidad - 1);
  for (let posicion = 0; posicion < cantidad; posicion += 1) {
    const columna = primeraColumna + posicion * 2;
    CELDAS_TABLERO.push([fila, columna]);
    CODIGOS_CELDA.add(`${fila},${columna}`);
  }
});

function crearDistanciasMeta(esMeta) {
  const distancias = new Map();
  const porVisitar = [];

  for (const [fila, columna] of CELDAS_TABLERO) {
    if (esMeta(fila)) {
      const codigo = `${fila},${columna}`;
      distancias.set(codigo, 0);
      porVisitar.push([fila, columna]);
    }
  }

  let indice = 0;
  while (indice < porVisitar.length) {
    const [fila, columna] = porVisitar[indice];
    indice += 1;
    const distanciaSiguiente = distancias.get(`${fila},${columna}`) + 1;

    for (const [cambioFila, cambioColumna] of DIRECCIONES_PASO) {
      const vecina = [fila + cambioFila, columna + cambioColumna];
      const codigoVecina = `${vecina[0]},${vecina[1]}`;
      if (CODIGOS_CELDA.has(codigoVecina) && !distancias.has(codigoVecina)) {
        distancias.set(codigoVecina, distanciaSiguiente);
        porVisitar.push(vecina);
      }
    }
  }

  return distancias;
}

const DISTANCIAS_MAX = crearDistanciasMeta(fila => fila >= 13);
const DISTANCIAS_MIN = crearDistanciasMeta(fila => fila <= 3);

let ejemploActual = null;
let pasos = [];
let indicePaso = 0;
let temporizador = null;

function crearElementoSvg(etiqueta, atributos = {}) {
  const elemento = document.createElementNS(ESPACIO_SVG, etiqueta);
  for (const [nombre, valor] of Object.entries(atributos)) {
    elemento.setAttribute(nombre, valor);
  }
  return elemento;
}

function crearRaiz(ejemplo) {
  return {
    id: "raiz",
    move: "Estado actual",
    player: ejemplo.root_player,
    children: ejemplo.children,
  };
}

function crearEstadoBusqueda() {
  return {
    nodos: 0,
    hojas: 0,
    podas: 0,
    valores: {},
    nodosVisitados: [],
    aristasVisitadas: [],
    nodosPodados: [],
    aristasPodadas: [],
    nodoActual: "raiz",
    aristaActual: null,
    nodoTablero: "raiz",
    alpha: -Infinity,
    beta: Infinity,
    mejorJugada: null,
  };
}

function copiarEstado(estado) {
  return {
    ...estado,
    valores: { ...estado.valores },
    nodosVisitados: [...estado.nodosVisitados],
    aristasVisitadas: [...estado.aristasVisitadas],
    nodoTablero: estado.nodoTablero,
    nodosPodados: [...estado.nodosPodados],
    aristasPodadas: [...estado.aristasPodadas],
  };
}

function contarHojas(nodo) {
  if (!nodo.children || nodo.children.length === 0) return 1;
  return nodo.children.reduce((total, hijo) => total + contarHojas(hijo), 0);
}

function buscarCaminoHastaNodo(nodo, idBuscado, camino = []) {
  if (nodo.id === idBuscado) return camino;

  for (const hijo of nodo.children || []) {
    const caminoEncontrado = buscarCaminoHastaNodo(hijo, idBuscado, [...camino, hijo]);
    if (caminoEncontrado !== null) return caminoEncontrado;
  }

  return null;
}

function crearTableroParaPaso(ejemplo, idNodo) {
  const tablero = {
    red: ejemplo.board_state.red.map(celda => [...celda]),
    blue: ejemplo.board_state.blue.map(celda => [...celda]),
  };
  const raiz = crearRaiz(ejemplo);
  const camino = buscarCaminoHastaNodo(raiz, idNodo) || [];
  let ultimoMovimiento = null;

  for (const nodo of camino) {
    const movimiento = nodo.piece_move;
    if (!movimiento) continue;

    const piezas = nodo.mover === "AZUL" ? tablero.blue : tablero.red;
    const indicePieza = piezas.findIndex(celda =>
      celda[0] === movimiento.from[0] && celda[1] === movimiento.from[1]
    );
    const destinoOcupado = [...tablero.red, ...tablero.blue].some(celda =>
      celda[0] === movimiento.to[0] && celda[1] === movimiento.to[1]
    );

    if (indicePieza !== -1 && !destinoOcupado) {
      piezas[indicePieza] = [...movimiento.to];
      ultimoMovimiento = { ...movimiento, mover: nodo.mover };
    }
  }

  return { tablero, ultimoMovimiento };
}

function formatearCasilla(celda) {
  const fila = celda[0];
  const primeraColumna = 12 - (CANTIDAD_FILAS[fila] - 1);
  const columna = Math.floor((celda[1] - primeraColumna) / 2) + 1;
  return `F${fila + 1}-C${columna}`;
}

function copiarTablero(tablero) {
  return {
    red: tablero.red.map(celda => [...celda]),
    blue: tablero.blue.map(celda => [...celda]),
  };
}

function aplicarMovimientoDelEjemplo(tablero, nodo) {
  const movimiento = nodo.piece_move;
  const nuevoTablero = copiarTablero(tablero);
  const piezas = nodo.mover === "AZUL" ? nuevoTablero.blue : nuevoTablero.red;
  const origen = movimiento.from;
  const destino = movimiento.to;
  const indicePieza = piezas.findIndex(celda => celda[0] === origen[0] && celda[1] === origen[1]);
  const destinoOcupado = [...nuevoTablero.red, ...nuevoTablero.blue].some(
    celda => celda[0] === destino[0] && celda[1] === destino[1],
  );

  if (indicePieza === -1 || destinoOcupado) {
    throw new Error(`El movimiento ilustrativo no es válido: ${nodo.move}.`);
  }

  piezas[indicePieza] = [...destino];
  return nuevoTablero;
}

function calcularDistanciaTotal(tablero, jugador) {
  const piezas = jugador === "MAX" ? tablero.red : tablero.blue;
  const distancias = jugador === "MAX" ? DISTANCIAS_MAX : DISTANCIAS_MIN;
  let total = 0;

  for (const [fila, columna] of piezas) {
    total += distancias.get(`${fila},${columna}`);
  }

  return total;
}

function calcularPenalizacionEje(tablero) {
  let desviacionMax = 0;
  let desviacionMin = 0;

  for (const [, columna] of tablero.red) desviacionMax += Math.abs(columna - 12);
  for (const [, columna] of tablero.blue) desviacionMin += Math.abs(columna - 12);

  return desviacionMax - desviacionMin;
}

function evaluarEstado(tablero, heuristica) {
  const e1 = calcularDistanciaTotal(tablero, "MIN") - calcularDistanciaTotal(tablero, "MAX");

  if (heuristica === "E1") return e1;
  if (heuristica === "E2") return e1 - 0.5 * calcularPenalizacionEje(tablero);

  let distanciaMasAtrasada = 0;
  for (const [fila, columna] of tablero.red) {
    const distancia = DISTANCIAS_MAX.get(`${fila},${columna}`);
    if (distancia > distanciaMasAtrasada) distanciaMasAtrasada = distancia;
  }
  return e1 - 2 * distanciaMasAtrasada;
}

function actualizarEvaluacionesDeHojas(ejemplo, heuristica) {
  const tableroInicial = ejemplo.board_state;

  function evaluarRamas(nodos, tablero) {
    for (const nodo of nodos) {
      const tableroHijo = aplicarMovimientoDelEjemplo(tablero, nodo);
      if (nodo.children && nodo.children.length > 0) {
        evaluarRamas(nodo.children, tableroHijo);
      } else {
        nodo.value = evaluarEstado(tableroHijo, heuristica);
      }
    }
  }

  evaluarRamas(ejemplo.children, tableroInicial);
}

function calcularValorArbol(nodo) {
  if (!nodo.children || nodo.children.length === 0) return nodo.value;

  const valoresHijos = nodo.children.map(calcularValorArbol);
  if (nodo.player === "MAX") return Math.max(...valoresHijos);
  return Math.min(...valoresHijos);
}

function actualizarMejorJugada(ejemplo) {
  let mejorHijo = null;
  let mejorValor = ejemplo.root_player === "MAX" ? -Infinity : Infinity;

  for (const hijo of ejemplo.children) {
    const valor = calcularValorArbol(hijo);
    const esMejor = ejemplo.root_player === "MAX" ? valor > mejorValor : valor < mejorValor;
    if (mejorHijo === null || esMejor) {
      mejorHijo = hijo;
      mejorValor = valor;
    }
  }

  ejemplo.expected_value = mejorValor;
  ejemplo.best_move = mejorHijo ? mejorHijo.move : "—";
}

function construirPasos(ejemplo) {
  const raiz = crearRaiz(ejemplo);
  const estado = crearEstadoBusqueda();
  const eventos = [];
  const usaAlfaBeta = ejemplo.algorithm === "alphabeta";
  const usaVoraz = ejemplo.algorithm === "greedy";

  function agregarPaso(titulo, explicacion, linea) {
    eventos.push({ titulo, explicacion, linea, estado: copiarEstado(estado) });
  }

  function idArista(padre, hijo) {
    return `${padre.id}_${hijo.id}`;
  }

  function marcarRamaPodada(padre, hijo) {
    estado.aristasPodadas.push(idArista(padre, hijo));
    estado.nodosPodados.push(hijo.id);
    for (const nieto of hijo.children || []) marcarRamaPodada(hijo, nieto);
  }

  function explorar(nodo, alpha, beta, aristaEntrada = null) {
    estado.alpha = alpha;
    estado.beta = beta;
    estado.nodos += 1;
    estado.nodosVisitados.push(nodo.id);
    estado.nodoActual = nodo.id;
    estado.nodoTablero = nodo.id;
    estado.aristaActual = aristaEntrada;

    const hijos = nodo.children || [];
    if (hijos.length === 0) {
      estado.hojas += 1;
      estado.valores[nodo.id] = nodo.value;
      agregarPaso(
        `Evaluar ${nodo.move}: ${formatearValor(nodo.value)}`,
        `La heurística asigna ${formatearValor(nodo.value)} a esta posición. Un valor alto favorece a ROJO (MAX); uno bajo, a AZUL (MIN).`,
        "evaluar",
      );
      return nodo.value;
    }

    estado.nodoActual = nodo.id;
    agregarPaso(
      `Generar ${hijos.length} movimientos`,
      `${nodo.player} revisa sus movimientos posibles.`,
      "movimientos",
    );

    const esMax = nodo.player === "MAX";
    let mejorValor = esMax ? -Infinity : Infinity;
    let mejorHijo = null;

    if (!usaVoraz) {
      agregarPaso(
        esMax ? "Turno MAX: buscar el valor mayor" : "Turno MIN: buscar el valor menor",
        esMax ? "MAX quiere subir la evaluación." : "MIN quiere bajar la evaluación.",
        esMax ? "max" : "min",
      );
    }

    for (let indice = 0; indice < hijos.length; indice += 1) {
      const hijo = hijos[indice];
      const idActual = idArista(nodo, hijo);
      estado.nodoActual = hijo.id;
      estado.nodoTablero = hijo.id;
      estado.aristaActual = idActual;
      estado.aristasVisitadas.push(idActual);
      agregarPaso(
        `Probar ${hijo.move}`,
        usaVoraz
          ? "La IA aplica esta jugada y evalúa de inmediato el nuevo estado."
          : "El algoritmo baja al estado hijo para calcular su resultado.",
        usaVoraz ? "movimiento" : "explorar",
      );

      if (usaVoraz) {
        agregarPaso("Crear copia del estado", "La evaluación no debe modificar la partida original.", "copiar");
        agregarPaso("Aplicar el movimiento", `Se crea el estado hijo: ${hijo.move}.`, "aplicar");
      } else {
        agregarPaso(
          `Llamar ${ejemplo.algorithm === "minimax" ? "Minimax" : "Alfa-Beta"}`,
          "La búsqueda analiza el estado hijo con la misma heurística elegida.",
          "llamar",
        );
      }

      // Python prueba cada jugada raíz por separado, reiniciando alpha y beta.
      const reiniciarLimites = usaAlfaBeta && nodo.id === "raiz";
      const alphaHijo = reiniciarLimites ? -Infinity : alpha;
      const betaHijo = reiniciarLimites ? Infinity : beta;
      const valorHijo = explorar(hijo, alphaHijo, betaHijo, idActual);
      const esMejor = esMax ? valorHijo > mejorValor : valorHijo < mejorValor;
      if (mejorHijo === null || esMejor) {
        mejorValor = valorHijo;
        mejorHijo = hijo;
      }

      estado.valores[nodo.id] = mejorValor;
      if (nodo.id === "raiz") estado.mejorJugada = mejorHijo.move;
      estado.nodoActual = nodo.id;
      estado.aristaActual = idActual;

      let lineaPropagacion;
      if (usaVoraz) lineaPropagacion = "comparar";
      else lineaPropagacion = esMax ? "propagarMax" : "propagarMin";
      agregarPaso(
        `Conservar ${formatearValor(mejorValor)}`,
        `${nodo.player} guarda el mejor valor visto hasta ahora: ${formatearValor(mejorValor)}.`,
        lineaPropagacion,
      );

      if (usaAlfaBeta && nodo.id !== "raiz") {
        if (esMax) {
          alpha = Math.max(alpha, mejorValor);
          estado.alpha = alpha;
          agregarPaso(`Actualizar alpha = ${formatearValor(alpha)}`, "MAX ya tiene garantizado al menos este valor.", "alpha");
        } else {
          beta = Math.min(beta, mejorValor);
          estado.beta = beta;
          agregarPaso(`Actualizar beta = ${formatearValor(beta)}`, "MIN ya puede limitar el resultado a este valor o menos.", "beta");
        }
      }

      const restantes = hijos.slice(indice + 1);
      if (usaAlfaBeta && nodo.id !== "raiz" && beta <= alpha && restantes.length > 0) {
        estado.podas += restantes.length;
        for (const hijoSinRevisar of restantes) marcarRamaPodada(nodo, hijoSinRevisar);
        estado.nodoActual = nodo.id;
        estado.aristaActual = null;
        agregarPaso(
          `Poda: beta (${formatearValor(beta)}) ≤ alpha (${formatearValor(alpha)})`,
          `Las ${restantes.length} opciones restantes no cambian la decisión y no hace falta evaluarlas.`,
          "corte",
        );
        break;
      }
    }

    estado.valores[nodo.id] = mejorValor;
    estado.nodoActual = nodo.id;
    estado.aristaActual = null;
    agregarPaso(
      `Devolver ${formatearValor(mejorValor)}`,
      `${nodo.player} entrega este valor a su estado anterior.`,
      "devolver",
    );
    return mejorValor;
  }

  agregarPaso("Estado inicial", ejemplo.description, "inicio");
  const valorFinal = explorar(raiz, -Infinity, Infinity);
  if (valorFinal !== ejemplo.expected_value || estado.mejorJugada !== ejemplo.best_move) {
    throw new Error("Los valores o la mejor jugada del ejemplo no coinciden con su árbol.");
  }
  estado.valores.raiz = valorFinal;
  estado.nodoActual = "raiz";
  const mejorNodo = raiz.children.find(hijo => hijo.move === ejemplo.best_move);
  if (mejorNodo) estado.nodoTablero = mejorNodo.id;
  agregarPaso(
    `Decisión: ${ejemplo.best_move}`,
    `La IA elige ${ejemplo.best_move}, con valor ${formatearValor(valorFinal)}.`,
    "devolver",
  );
  return eventos;
}

function formatearValor(valor) {
  if (valor === Infinity) return "+∞";
  if (valor === -Infinity) return "−∞";
  return String(valor);
}

function dibujarPseudocodigo(algoritmo, lineaActual) {
  elementos.pseudocodigo.replaceChildren();
  const heuristica = elementos.heuristica.value;
  for (const [clave, textoOriginal] of PSEUDOCODIGO[algoritmo]) {
    const linea = document.createElement("li");
    linea.textContent = textoOriginal.replaceAll("{heuristica}", heuristica);
    if (clave === lineaActual) linea.classList.add("actual");
    elementos.pseudocodigo.append(linea);
  }
  elementos.formulaHeuristica.textContent = FORMULAS_HEURISTICAS[heuristica];
  elementos.resumenAlgoritmo.textContent = EXPLICACIONES[algoritmo];
  const notaBusqueda = algoritmo === "greedy"
    ? "La voraz no explora respuestas futuras."
    : algoritmo === "alphabeta"
      ? "alpha es el límite de MAX; beta, el de MIN. Si beta <= alpha, se corta la rama."
      : "Cada movimiento consume un nivel de profundidad.";
  elementos.notaAlgoritmo.textContent = `${EXPLICACIONES_HEURISTICAS[heuristica]} ${notaBusqueda}`;
  elementos.estadisticaPodas.hidden = algoritmo !== "alphabeta";
}

function dibujarTablero(estadoTablero, movimiento) {
  elementos.tablero.replaceChildren();
  CANTIDAD_FILAS.forEach((cantidad, fila) => {
    const primeraColumna = 12 - (cantidad - 1);
    for (let posicion = 0; posicion < cantidad; posicion += 1) {
      const columna = primeraColumna + posicion * 2;
      const x = (columna - 12) * 11.5;
      const y = (fila - 8) * 19.9;
      const color = fila <= 3 ? "#dcead6" : fila >= 13 ? "#eadfb8" : "#d1dfcd";
      elementos.tablero.append(crearElementoSvg("circle", {
        cx: x, cy: y, r: 5, fill: color, stroke: "#71896e", "stroke-width": 1,
      }));
    }
  });

  if (movimiento) {
    const origenX = (movimiento.from[1] - 12) * 11.5;
    const origenY = (movimiento.from[0] - 8) * 19.9;
    const destinoX = (movimiento.to[1] - 12) * 11.5;
    const destinoY = (movimiento.to[0] - 8) * 19.9;
    elementos.tablero.append(crearElementoSvg("line", {
      x1: origenX, y1: origenY, x2: destinoX, y2: destinoY,
      stroke: "#d49822", "stroke-width": 2.3, "stroke-dasharray": "4 3",
    }));
    elementos.tablero.append(crearElementoSvg("circle", {
      cx: destinoX, cy: destinoY, r: 7, fill: "none", stroke: "#d49822", "stroke-width": 2,
    }));
    elementos.movimientoActual.textContent =
      `Movimiento ${movimiento.mover}: ${formatearCasilla(movimiento.from)} → ${formatearCasilla(movimiento.to)}`;
  } else {
    elementos.movimientoActual.textContent = "Estado inicial: todavía no se ha movido ninguna pieza.";
  }

  const fichas = [
    ...estadoTablero.red.map(([fila, columna]) => ({ fila, columna, color: "#b94f45" })),
    ...estadoTablero.blue.map(([fila, columna]) => ({ fila, columna, color: "#4c7e9c" })),
  ];
  for (const ficha of fichas) {
    elementos.tablero.append(crearElementoSvg("circle", {
      cx: (ficha.columna - 12) * 11.5,
      cy: (ficha.fila - 8) * 19.9,
      r: 4.1,
      fill: ficha.color,
      stroke: "#fff",
      "stroke-width": 1.1,
    }));
  }
}

function prepararPosiciones(raiz) {
  const nodos = [];
  const aristas = [];
  const izquierda = 45;
  const derecha = 805;

  function ubicar(nodo, nivel, inicio, fin, idPadre = null) {
    const hijos = nodo.children || [];
    let x;
    if (hijos.length === 0) {
      x = (inicio + fin) / 2;
    } else {
      const hojasTotales = hijos.reduce((suma, hijo) => suma + contarHojas(hijo), 0);
      let desde = inicio;
      const posicionesHijos = [];
      for (const hijo of hijos) {
        const anchoHijo = (fin - inicio) * contarHojas(hijo) / hojasTotales;
        const hasta = desde + anchoHijo;
        const posicionHijo = ubicar(hijo, nivel + 1, desde, hasta, nodo.id);
        posicionesHijos.push(posicionHijo.x);
        aristas.push({ padre: nodo, hijo });
        desde = hasta;
      }
      x = posicionesHijos.reduce((suma, posicion) => suma + posicion, 0) / posicionesHijos.length;
    }
    const posicion = { ...nodo, x, y: 43 + nivel * 96, idPadre };
    nodos.push(posicion);
    return posicion;
  }

  ubicar(raiz, 0, izquierda, derecha);
  return { nodos, aristas };
}

function dibujarArbol(ejemplo, estado) {
  elementos.arbol.replaceChildren();
  const raiz = crearRaiz(ejemplo);
  const { nodos, aristas } = prepararPosiciones(raiz);
  const ubicaciones = new Map(nodos.map(nodo => [nodo.id, nodo]));

  for (const arista of aristas) {
    const padre = ubicaciones.get(arista.padre.id);
    const hijo = ubicaciones.get(arista.hijo.id);
    const id = `${arista.padre.id}_${arista.hijo.id}`;
    let clase = "arista";
    if (estado.aristasVisitadas.includes(id)) clase += " recorrida";
    if (estado.aristaActual === id) clase += " actual";
    if (estado.aristasPodadas.includes(id)) clase += " podada";
    elementos.arbol.append(crearElementoSvg("line", {
      x1: padre.x, y1: padre.y + 23, x2: hijo.x, y2: hijo.y - 22, class: clase,
    }));
  }

  for (const nodo of nodos) {
    const esHoja = !nodo.children || nodo.children.length === 0;
    let clase = "nodo " + (esHoja ? "hoja" : nodo.player.toLowerCase());
    if (estado.nodosVisitados.includes(nodo.id)) clase += " visitado";
    if (estado.nodoActual === nodo.id) clase += " actual";
    if (estado.nodosPodados.includes(nodo.id)) clase += " podado";
    const grupo = crearElementoSvg("g", { class: clase, transform: `translate(${nodo.x},${nodo.y})` });
    grupo.append(crearElementoSvg("circle", { r: 22 }));

    const rol = crearElementoSvg("text", { y: -29, class: "rol-nodo" });
    rol.textContent = nodo.id === "raiz" ? `${nodo.player} · ROJO` : (esHoja ? "HOJA" : nodo.player);
    grupo.append(rol);

    const valor = crearElementoSvg("text", { class: "valor-nodo" });
    valor.textContent = estado.nodosPodados.includes(nodo.id)
      ? "×"
      : Object.hasOwn(estado.valores, nodo.id)
        ? formatearValor(estado.valores[nodo.id])
        : "?";
    grupo.append(valor);

    const etiqueta = crearElementoSvg("text", { y: 37, class: "etiqueta-nodo" });
    etiqueta.textContent = nodo.id === "raiz" ? "Estado actual" : nodo.move;
    grupo.append(etiqueta);
    elementos.arbol.append(grupo);
  }

  if (ejemplo.algorithm === "alphabeta") {
    const limites = crearElementoSvg("text", {
      x: 420, y: 482, class: "etiqueta-arista",
    });
    limites.textContent = `alpha = ${formatearValor(estado.alpha)}  ·  beta = ${formatearValor(estado.beta)}`;
    elementos.arbol.append(limites);
  }
}

function mostrarPaso() {
  if (pasos.length === 0) return;
  const paso = pasos[indicePaso];
  const estado = paso.estado;
  elementos.tituloPaso.textContent = paso.titulo;
  elementos.explicacionPaso.textContent = paso.explicacion;
  elementos.contadorPaso.textContent = `Paso ${indicePaso + 1} de ${pasos.length}`;
  elementos.nodosVisitados.textContent = estado.nodos;
  elementos.hojasEvaluadas.textContent = estado.hojas;
  elementos.podas.textContent = estado.podas;
  elementos.mejorJugada.textContent = estado.mejorJugada || "—";
  elementos.valorRaiz.textContent = Object.hasOwn(estado.valores, "raiz")
    ? formatearValor(estado.valores.raiz)
    : "—";
  elementos.anterior.disabled = indicePaso === 0;
  elementos.siguiente.disabled = indicePaso === pasos.length - 1;
  dibujarPseudocodigo(ejemploActual.algorithm, paso.linea);
  const posicionTablero = crearTableroParaPaso(ejemploActual, estado.nodoTablero);
  dibujarTablero(posicionTablero.tablero, posicionTablero.ultimoMovimiento);
  dibujarArbol(ejemploActual, estado);
}

function irAlPaso(indice) {
  if (indice < 0 || indice >= pasos.length) return;
  indicePaso = indice;
  mostrarPaso();
}

function detenerReproduccion() {
  if (temporizador !== null) {
    window.clearInterval(temporizador);
    temporizador = null;
  }
  elementos.reproducir.textContent = "▶ Reproducir";
}

function alternarReproduccion() {
  if (temporizador !== null) {
    detenerReproduccion();
    return;
  }
  if (indicePaso === pasos.length - 1) irAlPaso(0);
  elementos.reproducir.textContent = "Ⅱ Pausar";
  temporizador = window.setInterval(() => {
    if (indicePaso === pasos.length - 1) {
      detenerReproduccion();
      return;
    }
    irAlPaso(indicePaso + 1);
  }, 1100);
}

async function cargarEjemplo(algoritmo, heuristica) {
  detenerReproduccion();
  elementos.errorCarga.hidden = true;
  try {
    const respuesta = await fetch(ARCHIVOS_EJEMPLO[algoritmo]);
    if (!respuesta.ok) throw new Error(`No se pudo abrir el ejemplo (${respuesta.status}).`);
    ejemploActual = await respuesta.json();
    ejemploActual.algorithm = algoritmo;
    ejemploActual.heuristica = heuristica;
    actualizarEvaluacionesDeHojas(ejemploActual, heuristica);
    actualizarMejorJugada(ejemploActual);
    pasos = construirPasos(ejemploActual);
    indicePaso = 0;
    elementos.tituloEjemplo.textContent = ejemploActual.title;
    elementos.notaTablero.textContent = `${ejemploActual.position_note} Evaluación activa: ${heuristica}.`;
    mostrarPaso();
  } catch (error) {
    elementos.errorCarga.hidden = false;
    elementos.errorCarga.textContent = `${error.message} Abre la carpeta del proyecto en un servidor local: .\\.venv\\Scripts\\python.exe -m http.server 8000`;
    elementos.tituloPaso.textContent = "No se pudo cargar el ejemplo.";
  }
}

elementos.anterior.addEventListener("click", () => irAlPaso(indicePaso - 1));
elementos.siguiente.addEventListener("click", () => irAlPaso(indicePaso + 1));
elementos.reiniciar.addEventListener("click", () => {
  detenerReproduccion();
  irAlPaso(0);
});
elementos.reproducir.addEventListener("click", alternarReproduccion);
elementos.algoritmo.addEventListener("change", evento => {
  cargarEjemplo(evento.target.value, elementos.heuristica.value);
});
elementos.heuristica.addEventListener("change", evento => {
  cargarEjemplo(elementos.algoritmo.value, evento.target.value);
});

cargarEjemplo(elementos.algoritmo.value, elementos.heuristica.value);
