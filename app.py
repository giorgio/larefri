"""larefri.: dile qué tienes en casa y te da recetas para hoy SIN GASTAR NADA.

Hermana de canastas. y sazona.
  1. Eliges o escribes lo que tienes (más los básicos de despensa).
  2. La IA propone recetas SOLO con eso; la app revisa cada ingrediente y descarta lo que no tienes.
  3. Cada receta muestra "$0 · No compras nada" y cuánto te ahorras por no salir a comprar.
  Opcional: recetas a las que les falta UN ingrediente barato (apagado por defecto).

Ejecutar en local:  streamlit run app.py
Claves en .streamlit/secrets.toml o en los Secrets de Streamlit Cloud: GEMINI_API_KEY y PEXELS_API_KEY.
"""

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

ESPERA_ENTRE_CONSULTAS = 6
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


@st.cache_data(ttl=7 * 86400, show_spinner=False, max_entries=500)
def foto(consulta: str, plato: str = "", version: int = 5):
    """Busca la foto y, si hay clave de IA, la IA mira cada candidata y solo acepta la que es ese plato.
    Si la revisión falla (cuota de la IA), se lanza error para NO guardar 'sin foto' y reintentar luego."""
    verificar = None
    if secreto("GEMINI_API_KEY"):
        cliente = cliente_gemini()

        def verificar(url):
            try:
                img = requests.get(url, timeout=5).content
            except requests.RequestException:
                return False
            return n.foto_coincide(cliente, img, plato or consulta, consulta)
    return fotos.buscar_foto(consulta, secreto("PEXELS_API_KEY"), secreto("UNSPLASH_ACCESS_KEY"), verificar)


def mostrar_foto(r):
    try:
        f = foto(r.busqueda_foto, r.nombre)
    except Exception:  # noqa: BLE001  (la IA no pudo revisar la foto ahora: sin foto por esta vez)
        f = None
    if f:
        st.image(f["url"], width="stretch")
        d.credito_foto(f)
    else:
        d.foto_vacia()


def ir(_pagina="inicio", *_):
    """El logo vuelve al principio: borra los resultados."""
    st.session_state["cero"], st.session_state["uno"], st.session_state["pedido"] = [], [], None


def lo_que_tiene() -> list[str]:
    s = st.session_state
    extra = c.separar_lista(s.get("extra_txt", ""))
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


ESPERA_HTML = """<div class="dp-espera">
<svg width="92" height="92" viewBox="0 0 48 48" aria-hidden="true">
 <rect width="48" height="48" rx="12" fill="#FF7A1A"/>
 <g fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <path d="M18 12 H30 Q35 12 35 17 V37 Q35 42 30 42 H18 Q13 42 13 37 V17 Q13 12 18 12 Z" opacity=".35"/>
  <path d="M15.5 27 H32.5 M15.5 33 H32.5" opacity=".35"/>
  <g class="dp-puerta"><path d="M18 12 H30 Q35 12 35 17 V37 Q35 42 30 42 H18 Q13 42 13 37 V17 Q13 12 18 12 Z M13 23 H35 M18 16 V19 M18 27 V33"/></g>
  <path class="dp-hoja" d="M24 12 C24 7 28 4 33 4 C33 9 29 12 24 12 Z"/>
 </g></svg>
<p>Abriendo la refri y pensando qué cocinar…</p></div>"""

ESTILOS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@500;700&display=swap');
.dp-sello { display:flex; align-items:baseline; gap:.55rem; background:#0E9C98; color:#fff; border-radius:14px;
  padding:.55rem .9rem; margin:.35rem 0 .3rem; }
