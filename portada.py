"""Portada pop de LaRefri: presentación y selección, sin llamadas de IA."""
import html
import streamlit as st
import casa as c
import nucleo as n

ICONOS = dict(zip(c.COMUNES, ['🍚','🥚','🥔','🍌','🍌','🥔','🍝','🐟','🍗','🥩','🫘','🫘','🌽','🧀','🥛','🍅','🫑','🥕','🧅','🧄','🍋','🥑','🍞','🌾','🍌','🐟','🌭','🫛']))
GRUPOS = {
    'Proteínas': {'Huevos', 'Atún', 'Pollo', 'Carne molida', 'Sardina', 'Salchicha'},
    'Despensa': {'Arroz', 'Fideo', 'Lenteja', 'Fréjol', 'Pan', 'Avena'},
    'Lácteos': {'Queso', 'Leche'},
}
GRUPOS['Verduras y frutas'] = set(c.COMUNES) - set().union(*GRUPOS.values())
PRIMEROS = ['Tomate', 'Huevos', 'Arroz', 'Cebolla', 'Queso', 'Pollo', 'Papa', 'Atún', 'Zanahoria', 'Lenteja', 'Aguacate', 'Pan']

CSS = '''<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@700&display=swap');
.stApp {background:#fff0f6; color:#19234c;}
.block-container {max-width:1240px; padding:1.4rem 2rem 3rem !important;}
header[data-testid="stHeader"] {background:transparent;}
.rf-header {display:flex; align-items:center; justify-content:space-between; border-bottom:2px solid #e8a1c8; padding:.4rem 0 1rem; gap:1rem;}
.rf-brand {display:flex; align-items:center; gap:.7rem; font-size:2rem; font-weight:850; letter-spacing:-.06em; color:#141414;}
.rf-brand > span:first-child {display:grid;place-items:center;background:#ff701d;border-radius:12px;width:48px;height:48px;}
.rf-brand b {color:#ff563e;}
.rf-nav {background:#fff5ab; border:1px solid #edbd2e; padding:.5rem 1rem; border-radius:30px; font-weight:700; font-size:.9rem;}
.rf-hero {position:relative;text-align:center;padding:1.6rem 0 1.3rem;}
.rf-hero h1 {font-family:'Caveat',cursive;font-size:clamp(2.6rem,5.5vw,4.6rem);line-height:1.08;letter-spacing:-.025em;color:#073bcb;padding:0;margin:0;}
.rf-hero h1::after {content:'';display:block;width:32%;height:6px;margin:.45rem auto .8rem;background:#ff721b;border-radius:50%;transform:rotate(-2deg);}
.rf-hero p {color:#59617b;font-size:1rem;margin:0;}
.rf-sticker {font-size:2.4rem;display:inline-block;vertical-align:middle;transform:rotate(-12deg);margin:0 .6rem;}
.st-key-tarjeta {background:#fff;border:1.5px solid #d95eac !important;border-radius:24px !important;padding:1.4rem 1.5rem !important;}
.rf-counter {display:inline-block;background:#fff176;color:#183280;border-radius:30px;padding:.5rem 1rem;font-weight:750;font-size:.9rem;margin-bottom:.25rem;}
.st-key-filtro_ingredientes input {font-size:1rem;}
.st-key-filtro_ingredientes [data-baseweb="input"] {border:2px solid #173aa8;border-radius:30px;background:#fff !important;}
.st-key-categoria [data-testid="stButtonGroup"] {flex-wrap:wrap;}
.st-key-cuadros [data-testid="stHorizontalBlock"] {gap:.75rem;flex-wrap:nowrap;}
.st-key-cuadros [data-testid="stColumn"] {min-width:0;}
[class*="st-key-alimento_"] button {position:relative;display:flex;align-items:center;justify-content:center;aspect-ratio:1 / 1;width:100%;height:auto;min-height:110px;border:2px solid #2143af !important;border-radius:17px;background:#fff !important;color:#171d33 !important;padding:.7rem .25rem !important;box-shadow:0 3px 0 #e7ebf8;transition:transform .15s;}
[class*="st-key-alimento_"] button p {font-size:.97rem !important;font-weight:750 !important;line-height:1.2;}
[class*="st-key-alimento_"] button > div {display:flex;flex-direction:column;gap:.2rem;}
[class*="st-key-alimento_"] button p::before {display:block;font-size:2.8rem;line-height:1.3;margin-bottom:.3rem;}
[class*="st-key-alimento_"] button:hover {transform:translateY(-3px);background:#fff5ed !important;}
[class*="st-key-alimento_"] button[kind="primary"] {background:#ffe4d9 !important;border-color:#ff6047 !important;color:#171d33 !important;}
[class*="st-key-alimento_"] button[kind="primary"]::after {content:'✓';position:absolute;top:6px;right:6px;width:23px;height:23px;background:#ff6047;border-radius:50%;color:white;font-weight:bold;}
[class*="st-key-alimento_"] button:focus-visible {outline:3px solid #123bd1;outline-offset:3px;}
.st-key-notas {background:#fff7b8;border-radius:18px;padding:1rem !important;}
.st-key-notas [data-testid="stWidgetLabel"] p {font-size:.9rem;font-weight:750;color:#19234c;}
.st-key-buscar button {background:#093ed7 !important;border:2px solid #082b9c !important;border-radius:40px;box-shadow:0 5px 0 #082b9c;min-height:62px;}
.st-key-buscar button p {font-family:'Caveat',cursive;font-size:2rem !important;color:white !important;}
.st-key-buscar button:disabled {opacity:.45;}
.rf-small {color:#67718a;font-size:.85rem;margin:.2rem 0;}
.dp-sello {display:flex;align-items:baseline;gap:.5rem;background:#087c70;color:white;border-radius:12px;padding:.5rem .8rem;}
.dp-sello b {font-size:1.5rem;}.dp-ahorro {color:#087466;font-size:.85rem;}
.dp-falta {background:#fff3bd;color:#614700;padding:.7rem;border-radius:12px;}
.dp-banner {display:flex;flex-wrap:wrap;gap:1rem;margin:1rem 0;}
.dp-banner > div {flex:1;background:#fff;border-radius:16px;padding:1rem;border:1px solid #e8d5e4;}
.dp-banner b {display:block;font-size:1.8rem;}.dp-banner .cero {background:#e0f5ed;color:#065747;}
.dp-espera {display:flex;justify-content:center;padding:1rem;}
@media(max-width:700px) {
.block-container {padding:1rem .8rem 2rem !important;}
.rf-brand {font-size:1.65rem;}.rf-brand > span:first-child {width:40px;height:40px;}
.rf-nav {font-size:.8rem;padding:.4rem .7rem;}
.rf-hero {padding:1.3rem 0;}.rf-hero h1 {font-size:2.9rem;}.rf-sticker {display:none;}
.rf-hero p {font-size:.9rem;}.st-key-tarjeta {padding:1rem .8rem !important;border-radius:20px !important;}
.st-key-cuadros [data-testid="stHorizontalBlock"] {flex-wrap:wrap !important;gap:.6rem !important;}
.st-key-cuadros [data-testid="stColumn"] {width:calc(33.333% - .4rem) !important;flex:0 0 calc(33.333% - .4rem) !important;min-width:0 !important;}
[class*="st-key-alimento_"] button {min-height:95px;border-radius:13px;padding:.4rem .1rem !important;}
[class*="st-key-alimento_"] button p {font-size:.77rem !important;}
[class*="st-key-alimento_"] button p::before {font-size:2.15rem;}
[class*="st-key-alimento_"] button[kind="primary"]::after {width:19px;height:19px;top:4px;right:4px;font-size:.75rem;}
.st-key-notas [data-testid="stHorizontalBlock"] {gap:.5rem;}
.rf-counter {font-size:.8rem;}
}
/* Animaciones cortas al entrar e interactuar; solo la carga se repite. */
@keyframes rf-bienvenida {
  0% {transform:translateY(-16px) rotate(-18deg) scale(.8);opacity:0;}
  55% {transform:translateY(0) rotate(9deg) scale(1.1);opacity:1;}
  78% {transform:rotate(-5deg) scale(.97);}
  100% {transform:none;opacity:1;}
}
.rf-entrada .rf-brand > span:first-child {animation:rf-bienvenida .85s ease-out both;}
@keyframes rf-saltito {
  0%,100% {transform:translateY(0) rotate(0);}
  35% {transform:translateY(-7px) rotate(-9deg) scale(1.08);}
  70% {transform:translateY(-2px) rotate(7deg);}
}
@media(hover:hover) and (pointer:fine) {
  [class*="st-key-alimento_"] button:hover p::before {animation:rf-saltito .5s ease-in-out;}
  .rf-brand > span:first-child:hover svg {animation:rf-saltito .6s ease-in-out;}
}
[class*="st-key-alimento_"] button:focus-visible p::before {animation:rf-saltito .5s ease-in-out;}
[class*="st-key-alimento_"] button:active {transform:scale(.94);}
@keyframes rf-flotar {0%,100% {transform:translateY(0) rotate(-4deg);}50% {transform:translateY(-10px) rotate(5deg);}}
@keyframes rf-colores {0%,100% {fill:#ff701d;}25% {fill:#0b45d9;}50% {fill:#b52cb3;}75% {fill:#078b80;}}
@keyframes rf-puerta {0%,15%,90%,100% {transform:scaleX(1);}45%,60% {transform:scaleX(.18);}}
@keyframes rf-hoja {0%,100% {transform:rotate(0);}50% {transform:rotate(-18deg);}}
.dp-espera {position:fixed;inset:0;z-index:99999;background:rgba(255,240,246,.78);backdrop-filter:blur(3px);display:flex;align-items:center;justify-content:center;padding:1rem;}
.rf-cargando {display:flex;flex-direction:column;align-items:center;gap:.7rem;background:#fff;border:2px solid #f1b6d8;border-radius:24px;padding:2rem 2.5rem;box-shadow:0 18px 60px #45256820;text-align:center;max-width:90vw;}
.rf-cargando > svg {animation:rf-flotar 1.8s ease-in-out infinite;overflow:visible;}
.dp-color {animation:rf-colores 5s linear infinite;}
.dp-puerta {transform-box:view-box;transform-origin:13px 27px;animation:rf-puerta 2.4s ease-in-out infinite;}
.dp-hoja {transform-box:view-box;transform-origin:24px 12px;animation:rf-hoja 1.8s ease-in-out infinite;}
.rf-cargando p {margin:0;font-size:1.1rem;font-weight:750;color:#123ba8;}
.rf-cargando small {color:#63708b;}
@media(prefers-reduced-motion:reduce) {
  *,*::before,*::after {transition:none !important;animation:none !important;}
}
</style>'''


