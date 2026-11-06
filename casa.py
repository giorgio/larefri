"""Lógica de larefri. (sin interfaz): recetas con lo que ya tienes en casa, sin gastar nada.
"""

from __future__ import annotations

import re
from pydantic import BaseModel, Field

import nucleo as n

BASICOS = ["Sal", "Pimienta", "Aceite", "Agua", "Ajo en polvo", "Comino", "Orégano", "Achiote", "Azúcar",
           "Vinagre", "Paprika", "Laurel", "Canela", "Caldo en cubo", "Ajo", "Cebolla", "Cebolla paiteña",
           "Cebolla blanca", "Cebolla larga", "Culantro", "Perejil", "Pimiento", "Pimiento verde", "Pimiento rojo",
           "Tomate", "Tomate riñón"]
BASICOS_FIJOS = ["Sal", "Agua"]

COMUNES = ["Arroz", "Huevos", "Papa", "Verde", "Maduro", "Yuca", "Fideo", "Atún", "Pollo", "Carne molida",
           "Lenteja", "Fréjol", "Choclo", "Queso", "Leche", "Tomate", "Pimiento", "Zanahoria", "Cebolla",
           "Ajo", "Limón", "Aguacate", "Pan", "Avena", "Plátano", "Sardina", "Salchicha", "Arveja"]

TODOS = sorted(set(COMUNES + [
    "Mote", "Col", "Coliflor", "Brócoli", "Lechuga", "Pepino", "Rábano", "Remolacha", "Vainitas", "Zapallo",
    "Zucchini", "Berenjena", "Espinaca", "Acelga", "Apio", "Culantro", "Perejil", "Cebolla paiteña", "Cebolla blanca",
    "Cebolla larga", "Pimiento rojo", "Pimiento verde", "Ají", "Tomate de árbol", "Tomate riñón", "Papa chola",
    "Camote", "Melloco", "Habas", "Garbanzo", "Chocho", "Quinua", "Maní", "Canguil", "Harina", "Harina de maíz",
    "Maicena", "Fideo cabello de ángel", "Tallarín", "Spaghetti", "Macarrones", "Arroz integral", "Pan de molde",
    "Tortillas", "Galletas", "Plátano verde", "Guineo", "Manzana", "Pera", "Naranja", "Mandarina", "Piña", "Papaya",
    "Sandía", "Melón", "Mora", "Frutilla", "Maracuyá", "Naranjilla", "Coco", "Uvas", "Mango", "Durazno",
    "Pollo entero", "Pechuga de pollo", "Alas de pollo", "Muslos de pollo", "Carne de res", "Carne de cerdo",
    "Chuleta", "Costilla", "Hígado", "Chorizo", "Mortadela", "Jamón", "Tocino", "Pescado", "Tilapia", "Corvina",
    "Camarón", "Concha", "Calamar", "Atún en lata", "Sardina en lata", "Huevo", "Queso fresco", "Queso mozzarella",
    "Quesillo", "Yogur", "Crema de leche", "Mantequilla", "Margarina", "Leche en polvo", "Leche de coco",
    "Salsa de tomate", "Mayonesa", "Mostaza", "Salsa china", "Pasta de tomate", "Achiote", "Comino", "Orégano",
    "Panela", "Azúcar", "Miel", "Avena", "Granola", "Cacao", "Café", "Chocolate", "Pasas", "Nueces", "Almendras",
    "Tofu", "Soya", "Lenteja", "Fréjol rojo", "Fréjol negro", "Arveja tierna", "Choclo desgranado", "Sobrante de arroz",
    "Pollo sobrante", "Carne sobrante", "Pan duro", "Papas cocinadas",
]))

def _dict_obj(obj):
    return obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()

def _sin_variantes(lista):
    distintos = {"Tomate de árbol", "Leche de coco"}
    base = {_raiz(n._clave(x).split()[0]) for x in COMUNES}
    out = []
    for x in lista:
        k = n._clave(x)
        if x in COMUNES or x in distintos:
            out.append(x)
        elif "sobrante" in k or any(_raiz(w) in base for w in k.split()):
            continue
        else:
            out.append(x)
    return sorted(set(out))