.dp-sello b { font-size:1.7rem; font-weight:800; letter-spacing:-.03em; }
.dp-sello span { font-size:.95rem; font-weight:700; }
.dp-ahorro { color:#0A7470; font-size:.86rem; font-weight:600; margin-bottom:.35rem; }
.dp-falta { background:#FCEBC4; border:1px solid #E9C46A; color:#6B4300; border-radius:12px; padding:.5rem .75rem;
  font-size:.9rem; margin:.35rem 0 .4rem; }
.dp-banner { display:flex; flex-wrap:wrap; gap:.8rem; margin:.4rem 0 1.2rem; }
.dp-banner div { flex:1; min-width:180px; background:#fff; border:1px solid #EADFD8; border-radius:16px; padding:.9rem 1.1rem; }
.dp-banner small { color:#7A6A61; font-size:.82rem; }
.dp-banner b { display:block; font-size:1.8rem; font-weight:800; letter-spacing:-.03em; color:#2A1F1A; }
.dp-banner .cero { background:#0E9C98; border-color:#0E9C98; }
.dp-banner .cero small, .dp-banner .cero b { color:#fff; }
.dp-usa li { margin:.1rem 0; }
.st-key-papel { position:relative; background:#FFFFFF; border-radius:3px; padding:2.2rem 1.6rem 1.3rem 1.8rem !important;
  background-image:repeating-linear-gradient(to bottom, transparent 0 39px, #E6EEF4 39px 40px); background-position:0 66px;
  transform:rotate(-2.2deg);
  margin:1.2rem .6rem .8rem; gap:0 !important; }
div:has(> .st-key-papel) { position:relative; filter:drop-shadow(0 2px 2px rgba(0,0,0,.08)) drop-shadow(0 12px 14px rgba(80,50,20,.16)); }
div:has(> .st-key-papel)::before { content:""; position:absolute; top:2px; left:50%; width:46px; height:46px; margin-left:-23px;
  border-radius:12px; background:url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2048%2048%22%3E%3Crect%20width%3D%2248%22%20height%3D%2248%22%20rx%3D%2212%22%20fill%3D%22%23FF7A1A%22/%3E%3Cpath%20d%3D%22M18%2012%20H30%20Q35%2012%2035%2017%20V37%20Q35%2042%2030%2042%20H18%20Q13%2042%2013%2037%20V17%20Q13%2012%2018%2012%20Z%20M13%2023%20H35%20M18%2016%20V19%20M18%2027%20V33%20M24%2012%20C24%207%2028%204%2033%204%20C33%209%2029%2012%2024%2012%20Z%22%20fill%3D%22none%22%20stroke%3D%22%23fff%22%20stroke-width%3D%223.2%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22/%3E%3C/svg%3E") center/100% no-repeat; transform:rotate(7deg);
  box-shadow:0 5px 10px rgba(0,0,0,.28), inset 0 -3px 0 rgba(0,0,0,.12); z-index:3; }
.papel-titulo { font-family:'Caveat', 'Segoe Print', cursive; font-weight:700; font-size:2.1rem; color:#E2571A; line-height:40px;
  margin:0 0 10px; transform:rotate(-1deg); }
.st-key-papel [data-testid="stVerticalBlock"], .st-key-papel [data-testid="stHorizontalBlock"] { gap:0 !important; }
.st-key-papel [data-testid="stElementContainer"] { margin:0 !important; }
.st-key-papel [data-testid="stCheckbox"] { height:40px; min-height:40px; display:flex; align-items:flex-end; padding-bottom:2px; }
.st-key-papel [data-testid="stCheckbox"], .st-key-papel [data-testid="stCheckbox"] * { overflow:visible !important; text-overflow:clip !important; white-space:nowrap; }
.st-key-papel [data-testid="stCheckbox"] label p { font-family:'Caveat', 'Segoe Print', cursive; font-weight:500; font-size:1.55rem;
  color:#23396B; line-height:1; }
.st-key-papel [data-testid="stCheckbox"] label:has(input:checked) p { color:#0E9C98; font-weight:700; }
.st-key-papel [data-testid="stColumn"]:nth-child(1) [data-testid="stElementContainer"]:nth-child(odd) { transform:translateX(2px) rotate(-1.4deg); }
.st-key-papel [data-testid="stColumn"]:nth-child(1) [data-testid="stElementContainer"]:nth-child(even) { transform:translateX(-3px) rotate(.8deg); }
.st-key-papel [data-testid="stColumn"]:nth-child(2) [data-testid="stElementContainer"]:nth-child(3n) { transform:translateX(5px) rotate(1.5deg); }
.st-key-papel [data-testid="stColumn"]:nth-child(2) [data-testid="stElementContainer"]:nth-child(3n+1) { transform:translateX(-2px) rotate(-.9deg); }
.st-key-papel [data-testid="stColumn"]:nth-child(3) [data-testid="stElementContainer"]:nth-child(odd) { transform:translateX(-4px) rotate(1.1deg); }
.st-key-papel [data-testid="stColumn"]:nth-child(3) [data-testid="stElementContainer"]:nth-child(even) { transform:translateX(3px) rotate(-1.6deg); }
.st-key-papel [data-testid="stColumn"]:nth-child(4) [data-testid="stElementContainer"]:nth-child(3n+2) { transform:translateX(6px) rotate(-1.2deg); }
.st-key-papel [data-testid="stColumn"]:nth-child(4) [data-testid="stElementContainer"]:nth-child(3n) { transform:translateX(-3px) rotate(1.3deg); }
.st-key-papel [data-testid="stTextInput"] label p { font-family:'Caveat', cursive; font-weight:700; font-size:1.6rem; color:#E2571A; }
.st-key-papel [data-testid="stTextInput"] input { font-family:'Caveat', cursive; font-size:1.5rem; color:#23396B;
  background:transparent; border:none; border-bottom:2px dashed #D5E2EC; border-radius:0; }
.st-key-papel [data-testid="stTextInput"] [data-baseweb="input"],
.st-key-papel [data-testid="stTextInput"] [data-baseweb="base-input"] { background:transparent !important; border:none !important; box-shadow:none !important; }
.st-key-papel [data-testid="stTextInput"] { margin-top:.4rem; }
/* Letra a mano solo en el título y en las notitas; el resto queda en letra normal */
.sz-titulo { font-family:'Caveat', 'Segoe Print', cursive !important; font-weight:700 !important; color:#E2571A !important;
  font-size:clamp(3rem, 6.5vw, 4.6rem) !important; letter-spacing:0 !important; transform:rotate(-1.5deg); display:inline-block; }
.sz-ceja { color:#0E9C98 !important; }
.st-key-notas [data-testid="stColumn"] { background:#fff; padding:1.3rem .9rem .8rem; border-radius:3px; position:relative;
  box-shadow:0 2px 4px rgba(0,0,0,.06), 0 10px 18px rgba(80,50,20,.14); margin:.8rem .2rem; }
.st-key-notas [data-testid="stColumn"]::before { content:""; position:absolute; top:-9px; left:50%; width:64px; height:20px;
  margin-left:-32px; background:rgba(14,156,152,.28); transform:rotate(-4deg); }
.st-key-notas [data-testid="stColumn"]:nth-child(1) { transform:rotate(-2.4deg); }
.st-key-notas [data-testid="stColumn"]:nth-child(2) { transform:rotate(1.6deg) translateY(6px); }
.st-key-notas [data-testid="stColumn"]:nth-child(3) { transform:rotate(-1deg) translateY(-3px); }
.st-key-notas [data-testid="stColumn"]:nth-child(4) { transform:rotate(2.2deg) translateY(4px); }
.st-key-notas label p { font-family:'Caveat', 'Segoe Print', cursive !important; color:#E2571A !important; font-weight:700;
  font-size:1.6rem !important; }
.st-key-notas div[data-baseweb="select"] > div, .st-key-notas [data-testid="stNumberInputContainer"] {
  background:transparent !important; border:none !important; border-bottom:2px dashed #D5E2EC !important; border-radius:0 !important;
  box-shadow:none !important; }
.st-key-notas input, .st-key-notas div[data-baseweb="select"] div { font-family:'Caveat', 'Segoe Print', cursive !important;
  color:#23396B !important; font-size:1.45rem !important; background:transparent !important; }
.st-key-notas [data-testid="stNumberInputContainer"] button { background:transparent !important; }
.st-key-notas [data-testid="stSelectbox"] [role="group"] { background:#FFE9D6 !important; border:none !important;
  border-radius:8px !important; box-shadow:none !important; }
.st-key-notas [data-testid="stSelectbox"] input[role="combobox"] { font-family:'Caveat', 'Segoe Print', cursive !important;
  font-size:1.45rem !important; color:#23396B !important; background:transparent !important; }
.st-key-notas [data-testid="stSelectbox"] button svg { color:#23396B; }
/* el menú que se despliega: mismo rosado, misma letra y tinta azul */
[data-testid="stSelectboxVirtualDropdown"], [data-testid="stSelectboxVirtualDropdown"] [role="listbox"] {
  background:#FFE9D6 !important; border-radius:10px !important; }
[data-testid="stSelectboxVirtualDropdown"] [role="option"], [data-testid="stSelectboxVirtualDropdown"] [role="option"] * {
  font-family:'Caveat', 'Segoe Print', cursive !important; font-size:1.45rem !important; color:#23396B !important; }
[data-testid="stSelectboxVirtualDropdown"] [role="option"] { background:transparent !important; }
[data-testid="stSelectboxVirtualDropdown"] [role="option"][data-hovered="true"],
[data-testid="stSelectboxVirtualDropdown"] [role="option"][data-focused="true"],
[data-testid="stSelectboxVirtualDropdown"] [role="option"][aria-selected="true"] { background:#FFD3B0 !important; }
/* ---------- Movimiento ---------- */
@keyframes dp-caer { 0% { opacity:0; transform:translateY(-90px) rotate(-9deg); }
  60% { opacity:1; transform:translateY(8px) rotate(-1deg); } 80% { transform:translateY(-3px) rotate(-2.6deg); }
  100% { transform:translateY(0) rotate(-2.2deg); } }
@keyframes dp-clac { 0%, 55% { transform:rotate(7deg) scale(0); } 75% { transform:rotate(7deg) scale(1.25); } 100% { transform:rotate(7deg) scale(1); } }
.st-key-papel { animation:dp-caer .9s cubic-bezier(.2,.8,.3,1.2) both; }
div:has(> .st-key-papel)::before { animation:dp-clac 1.1s ease-out both; }
@keyframes dp-salto { 0% { transform:translateY(0) scale(1); } 40% { transform:translateY(-7px) scale(1.12); } 100% { transform:translateY(0) scale(1); } }
@keyframes dp-trazo { from { background-size:0% 2.5px; } to { background-size:100% 2.5px; } }
.st-key-papel [data-testid="stCheckbox"] label:has(input:checked) p { display:inline-block; animation:dp-salto .35s ease-out;
  background:linear-gradient(#0E9C98, #0E9C98) left bottom / 100% 2.5px no-repeat; padding-bottom:5px;
  animation:dp-salto .3s ease-out, dp-trazo .16s ease-in .05s both; }
.dp-espera { display:flex; flex-direction:column; align-items:center; gap:.6rem; padding:2rem 0; }
.dp-espera p { font-family:'Caveat', cursive; font-size:1.6rem; color:#E2571A; margin:0; }
@keyframes dp-abrir { 0%, 15% { transform:scaleX(1); } 45%, 60% { transform:scaleX(-.25); } 90%, 100% { transform:scaleX(1); } }
@keyframes dp-hoja { 0%, 100% { transform:rotate(0); } 50% { transform:rotate(-14deg); } }
.dp-puerta { transform-origin:13px 27px; animation:dp-abrir 1.6s ease-in-out infinite; }
.dp-hoja { transform-origin:24px 12px; animation:dp-hoja 1.6s ease-in-out infinite; }
@keyframes dp-subir { from { opacity:0; transform:translateY(28px) scale(.97); } to { opacity:1; transform:none; } }
[class*="st-key-rc_"] { animation:dp-subir .5s ease-out both; }
[data-testid="stColumn"]:nth-child(2) [class*="st-key-rc_"] { animation-delay:.12s; }
[data-testid="stColumn"]:nth-child(3) [class*="st-key-rc_"] { animation-delay:.24s; }
@keyframes dp-sello { 0% { opacity:0; transform:scale(2.4) rotate(-14deg); } 70% { opacity:1; transform:scale(.94) rotate(1deg); }
  100% { transform:scale(1) rotate(-1.5deg); } }
.dp-sello { animation:dp-sello .45s cubic-bezier(.3,1.4,.5,1) .45s both; transform-origin:30% 50%; }
.dp-banner .cero { animation:dp-sello .5s cubic-bezier(.3,1.4,.5,1) .1s both; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation:none !important; } }
@media (max-width: 640px) {
  .st-key-papel { padding-left:1.2rem !important; padding-right:1rem !important; transform:rotate(-1.4deg); }
  .st-key-papel [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; flex-direction:row !important; }
  .st-key-papel [data-testid="stColumn"] { width:50% !important; flex:0 0 50% !important; min-width:0 !important; }
  .st-key-papel [data-testid="stCheckbox"] label p { font-size:1.4rem; }
}
</style>"""


# ---------------------------------------------------------------------------
# Detalle de una receta
# ---------------------------------------------------------------------------

@st.dialog("Receta", width="large")
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
        mostrar_foto(r)
        d.info_receta(r)
        st.markdown(sello_cero(r) if cero else sello_falta(r), unsafe_allow_html=True)
        if st.button("Ver receta", key=f"ver_{clave}", icon=":material/menu_book:", type="primary", width="stretch"):
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
                  categoria="" if s["tipo_in"] == "Cualquiera" else s["tipo_in"], permitir=False,
                  basicos=list(s.get("basicos") or []))
    esperar_turno()
    excluir = [r.nombre for r in s["cero"] + s["uno"]] if mas else []
    espera = st.empty()
    espera.markdown(ESPERA_HTML, unsafe_allow_html=True)
    try:
        cero, uno = c.buscar_con_lo_que_hay(
            cliente_gemini(), pedido["tiene"], pedido["personas"], pedido["tiempo"], pedido["dieta"],
            pedido["categoria"], pedido["permitir"], excluir=excluir, basicos=pedido["basicos"])
    finally:
        espera.empty()
    if mas:
        s["cero"], s["uno"] = s["cero"] + cero, s["uno"] + uno
    else:
        s["cero"], s["uno"] = cero, uno
    s["pedido"] = pedido


def formulario():
    d.titulo("Cocina con lo que ya tienes", "¿Hay algo en la refri?",
             "Marca lo que tienes y te damos recetas para hoy <b>sin comprar nada</b>. Gasto: $0.")
    with st.container(border=True, key="tarjeta"):
        with st.container(key="papel"):                 # la lista de papel, como la de ir al súper
            st.markdown('<div class="papel-titulo">Lo que hay en la refri</div>', unsafe_allow_html=True)
            cols = st.columns(4, gap="small")
            for i, x in enumerate(c.COMUNES):
                cols[i % 4].checkbox(x, key=f"ing_{i}")
            st.text_input("¿Algo más?", key="extra_txt",
                          placeholder="escribe aquí: media col, 2 salchichas, mote, sobrante de arroz…")
        with st.expander("Básicos de cocina que tienes (sal, aceite, especias…)"):
            st.pills("Básicos", c.BASICOS, selection_mode="multi", default=c.BASICOS, key="basicos",
                     label_visibility="collapsed")
            st.caption("La sal y el agua siempre se asumen.")
        with st.container(key="notas"):
            a, b, f = st.columns(3, gap="medium")
            a.number_input("Personas", 1, 12, 2, key="personas_in")
            b.selectbox("Tiempo", [15, 30, 45, 60], index=1, key="tiempo_in", format_func=lambda m: f"{m} min o menos")
            f.selectbox("Tipo de plato", ["Cualquiera"] + n.CATEGORIAS, key="tipo_in")
        tiene = lo_que_tiene()
        st.caption(f"Tienes {len(tiene)} ingrediente{'s' if len(tiene) != 1 else ''} marcados"
                   + (f": {', '.join(tiene)}." if tiene else ". Elige al menos uno."))
        if st.button("¿Qué cocino sin gastar?", icon=":material/soup_kitchen:", type="primary", width="stretch",
                     disabled=not tiene, key="buscar"):
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
    ahorro_max = max([c.ahorro(r) for r in cero] or [0])
    st.markdown(
        f'<div class="dp-banner"><div class="cero"><small>Gasto de hoy</small><b>$0.00</b></div>'
        f'<div><small>Recetas sin comprar nada</small><b>{len(cero)}</b></div>'
        f'<div><small>Te ahorras hasta</small><b>${ahorro_max:.2f}</b></div></div>',
        unsafe_allow_html=True)
    if cero:
        st.markdown('<p class="sz-seccion">✅ Con lo que tienes: no compras nada</p>', unsafe_allow_html=True)
        cuadricula(cero, "c", True)
    else:
        st.info("Con lo que marcaste no salió ninguna receta sin comprar. Agrega uno o dos ingredientes más que "
                "tengas (un huevo, una papa, un poco de arroz) y vuelve a buscar.")
    if uno:
        st.write("")
        st.markdown('<p class="sz-seccion">🛒 Si quieres gastar un poquito: te falta solo una cosa</p>',
                    unsafe_allow_html=True)
        cuadricula(uno, "u", False)
    st.write("")
    if st.button("Ver otras recetas con lo mismo", icon=":material/refresh:", width="stretch", key="mas"):
        try:
            buscar(mas=True)
            st.rerun()
        except n.ErrorIA as err:
            st.error(str(err))


d.aplicar_estilos()
st.markdown(ESTILOS, unsafe_allow_html=True)
d.cabecera(ir)
formulario()
resultados()
st.divider()
st.caption("larefri. · hermana de canastas. y sazona. · IA: Google Gemini · Fotos: "
           "[Unsplash](https://unsplash.com/?utm_source=larefri&utm_medium=referral) / [Wikimedia Commons](https://commons.wikimedia.org) · Precios y valores nutricionales aproximados.")