def estilos():
    st.markdown(CSS, unsafe_allow_html=True)
    icons = ''.join(f'.st-key-alimento_{i} button p::before {{content:"{ICONOS[x]}";}}' for i, x in enumerate(c.COMUNES))
    st.markdown('<style>'+icons+'</style>', unsafe_allow_html=True)


def cabecera(svg):
    entrada = " rf-entrada" if not st.session_state.get("_portada_vista") else ""
    st.session_state["_portada_vista"] = True
    st.markdown(f'<div class="rf-header{entrada}"><div class="rf-brand"><span>{svg}</span><span>larefri<b>.</b></span></div><span class="rf-nav">Mi refri</span></div>', unsafe_allow_html=True)


def hero():
    st.markdown('<div class="rf-hero"><h1><span class="rf-sticker" aria-hidden="true">🧀 🥑</span>Aquí se cocina con lo que hay.<span class="rf-sticker" aria-hidden="true">🍅 🥚</span></h1><p>Elige tus ingredientes. Descubre qué cocinar <b>sin comprar nada.</b></p></div>', unsafe_allow_html=True)


def alternar(indice):
    clave = f'ing_{indice}'
    st.session_state[clave] = not st.session_state.get(clave, False)


def ingredientes():
    consulta = st.text_input('Busca un ingrediente', placeholder='Busca un ingrediente: tomate, arroz, queso…', key='filtro_ingredientes', label_visibility='collapsed')
    categoria = st.pills('Categorías', ['Todo', 'Verduras y frutas', 'Proteínas', 'Despensa', 'Lácteos'], default='Todo', key='categoria', label_visibility='collapsed')
    orden = PRIMEROS + [x for x in c.COMUNES if x not in PRIMEROS]
    visibles = [x for x in orden if (not categoria or categoria == 'Todo' or x in GRUPOS[categoria]) and n._clave(consulta) in n._clave(x)]
    ampliar = st.session_state.get('ver_todos', False)
    if not consulta and categoria in (None, 'Todo') and not ampliar:
        visibles = visibles[:12]
    if not visibles:
        st.info('No está en la lista rápida. Puedes añadirlo abajo, en «Otros ingredientes».')
    with st.container(key='cuadros'):
        for inicio in range(0, len(visibles), 6):
            cols = st.columns(6, gap='small')
            for col, x in zip(cols, visibles[inicio:inicio+6]):
                i = c.COMUNES.index(x)
                activo = st.session_state.get(f'ing_{i}', False)
                col.button(x, key=f'alimento_{i}', type='primary' if activo else 'secondary', width='stretch', on_click=alternar, args=(i,), help=('Quitar ' if activo else 'Añadir ') + x)

    if not consulta and categoria in (None, 'Todo'):
        st.toggle('Ver todos los ingredientes', key='ver_todos')
