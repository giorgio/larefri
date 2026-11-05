# LAREFRI — todos los cambios visuales reunidos en este archivo.
# Reemplaza app.py en tu proyecto existente. Conserva los módulos de recetas,
# requirements.txt y las variables de Railway. No necesitas actualizar
# campo.py ni portada.py: sus versiones actualizadas están incluidas aquí.
import types as _types

def _modulo_visual(nombre, codigo):
    modulo = _types.ModuleType(nombre)
    modulo.__file__ = __file__
    exec(compile(codigo, nombre + ".py", "exec"), modulo.__dict__)
    return modulo

campo = _modulo_visual('campo_integrado', '"""Campo "¿Algo más?": se escribe y la palabra se completa sola en el mismo campo (sin menú desplegable).\nTab, Enter o → aceptan; cada ingrediente queda en su propio cuadrito con ✕. La coma o "y" separan."""\n\nfrom __future__ import annotations\n\nimport streamlit as st\n\nCSS = """\n@import url(\'https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&display=swap\');\n.caja { display:flex; flex-wrap:wrap; align-items:center; gap:.55rem; padding:.65rem .8rem; min-height:3.2rem;\n  background:#fff; border:1px solid #2143af; border-radius:16px; font-family:"DM Sans",sans-serif; box-sizing:border-box; }\n.caja:focus-within { box-shadow:0 0 0 3px #2143af18; }\n.chip { display:inline-flex; align-items:center; gap:.5rem; padding:.35rem .45rem .35rem .75rem;\n  border:1px solid #ff7658; border-radius:8px; background:#ffe9df; color:#253568;\n  font-family:"DM Sans",sans-serif; font-size:1rem; line-height:1.4; max-width:100%; overflow-wrap:anywhere;\n  box-sizing:border-box; animation:entra .2s ease-out; }\n.chip button { all:unset; cursor:pointer; flex-shrink:0; display:grid; place-items:center; color:#9f351e;\n  font-size:.9rem; width:30px; height:30px; border-radius:6px; font-family:sans-serif; }\n.chip button:hover {background:#ffd0bf;}\n.chip button:focus-visible {outline:1px solid #2143af;outline-offset:1px;}\n.escribe {position:relative; flex:1 1 12rem; min-width:0;}\n.escribe input, .escribe .fantasma {font-family:"DM Sans",sans-serif;font-size:1rem;color:#23396b;\n  padding:0;margin:0;border:none;outline:none;background:transparent;width:100%;letter-spacing:normal;line-height:2;}\n.escribe .fantasma {position:absolute;inset:0;pointer-events:none;white-space:pre;color:transparent;overflow:hidden;}\n.escribe .fantasma i {font-style:normal;color:#23396b;opacity:.35;}\n.escribe input::placeholder {color:#74809a;font-family:"DM Sans",sans-serif;font-size:1.15rem;}\n.aviso {width:100%;color:#a43b25;font-size:1rem;font-family:"DM Sans",sans-serif;}\n.aviso:empty {display:none;}\n@keyframes entra {from {transform:scale(.9);opacity:0;}to {transform:scale(1);opacity:1;}}\n@media(pointer:coarse) {.chip button {width:36px;height:36px;}.chip button:active {background:#ffd0bf;}}\n@media(prefers-reduced-motion:reduce) {.chip {animation:none;}}\n"""\n\n\nJS = r"""\nexport default function(component) {\n  const { data, setStateValue, parentElement } = component;\n  const norm = (t) => (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();\n  const sug = data.sugerencias || [];\n  let root = parentElement.querySelector(".caja");\n  if (!root) {\n    root = document.createElement("div");\n    root.className = "caja";\n    root.innerHTML = \'<div class="escribe"><div class="fantasma"></div><input type="text" autocomplete="off" spellcheck="false"></div><div class="aviso"></div>\';\n    parentElement.appendChild(root);\n    root.__items = (data.valor || []).slice();\n  }\n  const input = root.querySelector("input");\n  const fantasma = root.querySelector(".fantasma");\n  const aviso = root.querySelector(".aviso");\n  const escribe = root.querySelector(".escribe");\n  input.placeholder = data.placeholder || "";\n  input.setAttribute("aria-label", "Busca o añade ingredientes");\n\n  const guardar = () => setStateValue("lista", root.__items.slice());\n  const pintar = () => {\n    root.querySelectorAll(".chip").forEach((c) => c.remove());\n    root.__items.forEach((x, i) => {\n      const c = document.createElement("span");\n      c.className = "chip";\n      c.textContent = x;\n      const b = document.createElement("button");\n      b.type = "button"; b.textContent = "✕"; b.setAttribute("aria-label", "Quitar " + x);\n      b.onclick = () => { root.__items.splice(i, 1); pintar(); guardar(); input.focus(); };\n      c.appendChild(b);\n      root.insertBefore(c, escribe);\n    });\n  };\n  const completar = (t) => {\n    const k = norm(t);\n    if (!k) return null;\n    const ya = new Set(root.__items.map(norm));\n    return sug.find((s) => norm(s).startsWith(k) && !ya.has(norm(s))) || null;\n  };\n  const mostrarFantasma = () => {\n    const t = input.value;\n    const s = completar(t);\n    fantasma.innerHTML = "";\n    if (s && t) {\n      const a = document.createElement("span"); a.textContent = t;\n      const b = document.createElement("i"); b.textContent = s.slice(t.length);\n      fantasma.append(a, b);\n    }\n  };\n  const agregar = (texto, usarSugerencia) => {\n    let hubo = false;\n    for (let parte of (texto || "").split(/[,;\\n]+|\\s+y\\s+/i)) {\n      parte = parte.trim().replace(/\\s+/g, " ");\n      if (!parte) continue;\n      if (/sobrante|sobras?\\b/i.test(norm(parte))) { aviso.textContent = "Escribe solo el ingrediente (por ejemplo: arroz)."; continue; }\n      const s = usarSugerencia ? completar(parte) : null;\n      const exacta = sug.find((x) => norm(x) === norm(parte));\n      const final = s || exacta || (parte.charAt(0).toUpperCase() + parte.slice(1));\n      if (root.__items.some((x) => norm(x) === norm(final))) continue;\n      root.__items.push(final); hubo = true; aviso.textContent = "";\n    }\n    input.value = ""; mostrarFantasma();\n    if (hubo) { pintar(); guardar(); }\n  };\n\n  input.oninput = () => {\n    // espacio = como la coma, salvo que la palabra siga (p. ej. "carne " -> "Carne molida", "leche " -> "Leche de coco")\n    if (/\\S\\s$/.test(input.value)) {\n      const t = norm(input.value);\n      const sigue = sug.some((s) => norm(s).startsWith(t + " "));\n      if (!sigue) { agregar(input.value.trim(), true); aviso.textContent = ""; mostrarFantasma(); return; }\n    }\n    if (/[,;]/.test(input.value) || /\\s+y\\s+$/i.test(input.value)) {\n      const partes = input.value.split(/[,;]|\\s+y\\s+$/i);\n      const resto = partes.pop();\n      agregar(partes.join(","), true);\n      input.value = resto.trimStart();\n    }\n    aviso.textContent = "";\n    mostrarFantasma();\n  };\n  input.onkeydown = (e) => {\n    if (e.key === "Enter" || e.key === "Tab" || (e.key === "ArrowRight" && input.selectionStart === input.value.length && completar(input.value))) {\n      if (!input.value.trim()) return;\n      e.preventDefault();\n      agregar(input.value, true);\n    } else if (e.key === "Backspace" && !input.value && root.__items.length) {\n      root.__items.pop(); pintar(); guardar();\n    }\n  };\n  input.onblur = () => { if (input.value.trim()) agregar(input.value, true); };\n  root.onclick = (e) => { if (e.target === root) input.focus(); };\n  pintar();\n  mostrarFantasma();\n}\n"""\n\n_componente = st.components.v2.component("larefri_algo_mas", html="", css=CSS, js=JS)\n\n\ndef algo_mas(sugerencias: list[str], placeholder: str, key: str = "algo_mas") -> list[str]:\n    previo = st.session_state.get(key + "_items", [])\n    r = _componente(key=key, data={"sugerencias": sugerencias, "valor": previo, "placeholder": placeholder},\n                    default={"lista": previo}, on_lista_change=lambda: None)\n    valor = getattr(r, "lista", None)\n    items = list(previo if valor is None else valor)\n    st.session_state[key + "_items"] = items\n    return items\n\n\n_JS_FINAL = r"""\nexport default function(component) {\n  const { setTriggerValue, parentElement, data } = component;\n  let el = parentElement.querySelector(".fin");\n  if (!el) { el = document.createElement("div"); el.className = "fin"; el.style.height = "1px"; parentElement.appendChild(el); }\n  if (el.__obs) el.__obs.disconnect();\n  if (!window.__escucha) { window.__escucha = true; window.__bajo = false;\n    document.addEventListener("wheel", () => { window.__bajo = true; }, { passive: true, capture: true });\n    document.addEventListener("touchmove", () => { window.__bajo = true; }, { passive: true, capture: true });\n    document.addEventListener("keydown", (e) => { if (/Page|Arrow|End| /.test(e.key)) window.__bajo = true; }, true); }\n  let avisado = false;\n  el.__obs = new IntersectionObserver((e) => {\n    // no cargar si hay una receta abierta (se cerraría) ni si la persona no ha bajado\n    if (e[0].isIntersecting && !avisado && !document.querySelector(\'[role="dialog"]\') && window.__bajo) {\n      avisado = true; setTriggerValue("cargar", data.n);\n    }\n  }, { rootMargin: "400px" });\n  el.__obs.observe(el);\n  return () => el.__obs && el.__obs.disconnect();\n}\n"""\n\n_final = st.components.v2.component("larefri_final", html="", js=_JS_FINAL)\n\n\ndef llego_al_final(n: int, key: str = "fin") -> bool:\n    """True cuando la persona bajó hasta el final de las recetas (para cargar más sin botón)."""\n    r = _final(key=key, data={"n": n}, on_cargar_change=lambda: None)\n    return bool(getattr(r, "cargar", None))\n')

