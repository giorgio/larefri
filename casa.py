"""Lógica de larefri. (sin interfaz): recetas con lo que ya tienes en casa, sin gastar nada.

Usa el núcleo de sazona. (Gemini, precios, alérgenos, dietas) y agrega:
  - el pedido a la IA: SOLO tus ingredientes + lo básico de despensa;
  - una revisión propia: si una receta trae algo que no tienes, se marca como "te falta" o se descarta.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

import nucleo as n

# Lo que se asume que hay en cualquier cocina (no cuenta como compra)
BASICOS = ["Sal", "Pimienta", "Aceite", "Agua", "Ajo en polvo", "Comino", "Orégano", "Achiote", "Azúcar",
           "Vinagre", "Paprika", "Laurel", "Canela", "Caldo en cubo"]
BASICOS_FIJOS = ["Sal", "Agua"]          # siempre se asumen

# Botones rápidos: lo que más suele haber en una casa en Ecuador
COMUNES = ["Arroz", "Huevos", "Papa", "Verde", "Maduro", "Yuca", "Fideo", "Atún", "Pollo", "Carne molida",
           "Lenteja", "Fréjol", "Choclo", "Queso", "Leche", "Tomate", "Pimiento", "Zanahoria", "Cebolla",
           "Ajo", "Limón", "Aguacate", "Pan", "Avena", "Plátano", "Sardina", "Salchicha", "Arveja"]

# Para el buscador "¿Algo más?": se completan solas al escribir (nombres como se dicen en Ecuador)
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

def _sin_variantes(lista):
    """Quita variantes de lo que ya está en la lista de papel ('Arroz integral', 'Sobrante de arroz'...)."""
    distintos = {"Tomate de árbol", "Leche de coco"}          # se llaman parecido pero son otra cosa
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
    de_tu_casa: bool = Field(description="True si el usuario lo tiene (está en su lista o es básico de despensa)")


class RecetaCasa(n.Receta):
    ingredientes: list[IngredienteCasa]


class CatalogoCasa(BaseModel):
    recetas: list[RecetaCasa]


PROMPT_CASA = """El usuario NO quiere gastar dinero hoy. Propón {n} recetas distintas que pueda cocinar
SOLO con lo que tiene en casa.

LO QUE TIENE EN CASA: {tiene}
BÁSICOS DE DESPENSA (puedes usarlos sin que cuenten como compra): {basicos}
- Personas (porciones): {personas}
- Tiempo máximo: {tiempo} minutos
{dieta}{categoria}
REGLAS
1. PROHIBIDO usar ingredientes que no estén en su lista ni en los básicos. {faltante}
2. SOLO PLATOS QUE EXISTEN DE VERDAD y que la gente reconoce por su nombre, de TODO EL MUNDO y SIN dar
   prioridad a la cocina ecuatoriana: varía países (asiática, italiana, mexicana, peruana, india, española,
   árabe, etc.). P. ej. arroz frito con huevo, tortilla española, shakshuka, pasta aglio e olio, huevos
   rancheros, dal de lenteja, sopa de fideo. PROHIBIDO inventar platos o nombres creativos o con adjetivos
   ("express", "saludable", "delicia", "bowl", "fusión"). No hace falta usar todo:
   elige solo los ingredientes que ese plato lleva. Si con lo que hay no sale un plato conocido, propón menos
   recetas (aunque sea una o dos) en vez de inventar.
3. Marca de_tu_casa = true en cada ingrediente que el usuario tiene o que es básico.
4. Cantidades realistas para {personas} personas. Si algo no alcanza (p. ej. 2 huevos para 4), ajusta la
   receta o las porciones en vez de inventar más.
5. Para cada ingrediente da también la presentación en que se vende en Ecuador y su precio estimado
   (solo para mostrarle cuánto está AHORRANDO al no comprar), y fraccion_usada.
