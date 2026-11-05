"""Pruebas de la memoria de recetas en larefri: el recetario guardado responde solo, sin IA.
Corre:  python test_memoria.py"""

import casa as c
import memoria
import nucleo as n

# --- memoria básica (igual que en sazona) ---
assert len(memoria.todas()) == 10, "el recetario semilla tiene 10 recetas"

# --- recetas_de_la_memoria: solo las que salen con lo que hay ---
una = c.recetas_de_la_memoria(["Arroz", "Huevos"], 4, 30)
assert [r.nombre for r in una] == ["Arroz con huevo"], f"solo arroz con huevo sale con arroz y huevos: {[r.nombre for r in una]}"
assert all(i.de_tu_casa for i in una[0].ingredientes), "todo queda marcado como de tu casa"

ricas = c.recetas_de_la_memoria(["Arroz", "Huevos", "Tomate", "Cebolla larga", "Zanahoria", "Salsa china"], 4, 30)
nombres = [r.nombre for r in ricas]
assert nombres == ["Arroz frito con huevo", "Huevos pericos", "Arroz con huevo"], \
    f"primero la que más aprovecha: {nombres}"

# --- escala porciones ---
mitad = c.recetas_de_la_memoria(["Arroz", "Huevos"], 2, 30)
assert mitad[0].porciones == 2, "la receta guardada se ajusta al número de personas"

# --- respeta dieta, tiempo y excluir ---
assert c.recetas_de_la_memoria(["Arroz", "Huevos"], 4, 30, dieta="Vegana") == [], "vegana: el huevo no pasa"
assert len(c.recetas_de_la_memoria(["Arroz", "Huevos"], 4, 10)) == 1, "25 min cabe en 10 por la tolerancia de 15"
assert c.recetas_de_la_memoria(["Arroz", "Huevos"], 4, 5) == [], "25 minutos no caben en 5"
assert c.recetas_de_la_memoria(["Arroz", "Huevos"], 4, 30, excluir=["Arroz con huevo"]) == [], "excluir la quita"
sopas = c.recetas_de_la_memoria(["Lenteja", "Zanahoria", "Papa", "Cebolla", "Ajo"], 4, 60, categoria="Sopas")
assert [r.nombre for r in sopas] == ["Sopa de lentejas"], "el filtro de categoría funciona"

# --- hay_suficiente_en_memoria ---
assert c.hay_suficiente_en_memoria(["Arroz", "Huevos"], 4, 30, cantidad=1), "alcanza para 1"
assert not c.hay_suficiente_en_memoria(["Arroz", "Huevos"], 4, 30, cantidad=5), "no alcanza para 5"

# --- la búsqueda completa NO llama a la IA cuando el recetario cubre (cliente=None a propósito) ---
cero, uno = c.buscar_con_lo_que_hay(None, ["Arroz", "Huevos"], 4, 30, cantidad=1)
assert [r.nombre for r in cero] == ["Arroz con huevo"] and uno == [], "búsqueda gratis, sin IA"

print("TODAS LAS PRUEBAS DE MEMORIA DE LAREFRI OK")