portada = _modulo_visual("portada_integrada", '"""Portada pop de LaRefri: presentación y selección, sin llamadas de IA."""\nimport html\nimport streamlit as st\nimport casa as c\nimport nucleo as n\n\nICONOS = dict(zip(c.COMUNES, [\'🍚\',\'🥚\',\'🥔\',\'🍌\',\'🍌\',\'🥔\',\'🍝\',\'🐟\',\'🍗\',\'🥩\',\'🫘\',\'🫘\',\'🌽\',\'🧀\',\'🥛\',\'🍅\',\'🫑\',\'🥕\',\'🧅\',\'🧄\',\'🍋\',\'🥑\',\'🍞\',\'🌾\',\'🍌\',\'🐟\',\'🌭\',\'🫛\']))\nGRUPOS = {\n    \'Proteínas\': {\'Huevos\', \'Atún\', \'Pollo\', \'Carne molida\', \'Sardina\', \'Salchicha\'},\n    \'Despensa\': {\'Arroz\', \'Fideo\', \'Lenteja\', \'Fréjol\', \'Pan\', \'Avena\'},\n    \'Lácteos\': {\'Queso\', \'Leche\'},\n}\nGRUPOS[\'Verduras y frutas\'] = set(c.COMUNES) - set().union(*GRUPOS.values())\nPRIMEROS = [\'Tomate\', \'Huevos\', \'Arroz\', \'Cebolla\', \'Queso\', \'Pollo\', \'Papa\', \'Atún\', \'Zanahoria\', \'Lenteja\', \'Aguacate\', \'Pan\', \'Ajo\', \'Limón\', \'Fideo\', \'Leche\']\n\nCSS = \'\'\'<style>\n@import url(\'https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&display=swap\');\n.stApp {background:#fff0f6; color:#19234c;}\n.block-container {max-width:1240px; padding:1.4rem 2rem 3rem !important;}\nheader[data-testid="stHeader"] {background:transparent;}\n.rf-header {display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #e8a1c8; padding:.4rem 0 1rem; gap:1rem;}\n.rf-brand {display:flex; align-items:center; gap:.7rem; font-size:2rem; font-weight:850; letter-spacing:-.06em; color:#141414;}\n.rf-brand > span:first-child {display:grid;place-items:center;background:#ff701d;border-radius:12px;width:48px;height:48px;}\n.rf-brand b {color:#ff563e;}\na.rf-brand, a.rf-brand:visited, a.rf-brand:hover {color:#141414;text-decoration:none;}\na.rf-brand {cursor:pointer;border-radius:12px;}\na.rf-brand:focus-visible {outline:1px solid #123fd0;outline-offset:5px;}\n.rf-nav {background:#fff5ab; border:1px solid #edbd2e; padding:.5rem 1rem; border-radius:30px; font-weight:700; font-size:.9rem;}\n.rf-hero {position:relative;text-align:center;padding:1.6rem 0 1.3rem;}\n.rf-hero h1 {font-family:\'Caveat\',cursive;font-size:clamp(2.6rem,5.5vw,4.6rem);line-height:1.08;letter-spacing:-.025em;color:#073bcb;padding:0;margin:0;}\n.rf-hero h1::after {content:\'\';display:block;width:32%;height:2px;margin:.45rem auto .8rem;background:#ff721b;border-radius:50%;transform:rotate(-2deg);transform-origin:left center;animation:rf-trazo 1.15s cubic-bezier(.55,.06,.35,1) .25s both;}\n@keyframes rf-trazo {from {transform:rotate(-2deg) scaleX(0);} to {transform:rotate(-2deg) scaleX(1);}}\n.rf-hero p {color:#59617b;font-size:1rem;margin:0;}\n.rf-sticker {font-size:2.4rem;display:inline-block;vertical-align:middle;transform:rotate(-12deg);margin:0 .6rem;}\n.st-key-tarjeta {background:#fff;border:1px solid #d95eac !important;border-radius:24px !important;padding:1.4rem 1.5rem !important;}\n.rf-counter {display:inline-block;background:#fff176;color:#183280;border-radius:30px;padding:.5rem 1rem;font-weight:750;font-size:.9rem;margin-bottom:.25rem;}\n.st-key-filtro_ingredientes input {font-size:1rem;}\n.st-key-filtro_ingredientes [data-baseweb="input"] {border:1px solid #173aa8;border-radius:30px;background:#fff !important;}\n.st-key-categoria [data-testid="stButtonGroup"] {flex-wrap:wrap;}\n.st-key-cuadros {max-width:640px;margin-inline:auto;gap:6px !important;}\n.st-key-cuadros [data-testid="stHorizontalBlock"] {gap:6px !important;flex-wrap:nowrap;}\n.st-key-cuadros [data-testid="stColumn"] {min-width:0;}\n[class*="st-key-alimento_"] button {position:relative;display:flex;align-items:center;justify-content:center;aspect-ratio:1 / 1;width:100%;max-width:none;margin-inline:auto;height:auto;min-height:0;border:1px solid #2143af !important;border-radius:8px !important;background:#fff !important;color:#171d33 !important;padding:.4rem .2rem !important;box-shadow:0 1px 0 #e7ebf8;transition:transform .15s;}\n.stApp [class*="st-key-alimento_"] button p {font-size:.86rem !important;font-weight:750 !important;line-height:1.2;}\n[class*="st-key-alimento_"] button > div {display:flex;flex-direction:column;gap:.2rem;}\n[class*="st-key-alimento_"] button p::before {display:block;font-size:2.25rem;line-height:1.2;margin-bottom:.2rem;}\n[class*="st-key-alimento_"] button:hover {transform:translateY(-3px);background:#fff5ed !important;}\n[class*="st-key-alimento_"] button[kind="primary"] {background:#ffe4d9 !important;border-color:#ff6047 !important;color:#171d33 !important;}\n[class*="st-key-alimento_"] button[kind="primary"]::after {content:\'✓\';position:absolute;top:6px;right:6px;width:23px;height:23px;background:#ff6047;border-radius:50%;color:white;font-weight:bold;}\n[class*="st-key-alimento_"] button:focus-visible {outline:1px solid #123bd1;outline-offset:3px;}\n.st-key-notas {background:#fff9c4;border-radius:18px;padding:1rem !important;}\n.st-key-notas [data-testid="stWidgetLabel"] p {font-size:.95rem;font-weight:700;color:#19234c;}\n.st-key-notas [data-baseweb="select"] > div,\n.st-key-notas [data-testid="stSelectbox"] .react-aria-ComboBox > div {background:#FFF176 !important;border-color:#E0B90D !important;border-radius:14px !important;}\n.st-key-notas [data-testid="stNumberInputContainer"],\n.st-key-notas [data-testid="stNumberInputContainer"] input {background:#FFF176 !important;border-color:#E0B90D !important;border-radius:14px !important;}\n.st-key-chef {display:flex; justify-content:center;}\n.st-key-chef [data-testid="stWidgetLabel"] p {font-size:1.1rem !important; font-weight:700; color:#19234c;}\n.st-key-buscar button {background:#093ed7 !important;border:1px solid #082b9c !important;border-radius:40px;box-shadow:0 1px 0 #082b9c;min-height:62px;}\n.stApp .st-key-buscar button p {font-size:2.1rem !important;font-weight:700;color:white !important;}\n.st-key-buscar button:disabled {opacity:.45;}\n.rf-small {color:#67718a;font-size:.85rem;margin:.2rem 0;}\n.dp-sello {display:flex;align-items:baseline;gap:.5rem;background:#087c70;color:white;border-radius:12px;padding:.5rem .8rem;}\n.dp-sello b {font-size:1.5rem;}.dp-ahorro {color:#087466;font-size:.85rem;}\n.dp-falta {background:#fff3bd;color:#614700;padding:.7rem;border-radius:12px;}\n.dp-banner {display:flex;flex-wrap:wrap;gap:1rem;margin:1rem 0;}\n.dp-banner > div {flex:1;background:#fff;border-radius:16px;padding:1rem;border:1px solid #e8d5e4;}\n.dp-banner b {display:block;font-size:1.8rem;}.dp-banner .cero {background:#e0f5ed;color:#065747;}\n.dp-espera {display:flex;justify-content:center;padding:1rem;}\n@media(max-width:700px) {\n.block-container {padding:1rem .8rem 2rem !important;}\n.rf-brand {font-size:1.65rem;}.rf-brand > span:first-child {width:40px;height:40px;}\n.rf-nav {font-size:.8rem;padding:.4rem .7rem;}\n.rf-hero {padding:1.3rem 0;}.rf-hero h1 {font-size:2.9rem;}.rf-sticker {display:none;}\n.rf-hero p {font-size:.9rem;}.st-key-tarjeta {padding:1rem .8rem !important;border-radius:20px !important;}\n.st-key-cuadros [data-testid="stHorizontalBlock"] {flex-wrap:wrap !important;gap:3px !important;}\n.st-key-cuadros [data-testid="stColumn"] {width:calc(33.333% - 2px) !important;flex:0 0 calc(33.333% - 2px) !important;min-width:0 !important;}\n[class*="st-key-alimento_"] button {max-width:none;min-height:0;border-radius:8px !important;padding:.4rem .1rem !important;}\n.stApp [class*="st-key-alimento_"] button p {font-size:.72rem !important;}\n[class*="st-key-alimento_"] button p::before {font-size:1.8rem;}\n[class*="st-key-alimento_"] button[kind="primary"]::after {width:19px;height:19px;top:4px;right:4px;font-size:.75rem;}\n.st-key-notas [data-testid="stHorizontalBlock"] {gap:.5rem;}\n.rf-counter {font-size:.8rem;}\n}\n/* Animaciones cortas al entrar e interactuar; solo la carga se repite. */\n@keyframes rf-bienvenida {\n  0% {transform:translateY(-16px) rotate(-18deg) scale(.8);opacity:0;}\n  55% {transform:translateY(0) rotate(9deg) scale(1.1);opacity:1;}\n  78% {transform:rotate(-5deg) scale(.97);}\n  100% {transform:none;opacity:1;}\n}\n.rf-entrada .rf-brand > span:first-child {animation:rf-bienvenida .85s ease-out both;}\n@keyframes rf-saltito {\n  0%,100% {transform:translateY(0) rotate(0);}\n  35% {transform:translateY(-7px) rotate(-9deg) scale(1.08);}\n  70% {transform:translateY(-2px) rotate(7deg);}\n}\n@media(hover:hover) and (pointer:fine) {\n  [class*="st-key-alimento_"] button:hover p::before {animation:rf-saltito .5s ease-in-out;}\n  .rf-brand > span:first-child:hover svg {animation:rf-saltito .6s ease-in-out;}\n}\n[class*="st-key-alimento_"] button:focus-visible p::before {animation:rf-saltito .5s ease-in-out;}\n/* Respuesta táctil: se comprime al tocar y recupera su tamaño al soltar. */\n@media(hover:none), (pointer:coarse) {\n  [class*="st-key-alimento_"] button {\n    touch-action:manipulation;\n    -webkit-tap-highlight-color:transparent;\n    transition:transform .32s cubic-bezier(.34,1.8,.5,1), box-shadow .2s ease;\n  }\n  [class*="st-key-alimento_"] button:hover {transform:none;}\n  [class*="st-key-alimento_"] button:active {\n    transform:scale(.89);\n    box-shadow:0 1px 0 #e7ebf8;\n    transition:transform .09s ease-out;\n  }\n  .st-key-buscar button {\n    touch-action:manipulation;\n    transition:transform .32s cubic-bezier(.34,1.8,.5,1), box-shadow .2s ease;\n  }\n  .st-key-buscar button:not(:disabled):active {\n    transform:scale(.95);\n    box-shadow:0 1px 0 #082b9c;\n    transition:transform .09s ease-out;\n  }\n}\n@media(hover:hover) and (pointer:fine) {\n  [class*="st-key-alimento_"] button:active {transform:scale(.94);}\n}\n@keyframes rf-flotar {0%,100% {transform:translateY(0) rotate(-4deg);}50% {transform:translateY(-10px) rotate(5deg);}}\n@keyframes rf-colores {0%,100% {fill:#ff701d;}25% {fill:#0b45d9;}50% {fill:#b52cb3;}75% {fill:#078b80;}}\n@keyframes rf-puerta {0%,15%,90%,100% {transform:scaleX(1);}45%,60% {transform:scaleX(.18);}}\n@keyframes rf-hoja {0%,100% {transform:rotate(0);}50% {transform:rotate(-18deg);}}\n/* Carga: solo el isotipo flotando y cambiando de color, sin tarjeta ni fondo. */\n.dp-espera {position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;pointer-events:none;}\n.rf-cargando {display:flex;align-items:center;justify-content:center;}\n.rf-cargando > svg {animation:rf-flotar 1.8s ease-in-out infinite;overflow:visible;}\n.dp-color {animation:rf-colores 5s linear infinite;}\n.dp-puerta {transform-box:view-box;transform-origin:13px 27px;animation:rf-puerta 2.4s ease-in-out infinite;}\n.dp-hoja {transform-box:view-box;transform-origin:24px 12px;animation:rf-hoja 1.8s ease-in-out infinite;}\n@media(prefers-reduced-motion:reduce) {\n  *,*::before,*::after {transition:none !important;animation:none !important;}\n  [class*="st-key-alimento_"] button:active,\n  .st-key-buscar button:not(:disabled):active {transform:none !important;}\n}\n\n/* Toda la página en imprenta (DM Sans), salvo el título y la frase de debajo del héroe. */\n.stApp, .stApp :is(p,h1,h2,h3,h4,h5,h6,label,input,textarea,select,li,td,th,a,small,strong,b,summary),\n.rf-brand, .rf-counter, .sz-nombre, .sz-chip, .sz-desc, .dp-falta {\n  font-family:\'DM Sans\',\'Segoe UI\',sans-serif !important;\n}\n.rf-hero h1, .rf-hero h1 *, .rf-hero p, .rf-hero p * {font-family:\'Caveat\',\'Segoe Print\',cursive !important;}\n.rf-hero p {font-size:1.65rem !important; color:#3c4566;}\n.stApp button, .stApp button p, .rf-nav {font-family:\'DM Sans\',\'Segoe UI\',sans-serif !important;}\n.stApp button p {font-size:1.02rem !important;font-weight:600;}\n.rf-nav {font-weight:700;font-size:1.05rem;}\n.stApp :is(input,select,textarea) {font-size:1.02rem;}\n.rf-nav,.rf-counter {font-size:1rem;}\n.st-key-notas [data-testid="stWidgetLabel"] p {font-size:1rem;}\n[class*="st-key-alimento_"] button p, [class*="st-key-alimento_"] button p * {\n  font-family:\'DM Sans\',\'Segoe UI\',sans-serif !important;\n}\n/* Categorías: centradas, letra más fina, recuadros redondeados amarillos. */\n.st-key-categoria {display:flex; justify-content:center;}\n.st-key-categoria [data-testid="stButtonGroup"] {flex-wrap:wrap; justify-content:center;}\n.st-key-categoria button {background:#fff59d !important;border:1px solid #e6c93c !important;box-shadow:0 1px 0 #eadf9a !important;padding:.38rem .95rem !important;border-radius:999px !important;}\n.st-key-categoria button p {color:#253568 !important;font-weight:500 !important;font-size:1rem !important;}\n.st-key-categoria button[kind="primary"] {background:#ffe93e !important;border-color:#d9b800 !important;}\n.st-key-categoria button[kind="primary"] p {color:#073bcb !important;font-weight:600 !important;}\n/* Ventanas desplegables (foto de la refri, básicos): con caja clara otra vez. */\n.st-key-tarjeta [data-testid="stExpander"] {border:1px solid #d9e0f2 !important;background:#fff !important;border-radius:14px !important;box-shadow:none !important;padding:.25rem .9rem !important;}\n.st-key-tarjeta [data-testid="stExpander"] summary {padding-left:.1rem !important;}\n/* Botón de la cámara: cuadrado grande, centrado, puntas redondeadas. */\n.st-key-foto_refri [data-testid="stFileUploader"] {display:flex; justify-content:center;}\n.st-key-foto_refri [data-testid="stFileUploaderDropzone"] {\n  width:230px; max-width:60vw; aspect-ratio:1/1; margin:0 auto;\n  border-radius:32px !important; border:2px solid #ff701d !important; background:#fff !important;\n  display:flex; align-items:center; justify-content:center; cursor:pointer;\n}\n.st-key-foto_refri [data-testid="stFileUploaderDropzone"] > * {display:none !important;}\n.st-key-foto_refri [data-testid="stFileUploaderDropzone"]::after {content:"📷"; font-size:5.5rem; line-height:1;}\n.rf-foto-pie {text-align:center !important; font-weight:700; color:#19234c; margin:.5rem 0 .3rem; font-size:1.6rem !important;}\n/* Bordes finos también en selectores, categorías y recetas. */\n.stApp button, .stApp [data-baseweb="select"] > div,\n.stApp [data-baseweb="input"], .stApp [data-testid="stNumberInputContainer"],\n.stApp [data-testid="stExpander"], [class*="st-key-rc_"] {border-width:1px !important;}\n</style>\'\'\'\n\n\ndef estilos():\n    st.markdown(CSS, unsafe_allow_html=True)\n    icons = \'\'.join(f\'.st-key-alimento_{i} button p::before {{content:"{ICONOS[x]}";}}\' for i, x in enumerate(c.COMUNES))\n    verde = c.COMUNES.index(\'Verde\')\n    icons += f\'.st-key-alimento_{verde} button p::before {{filter:hue-rotate(65deg) saturate(1.6) brightness(.95);}}\'   # mismo platano del Maduro, pero verde\n    st.markdown(\'<style>\'+icons+\'</style>\', unsafe_allow_html=True)\n\n\ndef cabecera(svg):\n    entrada = " rf-entrada" if not st.session_state.get("_portada_vista") else ""\n    st.session_state["_portada_vista"] = True\n    st.markdown(f\'<div class="rf-header{entrada}"><a class="rf-brand" href="./" target="_self" aria-label="LaRefri: volver al inicio"><span>{svg}</span><span>larefri<b>.</b></span></a></div>\', unsafe_allow_html=True)\n\n\ndef hero():\n    st.markdown(\'<div class="rf-hero"><h1><span class="rf-sticker" aria-hidden="true">🧀 🥑</span>Aquí se cocina con lo que hay.<span class="rf-sticker" aria-hidden="true">🍅 🥚</span></h1><p>Descubre qué cocinar <b>sin tener que gastar de más.</b></p></div>\', unsafe_allow_html=True)\n\n\ndef alternar(indice):\n    clave = f\'ing_{indice}\'\n    st.session_state[clave] = not st.session_state.get(clave, False)\n\n\ndef ingredientes():\n    consulta = \'\'  # La entrada principal añade ingredientes como etiquetas independientes.\n    categoria = st.pills(\'Categorías\', [\'Todo\', \'Verduras y frutas\', \'Proteínas\', \'Despensa\', \'Lácteos\'], default=\'Todo\', key=\'categoria\', label_visibility=\'collapsed\')\n    orden = PRIMEROS + [x for x in c.COMUNES if x not in PRIMEROS]\n    visibles = [x for x in orden if (not categoria or categoria == \'Todo\' or x in GRUPOS[categoria]) and n._clave(consulta) in n._clave(x)]\n    if not visibles:\n        st.info(\'No está en la lista rápida. Puedes añadirlo abajo, en «Otros ingredientes».\')\n    with st.container(key=\'cuadros\'):\n        for inicio in range(0, len(visibles), 4):\n            cols = st.columns(4, gap=\'small\')\n            for col, x in zip(cols, visibles[inicio:inicio+4]):\n                i = c.COMUNES.index(x)\n                activo = st.session_state.get(f\'ing_{i}\', False)\n                col.button(x, key=f\'alimento_{i}\', type=\'primary\' if activo else \'secondary\', width=\'stretch\', on_click=alternar, args=(i,))\n')