6. Marca sal, pimienta, aceite y especias como basico_de_despensa.
7. Saludables: con verduras o legumbres si las hay, sin frituras profundas.
8. Pasos cortos (máximo 8), para alguien que cocina poco. Calorías y proteína aproximadas."""

SIN_FALTANTES = "Ningún ingrediente nuevo: la receta tiene que salir con lo que hay."
UN_FALTANTE = ("Excepción: hasta la MITAD de las recetas pueden tener UN solo ingrediente que no tiene, "
               "barato y fácil de conseguir; márcalo de_tu_casa = false.")


# ---------------------------------------------------------------------------
# Revisar qué ingredientes tiene de verdad el usuario
# ---------------------------------------------------------------------------

def _raiz(w: str) -> str:
    """'tomates', 'tomate' -> 'tomat'; 'huevos' -> 'huev' (plural y vocal final no importan)."""
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
    """'arroz, 3 huevos y media cebolla' -> ['arroz', '3 huevos', 'media cebolla']"""
    partes = re.split(r"[,\n;]+|\s+y\s+", texto or "")
    return [p.strip() for p in partes if p.strip()]


def lo_tiene(nombre_ingrediente: str, tiene: list[str]) -> bool:
    """¿El ingrediente de la receta está en lo que escribió el usuario (o en los básicos)?"""
    palabras = _palabras(nombre_ingrediente)
    if not palabras:
        return True
    for t in list(tiene) + BASICOS_FIJOS:
        pt = _palabras(t)
        if pt and (pt & palabras):
            return True
    return False


def es_basico(i) -> bool:
    """Solo cuenta como básico si DE VERDAD es sal, aceite, especia... (la IA a veces marca el tomate como básico)."""
    return i.basico_de_despensa and lo_tiene(i.nombre, BASICOS + ["Pimienta negra", "Especias", "Hierbas"])


def faltantes(r: RecetaCasa, tiene: list[str]) -> list[str]:
    return [i.nombre for i in r.ingredientes if not es_basico(i) and not lo_tiene(i.nombre, tiene)]


def revisar(r: RecetaCasa, tiene: list[str]) -> RecetaCasa:
    """No confiamos solo en la IA: marcamos nosotros qué tiene y qué no."""
    for i in r.ingredientes:
        i.basico_de_despensa = es_basico(i)
        i.de_tu_casa = i.basico_de_despensa or lo_tiene(i.nombre, tiene)
    return r


def costo_faltantes(r: RecetaCasa) -> float:
    """Lo que tendría que gastar (paquetes enteros de lo que le falta)."""
    import math
    return round(sum(max(1, math.ceil(round(i.fraccion_usada, 3) - 1e-9)) * i.precio_presentacion_usd
                     for i in r.ingredientes if not i.de_tu_casa), 2)


def ahorro(r: RecetaCasa) -> float:
    """Cuánto costaría comprar lo que usa de su casa (lo que se ahorra)."""
    return round(sum(n.costo_ingrediente(i) for i in r.ingredientes if i.de_tu_casa and not i.basico_de_despensa), 2)


def buscar_con_lo_que_hay(cliente, tiene: list[str], personas: int, tiempo: int, dieta: str = "Todas",
                          categoria: str = "", permitir_faltante: bool = False, excluir=(), cantidad=POR_BUSQUEDA,
                          basicos=None):
    """Devuelve (recetas_sin_gastar, recetas_con_un_faltante). 'basicos' = lo de despensa que sí tiene."""
    basicos = list(BASICOS if basicos is None else basicos)
    if not tiene:
        raise n.ErrorIA("Escribe o elige al menos un ingrediente que tengas en casa.")
    prompt = PROMPT_CASA.format(
        n=cantidad, tiene=", ".join(tiene), basicos=", ".join(sorted(set(basicos + BASICOS_FIJOS))), personas=personas, tiempo=tiempo,
        dieta=(f"- Dieta OBLIGATORIA: {n.DIETAS[dieta]}.\n") if n.DIETAS.get(dieta) else "",
        categoria=(f"- Tipo de plato: {categoria}.\n") if categoria else "",
        faltante=UN_FALTANTE if permitir_faltante else SIN_FALTANTES,
    )
    todo = list(tiene) + basicos
    cero = [] if categoria else recetas_del_recetario(cliente, tiene, personas, tiempo, dieta, basicos, excluir)
    uno = []
    excluir = list(excluir) + [r.nombre for r in cero]
    if len(cero) >= cantidad:
        return cero[:cantidad], uno
    prompt = prompt.replace(f"Propón {cantidad} recetas", f"Propón {cantidad - len(cero)} recetas")
    if excluir:
        prompt += "\nNo repitas estas recetas: " + ", ".join(excluir)
    try:
        cat, _ = n.llamar_gemini(cliente, prompt, CatalogoCasa, razonamiento="minimal")
    except n.ErrorIA:
        if cero:
            return cero, uno
        raise
    for r in cat.recetas:
        r = n.limpiar_receta(r)
        if not r.ingredientes or not r.pasos or not n.cumple_dieta(r, dieta) or not r.plato_conocido \
                or n.nombre_inventado(r.nombre):
            continue
        r = revisar(r, todo)
        falta = faltantes(r, todo)
        if not falta:
            cero.append(r)
        elif permitir_faltante and len(falta) == 1:
            uno.append(r)
    if not cero and not uno:
        raise n.ErrorIA("Con esos ingredientes no salió ninguna receta sin comprar nada. "
                        "Agrega uno o dos ingredientes más que tengas y vuelve a buscar.")
    return cero, sorted(uno, key=costo_faltantes)


PROMPT_MEALDB = """Estas son recetas REALES de un recetario (TheMealDB). Conviértelas al formato pedido, en español
de Ecuador. NO cambies el plato ni agregues ingredientes: usa solo los que trae cada una.
- nombre: el nombre conocido del plato en español (si no tiene traducción conocida, el original).
- busqueda_foto: EXACTAMENTE el nombre original en inglés que va después de ###.
- plato_conocido = true. Cantidades para {personas} personas, en números enteros cuando son unidades.
- Pasos cortos (máximo 8) para alguien que cocina poco. Estima tiempo, calorías y proteína.
- Para cada ingrediente: presentación en que se vende en Ecuador, precio estimado y fraccion_usada.
  Marca sal, pimienta, aceite, agua y especias como basico_de_despensa; de_tu_casa = true en todos.
