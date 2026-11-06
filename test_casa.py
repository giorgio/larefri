"""Pruebas de larefri.: recetas con lo que hay en casa, sin gastar nada.
Corre:  python test_casa.py"""

import casa as c
import nucleo as n

tiene = ["Arroz", "Huevos"]
sugeridas = c.SUGERENCIAS
assert "Mote" in sugeridas and "Arroz" in sugeridas, "sugerencias completas"

# --- separar_lista ---
assert c.separar_lista("arroz, 3 huevos y media cebolla") == ["arroz", "3 huevos", "media cebolla"]

# --- lo_tiene: reconoce variaciones y plurales ---
assert c.lo_tiene("1 libra de arroz blanco", ["Arroz"]), "reconoce el arroz"
assert c.lo_tiene("2 huevos frescos", ["Huevos"]), "reconoce los huevos"
assert c.lo_tiene("Sal al gusto", ["Arroz"]), "la sal siempre se asume"
assert not c.lo_tiene("Pechuga de pollo", ["Arroz", "Huevos"]), "el pollo no lo tiene"
assert not c.lo_tiene("Plátano maduro", ["Verde"]), "maduro != verde"

# --- es_basico ---
assert c.es_basico(n.Ingrediente(nombre="Sal", cantidad="1 g", presentacion="funda", precio_presentacion_usd=0.5, fraccion_usada=0.01, basico_de_despensa=True)), "la sal es básica"

# --- faltantes ---
class I(n.Ingrediente):
    def __init__(self, nombre, presentacion, precio, fraccion, basico=False):
        super().__init__(nombre=nombre, cantidad="1", presentacion=presentacion,
                         precio_presentacion_usd=precio, fraccion_usada=fraccion,
                         basico_de_despensa=basico)

class R(c.RecetaCasa):
    def __init__(self, nombre, ings):
        super().__init__(nombre=nombre, cocina="Ecuatoriana", descripcion="desc", porciones=2,
                         tiempo_minutos=20, dificultad="Fácil", etiquetas=[],
                         ingredientes=[c.IngredienteCasa(**i.dict(), de_tu_casa=False) for i in ings],
                         pasos=["paso"], calorias_por_porcion=300, proteina_g_por_porcion=15,
                         por_que_es_saludable="sano", busqueda_foto="foto", icono="arroz")

r_ok = R("Arroz con huevo", [I("Arroz", "funda de 2 kg", 3.2, 0.1), I("Huevos", "cubeta de 30", 4.1, 0.07),
                             I("Aceite", "botella de 1 litro", 2.8, 0.01, True)])
assert c.faltantes(r_ok, tiene) == [], "ningún faltante"

r_falta = R("Arroz con aguacate", [I("Arroz", "funda de 2 kg", 3.2, 0.1), I("Aguacate", "unidad", 0.6, 1)])
assert c.faltantes(r_falta, tiene) == ["Aguacate"], "falta el aguacate"

# --- buscar_con_lo_que_hay con respuesta falsa de la IA ---
def falso(*_a, **_k):
    return c.CatalogoCasa(recetas=[
        R("Arroz con huevo", [I("Arroz", "funda de 2 kg", 3.2, 0.1), I("Huevos", "cubeta de 30", 4.1, 0.07),
                              I("Aceite", "botella de 1 litro", 2.8, 0.01, True)]),
        R("Arroz con aguacate", [I("Arroz", "funda de 2 kg", 3.2, 0.1), I("Aguacate", "unidad", 0.6, 1)]),
    ]), "falso"

n.llamar_gemini = falso
cero, uno = c.buscar_con_lo_que_hay(None, tiene, 2, 30)
assert cero[0].nombre == "Arroz con huevo" and uno == []

print("TODAS LAS PRUEBAS DE LAREFRI OK")
