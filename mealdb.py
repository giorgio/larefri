"""Recetas REALES de TheMealDB y Spoonacular (cada una con su foto) que se pueden hacer solo con lo que hay en casa.
Clave gratis de prueba "1" en TheMealDB; clave SPOONACULAR_API_KEY en Railway/Streamlit.
"""

from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = "https://www.themealdb.com/api/json/v1/{clave}/"

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

BASICOS_EN = ["salt", "pepper", "black pepper", "water", "oil", "olive oil", "vegetable oil", "sunflower oil",
              "sugar", "vinegar", "cumin", "oregano", "paprika", "bay leaf", "bay leaves", "cinnamon",
              "stock cube", "chicken stock", "vegetable stock", "garlic powder", "ice"]

def _clave() -> str:
    return os.environ.get("MEALDB_API_KEY") or "1"

def _get(ruta: str, **params):
    try:
        r = requests.get(BASE.format(clave=_clave()) + ruta, params=params, timeout=1.5)
        return (r.json() or {}).get("meals") or [] if r.status_code == 200 else []
    except Exception:
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
    ok = [_norm(x) for x in tiene_en]
    basicos = {_norm(x) for x in BASICOS_EN}
    for nombre, _ in ingredientes(m):
        k = _norm(nombre)
        if k in basicos:
            continue
        if not any(o == k or o in k.split() or (len(o) > 4 and o in k) for o in ok):
            return False
    return True

def de_spoonacular(tiene_en: list[str], numero: int = 4) -> list[dict]:
    """Búsqueda directa en Spoonacular API cuando la variable SPOONACULAR_API_KEY está configurada."""
    clave = os.environ.get("SPOONACULAR_API_KEY")
    if not clave:
        return []
    try:
        r = requests.get("https://api.spoonacular.com/recipes/findByIngredients", timeout=2.5, params={
            "ingredients": ",".join(tiene_en), "number": numero, "ranking": 2, "ignorePantry": "true", "apiKey": clave})
        if r.status_code != 200:
            return []
        lista = r.json() or []
        ids = [str(x["id"]) for x in lista if isinstance(x, dict) and x.get("id")][:4]
        if not ids:
            return []
        info = requests.get("https://api.spoonacular.com/recipes/informationBulk", timeout=2.5, params={"ids": ",".join(ids), "apiKey": clave})
        datos = info.json() if info.status_code == 200 else []
        out = []
        for d in datos:
            m = {
                "strMeal": d.get("title"),
                "strArea": (d.get("cuisines") or ["Internacional"])[0] if d.get("cuisines") else "Internacional",
                "strCategory": (d.get("dishTypes") or ["Plato fuerte"])[0] if d.get("dishTypes") else "Plato fuerte",
                "strInstructions": " ".join(p.get("step", "") for b in (d.get("analyzedInstructions") or []) for p in b.get("steps", [])) or (d.get("instructions") or "Cocinar adecuadamente."),
                "_foto": d.get("image"),
                "_fuente": "Spoonacular",
                "_pagina": d.get("spoonacularSourceUrl") or d.get("sourceUrl") or "https://spoonacular.com/"
            }
            for i, ing in enumerate((d.get("extendedIngredients") or [])[:20], 1):
                m[f"strIngredient{i}"] = ing.get("name") or ""
                m[f"strMeasure{i}"] = f'{ing.get("amount", "")} {ing.get("unit", "")}'.strip()
            if m["strMeal"] and m["_foto"]:
                out.append(m)
        return out
    except Exception:
        return []

def de_edamam(tiene_en: list[str]) -> list[dict]:
    return []

def recetas_posibles(tiene: list[str], maximo: int = 4) -> list[dict]:
    tiene_en = a_ingles(tiene)
    if not tiene_en:
        return []
    buenos = []
    
    # 1. Probar TheMealDB
    principales = [x for x in tiene_en if x not in ("garlic", "onion", "salt", "lemon", "lime", "pepper")][:3]
    try:
        with ThreadPoolExecutor(3) as ex:
            listas = list(ex.map(lambda i: _get("filter.php", i=i.replace(" ", "_")), principales or tiene_en[:2]))
        ids = list(dict.fromkeys(m["idMeal"] for lista in listas for m in lista[:5] if m.get("idMeal")))[:6]
        if ids:
            with ThreadPoolExecutor(3) as ex:
                completos = [x[0] for x in ex.map(lambda i: _get("lookup.php", i=i), ids) if x]
            buenos = [m for m in completos if se_puede(m, tiene_en)]
            for b in buenos:
                b["_foto"], b["_fuente"], b["_pagina"] = b.get("strMealThumb"), "TheMealDB", "https://www.themealdb.com/"
    except Exception:
        pass

    # 2. Si SPOONACULAR_API_KEY existe, incluir también recetas de Spoonacular
    spoon_recetas = de_spoonacular(tiene_en, numero=4)
    buenos.extend(spoon_recetas)

    return buenos[:maximo]

def texto_para_ia(m: dict) -> str:
    ings = "; ".join(f"{q} {n}".strip() for n, q in ingredientes(m))
    return (f"### {m.get('strMeal')} ({m.get('strArea')}, {m.get('strCategory')})\n"
            f"Ingredientes: {ings}\nPreparación: {(m.get('strInstructions') or '')[:1000]}")