import html
import os
import time

import requests
import streamlit as st

import casa as c
import diseno as d
import fotos
import nucleo as n

ICONO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.png")
st.set_page_config(page_title="larefri.", page_icon=ICONO if os.path.exists(ICONO) else "🧊", layout="wide")

ESPERA_ENTRE_CONSULTAS = 1
POR_PAGINA = 6
INICIALES = {"cero": [], "uno": [], "pedido": None, "personas": 2, "ultima_consulta": 0.0}
for _k, _v in INICIALES.items():
    st.session_state.setdefault(_k, _v)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def secreto(nombre):
    try:
        return st.secrets.get(nombre) or os.environ.get(nombre)
    except Exception:  # noqa: BLE001  (sin secrets.toml en local)
        return os.environ.get(nombre)


def cliente_gemini():
    from google import genai
    clave = secreto("GEMINI_API_KEY")
    if not clave:
        raise n.ErrorIA("Falta la clave de la IA (GEMINI_API_KEY): agrégala en Variables de Railway y vuelve a desplegar.")
    return genai.Client(api_key=clave)


def esperar_turno():
    falta = ESPERA_ENTRE_CONSULTAS - (time.time() - st.session_state["ultima_consulta"])
    if falta > 0:
        time.sleep(falta)
    st.session_state["ultima_consulta"] = time.time()


