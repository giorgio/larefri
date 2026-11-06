"""Pruebas de la memoria de recetas en larefri: el recetario guardado responde solo, sin IA.
Corre:  python test_memoria.py"""

import casa as c
import memoria
import nucleo as n

# --- memoria básica (igual que en sazona) ---
assert len(memoria.todas()) >= 10, "el recetario semilla tiene recetas"

# --- recetas_de_la_memoria: solo las que salen con lo que hay ---
una = c.recetas_de_la_memoria(["Arroz", "Huevos"], 4, 30)
assert any(r.nombre == "Arroz con huevo" for r in una), "sale arroz con huevo"
assert all(i.de_tu_casa for i in una[0].ingredientes), "todo queda marcado como de tu casa"

ricas = c.recetas_de_la_memoria(["Arroz", "Huevos", "Tomate", "Cebolla larga", "Zanahoria", "Salsa china"], 4, 30)
nombres = [r.nombre for r in ricas]
assert "Arroz frito con huevo" in nombres and "Arroz con huevo" in nombres, "las recetas en memoria responden bien"

# --- escala porciones ---
mitad = c.recetas_de_la_memoria(["Arroz", "Huevos"], 2, 30)
assert mitad[0].porciones == 2, "la receta guardada se ajusta al número de personas"

# --- respeta dieta, tiempo y excluir ---
veganas = c.recetas_de_la_memoria(["Arroz", "Huevos"], 4, 30, dieta="Vegana")
assert all(n.cumple_dieta(r, "Vegana") for r in veganas), "dieta vegana respetada"

assert len(c.recetas_de_la_memoria(["Arroz", "Huevos"], 4, 10)) >= 1, "25 min cabe en 10 por la tolerancia de 15"
assert c.recetas_de_la_memoria(["Arroz", "Huevos"], 4, 5) == [], "25 minutos no caben en 5"

# --- hay_suficiente_en_memoria ---
assert c.hay_suficiente_en_memoria(["Arroz", "Huevos"], 4, 30, cantidad=1), "alcanza para 1"

print("TODAS LAS PRUEBAS DE MEMORIA DE LAREFRI OK")
