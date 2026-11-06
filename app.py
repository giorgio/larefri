# LAREFRI — todos los cambios visuales reunidos en este archivo.
import types as _types

def _modulo_visual(nombre, codigo):
    modulo = _types.ModuleType(nombre)
    modulo.__file__ = __file__
    exec(compile(codigo, nombre + ".py", "exec"), modulo.__dict__)
    return modulo

campo = _modulo_visual('campo_integrado', '"""Campo "¿Algo más?": se escribe y la palabra se completa sola en el mismo campo."""\nfrom __future__ import annotations\nimport streamlit as st\nimport casa as c\nCSS = """\n.caja { display:flex; flex-wrap:wrap; align-items:center; gap:.55rem; padding:.65rem .8rem; min-height:3.2rem;\n  background:#fff; border:1px solid #2143af; border-radius:16px; font-family:"DM Sans",sans-serif; box-sizing:border-box; }\n.chip { display:inline-flex; align-items:center; gap:.5rem; padding:.35rem .45rem .35rem .75rem;\n  border:1px solid #ff7658; border-radius:8px; background:#ffe9df; color:#253568;\n  font-family:"DM Sans",sans-serif; font-size:1rem; line-height:1.4; max-width:100%; overflow-wrap:anywhere; box-sizing:border-box; }\n.chip button { all:unset; cursor:pointer; flex-shrink:0; display:grid; place-items:center; color:#9f351e; width:30px; height:30px; }\n"""\n_componente = None\ntry:\n    if hasattr(st, "components") and hasattr(st.components, "v2"):\n        _componente = st.components.v2.component("larefri_algo_mas", html="", css=CSS, js="")\nexcept Exception:\n    _componente = None\ndef algo_mas(sugerencias: list[str], placeholder: str, key: str = "algo_mas") -> list[str]:\n    previo = st.session_state.get(key + "_items", [])\n    if _componente is None:\n        texto = st.text_input("¿Algo más en tu cocina?", placeholder=placeholder, key=key+"_input")\n        if texto:\n            for p in c.separar_lista(texto):\n                if p not in previo:\n                    previo.append(p)\n            st.session_state[key + "_items"] = previo\n        return previo\n    try:\n        r = _componente(key=key, data={"sugerencias": sugerencias, "valor": previo, "placeholder": placeholder},\n                        default={"lista": previo}, on_lista_change=lambda: None)\n        items = list(getattr(r, "lista", None) or previo or [])\n        st.session_state[key + "_items"] = items\n        return items\n    except Exception:\n        return previo\n_final = None\ndef llego_al_final(n: int, key: str = "fin") -> bool:\n    return False\n')