class SinFoto(Exception):
    """No se guarda en caché: así se vuelve a intentar más tarde (cuota de Unsplash o de la IA)."""


@st.cache_resource
def _sin_foto_reciente() -> dict:
    return {}                                # consulta -> hora en que no se encontró (para no gastar cuota)


@st.cache_data(ttl=7 * 86400, show_spinner=False, max_entries=500)
def foto(consulta: str, plato: str = "", version: int = 15):
    """Busca la foto y, si hay clave de IA, la IA mira cada candidata y solo acepta la que es ese plato.
    Solo se guarda cuando SÍ hay foto; si no, se reintenta en una hora."""
    verificar = None
    if secreto("GEMINI_API_KEY"):
        cliente = cliente_gemini()

        def verificar(url):
            try:
                img = requests.get(url, timeout=5).content
            except requests.RequestException:
                return False
            try:
                return n.foto_coincide(cliente, img, plato or consulta, consulta)
            except n.ErrorIA:
                return None          # no se pudo revisar: fotos.py decide por el título
    f = fotos.buscar_foto(consulta, secreto("PEXELS_API_KEY"), secreto("UNSPLASH_ACCESS_KEY"), verificar)
    if not f:
        raise SinFoto(consulta)
    return f


def _buscar_foto(r):
    malas = _sin_foto_reciente()
    if time.time() - malas.get(r.busqueda_foto, 0) <= 3600:
        return None
    try:
        return foto(r.busqueda_foto, f"{r.nombre} — lleva SOLO: "
                    + ", ".join(i.nombre for i in r.ingredientes if not i.basico_de_despensa))
    except Exception as e:  # noqa: BLE001
        print(f"[foto] sin foto para {r.nombre!r}: {type(e).__name__} {e}", flush=True)
        malas[r.busqueda_foto] = time.time()
        return None


