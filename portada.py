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
PRIMEROS = ['Tomate', 'Huevos', 'Arroz', 'Cebolla', 'Queso', 'Pollo', 'Papa', 'Atún', 'Zanahoria', 'Lenteja', 'Aguacate', 'Pan', 'Ajo', 'Limón', 'Fideo', 'Leche']

CSS = '''<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&display=swap');
.stApp {background:#fff0f6; color:#19234c;}
.block-container {max-width:1240px; padding:1.4rem 2rem 3rem !important;}
header[data-testid="stHeader"] {background:transparent;}
.rf-header {display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #e8a1c8; padding:.4rem 0 1rem; gap:1rem;}
.rf-brand {display:flex; align-items:center; gap:.7rem; font-size:2rem; font-weight:850; letter-spacing:-.06em; color:#141414;}
.rf-brand > span:first-child {display:grid;place-items:center;background:#ff701d;border-radius:12px;width:48px;height:48px;}
.rf-brand b {color:#ff563e;}
a.rf-brand, a.rf-brand:visited, a.rf-brand:hover {color:#141414;text-decoration:none;}
a.rf-brand {cursor:pointer;border-radius:12px;}
a.rf-brand:focus-visible {outline:1px solid #123fd0;outline-offset:5px;}
.rf-nav {background:#fff5ab; border:1px solid #edbd2e; padding:.5rem 1rem; border-radius:30px; font-weight:700; font-size:.9rem;}
.rf-hero {position:relative;text-align:center;padding:1.6rem 0 1.3rem;}
.rf-hero h1 {font-family:'Caveat',cursive;font-size:clamp(2.6rem,5.5vw,4.6rem);line-height:1.08;letter-spacing:-.025em;color:#073bcb;padding:0;margin:0;}
.rf-hero h1::after {content:'';display:block;width:32%;height:2px;margin:.45rem auto .8rem;background:#ff721b;border-radius:50%;transform:rotate(-2deg);transform-origin:left center;animation:rf-trazo 1.15s cubic-bezier(.55,.06,.35,1) .25s both;}
@keyframes rf-trazo {from {transform:rotate(-2deg) scaleX(0);} to {transform:rotate(-2deg) scaleX(1);}}
.rf-hero p {color:#59617b;font-size:1rem;margin:0;}
.rf-sticker {font-size:2.4rem;display:inline-block;vertical-align:middle;transform:rotate(-12deg);margin:0 .6rem;}
.st-key-tarjeta {background:#fff;border:1px solid #d95eac !important;border-radius:24px !important;padding:1.4rem 1.5rem !important;}
.rf-counter {display:inline-block;background:#fff176;color:#183280;border-radius:30px;padding:.5rem 1rem;font-weight:750;font-size:.9rem;margin-bottom:.25rem;}
.st-key-filtro_ingredientes input {font-size:1rem;}
.st-key-filtro_ingredientes [data-baseweb="input"] {border:1px solid #173aa8;border-radius:30px;background:#fff !important;}
.st-key-categoria [data-testid="stButtonGroup"] {flex-wrap:wrap;}
.st-key-cuadros {max-width:640px;margin-inline:auto;gap:6px !important;}
.st-key-cuadros [data-testid="stHorizontalBlock"] {gap:6px !important;flex-wrap:nowrap;}
.st-key-cuadros [data-testid="stColumn"] {min-width:0;}
[class*="st-key-alimento_"] button {position:relative;display:flex;align-items:center;justify-content:center;aspect-ratio:1 / 1;width:100%;max-width:none;margin-inline:auto;height:auto;min-height:0;border:1px solid #2143af !important;border-radius:8px !important;background:#fff !important;color:#171d33 !important;padding:.4rem .2rem !important;box-shadow:0 1px 0 #e7ebf8;transition:transform .15s;}
.stApp [class*="st-key-alimento_"] button p {font-size:.86rem !important;font-weight:750 !important;line-height:1.2;}
[class*="st-key-alimento_"] button > div {display:flex;flex-direction:column;gap:.2rem;}
[class*="st-key-alimento_"] button p::before {display:block;font-size:2.25rem;line-height:1.2;margin-bottom:.2rem;}
[class*="st-key-alimento_"] button:hover {transform:translateY(-3px);background:#fff5ed !important;}
[class*="st-key-alimento_"] button[kind="primary"] {background:#ffe4d9 !important;border-color:#ff6047 !important;color:#171d33 !important;}
[class*="st-key-alimento_"] button[kind="primary"]::after {content:'✓';position:absolute;top:6px;right:6px;width:23px;height:23px;background:#ff6047;border-radius:50%;color:white;font-weight:bold;}
[class*="st-key-alimento_"] button:focus-visible {outline:1px solid #123bd1;outline-offset:3px;}
.st-key-notas {background:#fff9c4;border-radius:18px;padding:1rem !important;}
.st-key-notas [data-testid="stWidgetLabel"] p {font-size:.95rem;font-weight:700;color:#19234c;}
.st-key-notas [data-baseweb="select"] > div,
.st-key-notas [data-testid="stSelectbox"] .react-aria-ComboBox > div {background:#FFF176 !important;border-color:#E0B90D !important;border-radius:14px !important;}
.st-key-notas [data-testid="stNumberInputContainer"],
.st-key-notas [data-testid="stNumberInputContainer"] input {background:#FFF176 !important;border-color:#E0B90D !important;border-radius:14px !important;}
.st-key-chef {display:flex; justify-content:center;}
.st-key-chef [data-testid="stWidgetLabel"] p {font-size:1.1rem !important; font-weight:700; color:#19234c;}
.st-key-buscar button {background:#093ed7 !important;border:1px solid #082b9c !important;border-radius:40px;box-shadow:0 1px 0 #082b9c;min-height:62px;}
.stApp .st-key-buscar button p {font-size:2.1rem !important;font-weight:700;color:white !important;}
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
.st-key-cuadros [data-testid="stHorizontalBlock"] {flex-wrap:wrap !important;gap:3px !important;}
.st-key-cuadros [data-testid="stColumn"] {width:calc(33.333% - 2px) !important;flex:0 0 calc(33.333% - 2px) !important;min-width:0 !important;}
[class*="st-key-alimento_"] button {max-width:none;min-height:0;border-radius:8px !important;padding:.4rem .1rem !important;}
.stApp [class*="st-key-alimento_"] button p {font-size:.72rem !important;}
[class*="st-key-alimento_"] button p::before {font-size:1.8rem;}
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
/* Respuesta táctil: se comprime al tocar y recupera su tamaño al soltar. */
@media(hover:none), (pointer:coarse) {
  [class*="st-key-alimento_"] button {
    touch-action:manipulation;
    -webkit-tap-highlight-color:transparent;
    transition:transform .32s cubic-bezier(.34,1.8,.5,1), box-shadow .2s ease;
  }
  [class*="st-key-alimento_"] button:hover {transform:none;}
  [class*="st-key-alimento_"] button:active {
    transform:scale(.89);
    box-shadow:0 1px 0 #e7ebf8;
    transition:transform .09s ease-out;
  }
  .st-key-buscar button {
    touch-action:manipulation;
    transition:transform .32s cubic-bezier(.34,1.8,.5,1), box-shadow .2s ease;
  }
  .st-key-buscar button:not(:disabled):active {
    transform:scale(.95);
    box-shadow:0 1px 0 #082b9c;
    transition:transform .09s ease-out;
  }
}
@media(hover:hover) and (pointer:fine) {
  [class*="st-key-alimento_"] button:active {transform:scale(.94);}
}
@keyframes rf-flotar {0%,100% {transform:translateY(0) rotate(-4deg);}50% {transform:translateY(-10px) rotate(5deg);}}
@keyframes rf-colores {0%,100% {fill:#ff701d;}25% {fill:#0b45d9;}50% {fill:#b52cb3;}75% {fill:#078b80;}}
@keyframes rf-puerta {0%,15%,90%,100% {transform:scaleX(1);}45%,60% {transform:scaleX(.18);}}
@keyframes rf-hoja {0%,100% {transform:rotate(0);}50% {transform:rotate(-18deg);}}
/* Carga: solo el isotipo flotando y cambiando de color, sin tarjeta ni fondo. */
.dp-espera {position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;pointer-events:none;}
.rf-cargando {display:flex;align-items:center;justify-content:center;}
.rf-cargando > svg {animation:rf-flotar 1.8s ease-in-out infinite;overflow:visible;}
.dp-color {animation:rf-colores 5s linear infinite;}
.dp-puerta {transform-box:view-box;transform-origin:13px 27px;animation:rf-puerta 2.4s ease-in-out infinite;}
.dp-hoja {transform-box:view-box;transform-origin:24px 12px;animation:rf-hoja 1.8s ease-in-out infinite;}
@media(prefers-reduced-motion:reduce) {
  *,*::before,*::after {transition:none !important;animation:none !important;}
  [class*="st-key-alimento_"] button:active,
  .st-key-buscar button:not(:disabled):active {transform:none !important;}
}

/* Toda la página en imprenta (DM Sans), salvo el título y la frase de debajo del héroe. */
.stApp, .stApp :is(p,h1,h2,h3,h4,h5,h6,label,input,textarea,select,li,td,th,a,small,strong,b,summary),
.rf-brand, .rf-counter, .sz-nombre, .sz-chip, .sz-desc, .dp-falta {
  font-family:'DM Sans','Segoe UI',sans-serif !important;
}
.rf-hero h1, .rf-hero h1 *, .rf-hero p, .rf-hero p * {font-family:'Caveat','Segoe Print',cursive !important;}
.rf-hero p {font-size:1.65rem !important; color:#3c4566;}
.stApp button, .stApp button p, .rf-nav {font-family:'DM Sans','Segoe UI',sans-serif !important;}
.stApp button p {font-size:1.02rem !important;font-weight:600;}
.rf-nav {font-weight:700;font-size:1.05rem;}
.stApp :is(input,select,textarea) {font-size:1.02rem;}
.rf-nav,.rf-counter {font-size:1rem;}
.st-key-notas [data-testid="stWidgetLabel"] p {font-size:1rem;}
[class*="st-key-alimento_"] button p, [class*="st-key-alimento_"] button p * {
  font-family:'DM Sans','Segoe UI',sans-serif !important;
}
/* Categorías: centradas en la página, letra más fina, recuadros redondeados amarillos. */
.st-key-categoria {display:flex; justify-content:center; margin-left:auto !important; margin-right:auto !important;}
.st-key-categoria [data-testid="stButtonGroup"] {flex-wrap:wrap; justify-content:center;}
.st-key-categoria [role="radiogroup"] {justify-content:center !important;}
.st-key-categoria button {background:#fff59d !important;border:1px solid #e6c93c !important;box-shadow:0 1px 0 #eadf9a !important;padding:.38rem .95rem !important;border-radius:999px !important;}
.st-key-categoria button p {color:#253568 !important;font-weight:500 !important;font-size:1rem !important;}
.st-key-categoria button[kind="primary"] {background:#ffe93e !important;border-color:#d9b800 !important;}
.st-key-categoria button[kind="primary"] p {color:#073bcb !important;font-weight:600 !important;}
/* Ventanas desplegables (foto de la refri, básicos): con caja clara otra vez. */
.st-key-tarjeta [data-testid="stExpander"] {border:1px solid #d9e0f2 !important;background:#fff !important;border-radius:14px !important;box-shadow:none !important;padding:.25rem .9rem !important;}
.st-key-tarjeta [data-testid="stExpander"] summary {padding-left:.1rem !important;}
/* Botón de la cámara: cuadrado grande, centrado, puntas redondeadas. */
.st-key-foto_refri [data-testid="stFileUploader"] {display:flex; justify-content:center;}
.st-key-foto_refri [data-testid="stFileUploaderDropzone"] {
  width:230px; max-width:60vw; aspect-ratio:1/1; margin:0 auto;
  border-radius:32px !important; border:2px solid #ff701d !important; background:#fff !important;
  display:flex; align-items:center; justify-content:center; cursor:pointer;
}
.st-key-foto_refri [data-testid="stFileUploaderDropzone"] > * {display:none !important;}
.st-key-foto_refri [data-testid="stFileUploaderDropzone"]::after {content:"📷"; font-size:5.5rem; line-height:1;}
.rf-foto-pie {text-align:center !important; font-weight:700; color:#19234c; margin:.5rem 0 .3rem; font-size:1.6rem !important;}
/* Bordes finos también en selectores, categorías y recetas. */
.stApp button, .stApp [data-baseweb="select"] > div,
.stApp [data-baseweb="input"], .stApp [data-testid="stNumberInputContainer"],
.stApp [data-testid="stExpander"], [class*="st-key-rc_"] {border-width:1px !important;}
</style>'''


