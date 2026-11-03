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
        raise n.ErrorIA("Falta la clave de la IA (GEMINI_API_KEY) en los Secrets de la app.")
    return genai.Client(api_key=clave)


def esperar_turno():
    falta = ESPERA_ENTRE_CONSULTAS - (time.time() - st.session_state["ultima_consulta"])
    if falta > 0:
        time.sleep(falta)
    st.session_state["ultima_consulta"] = time.time()


@st.cache_data(ttl=7 * 86400, show_spinner=False, max_entries=500)
def foto(consulta: str):
    return fotos.buscar_foto(consulta, secreto("PEXELS_API_KEY"))


def mostrar_foto(r):
    f = foto(r.busqueda_foto)
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


ESTILOS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap');
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
.st-key-papel { position:relative; background-color:#FFFDF4; border-radius:6px; padding:1.1rem 1.2rem 1.2rem 3.4rem !important;
  background-image:repeating-linear-gradient(to bottom, transparent 0 38px, #CBDDEB 38px 39px);
  background-position:0 54px; box-shadow:0 1px 0 #E9E2CF, 0 8px 18px rgba(80,50,20,.12); transform:rotate(-.4deg);
  border-top:10px solid #F1E9D2; gap:0 !important; }
.st-key-papel::before { content:""; position:absolute; top:0; bottom:0; left:2.4rem; width:2px; background:#F3A2A2; }
.st-key-papel::after { content:""; position:absolute; top:-10px; left:0; right:0; height:10px;
  background:radial-gradient(circle at 8px -2px, transparent 6px, #F1E9D2 6.5px) repeat-x; background-size:16px 10px; }
.papel-titulo { font-family:'Patrick Hand', 'Comic Sans MS', cursive; font-size:1.7rem; color:#C0392B; line-height:38px;
  margin:0 0 2px; }
.st-key-papel [data-testid="stVerticalBlock"], .st-key-papel [data-testid="stHorizontalBlock"] { gap:0 !important; }
.st-key-papel [data-testid="stElementContainer"] { margin:0 !important; }
.st-key-papel [data-testid="stCheckbox"] { height:39px; min-height:39px; display:flex; align-items:flex-end; padding-bottom:3px; }
.st-key-papel [data-testid="stCheckbox"] label p { font-family:'Patrick Hand', 'Comic Sans MS', cursive; font-size:1.3rem;
  color:#23396B; line-height:1; }
.st-key-papel [data-testid="stCheckbox"] label:has(input:checked) p { color:#0E9C98; }
.st-key-papel [data-testid="stTextInput"] label p { font-family:'Patrick Hand', cursive; font-size:1.3rem; color:#C0392B; }
.st-key-papel [data-testid="stTextInput"] input { font-family:'Patrick Hand', cursive; font-size:1.25rem; color:#23396B;
  background:transparent; border:none; border-bottom:2px dashed #CBDDEB; border-radius:0; }
.st-key-papel [data-testid="stTextInput"] [data-baseweb="input"],
.st-key-papel [data-testid="stTextInput"] [data-baseweb="base-input"] { background:transparent !important; border:none !important; box-shadow:none !important; }
.st-key-papel [data-testid="stTextInput"] { margin-top:.4rem; }
@media (max-width: 640px) {
  .st-key-papel { padding-left:2.6rem !important; }
  .st-key-papel::before { left:1.8rem; }
  .st-key-papel [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; flex-direction:row !important; }
  .st-key-papel [data-testid="stColumn"] { width:50% !important; flex:0 0 50% !important; min-width:0 !important; }
  .st-key-papel [data-testid="stCheckbox"] label p { font-size:1.15rem; }
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
    pedido = dict(tiene=tiene, personas=s["personas_in"], tiempo=s["tiempo_in"], dieta=s["dieta_in"],
                  categoria="" if s["tipo_in"] == "Cualquiera" else s["tipo_in"], permitir=s["falta_in"],
                  basicos=list(s.get("basicos") or []))
    esperar_turno()
    excluir = [r.nombre for r in s["cero"] + s["uno"]] if mas else []
    with st.spinner("Mirando qué se puede cocinar con lo que tienes…"):
        cero, uno = c.buscar_con_lo_que_hay(
            cliente_gemini(), pedido["tiene"], pedido["personas"], pedido["tiempo"], pedido["dieta"],
            pedido["categoria"], pedido["permitir"], excluir=excluir, basicos=pedido["basicos"])
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
        a, b, e, f = st.columns(4)
        a.number_input("Personas", 1, 12, 2, key="personas_in")
        b.selectbox("Tiempo", [15, 30, 45, 60], index=1, key="tiempo_in", format_func=lambda m: f"{m} min o menos")
        e.selectbox("Alimentación", list(n.DIETAS), key="dieta_in")
        f.selectbox("Tipo de plato", ["Cualquiera"] + n.CATEGORIAS, key="tipo_in")
        st.toggle("Mostrar también recetas a las que les falta 1 ingrediente barato", value=False, key="falta_in",
                  help="Apagado: solo recetas en las que no compras nada.")
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
           "[Wikimedia Commons](https://commons.wikimedia.org) / Pexels · Precios y valores nutricionales aproximados.")