@st.cache_resource
def _creadas_hoy() -> dict:
    return {}                                # día -> cuántas imágenes se crearon (límite para no gastar de más)


MAX_IMAGENES_DIA = 30
MODELOS_IMAGEN = ("gemini-2.5-flash-image", "gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview")


@st.cache_data(ttl=60 * 86400, show_spinner=False, max_entries=1000, persist="disk")
def crear_imagen(plato: str, ingredientes: str) -> bytes | None:
    """La IA crea la foto del plato (solo para recetas sin foto real). Se guarda para no pagarla dos veces."""
    from google.genai import types
    cuenta = _creadas_hoy()
    hoy = time.strftime("%Y-%m-%d")
    if cuenta.get(hoy, 0) >= MAX_IMAGENES_DIA:
        raise SinFoto("límite diario de imágenes")
    cliente = cliente_gemini()
    prompt = (f"Fotografía gastronómica realista, apetitosa, luz natural, plato servido sobre una mesa, vista de 3/4: "
              f"{plato}. Lleva SOLO estos ingredientes, que se reconozcan: {ingredientes}. "
              "Sin texto, sin personas, sin manos, sin ingredientes extra.")
    for modelo in MODELOS_IMAGEN:
        try:
            resp = cliente.models.generate_content(model=modelo, contents=prompt, config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]))
            datos = next(p.inline_data.data for p in resp.candidates[0].content.parts if p.inline_data)
            cuenta[hoy] = cuenta.get(hoy, 0) + 1
            print(f"[imagen] creada para {plato!r} con {modelo} ({cuenta[hoy]} hoy)", flush=True)
            return datos
        except Exception as e:  # noqa: BLE001
            print(f"[imagen] {modelo} falló: {str(e)[:200]}", flush=True)
    raise SinFoto("no se pudo crear la imagen")