def estilos():
    st.markdown(CSS, unsafe_allow_html=True)
    icons = ''.join(f'.st-key-alimento_{i} button p::before {{content:"{ICONOS[x]}";}}' for i, x in enumerate(c.COMUNES))
    verde = c.COMUNES.index('Verde')
    icons += f'.st-key-alimento_{verde} button p::before {{filter:hue-rotate(65deg) saturate(1.6) brightness(.95);}}'   # mismo platano del Maduro, pero verde
    st.markdown('<style>'+icons+'</style>', unsafe_allow_html=True)


def cabecera(svg):
    entrada = " rf-entrada" if not st.session_state.get("_portada_vista") else ""
    st.session_state["_portada_vista"] = True
    st.markdown(f'<div class="rf-header{entrada}"><a class="rf-brand" href="./" target="_self" aria-label="LaRefri: volver al inicio"><span>{svg}</span><span>larefri<b>.</b></span></a></div>', unsafe_allow_html=True)


def hero():
    st.markdown('<div class="rf-hero"><h1><span class="rf-sticker" aria-hidden="true">🧀 🥑</span>Aquí se cocina con lo que hay.<span class="rf-sticker" aria-hidden="true">🍅 🥚</span></h1><p>Descubre qué cocinar <b>sin tener que gastar de más.</b></p></div>', unsafe_allow_html=True)


def alternar(indice):
    clave = f'ing_{indice}'
    st.session_state[clave] = not st.session_state.get(clave, False)


def ingredientes():
    consulta = ''  # La entrada principal añade ingredientes como etiquetas independientes.
    categoria = st.pills('Categorías', ['Todo', 'Verduras y frutas', 'Proteínas', 'Despensa', 'Lácteos'], default='Todo', key='categoria', label_visibility='collapsed')
    orden = PRIMEROS + [x for x in c.COMUNES if x not in PRIMEROS]
    visibles = [x for x in orden if (not categoria or categoria == 'Todo' or x in GRUPOS[categoria]) and n._clave(consulta) in n._clave(x)]
    if not visibles:
        st.info('No está en la lista rápida. Puedes añadirlo abajo, en «Otros ingredientes».')
    with st.container(key='cuadros'):
        for inicio in range(0, len(visibles), 4):
            cols = st.columns(4, gap='small')
            for col, x in zip(cols, visibles[inicio:inicio+4]):
                i = c.COMUNES.index(x)
                activo = st.session_state.get(f'ing_{i}', False)
                col.button(x, key=f'alimento_{i}', type='primary' if activo else 'secondary', width='stretch', on_click=alternar, args=(i,))
