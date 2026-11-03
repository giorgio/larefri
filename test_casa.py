"""Pruebas de larefri. sin internet (se simula a Gemini). Ejecutar: python tests/test_casa.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import casa as c  # noqa: E402
import nucleo as n  # noqa: E402


def I(nombre, pres, precio, frac, basico=False):
    return c.IngredienteCasa(nombre=nombre, cantidad="x", presentacion=pres, precio_presentacion_usd=precio,
                             fraccion_usada=frac, basico_de_despensa=basico, de_tu_casa=True)


def R(nombre, ings):
    return c.RecetaCasa(nombre=nombre, cocina="Ecuatoriana", descripcion="d", porciones=2, tiempo_minutos=20,
                        dificultad="Fácil", etiquetas=[], ingredientes=ings, pasos=["a"], calorias_por_porcion=1,
                        proteina_g_por_porcion=1, por_que_es_saludable="x", busqueda_foto="x", icono="otro")


# separar lo que escribe el usuario
assert c.separar_lista("arroz, 3 huevos y media cebolla\natún") == ["arroz", "3 huevos", "media cebolla", "atún"]

# reconocer ingredientes (plural, tildes, nombres largos)
tiene = ["arroz", "3 huevos", "tomates", "papas", "atún en lata"]
for si in ["Arroz blanco", "Huevo", "Tomate riñón", "Papa chola", "Atún", "Sal", "Agua"]:
    assert c.lo_tiene(si, tiene), si
for no in ["Aguacate", "Pollo", "Queso fresco"]:
    assert not c.lo_tiene(no, tiene), no

# la IA dice que todo es de casa, pero trae aguacate: la app lo detecta
r = c.revisar(R("x", [I("Arroz", "funda de 2 kg", 3.2, 0.1), I("Aguacate", "unidad", 0.6, 1)]), tiene)
assert c.faltantes(r, tiene) == ["Aguacate"]
assert c.costo_faltantes(r) == 0.6
assert c.ahorro(r) == 0.32

# búsqueda simulada: sin faltantes por defecto, la receta con aguacate se descarta
def falso(cliente, prompt, esquema, **k):
    assert "PROHIBIDO" in prompt and "arroz" in prompt
    return c.CatalogoCasa(recetas=[
        R("Arroz con huevo", [I("Arroz", "funda de 2 kg", 3.2, 0.1), I("Huevos", "cubeta de 30", 4.1, 0.07),
                              I("Aceite", "botella de 1 litro", 2.8, 0.01, True)]),
        R("Arroz con aguacate", [I("Arroz", "funda de 2 kg", 3.2, 0.1), I("Aguacate", "unidad", 0.6, 1)]),
    ]), "falso"


n.llamar_gemini = falso
cero, uno = c.buscar_con_lo_que_hay(None, tiene, 2, 30)
assert [x.nombre for x in cero] == ["Arroz con huevo"] and uno == []
cero, uno = c.buscar_con_lo_que_hay(None, tiene, 2, 30, permitir_faltante=True)
assert [x.nombre for x in uno] == ["Arroz con aguacate"]

# dieta vegana: la receta con huevo se descarta
try:
    c.buscar_con_lo_que_hay(None, tiene, 2, 30, dieta="Vegana")
    raise AssertionError("debía fallar: ninguna receta vegana sin comprar")
except n.ErrorIA:
    pass

print("TODAS LAS PRUEBAS DE LAREFRI OK")
