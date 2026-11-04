"""Recetas REALES de TheMealDB (cada una con su foto) que se pueden hacer solo con lo que hay en casa.
Clave gratis de prueba "1" (uso educativo); con la de supporter se pone MEALDB_API_KEY en Railway."""

from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = "https://www.themealdb.com/api/json/v1/{clave}/"

# español -> nombres de ingredientes en TheMealDB (para filtrar)
INGLES = {
    "arroz": ["rice"], "huevo": ["egg"], "papa": ["potato"], "maduro": ["plantain"], "verde": [],
    "yuca": ["cassava"], "fideo": ["spaghetti", "pasta", "noodles"], "atun": ["tuna"], "pollo": ["chicken"],
    "carne molida": ["minced beef", "beef mince", "ground beef"], "carne": ["beef"], "lenteja": ["lentils"],
    "frejol": ["kidney beans", "black beans", "pinto beans", "red beans"], "choclo": ["sweetcorn", "corn"], "queso": ["cheese", "cheddar", "parmesan"],
    "leche": ["milk"], "tomate": ["tomato"], "pimiento": ["pepper"], "zanahoria": ["carrot"], "cebolla": ["onion"],
    "ajo": ["garlic"], "limon": ["lemon", "lime"], "aguacate": ["avocado"], "pan": ["bread"], "avena": ["oats"],
    "platano": ["banana"], "sardina": ["sardines"], "salchicha": ["sausage"], "arveja": ["peas"],
    "mantequilla": ["butter"], "harina": ["flour", "plain flour"], "cerdo": ["pork"], "pescado": ["fish"],
    "camaron": ["prawns", "shrimp"], "espinaca": ["spinach"], "brocoli": ["broccoli"], "col": ["cabbage"],
    "pepino": ["cucumber"], "mani": ["peanut"], "coco": ["coconut"], "yogur": ["yogurt"], "crema": ["cream"],
}
# lo que se asume en cualquier cocina
BASICOS_EN = ["salt", "pepper", "black pepper", "water", "oil", "olive oil", "vegetable oil", "sunflower oil",
              "sugar", "vinegar", "cumin", "oregano", "paprika", "bay leaf", "bay leaves", "cinnamon",
              "stock cube", "chicken stock", "vegetable stock", "garlic powder", "ice"]


def _clave() -> str:
    return os.environ.get("MEALDB_API_KEY") or "1"


def _get(ruta: str, **params):
    try:
        r = requests.get(BASE.format(clave=_clave()) + ruta, params=params, timeout=3)
        return (r.json() or {}).get("meals") or [] if r.status_code == 200 else []
    except (requests.RequestException, ValueError):
        return []


def _norm(t: str) -> str:
    t = (t or "").lower()
    for a, b in zip("áéíóúñ", "aeioun"):
        t = t.replace(a, b)
    return re.sub(r"s\b", "", t).strip()


def a_ingles(tiene: list[str]) -> list[str]:
    out = []
    for x in tiene:
        k = _norm(x)
        for es, en in INGLES.items():
            if es == k or k.startswith(es + " ") or es in k.split():
                out += en
                break
    return list(dict.fromkeys(out))


def ingredientes(m: dict) -> list[tuple[str, str]]:
    return [((m.get(f"strIngredient{i}") or "").strip(), (m.get(f"strMeasure{i}") or "").strip())
            for i in range(1, 21) if (m.get(f"strIngredient{i}") or "").strip()]


def se_puede(m: dict, tiene_en: list[str]) -> bool:
    """¿TODOS los ingredientes del plato están en casa (o son básicos)?"""
    ok = [_norm(x) for x in tiene_en]
    basicos = {_norm(x) for x in BASICOS_EN}
    for nombre, _ in ingredientes(m):
        k = _norm(nombre)
        if k in basicos:
            continue
        if not any(o == k or o in k.split() or (len(o) > 4 and o in k) for o in ok):
            return False
    return True


def recetas_posibles(tiene: list[str], maximo: int = 6) -> list[dict]:
    """Platos de TheMealDB que salen completos con lo que hay. Busca por los ingredientes principales."""
    tiene_en = a_ingles(tiene)
    if not tiene_en:
        return []
    principales = [x for x in tiene_en if x not in ("garlic", "onion", "salt", "lemon", "lime", "pepper")][:6]
    with ThreadPoolExecutor(6) as ex:
        listas = list(ex.map(lambda i: _get("filter.php", i=i.replace(" ", "_")), principales or tiene_en[:3]))
    ids = list(dict.fromkeys(m["idMeal"] for lista in listas for m in lista[:12] if m.get("idMeal")))[:30]
    with ThreadPoolExecutor(8) as ex:
        completos = [x[0] for x in ex.map(lambda i: _get("lookup.php", i=i), ids) if x]
    buenos = [m for m in completos if se_puede(m, tiene_en)]
    for b in buenos:
        b["_foto"], b["_fuente"], b["_pagina"] = b.get("strMealThumb"), "TheMealDB", "https://www.themealdb.com/"
    print(f"[mealdb] {tiene_en} -> {len(ids)} platos revisados, {len(buenos)} se pueden hacer", flush=True)
    otros = de_spoonacular(tiene_en) if len(buenos) < maximo else []
    if len(buenos) + len(otros) < maximo:
        otros += de_edamam(tiene_en)
    return (buenos + otros)[:maximo]


