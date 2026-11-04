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

import campo
import casa as c
import diseno as d
import fotos
import portada
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


ESPERA_HTML = """<div class="dp-espera" role="status" aria-live="polite" aria-atomic="true"><div class="rf-cargando">
<svg width="92" height="92" viewBox="0 0 48 48" aria-hidden="true">
 <rect class="dp-color" width="48" height="48" rx="12" fill="#FF7A1A"/>
 <g fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <path d="M18 12 H30 Q35 12 35 17 V37 Q35 42 30 42 H18 Q13 42 13 37 V17 Q13 12 18 12 Z" opacity=".35"/>
  <path d="M15.5 27 H32.5 M15.5 33 H32.5" opacity=".35"/>
  <g class="dp-puerta"><path d="M18 12 H30 Q35 12 35 17 V37 Q35 42 30 42 H18 Q13 42 13 37 V17 Q13 12 18 12 Z M13 23 H35 M18 16 V19 M18 27 V33"/></g>
  <path class="dp-hoja" d="M24 12 C24 7 28 4 33 4 C33 9 29 12 24 12 Z"/>
 </g></svg>
<p>Buscando ideas para tu cocina…</p><small>Con lo que ya tienes en la refri.</small>
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
                  basicos=list(s.get("basicos") or []))
    excluir = [r.nombre for r in s["cero"] + s["uno"]] if mas else []
    espera = st.empty()
    espera.markdown(ESPERA_HTML, unsafe_allow_html=True)
    try:
        esperar_turno()
        cero, uno = c.buscar_con_lo_que_hay(
            cliente_gemini(), pedido["tiene"], pedido["personas"], pedido["tiempo"], pedido["dieta"],
            pedido["categoria"], pedido["permitir"], excluir=excluir, basicos=pedido["basicos"])
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
        tiene = lo_que_tiene()
        st.markdown(f'<span class="rf-counter">{len(tiene)} ingrediente{'s' if len(tiene) != 1 else ''} seleccionado{'s' if len(tiene) != 1 else ''}</span>', unsafe_allow_html=True)
        portada.ingredientes()
        with st.expander("Otros ingredientes · añade lo que no aparece"):
            campo.algo_mas(c.SUGERENCIAS, "Escribe: mote, col, chorizo…")
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
        if st.button("¡Dame ideas!", icon=":material/soup_kitchen:", type="primary", width="stretch",
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