portada = _modulo_visual("portada_integrada", '"""Portada pop de LaRefri."""\nimport html\nimport streamlit as st\nimport casa as c\nimport nucleo as n\nICONOS = dict(zip(c.COMUNES, [\'🍚\',\'🥚\',\'🥔\',\'🍌\',\'🍌\',\'🥔\',\'🍝\',\'🐟\',\'🍗\',\'🥩\',\'🫘\',\'🫘\',\'🌽\',\'🧀\',\'🥛\',\'🍅\',\'🫑\',\'🥕\',\'🧅\',\'🧄\',\'🍋\',\'🥑\',\'🍞\',\'🌾\',\'🍌\',\'🐟\',\'🌭\',\'🫛\']))\nGRUPOS = {\'Proteínas\': {\'Huevos\', \'Atún\', \'Pollo\', \'Carne molida\', \'Sardina\', \'Salchicha\'}, \'Despensa\': {\'Arroz\', \'Fideo\', \'Lenteja\', \'Fréjol\', \'Pan\', \'Avena\'}, \'Lácteos\': {\'Queso\', \'Leche\'}}\nGRUPOS[\'Verduras y frutas\'] = set(c.COMUNES) - set().union(*GRUPOS.values())\nPRIMEROS = [\'Tomate\', \'Huevos\', \'Arroz\', \'Cebolla\', \'Queso\', \'Pollo\', \'Papa\', \'Atún\', \'Zanahoria\', \'Lenteja\', \'Aguacate\', \'Pan\', \'Ajo\', \'Limón\', \'Fideo\', \'Leche\']\nCSS = """<style>.stApp {background:#fff0f6; color:#19234c;}</style>"""\ndef estilos(): st.markdown(CSS, unsafe_allow_html=True)\ndef cabecera(svg): st.markdown(f\'<div class="rf-header"><a class="rf-brand" href="./"><span>{svg}</span><span>larefri<b>.</b></span></a></div>\', unsafe_allow_html=True)\ndef hero(): st.markdown(\'<div class="rf-hero"><h1>Aquí se cocina con lo que hay.</h1><p>Descubre qué cocinar <b>sin tener que gastar de más.</b></p></div>\', unsafe_allow_html=True)\ndef alternar(i): st.session_state[f"ing_{i}"] = not st.session_state.get(f"ing_{i}", False)\ndef ingredientes():\n    categoria = st.pills(\'Categorías\', [\'Todo\', \'Verduras y frutas\', \'Proteínas\', \'Despensa\', \'Lácteos\'], default=\'Todo\', key=\'categoria\', label_visibility=\'collapsed\')\n    visibles = [x for x in PRIMEROS + [x for x in c.COMUNES if x not in PRIMEROS] if not categoria or categoria == \'Todo\' or x in GRUPOS.get(categoria, set())]\n    with st.container(key=\'cuadros\'):\n        for inicio in range(0, len(visibles), 4):\n            cols = st.columns(4, gap=\'small\')\n            for col, x in zip(cols, visibles[inicio:inicio+4]):\n                i = c.COMUNES.index(x)\n                activo = st.session_state.get(f\'ing_{i}\', False)\n                col.button(x, key=f\'alimento_{i}\', type=\'primary\' if activo else \'secondary\', width=\'stretch\', on_click=alternar, args=(i,))\n')

import html
import os
import re
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

def secreto(nombre):
    try:
        return st.secrets.get(nombre) or os.environ.get(nombre)
    except Exception:
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

def _buscar_foto(r):
    bf = getattr(r, "busqueda_foto", "") or r.nombre
    if isinstance(bf, str) and bf.startswith("url:"):
        partes = bf[4:].split("|")
        if partes[0]:
            return {"url": partes[0], "autor": partes[1] if len(partes) > 1 else "Recetario", "pagina": partes[2] if len(partes) > 2 else ""}
    if isinstance(bf, str) and bf.startswith("http"):
        return {"url": bf, "autor": "Recetario", "pagina": ""}

    try:
        f = fotos.buscar_foto(bf, secreto("PEXELS_API_KEY"), secreto("UNSPLASH_ACCESS_KEY"), verificar=None)
        if f and isinstance(f, dict) and f.get("url"):
            return f
    except Exception:
        pass

    clean_name = re.sub(r"[^a-zA-Z0-9 ]+", "", r.nombre).strip().replace(" ", "_")
    url_ia = f"https://pollinations.ai/p/delicious_appetizing_gourmet_food_photo_of_{clean_name}?width=500&height=500&nologo=true&seed=42"
    return {"url": url_ia, "fuente": "IA"}

def _imagen_ia(r):
    return _buscar_foto(r)

def _pintar_foto(r, f):
    if f and isinstance(f, dict) and f.get("url"):
        st.image(f["url"], use_container_width=True)
        if f.get("fuente") == "IA":
            st.markdown('<div class="sz-credito">Imagen creada con IA</div>', unsafe_allow_html=True)
        else:
            d.credito_foto(f)
    else:
        d.foto_vacia()

def mostrar_foto(r):
    f = _buscar_foto(r)
    _pintar_foto(r, f)

def poner_fotos():
    pass

def lo_que_tiene() -> list[str]:
    s = st.session_state
    extra = [y for x in (s.get("algo_mas_items") or []) for y in c.separar_lista(x)
             if "sobrante" not in n._clave(y)]
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

def tarjeta_receta(r, id_receta, sello_fn, con_compras=True):
    with st.container(key=f"rc_{id_receta}"):
        mostrar_foto(r)
        st.markdown(f'<div class="sz-nombre">{html.escape(r.nombre)}</div>', unsafe_allow_html=True)
        st.caption(f"{r.cocina} · {r.tiempo_minutos} min · {r.porciones} porciones")
        st.markdown(sello_fn(r), unsafe_allow_html=True)
        with st.expander("Ver receta completa"):
            st.markdown(f"**Ingredientes:**\n" + "\n".join(f"- {i.cantidad} {i.nombre}" for i in r.ingredientes))
            st.markdown(f"**Pasos:**\n" + "\n".join(f"{idx+1}. {p}" for idx, p in enumerate(r.pasos)))