def _imagen_ia(r):
    if not secreto("GEMINI_API_KEY"):
        return None
    ings = ", ".join(i.nombre for i in r.ingredientes if not i.basico_de_despensa)
    try:
        datos = crear_imagen(r.nombre, ings)
    except Exception:  # noqa: BLE001
        return None
    return {"url": datos, "fuente": "IA"} if datos else None


# ---------------------------------------------------------------------------
# Foto de la refri: la IA reconoce los ingredientes y los marca solos
# ---------------------------------------------------------------------------

@st.cache_data(ttl=86400, show_spinner=False, max_entries=200)
def ingredientes_en_foto(datos: bytes, _sugerencias: tuple = ()) -> list[str]:
    """Gemini mira la foto y devuelve TODOS los ingredientes de cocina que reconoce (se guarda en
    caché: la misma foto no se paga dos veces)."""
    from google.genai import types
    esperar_turno()
    cliente = cliente_gemini()
    prompt = ("Esta es una foto de una refrigeradora o despensa. "
              "Lista TODOS los ingredientes de cocina que reconozcas. "
              "Responde únicamente con los nombres separados por coma, en español, en singular "
              "(sin cantidades, sin marcas, sin explicaciones). Si no hay ningún ingrediente, responde: ninguno")
    partes = [prompt, types.Part.from_bytes(data=datos, mime_type="image/jpeg")]
    resp = None
    for modelo in n.MODELOS_CASCADA:   # si la llave no tiene acceso a uno, prueba el siguiente
        try:
            resp = cliente.models.generate_content(model=modelo, contents=partes,
                                                   config=types.GenerateContentConfig(temperature=0.2))
            break
        except Exception:  # noqa: BLE001
            resp = None
    if resp is None:
        raise n.ErrorIA("La IA no pudo mirar la foto ahora. Inténtalo de nuevo en un momento.")
    texto = (resp.text or "").strip().lower()
    if not texto or "ninguno" in texto:
        return []
    return [x.strip().capitalize() for x in texto.split(",") if x.strip()]


def marcar_desde_foto(archivo):
    """Todo lo que la IA reconoció se marca en la cuadrícula o se añade como cuadrito de 'Añade un ingrediente'."""
    detectados = ingredientes_en_foto(archivo.getvalue(), tuple(c.SUGERENCIAS))
    claves_comunes = {n._clave(x): j for j, x in enumerate(c.COMUNES)}
    claves_comunes.update({n._clave(x).rstrip("s"): j for j, x in enumerate(c.COMUNES)})  # "tomates" -> "Tomate"
    marcados, vistos = [], set()
    for d in detectados:
        k = n._clave(d)
        if not k or k in vistos or "sobrante" in k:
            continue
        vistos.add(k)
        i = claves_comunes.get(k) or claves_comunes.get(k.rstrip("s")) or claves_comunes.get(k.removesuffix("es"))
        if i is not None:
            st.session_state[f"ing_{i}"] = True      # marca el botón del ingrediente
            marcados.append(c.COMUNES[i])
        else:
            items = st.session_state.setdefault("algo_mas_items", [])
            if all(n._clave(y) != k for y in items):
                items.append(d)                       # va como cuadrito propio
                marcados.append(d)
    st.session_state["_foto_mensaje"] = (
        "📷 De la foto reconocí: " + ", ".join(marcados) + "." if marcados else
        "No reconocí ingredientes de la lista en esa foto. Prueba con más luz o más de cerca.")


def foto_refri():
    archivo = st.file_uploader("Foto de tu refri o despensa", type=["jpg", "jpeg", "png", "webp"],
                               key="foto_refri", label_visibility="collapsed")
    st.markdown('<p class="rf-foto-pie">Sácale una foto a tu refri</p>', unsafe_allow_html=True)
    if archivo is not None and st.session_state.get("_foto_procesada") != archivo.file_id:
        with st.spinner("Mirando tu refri…"):
            try:
                marcar_desde_foto(archivo)
            except n.ErrorIA as err:
                st.error(str(err))
                st.session_state["_foto_procesada"] = archivo.file_id
                return
            except Exception:  # noqa: BLE001
                st.error("No pude mirar la foto. Prueba con otra o marca los ingredientes a mano.")
                st.session_state["_foto_procesada"] = archivo.file_id
                return
        st.session_state["_foto_procesada"] = archivo.file_id
        st.rerun()
    msg = st.session_state.pop("_foto_mensaje", None)
    if msg:
        st.success(msg)


def _pintar_foto(r, f):
    usadas = st.session_state.setdefault("_fotos_usadas", {})   # una misma foto no se repite en dos recetas
    if f and usadas.setdefault(f["url"], r.nombre) != r.nombre:
        f = None
    if f and f.get("fuente") == "IA":
        st.image(f["url"], width="stretch")
        st.markdown('<div class="sz-credito">Imagen creada con IA</div>', unsafe_allow_html=True)
    elif f:
        st.image(f["url"], width="stretch")
        d.credito_foto(f)
    else:
        d.foto_vacia()


PENDIENTES: list = []          # (hueco, receta): las fotos se ponen DESPUÉS de mostrar todas las recetas


def mostrar_foto(r, despues: bool = False):
    if despues:
        hueco = st.empty()
        with hueco.container():
            d.foto_vacia()
        PENDIENTES.append((hueco, r))
        return
    _pintar_foto(r, _buscar_foto(r))