LO QUE TIENE EN CASA: {tiene}

{recetas}"""


def recetas_del_recetario(cliente, tiene, personas, tiempo, dieta, basicos, excluir=()):
    """Platos reales de TheMealDB que salen con lo que hay, traducidos por la IA. [] si no hay o falla."""
    try:
        import mealdb
        platos = [m for m in mealdb.recetas_posibles(tiene) if m.get("strMeal") not in excluir]
        if not platos:
            return []
        prompt = PROMPT_MEALDB.format(personas=personas, tiene=", ".join(tiene),
                                      recetas="\n\n".join(mealdb.texto_para_ia(m) for m in platos))
        cat, _ = n.llamar_gemini(cliente, prompt, CatalogoCasa, razonamiento="minimal")
    except Exception as e:  # noqa: BLE001  (si el recetario falla, la IA propone como siempre)
        print(f"[mealdb] no se pudo usar: {e}", flush=True)
        return []
    todo = list(tiene) + list(basicos)
    out = []
    for r in cat.recetas:
        r = n.limpiar_receta(r)
        r.plato_conocido = True
        if not r.ingredientes or not r.pasos or not n.cumple_dieta(r, dieta) or r.tiempo_minutos > tiempo + 15:
            continue
        r = revisar(r, todo)
        if not faltantes(r, todo):
            out.append(r)
    print(f"[mealdb] {len(out)} recetas del recetario", flush=True)
    return out


SUGERENCIAS = _sin_variantes(TODOS)      # lo que se ofrece en "¿Algo más?" (sin repetir el arroz, el tomate...)
