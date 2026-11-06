"""Campo "¿Algo más?": se escribe y la palabra se completa sola en el mismo campo.
"""

from __future__ import annotations

import streamlit as st
import casa as c

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&display=swap');
.caja { display:flex; flex-wrap:wrap; align-items:center; gap:.55rem; padding:.65rem .8rem; min-height:3.2rem;
  background:#fff; border:1px solid #2143af; border-radius:16px; font-family:"DM Sans",sans-serif; box-sizing:border-box; }
.caja:focus-within { box-shadow:0 0 0 3px #2143af18; }
.chip { display:inline-flex; align-items:center; gap:.5rem; padding:.35rem .45rem .35rem .75rem;
  border:1px solid #ff7658; border-radius:8px; background:#ffe9df; color:#253568;
  font-family:"DM Sans",sans-serif; font-size:1rem; line-height:1.4; max-width:100%; overflow-wrap:anywhere;
  box-sizing:border-box; animation:entra .2s ease-out; }
.chip button { all:unset; cursor:pointer; flex-shrink:0; display:grid; place-items:center; color:#9f351e;
  font-size:.9rem; width:30px; height:30px; border-radius:6px; font-family:sans-serif; }
.chip button:hover {background:#ffd0bf;}
.chip button:focus-visible {outline:1px solid #2143af;outline-offset:1px;}
.escribe {position:relative; flex:1 1 12rem; min-width:0;}
.escribe input, .escribe .fantasma {font-family:"DM Sans",sans-serif;font-size:1rem;color:#23396b;
  padding:0;margin:0;border:none;outline:none;background:transparent;width:100%;letter-spacing:normal;line-height:2;}
.escribe .fantasma {position:absolute;inset:0;pointer-events:none;white-space:pre;color:transparent;overflow:hidden;}
.escribe .fantasma i {font-style:normal;color:#23396b;opacity:.35;}
.escribe input::placeholder {color:#74809a;font-family:"DM Sans",sans-serif;font-size:1.15rem;}
.aviso {width:100%;color:#a43b25;font-size:1rem;font-family:"DM Sans",sans-serif;}
.aviso:empty {display:none;}
@keyframes entra {from {transform:scale(.9);opacity:0;}to {transform:scale(1);opacity:1;}}
@media(pointer:coarse) {.chip button {width:36px;height:36px;}.chip button:active {background:#ffd0bf;}}
@media(prefers-reduced-motion:reduce) {.chip {animation:none;}}
"""

JS = r"""
export default function(component) {
  const { data, setStateValue, parentElement } = component;
  const norm = (t) => (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
  const sug = data.sugerencias || [];
  let root = parentElement.querySelector(".caja");
  if (!root) {
    root = document.createElement("div");
    root.className = "caja";
    root.innerHTML = '<div class="escribe"><div class="fantasma"></div><input type="text" autocomplete="off" spellcheck="false"></div><div class="aviso"></div>';
    parentElement.appendChild(root);
    root.__items = (data.valor || []).slice();
  }
  const input = root.querySelector("input");
  const fantasma = root.querySelector(".fantasma");
  const aviso = root.querySelector(".aviso");
  const escribe = root.querySelector(".escribe");
  input.placeholder = data.placeholder || "";
  input.setAttribute("aria-label", "Busca o añade ingredientes");

  const guardar = () => setStateValue("lista", root.__items.slice());
  const pintar = () => {
    root.querySelectorAll(".chip").forEach((c) => c.remove());
    root.__items.forEach((x, i) => {
      const c = document.createElement("span");
      c.className = "chip";
      c.textContent = x;
      const b = document.createElement("button");
      b.type = "button"; b.textContent = "✕"; b.setAttribute("aria-label", "Quitar " + x);
      b.onclick = () => { root.__items.splice(i, 1); pintar(); guardar(); input.focus(); };
      c.appendChild(b);
      root.insertBefore(c, escribe);
    });
  };
  const completar = (t) => {
    const k = norm(t);
    if (!k) return null;
    const ya = new Set(root.__items.map(norm));
    return sug.find((s) => norm(s).startsWith(k) && !ya.has(norm(s))) || null;
  };
  const mostrarFantasma = () => {
    const t = input.value;
    const s = completar(t);
    fantasma.innerHTML = "";
    if (s && t) {
      const a = document.createElement("span"); a.textContent = t;
      const b = document.createElement("i"); b.textContent = s.slice(t.length);
      fantasma.append(a, b);
    }
  };
  const agregar = (texto, usarSugerencia) => {
    let hubo = false;
    for (let parte of (texto || "").split(/[,;\n]+|\s+y\s+/i)) {
      parte = parte.trim().replace(/\s+/g, " ");
      if (!parte) continue;
      if (/sobrante|sobras?\b/i.test(norm(parte))) { aviso.textContent = "Escribe solo el ingrediente (por ejemplo: arroz)."; continue; }
      const s = usarSugerencia ? completar(parte) : null;
      const exacta = sug.find((x) => norm(x) === norm(parte));
      const final = s || exacta || (parte.charAt(0).toUpperCase() + parte.slice(1));
      if (root.__items.some((x) => norm(x) === norm(final))) continue;
      root.__items.push(final); hubo = true; aviso.textContent = "";
    }
    input.value = ""; mostrarFantasma();
    if (hubo) { pintar(); guardar(); }
  };

  input.oninput = () => {
    if (/\S\s$/.test(input.value)) {
      const t = norm(input.value);
      const sigue = sug.some((s) => norm(s).startsWith(t + " "));
      if (!sigue) { agregar(input.value.trim(), true); aviso.textContent = ""; mostrarFantasma(); return; }
    }
    if (/[,;]/.test(input.value) || /\s+y\s+$/i.test(input.value)) {
      const partes = input.value.split(/[,;]|\s+y\s+$/i);
      const resto = partes.pop();
      agregar(partes.join(","), true);
      input.value = resto.trimStart();
    }
    aviso.textContent = "";
    mostrarFantasma();
  };
  input.onkeydown = (e) => {
    if (e.key === "Enter" || e.key === "Tab" || (e.key === "ArrowRight" && input.selectionStart === input.value.length && completar(input.value))) {
      if (!input.value.trim()) return;
      e.preventDefault();
      agregar(input.value, true);
    } else if (e.key === "Backspace" && !input.value && root.__items.length) {
      root.__items.pop(); pintar(); guardar();
    }
  };
  input.onblur = () => { if (input.value.trim()) agregar(input.value, true); };
  root.onclick = (e) => { if (e.target === root) input.focus(); };
  pintar();
  mostrarFantasma();
}
"""

_componente = None
try:
    if hasattr(st, "components") and hasattr(st.components, "v2"):
        _componente = st.components.v2.component("larefri_algo_mas", html="", css=CSS, js=JS)
except Exception:
    _componente = None

def algo_mas(sugerencias: list[str], placeholder: str, key: str = "algo_mas") -> list[str]:
    previo = st.session_state.get(key + "_items", [])
    if _componente is None:
        texto = st.text_input("¿Algo más en tu cocina?", placeholder=placeholder, key=key+"_input")
        if texto:
            for p in c.separar_lista(texto):
                if p not in previo:
                    previo.append(p)
            st.session_state[key + "_items"] = previo
        return previo
    try:
        r = _componente(key=key, data={"sugerencias": sugerencias, "valor": previo, "placeholder": placeholder},
                        default={"lista": previo}, on_lista_change=lambda: None)
        items = list(getattr(r, "lista", None) or previo or [])
        st.session_state[key + "_items"] = items
        return items
    except Exception:
        return previo

_JS_FINAL = r"""
export default function(component) {
  const { setTriggerValue, parentElement, data } = component;
  let el = parentElement.querySelector(".fin");
  if (!el) { el = document.createElement("div"); el.className = "fin"; el.style.height = "1px"; parentElement.appendChild(el); }
  if (el.__obs) el.__obs.disconnect();
  if (!window.__escucha) { window.__escucha = true; window.__bajo = false;
    document.addEventListener("wheel", () => { window.__bajo = true; }, { passive: true, capture: true });
    document.addEventListener("touchmove", () => { window.__bajo = true; }, { passive: true, capture: true });
    document.addEventListener("keydown", (e) => { if (/Page|Arrow|End| /.test(e.key)) window.__bajo = true; }, true); }
  let avisado = false;
  el.__obs = new IntersectionObserver((e) => {
    if (e[0].isIntersecting && !avisado && !document.querySelector('[role="dialog"]') && window.__bajo) {
      avisado = true; setTriggerValue("cargar", data.n);
    }
  }, { rootMargin: "400px" });
  el.__obs.observe(el);
  return () => el.__obs && el.__obs.disconnect();
}
"""

_final = None
try:
    if hasattr(st, "components") and hasattr(st.components, "v2"):
        _final = st.components.v2.component("larefri_final", html="", js=_JS_FINAL)
except Exception:
    _final = None

def llego_al_final(n: int, key: str = "fin") -> bool:
    if _final is None:
        return False
    try:
        r = _final(key=key, data={"n": n}, on_cargar_change=lambda: None)
        return bool(getattr(r, "cargar", None))
    except Exception:
        return False