def poner_fotos():
    """Busca las fotos de todas las tarjetas a la vez (en paralelo) y las pone en su lugar."""
    from concurrent.futures import ThreadPoolExecutor
    from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
    pend, ctx = list(PENDIENTES), get_script_run_ctx()
    PENDIENTES.clear()
    if not pend:
        return

    def una(r):
        add_script_run_ctx(None, ctx)
        return _buscar_foto(r) or _imagen_ia(r)       # sin foto real: la IA la crea
    t0 = time.time()
    with ThreadPoolExecutor(6) as ex:
        fotos_ = list(ex.map(una, [r for _, r in pend]))
    print(f"[tiempo] fotos: {time.time() - t0:.1f} s", flush=True)
    for (hueco, r), f in zip(pend, fotos_):
        with hueco.container():
            _pintar_foto(r, f)


def ir(_pagina="inicio", *_):
    """El logo vuelve al principio: borra los resultados."""
    st.session_state["cero"], st.session_state["uno"], st.session_state["pedido"] = [], [], None
    st.session_state["_fotos_usadas"] = {}


def lo_que_tiene() -> list[str]:
    s = st.session_state
    extra = [y for x in (s.get("algo_mas_items") or []) for y in c.separar_lista(x)
             if "sobrante" not in n._clave(y)]                                      # cada uno en su cuadrito
    vistos, out = set(), []
    marcados = [x for i, x in enumerate(c.COMUNES) if s.get(f"ing_{i}")]
    for x in marcados + extra:
        k = n._clave(x)
        if k and k not in vistos:
            vistos.add(k)
            out.append(x)
    return out


def sello_cero(r) -> str:
    return (f'<div class="dp-sello"><b>$0</b><span>No compras nada</span></div>'
            f'<div class="dp-ahorro">Te ahorras ~${c.ahorro(r):.2f} usando lo de tu casa</div>')


def sello_falta(r) -> str:
    falta = ", ".join(i.nombre for i in r.ingredientes if not i.de_tu_casa)
    return (f'<div class="dp-falta">🛒 Te falta: <b>{html.escape(falta)}</b> · ~${c.costo_faltantes(r):.2f}</div>')


ESPERA_HTML = """<div class="dp-espera" role="status" aria-live="polite" aria-atomic="true" aria-label="Buscando recetas"><div class="rf-cargando">
<svg width="110" height="110" viewBox="0 0 48 48" aria-hidden="true">
 <rect class="dp-color" width="48" height="48" rx="12" fill="#FF7A1A"/>
 <g fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <path d="M18 12 H30 Q35 12 35 17 V37 Q35 42 30 42 H18 Q13 42 13 37 V17 Q13 12 18 12 Z" opacity=".35"/>
  <path d="M15.5 27 H32.5 M15.5 33 H32.5" opacity=".35"/>
  <g class="dp-puerta"><path d="M18 12 H30 Q35 12 35 17 V37 Q35 42 30 42 H18 Q13 42 13 37 V17 Q13 12 18 12 Z M13 23 H35 M18 16 V19 M18 27 V33"/></g>
  <path class="dp-hoja" d="M24 12 C24 7 28 4 33 4 C33 9 29 12 24 12 Z"/>
 </g></svg>
</div></div>"""




# ---------------------------------------------------------------------------
# Detalle de una receta
# ---------------------------------------------------------------------------

def _cerrar_receta():
    st.session_state["abierta"] = None


@st.dialog("Receta", width="large", on_dismiss=_cerrar_receta)
def ver_receta(r):
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        mostrar_foto(r)
    with c2:
        d.info_receta(r)
        st.markdown(sello_cero(r) if all(i.de_tu_casa for i in r.ingredientes) else sello_falta(r),
                    unsafe_allow_html=True)
    st.subheader("Lo que usas de tu casa")
    items = [f"<li><b>{html.escape(i.nombre)}</b>: {html.escape(n.lo_que_usas(i))}"
             f"{' · <i>básico de cocina</i>' if i.basico_de_despensa else ''}</li>"
             for i in r.ingredientes if i.de_tu_casa]
    st.markdown(f'<ul class="dp-usa">{"".join(items)}</ul>', unsafe_allow_html=True)
    falta = [i for i in r.ingredientes if not i.de_tu_casa]
    if falta:
        st.markdown("**Lo que te falta comprar**")
        st.dataframe([{"Producto": i.nombre, "Compras": i.presentacion, "Precio": i.precio_presentacion_usd}
                      for i in falta], hide_index=True, width="stretch",
                     column_config={"Precio": st.column_config.NumberColumn(format="$%.2f")})
    with st.expander("🧾 ¿Cuánto te ahorras? Lo que costaría comprar cada cosa"):
        filas = [{"Ingrediente": f["Ingrediente"], "Usas": f["Usas"], "Si lo compraras": f["Compras"],
                  "Valdría lo que usas": f["Vale lo que usas"]}
                 for f, i in zip(n.desglose_receta(r), r.ingredientes) if i.de_tu_casa and not i.basico_de_despensa]
        st.dataframe(filas, hide_index=True, width="stretch",
                     column_config={"Valdría lo que usas": st.column_config.NumberColumn(format="$%.2f")})
        st.caption(f"Usando lo que ya tienes te ahorras unos ${c.ahorro(r):.2f}. Precios estimados por IA en "
                   "tiendas de Ecuador; no los pagas porque ya los tienes.")
    st.subheader("Preparación")
    for k, p in enumerate(r.pasos, 1):
        st.markdown(f"{k}. {p}")
    st.caption(f"Dificultad: {r.dificultad} · {r.tiempo_minutos} min · para {r.porciones}")
    if r.alergenos:
        st.warning("⚠️ **Alérgenos:** " + ", ".join(r.alergenos) + ". Es una estimación: si tienes alergias, "
                   "revisa la etiqueta de cada producto.")
    if st.button("Atrás", icon=":material/arrow_back:", key=f"cerrar_{r.nombre}", width="stretch"):
        st.rerun()


def tarjeta(r, clave: str, cero: bool):
    with st.container(border=True, key=f"rc_{clave}"):
        mostrar_foto(r, despues=True)
        d.info_receta(r)
        st.markdown(sello_cero(r) if cero else sello_falta(r), unsafe_allow_html=True)
        if st.button("Ver receta", key=f"ver_{clave}", icon=":material/menu_book:", type="primary", width="stretch"):
            st.session_state["abierta"] = r.nombre
        if st.session_state.get("abierta") == r.nombre and not st.session_state.get("_dialogo_puesto"):
            st.session_state["_dialogo_puesto"] = True      # la receta sigue abierta aunque la página se recargue
            ver_receta(r)


def cuadricula(recetas, prefijo: str, cero: bool):
    for fila in range(0, len(recetas), 3):
        cols = st.columns(3, gap="medium")
        for j, r in enumerate(recetas[fila:fila + 3]):
            with cols[j]:
                tarjeta(r, f"{prefijo}{fila + j}", cero)


# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------