POR_BUSQUEDA = 6

class IngredienteCasa(n.Ingrediente):
    de_tu_casa: bool = Field(description="True si el usuario lo tiene")

class RecetaCasa(n.Receta):
    ingredientes: list[IngredienteCasa]

class CatalogoCasa(BaseModel):
    recetas: list[RecetaCasa]

PROMPT_CASA = """El usuario NO quiere gastar dinero hoy. Propón {n} recetas distintas que pueda cocinar
SOLO con lo que tiene en casa, aplicando armonía de sabores de The Flavor Bible.

LO QUE TIENE EN CASA: {tiene}
BÁSICOS DE DESPENSA: {basicos}
- Personas: {personas}
- Tiempo máximo: {tiempo} minutos
{dieta}{categoria}
REGLAS
1. Aprovecha al máximo los ingredientes que tiene en casa. {faltante}
2. {modo}
   {uso}
3. Marca de_tu_casa = true en cada ingrediente que el usuario tiene o que es básico.
4. Cantidades realistas para {personas} personas."""

SIN_FALTANTES = "Usa solo los ingredientes que tiene o básicos de alacena."
UN_FALTANTE = "Hasta la MITAD de las recetas pueden tener UN solo ingrediente adicional barato."
USO_PARCIAL = "Elige recetas deliciosas que aprovechen sus ingredientes."
USO_TOTAL = "RECOMENDADO: intenta aprovechar el máximo de los ingredientes de la lista del usuario (hasta el 100%)."

MODO_CONOCIDOS = "SOLO PLATOS QUE EXISTEN DE VERDAD y que la gente reconoce por su nombre."
MODO_CREATIVO = "MODO CREATIVO: INVENTA platos ORIGINALES y NUEVOS combinando los ingredientes de forma apetitosa. Dale a cada plato un NOMBRE PROPIO corto y creativo."

def _raiz(w: str) -> str:
    w = n._clave(w)
    if len(w) > 4 and w.endswith("es"):
        w = w[:-2]
    elif len(w) > 3 and w.endswith("s"):
        w = w[:-1]
    if len(w) > 3 and w[-1] in "aeo":
        w = w[:-1]
    return w

def _palabras(texto: str) -> set[str]:
    return {_raiz(w) for w in re.findall(r"[a-záéíóúñü]+", n._clave(texto)) if len(w) > 2} - {"del", "con", "las", "los", "para"}

def separar_lista(texto: str) -> list[str]:
    partes = re.split(r"[,\n;]+|\s+y\s+", texto or "", flags=re.IGNORECASE)
    return [p.strip() for p in partes if p.strip()]

def lo_tiene(nombre_ingrediente: str, tiene: list[str]) -> bool:
    palabras = _palabras(nombre_ingrediente)
    if not palabras:
        return True
    for t in list(tiene) + BASICOS + BASICOS_FIJOS:
        pt = _palabras(t)
        if pt and (pt & palabras) and not _distintos(palabras, pt):
            return True
    return False

_EXCLUYENTES = [{"madur", "verd"}, {"frejol", "lentej", "arvej", "garbanz", "habas"}]

def _distintos(a: set[str], b: set[str]) -> bool:
    for grupo in _EXCLUYENTES:
        ga, gb = a & grupo, b & grupo
        if ga and ga != gb:
            return True
    return False

def es_basico(i) -> bool:
    return i.basico_de_despensa or lo_tiene(i.nombre, BASICOS)

def faltantes(r: RecetaCasa, tiene: list[str]) -> list[str]:
    falta = [i.nombre for i in r.ingredientes if not es_basico(i) and not lo_tiene(i.nombre, tiene)]
    return falta

def faltan_en_nombre(r: RecetaCasa, tiene: list[str]) -> list[str]:
    return []

def revisar(r: RecetaCasa, tiene: list[str]) -> RecetaCasa:
    for i in r.ingredientes:
        i.basico_de_despensa = es_basico(i)
        i.de_tu_casa = i.basico_de_despensa or lo_tiene(i.nombre, tiene)
    return r

