"""Script para importar y poblar recetario.json con recetas reales de TheMealDB mapeadas al vocabulario ecuatoriano.
Ejecuta: python importar_mealdb_a_recetario.py
"""

import json
import os
import requests
import casa as c
import mealdb

ARCHIVO_RECETARIO = "recetario.json"

CATEGORIAS_MEALDB = ["Beef", "Chicken", "Vegetarian", "Pasta", "Seafood", "Side", "Starter"]

TRADUCCION_CATEGORIA = {
    "Beef": "Plato fuerte",
    "Chicken": "Plato fuerte",
    "Seafood": "Plato fuerte",
    "Pasta": "Plato fuerte",
    "Vegetarian": "Plato fuerte",
    "Side": "Entradas",
    "Starter": "Entradas"
}

TRADUCCION_PLATOS = {
    "Chicken Handi": "Pollo al Curry Casero",
    "Dal Makhani": "Guiso de Lentejas Cremoso",
    "Shakshuka": "Huevos Rancheros con Tomate",
    "Spaghetti Bolognese": "Spaghetti con Carne Molida",
    "Egg Drop Soup": "Sopa de Huevo Tradicional",
    "French Onion Soup": "Sopa de Cebolla",
    "Potato Gratin": "Pastel de Papa y Queso",
    "Fish Pie": "Pastel de Pescado",
    "Tuna Melt": "Sánduche de Atún y Queso"
}

def cargar_recetario():
    if os.path.exists(ARCHIVO_RECETARIO):
        try:
            with open(ARCHIVO_RECETARIO, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"version": 1, "recetas": []}

def guardar_recetario(datos):
    with open(ARCHIVO_RECETARIO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def poblar_recetario():
    print("Iniciando descarga e importación de recetas para recetario.json...")
    datos = cargar_recetario()
    nombres_existentes = {r["receta"]["nombre"].lower() for r in datos.get("recetas", [])}
    
    agregadas = 0
    for cat in CATEGORIAS_MEALDB:
        try:
            r = requests.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?c={cat}", timeout=5)
            platos = (r.json() or {}).get("meals") or []
        except Exception as e:
            print(f"Error obteniendo categoría {cat}: {e}")
            continue
            
        for p in platos[:5]: # Obtener 5 recetas por categoría
            meal_id = p.get("idMeal")
            try:
                det_resp = requests.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}", timeout=5)
                m = ((det_resp.json() or {}).get("meals") or [{}])[0]
            except Exception:
                continue
                
            nombre_orig = m.get("strMeal", "")
            if not nombre_orig:
                continue
                
            nombre_es = TRADUCCION_PLATOS.get(nombre_orig, c.a_ecuador(nombre_orig))
            if nombre_es.lower() in nombres_existentes:
                continue
                
            ingredientes_convertidos = []
            for ing_nombre, ing_cant in mealdb.ingredientes(m):
                ing_ec = c.a_ecuador(ing_nombre)
                ingredientes_convertidos.append({
                    "nombre": ing_ec,
                    "cantidad": ing_cant or "1 unidad",
                    "presentacion": f"empaque de {ing_ec}",
                    "precio_presentacion_usd": 1.25,
                    "fraccion_usada": 0.5,
                    "basico_de_despensa": c.lo_tiene(ing_ec, c.BASICOS)
                })
                
            pasos_texto = m.get("strInstructions") or "Preparar los ingredientes y cocinar a fuego medio."
            pasos_lista = [p.strip() for p in pasos_texto.split("\r\n") if p.strip()][:6]
            if not pasos_lista:
                pasos_lista = ["Mezclar ingredientes y cocinar."]

            receta_dict = {
                "nombre": nombre_es,
                "cocina": m.get("strArea", "Internacional"),
                "descripcion": f"Exquisito plato preparado con {ingredientes_convertidos[0]['nombre'] if ingredientes_convertidos else 'ingredientes caseros'}.",
                "porciones": 4,
                "tiempo_minutos": 30,
                "dificultad": "Fácil",
                "etiquetas": ["Económica", "Casera"],
                "ingredientes": ingredientes_convertidos,
                "pasos": pasos_lista,
                "calorias_por_porcion": 450,
                "proteina_g_por_porcion": 22,
                "por_que_es_saludable": "Preparación casera y nutritiva.",
                "busqueda_foto": m.get("strMealThumb") or "",
                "icono": "otro",
                "plato_conocido": True,
                "alergenos": []
            }
            
            cat_app = TRADUCCION_CATEGORIA.get(cat, "Plato fuerte")
            datos["recetas"].append({"categoria": cat_app, "receta": receta_dict})
            nombres_existentes.add(nombre_es.lower())
            agregadas += 1
            print(f"  + Agregada: {nombre_es} ({cat_app})")
            
    guardar_recetario(datos)
    print(f"\n¡Completado! Se importaron {agregadas} recetas. recetario.json ahora contiene {len(datos['recetas'])} recetas.")

if __name__ == "__main__":
    poblar_recetario()