def buscar(mas=False):
    s = st.session_state
    tiene = lo_que_tiene()
    pedido = dict(tiene=tiene, personas=s["personas_in"], tiempo=s["tiempo_in"], dieta=s.get("dieta_in", "Todas"),
                  categoria="" if s["tipo_in"] == "Cualquiera" else s["tipo_in"], permitir=True,
                  basicos=list(s.get("basicos") or []), creativo=bool(s.get("creativo")))
    excluir = [r.nombre for r in s["cero"] + s["uno"]] if mas else []
    gratis = (not pedido["creativo"]                    # el recetario guardado responde solo, sin IA ni espera
              and c.hay_suficiente_en_memoria(pedido["tiene"], pedido["personas"], pedido["tiempo"],
                                              pedido["dieta"], pedido["categoria"], excluir))
    espera = st.empty()
    if not mas and not gratis:                 # el isotipo de espera solo aparece en la primera búsqueda con IA
        espera.markdown(ESPERA_HTML, unsafe_allow_html=True)
    try:
        if not gratis:                         # sin llamada a la IA no hace falta espaciar consultas
            esperar_turno()
        cero, uno = c.buscar_con_lo_que_hay(
            cliente_gemini(), pedido["tiene"], pedido["personas"], pedido["tiempo"], pedido["dieta"],
            pedido["categoria"], pedido["permitir"], excluir=excluir, basicos=pedido["basicos"],
            creativo=pedido["creativo"])
    finally:
        espera.empty()
    if mas:
        vistos = {r.nombre for r in s["cero"] + s["uno"]}
        s["cero"] = s["cero"] + [r for r in cero if r.nombre not in vistos]
        ya = [i.nombre for r in s["uno"] for i in r.ingredientes if not i.de_tu_casa]
        s["uno"] = s["uno"] + c.un_faltante_distinto([r for r in uno if r.nombre not in vistos], ya)
    else:
        s["cero"], s["uno"], s["sin_mas"], s["abierta"] = cero, uno, False, None
    s["pedido"] = pedido


def formulario():
    portada.hero()
    with st.container(border=True, key="tarjeta"):
        foto_refri()
        portada.ingredientes()
        campo.algo_mas(c.SUGERENCIAS, "Añade un ingrediente…")
        with st.expander("Básicos de cocina que tienes (sal, aceite, especias…)"):
            st.pills("Básicos", c.BASICOS, selection_mode="multi", default=c.BASICOS, key="basicos",
                     label_visibility="collapsed")
            st.caption("Toca un básico para apagarlo si no lo tienes. La sal y el agua siempre se asumen.")
        with st.container(key="notas"):
            a, b, f = st.columns(3, gap="medium")
            a.number_input("Personas", 1, 12, 2, key="personas_in")
            b.selectbox("Tiempo", [15, 30, 45, 60], index=1, key="tiempo_in", format_func=lambda m: f"{m} min o menos")
            f.selectbox("Tipo de plato", ["Cualquiera"] + n.CATEGORIAS, key="tipo_in")
        tiene = lo_que_tiene()
        st.caption(f"Tienes {len(tiene)} ingrediente{'s' if len(tiene) != 1 else ''} marcados"
                   + (f": {', '.join(tiene)}." if tiene else ". Elige al menos uno."))
        col_normal, col_chef = st.columns(2, gap="medium")
        if col_normal.button("Vamos a cocinar!", icon=":material/soup_kitchen:", type="primary", width="stretch",
                             disabled=not tiene, key="buscar"):
            st.session_state["creativo"] = False
            try:
                buscar()
            except n.ErrorIA as err:
                st.error(str(err))
        if col_chef.button("Chef inteligente", icon=":material/auto_awesome:", width="stretch",
                           disabled=not tiene, key="buscar_chef",
                           help="La IA inventa platos nuevos y originales con tus ingredientes, en vez de limitarse a platos conocidos."):
            st.session_state["creativo"] = True
            try:
                buscar()
            except n.ErrorIA as err:
                st.error(str(err))


def resultados():
    s = st.session_state
    cero, uno = s["cero"], s["uno"]
    if not s["pedido"]:
        return
    st.write("")
    tiene = lo_que_tiene()
    usados = sum(1 for t in tiene if any(c.lo_tiene(i.nombre, [t]) for r in cero for i in r.ingredientes
                                         if not i.basico_de_despensa))
    st.markdown(
        '<div class="dp-banner"><div class="cero"><small>Gasto de hoy</small><b>$0.00</b></div>'
        + (f'<div><small>Recetas sin comprar nada</small><b>{len(cero)} de {len(cero) + len(uno)}</b>'
           f'<small>{len(uno)} necesitan 1 ingrediente más</small></div></div>' if uno else
           f'<div><small>Recetas sin comprar nada</small><b>{len(cero)}</b></div></div>'),
        unsafe_allow_html=True)
    if cero:
        st.markdown('<p class="sz-seccion">✅ Con lo que tienes: no compras nada</p>', unsafe_allow_html=True)
        cuadricula(cero, "c", True)
    else:
        st.info("Con lo que marcaste no salió ninguna receta sin comprar. Agrega uno o dos ingredientes más que "
                "tengas (un huevo, una papa, un poco de arroz) y vuelve a buscar.")
    if uno and (s.get("sin_mas") or len(cero) >= 30):     # las que necesitan comprar algo, al final de todo
        st.write("")
        st.markdown('<p class="sz-seccion">🛒 Si quieres gastar un poquito: te falta solo una cosa</p>',
                    unsafe_allow_html=True)
        cuadricula(uno, "u", False)
    st.write("")
    poner_fotos()
    total = len(cero) + len(uno)
    if st.session_state.get("sin_mas"):
        st.caption("Esas son todas las recetas que salen con lo que tienes.")
    elif total < 30 and not st.session_state.get("abierta") and campo.llego_al_final(total, key=f"fin_{total}"):    # bajó hasta el final: cargar más
        try:
            antes = total
            buscar(mas=True)
            if len(st.session_state["cero"]) + len(st.session_state["uno"]) == antes:
                st.session_state["sin_mas"] = True
        except n.ErrorIA:
            st.session_state["sin_mas"] = True
        st.rerun()


st.session_state["_dialogo_puesto"] = False
d.aplicar_estilos()
portada.estilos()
portada.cabecera(d.isotipo_svg("#fff", 30))
formulario()
resultados()
st.divider()
if os.environ.get("EDAMAM_APP_ID"):
    st.markdown('<div style="text-align:center;font-size:.8rem;color:#7A6A61">Recetas: TheMealDB · Spoonacular · '
                '<a href="https://www.edamam.com/" target="_blank">Powered by Edamam</a></div>', unsafe_allow_html=True)
st.caption("larefri. · hermana de canastas. y sazona. · IA: Google Gemini · Fotos: "
           "[Unsplash](https://unsplash.com/?utm_source=larefri&utm_medium=referral) / [Wikimedia Commons](https://commons.wikimedia.org) · Precios y valores nutricionales aproximados.")