def usa_todos(r: RecetaCasa, tiene: list[str]) -> bool:
    if not tiene:
        return True
    aprovechables = [i for i in r.ingredientes if not es_basico(i)]
    usados = sum(1 for t in tiene if any(lo_tiene(i.nombre, [t]) for i in aprovechables))
    return usados >= 1

def costo_faltantes(r: RecetaCasa) -> float:
    import math
    return round(sum(max(1, math.ceil(round(i.fraccion_usada, 3) - 1e-9)) * i.precio_presentacion_usd
                     for i in r.ingredientes if not i.de_tu_casa), 2)

def ahorro(r: RecetaCasa) -> float:
    return round(sum(n.costo_ingrediente(i) for i in r.ingredientes if i.de_tu_casa and not i.basico_de_despensa), 2)

def recetas_de_la_memoria(tiene, personas, tiempo, dieta="Todas", categoria="", excluir=()):
    import memoria
    todo = list(tiene) + BASICOS
    out = []
    for r in memoria.buscar(categoria=categoria, dieta=dieta, tiempo=tiempo, excluir=excluir):
        d = _dict_obj(r)
        rc = RecetaCasa.model_validate({**d, "ingredientes": [{**i, "de_tu_casa": False} for i in d["ingredientes"]]}) if hasattr(RecetaCasa, "model_validate") else RecetaCasa.parse_obj({**d, "ingredientes": [{**i, "de_tu_casa": False} for i in d["ingredientes"]]})
        rc = n.ajustar_porciones(rc, personas)
        rc = revisar(rc, todo)
        if len(faltantes(rc, todo)) <= 1:
            out.append(rc)

    def cuantos_usa(rc):
        return sum(1 for t in tiene if any(lo_tiene(i.nombre, [t]) for i in rc.ingredientes if not es_basico(i)))

    out.sort(key=lambda rc: (len(faltantes(rc, todo)), -cuantos_usa(rc), n.costo_porcion(rc)))
    return out

def hay_suficiente_en_memoria(tiene, personas, tiempo, dieta="Todas", categoria="", excluir=(),
                               cantidad=POR_BUSQUEDA):
    return len(recetas_de_la_memoria(tiene, personas, tiempo, dieta, categoria, excluir)) >= cantidad

def buscar_con_lo_que_hay(cliente, tiene: list[str], personas: int, tiempo: int, dieta: str = "Todas",
                          categoria: str = "", permitir_faltante: bool = True, excluir=(), cantidad=POR_BUSQUEDA,
                          basicos=None, creativo: bool = False):
    basicos = list(BASICOS if basicos is None else basicos)
    todo = list(tiene) + basicos
    if not tiene:
        raise n.ErrorIA("Escribe o elige al menos un ingrediente que tengas en casa.")
    de_memoria = [] if creativo else recetas_de_la_memoria(tiene, personas, tiempo, dieta, categoria, excluir)
    
    cero = [r for r in de_memoria if not faltantes(r, todo)]
    uno = [r for r in de_memoria if len(faltantes(r, todo)) == 1]
    
    if len(cero) >= cantidad or (len(cero) + len(uno) >= cantidad):
        return cero[:cantidad] if cero else de_memoria[:cantidad], uno[:cantidad]
        
    prompt = PROMPT_CASA.format(
        n=cantidad + 4, tiene=", ".join(tiene), basicos=", ".join(sorted(set(basicos + BASICOS_FIJOS))), personas=personas, tiempo=tiempo,
        dieta=(f"- Dieta OBLIGATORIA: {n.DIETAS[dieta]}.\n") if n.DIETAS.get(dieta) else "",
        categoria=(f"- Tipo de plato: {categoria}.\n") if categoria else "",
        faltante=UN_FALTANTE if permitir_faltante else SIN_FALTANTES,
        modo=MODO_CREATIVO if creativo else MODO_CONOCIDOS,
        uso=USO_TOTAL if creativo else USO_PARCIAL,
    )
    from concurrent.futures import ThreadPoolExecutor
    if excluir:
        prompt += "\nNo repitas estas recetas: " + ", ".join(excluir)
    nombres_memoria = {r.nombre for r in de_memoria}
    
    cat = None
    recetario = []
    try:
        with ThreadPoolExecutor(2) as ex:
            f_rec = ex.submit(lambda: [] if (categoria or creativo) else
                              recetas_del_recetario(cliente, tiene, personas, tiempo, dieta, basicos, excluir))
            f_ia = ex.submit(n.llamar_gemini, cliente, prompt, CatalogoCasa, razonamiento="minimal",
                             modelos=n.MODELOS_CASCADA)
            recetario = [r for r in f_rec.result() if r.nombre not in nombres_memoria]
            try:
                cat, _ = f_ia.result()
            except Exception:
                cat = None
    except Exception:
        cat = None

    ya = {r.nombre for r in cero}
    if cat and getattr(cat, "recetas", None):
        cat.recetas = [r for r in cat.recetas if r.nombre not in ya]
        for r in cat.recetas:
            r = n.limpiar_receta(r)
            if not r.ingredientes or not r.pasos or not n.cumple_dieta(r, dieta):
                continue
            r = revisar(r, todo)
            falta = faltantes(r, todo)
            if not falta:
                cero.append(r)
            elif len(falta) <= 2:
                uno.append(r)

    if not cero and not uno:
        cero = de_memoria

    return cero[:cantidad], un_faltante_distinto(sorted(uno, key=costo_faltantes)) if uno else []