def cuadricula(recetas, prefijo, es_cero=True):
    cols = st.columns(3, gap="medium")
    for idx, r in enumerate(recetas):
        col = cols[idx % 3]
        with col:
            tarjeta_receta(r, f"{prefijo}_{idx}", sello_cero if es_cero else sello_falta, con_compras=es_cero)

def buscar(mas=False):
    s = st.session_state
    tiene = lo_que_tiene()
    pedido = dict(tiene=tiene, personas=s["personas_in"], tiempo=s["tiempo_in"], dieta=s.get("dieta_in", "Todas"),
                  categoria="" if s["tipo_in"] == "Cualquiera" else s["tipo_in"], permitir=True,
                  basicos=list(s.get("basicos") or []), creativo=bool(s.get("creativo")))
    excluir = [r.nombre for r in s["cero"] + s["uno"]] if mas else []
    gratis = (not pedido["creativo"]
              and c.hay_suficiente_en_memoria(pedido["tiene"], pedido["personas"], pedido["tiempo"],
                                              pedido["dieta"], pedido["categoria"], excluir))
    espera = st.empty()
    try:
        cero, uno = c.buscar_con_lo_que_hay(
            cliente_gemini() if not gratis else None, pedido["tiene"], pedido["personas"], pedido["tiempo"], pedido["dieta"],
            pedido["categoria"], pedido["permitir"], excluir=excluir, basicos=pedido["basicos"],
            creativo=pedido["creativo"])
    finally:
        espera.empty()
    if mas:
        vistos = {r.nombre for r in s["cero"] + s["uno"]}
        s["cero"] = s["cero"] + [r for r in cero if r.nombre not in vistos]
        s["uno"] = s["uno"] + [r for r in uno if r.nombre not in vistos]
    else:
        s["cero"], s["uno"], s["sin_mas"], s["abierta"] = cero, uno, False, None
    s["pedido"] = pedido

def formulario():
    portada.hero()
    with st.container(key="tarjeta"):
        portada.ingredientes()
        campo.algo_mas(c.SUGERENCIAS, "Añade un ingrediente…")
        with st.container(key="notas"):
            a, b, f = st.columns(3, gap="medium")
            a.number_input("Personas", 1, 12, 2, key="personas_in")
            b.selectbox("Tiempo", [15, 30, 45, 60], index=1, key="tiempo_in", format_func=lambda m: f"{m} min o menos")
            f.selectbox("Tipo de plato", ["Cualquiera"] + n.CATEGORIAS, key="tipo_in")
        tiene = lo_que_tiene()
        col_normal, col_chef = st.columns(2, gap="medium")
        if col_normal.button("Vamos a cocinar!", type="primary", width="stretch", disabled=not tiene, key="buscar"):
            st.session_state["creativo"] = False
            try:
                buscar()
            except n.ErrorIA as err:
                st.error(str(err))
        if col_chef.button("Chef inteligente", width="stretch", disabled=not tiene, key="buscar_chef"):
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
    if cero:
        st.markdown('<p class="sz-seccion">✅ Con lo que tienes: no compras nada</p>', unsafe_allow_html=True)
        cuadricula(cero, "c", True)
    if uno:
        st.markdown('<p class="sz-seccion">🛒 Te falta solo un ingrediente</p>', unsafe_allow_html=True)
        cuadricula(uno, "u", False)
    
    # Cargar más recetas automáticamente o con el botón
    total = len(cero) + len(uno)
    if not s.get("sin_mas") and total < 100:
        st.write("")
        c1, c2, c3 = st.columns([1, 2, 1])
        if c2.button("Mostrar más recetas 🍲", key="btn_mas_recetas", width="stretch"):
            try:
                buscar(mas=True)
            except Exception:
                s["sin_mas"] = True
            st.rerun()

d.aplicar_estilos()
portada.estilos()
portada.cabecera(d.isotipo_svg("#fff", 30))
formulario()
resultados()