# --- Edamam: millones de recetas de webs de cocina (EDAMAM_APP_ID y EDAMAM_APP_KEY en Railway) ---
def de_edamam(tiene_en: list[str]) -> list[dict]:
    app_id, app_key = os.environ.get("EDAMAM_APP_ID"), os.environ.get("EDAMAM_APP_KEY")
    if not (app_id and app_key):
        return []
    principales = [x for x in tiene_en if x not in ("garlic", "onion", "lemon", "lime")][:3] or tiene_en[:2]
    try:
        r = requests.get("https://api.edamam.com/api/recipes/v2", timeout=6,
                         headers={"Edamam-Account-User": "larefri"},
                         params={"type": "public", "q": " ".join(principales), "app_id": app_id, "app_key": app_key})
        hits = (r.json() or {}).get("hits") or [] if r.status_code == 200 else []
        if r.status_code != 200:
            print(f"[edamam] respondió {r.status_code}: {r.text[:200]}", flush=True)
    except (requests.RequestException, ValueError) as e:
        print(f"[edamam] error: {e}", flush=True)
        return []
    out = []
    for h in hits[:20]:
        d = h.get("recipe") or {}
        m = {"strMeal": d.get("label"), "strArea": (d.get("cuisineType") or ["Internacional"])[0].title(),
             "strCategory": (d.get("dishType") or [""])[0],
             "strInstructions": "(sin pasos: escríbelos tú, cortos y fieles a estos ingredientes)",
             "_foto": ((d.get("images") or {}).get("REGULAR") or {}).get("url") or d.get("image"),
             "_fuente": "Edamam", "_pagina": d.get("url") or "https://www.edamam.com/"}
        for i, ing in enumerate((d.get("ingredients") or [])[:20], 1):
            m[f"strIngredient{i}"] = ing.get("food") or ""
            m[f"strMeasure{i}"] = f'{ing.get("quantity") or ""} {ing.get("measure") or ""}'.replace("<unit>", "").strip()
        if m["strMeal"] and m["_foto"] and se_puede(m, tiene_en):
            out.append(m)
    print(f"[edamam] {len(hits)} revisadas, {len(out)} se pueden hacer", flush=True)
    return out[:6]


# --- Spoonacular: búsqueda hecha para "recetas con estos ingredientes" (clave SPOONACULAR_API_KEY en Railway) ---
SPOON = "https://api.spoonacular.com/recipes/"


def de_spoonacular(tiene_en: list[str], numero: int = 12) -> list[dict]:
    clave = os.environ.get("SPOONACULAR_API_KEY")
    if not clave:
        return []
    try:
        r = requests.get(SPOON + "findByIngredients", timeout=5, params={
            "ingredients": ",".join(tiene_en), "number": numero, "ranking": 2, "ignorePantry": "true", "apiKey": clave})
        lista = r.json() if r.status_code == 200 else []
        ids = [str(x["id"]) for x in lista if x.get("missedIngredientCount", 1) == 0][:8]
        if not ids:
            print(f"[spoonacular] {r.status_code}: 0 recetas completas", flush=True)
            return []
        info = requests.get(SPOON + "informationBulk", timeout=6, params={"ids": ",".join(ids), "apiKey": clave})
        datos = info.json() if info.status_code == 200 else []
    except (requests.RequestException, ValueError) as e:
        print(f"[spoonacular] error: {e}", flush=True)
        return []
    out = []
    for d in datos:
        m = {"strMeal": d.get("title"), "strArea": (d.get("cuisines") or ["Internacional"])[0],
             "strCategory": (d.get("dishTypes") or [""])[0],
             "strInstructions": " ".join(p.get("step", "") for b in (d.get("analyzedInstructions") or [])
                                         for p in b.get("steps", [])) or (d.get("instructions") or ""),
             "_foto": d.get("image"), "_fuente": "Spoonacular",
             "_pagina": d.get("spoonacularSourceUrl") or d.get("sourceUrl") or "https://spoonacular.com/"}
        for i, ing in enumerate((d.get("extendedIngredients") or [])[:20], 1):
            m[f"strIngredient{i}"] = ing.get("name") or ""
            m[f"strMeasure{i}"] = f'{ing.get("amount", "")} {ing.get("unit", "")}'.strip()
        if m["strMeal"] and m["_foto"] and se_puede(m, tiene_en):
            out.append(m)
    print(f"[spoonacular] {len(ids)} revisadas, {len(out)} se pueden hacer", flush=True)
    return out


def texto_para_ia(m: dict) -> str:
    ings = "; ".join(f"{q} {n}".strip() for n, q in ingredientes(m))
    return (f"### {m.get('strMeal')} ({m.get('strArea')}, {m.get('strCategory')})\n"
            f"Ingredientes: {ings}\nPreparación: {(m.get('strInstructions') or '')[:1500]}")
