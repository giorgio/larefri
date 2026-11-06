"""Campo "¿Algo más?": se escribe y la palabra se completa sola en el mismo campo (sin menú desplegable).
Tab, Enter o → aceptan; cada ingrediente queda en su propio cuadrito con ✕. La coma o "y" separan."""

from __future__ import annotations

import streamlit as st

CSS = """
.caja { display:flex; flex-wrap:wrap; align-items:center; gap:.4rem; padding:.45rem .6rem; min-height:2.9rem;
  background:transparent; border:none; border-bottom:2px solid #9DB7D5; font-family:'Caveat', cursive; }
.chip { display:inline-flex; align-items:center; gap:.4rem; padding:.2rem .8rem; border:1px solid #FF7A1A;
  border-radius:999px; background:#FFF4EB; color:#EE6A12; font-family:"DM Sans", "Source Sans Pro", sans-serif;
  font-size:.95rem; line-height:1.4; animation: entra .25s ease-out; }
.chip button { all:unset; cursor:pointer; color:#EE6A12; font-size:.8rem; line-height:1; padding:0 .1rem; font-family:sans-serif; }
.chip button:hover { color:#C2410C; transform:scale(1.15); }
.escribe { position:relative; flex:1 1 9rem; min-width:9rem; }
.escribe input, .escribe .fantasma { font-family:'Caveat', cursive; font-size:1.45rem; color:#23396B;
  padding:0; margin:0; border:none; outline:none; background:transparent; width:100%; letter-spacing:normal; }
.escribe .fantasma { position:absolute; inset:0; pointer-events:none; white-space:pre; color:transparent; }
.escribe .fantasma i { font-style:normal; color:#23396B; opacity:.35; }
.escribe input::placeholder { color:#7C8FB0; opacity:.8; }
.aviso { width:100%; font-family:'Caveat', cursive; color:#E2552B; font-size:1.15rem; min-height:0; }
@keyframes entra { from { transform:scale(.6); opacity:0 } to { transform:scale(1); opacity:1 } }
@media (prefers-reduced-motion: reduce) { .chip { animation:none } }
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
    // espacio = como la coma, salvo que la palabra siga (p. ej. "carne " -> "Carne molida", "leche " -> "Leche de coco")
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

_componente = st.components.v2.component("larefri_algo_mas", html="", css=CSS, js=JS)


def algo_mas(sugerencias: list[str], placeholder: str, key: str = "algo_mas") -> list[str]:
    previo = st.session_state.get(key + "_items", [])
    r = _componente(key=key, data={"sugerencias": sugerencias, "valor": previo, "placeholder": placeholder},
                    default={"lista": previo}, on_lista_change=lambda: None)
    items = list(getattr(r, "lista", None) or previo or [])
    st.session_state[key + "_items"] = items
    return items


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
    // no cargar si hay una receta abierta (se cerraría) ni si la persona no ha bajado
    if (e[0].isIntersecting && !avisado && !document.querySelector('[role="dialog"]') && window.__bajo) {
      avisado = true; setTriggerValue("cargar", data.n);
    }
  }, { rootMargin: "400px" });
  el.__obs.observe(el);
  return () => el.__obs && el.__obs.disconnect();
}
"""

_final = st.components.v2.component("larefri_final", html="", js=_JS_FINAL)


def llego_al_final(n: int, key: str = "fin") -> bool:
    """True cuando la persona bajó hasta el final de las recetas (para cargar más sin botón)."""
    r = _final(key=key, data={"n": n}, on_cargar_change=lambda: None)
    return bool(getattr(r, "cargar", None))