def un_faltante_distinto(uno, ya=()):
    vistos = {_raiz(n._clave(x).split()[0]) for x in ya if x}
    out = []
    for r in uno:
        k = {_raiz(n._clave(i.nombre).split()[0]) for i in r.ingredientes if not i.de_tu_casa and i.nombre.strip()}
        if k & vistos:
            continue
        vistos |= k
        out.append(r)
    return out

PROMPT_MEALDB = """Estas son recetas REALES de un recetario (TheMealDB). Conviértelas al formato pedido, en español de Ecuador.
- nombre: el nombre conocido del plato en español.
- busqueda_foto: EXACTAMENTE el nombre original en inglés que va después de ###.
- plato_conocido = true.
LO QUE TIENE EN CASA: {tiene}

{recetas}"""

def _mismos_ingredientes(r, original) -> bool:
    import mealdb
    inverso = {en: es for es, ens in mealdb.INGLES.items() for en in ens}
    suyos = [i.nombre for i in r.ingredientes]
    for nombre, _ in mealdb.ingredientes(original):
        k = mealdb._norm(nombre)
        if k in {mealdb._norm(b) for b in mealdb.BASICOS_EN}:
            continue
        es = next((v for en, v in inverso.items() if mealdb._norm(en) == k or mealdb._norm(en) in k.split()), None)
        if es and not lo_tiene(es, suyos):
            return False
    return True

def recetas_del_recetario(cliente, tiene, personas, tiempo, dieta, basicos, excluir=()):
    try:
        import mealdb
        platos = [m for m in mealdb.recetas_posibles(tiene, maximo=4) if m.get("strMeal") not in excluir]
        if not platos:
            return []
        prompt = PROMPT_MEALDB.format(personas=personas, tiene=", ".join(tiene),
                                      recetas="\n\n".join(mealdb.texto_para_ia(m) for m in platos))
        cat, _ = n.llamar_gemini(cliente, prompt, CatalogoCasa, modelos=n.MODELOS_CASCADA, razonamiento="minimal")
    except Exception:
        return []
    todo = list(tiene) + list(basicos)
    out = []
    nombres = [m.get("strMeal") for m in platos]
    for j, r in enumerate(cat.recetas):
        r = n.limpiar_receta(r)
        r.plato_conocido = True
        if r.busqueda_foto not in nombres:
            continue
        original = platos[nombres.index(r.busqueda_foto)]
        if not _mismos_ingredientes(r, original):
            continue
        r.busqueda_foto = "url:" + "|".join([original.get("_foto") or "", original.get("_fuente") or "",
                                              original.get("_pagina") or ""])
        if not r.ingredientes or not r.pasos or not n.cumple_dieta(r, dieta) or r.tiempo_minutos > tiempo + 15:
            continue
        r = revisar(r, todo)
        if not faltantes(r, todo):
            out.append(r)
    return out

SUGERENCIAS = _sin_variantes(TODOS)
