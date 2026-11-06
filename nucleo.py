"""Lógica de sazona. (sin interfaz): recetas, costos, menú de la semana y sobrantes.

La IA propone recetas con sus ingredientes y el precio estimado de cada
presentación; la app calcula el costo de cada receta y por porción, arma la
lista de compras en paquetes enteros y detecta lo que sobra.
"""

from __future__ import annotations

import json
import os
import re
import math
import time
import unicodedata
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

# Nombres de modelos válidos de la API oficial de Google Gemini
MODELO_PRINCIPAL = os.environ.get("MODELO_GEMINI", "gemini-2.5-flash")
MODELO_RESPALDO = os.environ.get("MODELO_GEMINI_RESPALDO", "gemini-2.5-flash-lite")
MODELOS_CASCADA = tuple(dict.fromkeys(m.strip() for m in (MODELO_PRINCIPAL, MODELO_RESPALDO, "gemini-2.5-flash", "gemini-2.5-flash-lite") if m.strip()))

COCINAS = ["Ecuatoriana", "Italiana", "China", "Mexicana", "Peruana", "Mediterránea",
           "India", "Japonesa", "Tailandesa", "Árabe", "Colombiana", "Española"]
PAISES = {"Ecuador": "Ecuatoriana", "Italia": "Italiana", "China": "China", "México": "Mexicana",
          "Perú": "Peruana", "Colombia": "Colombiana", "España": "Española", "Mediterráneo": "Mediterránea",
          "India": "India", "Japón": "Japonesa", "Tailandia": "Tailandesa", "Medio Oriente": "Árabe"}
TIPOS = ["Alta en proteína", "Vegetariana", "Vegana", "Para niños", "Baja en grasa", "Sin gluten"]
ICONOS = ["pasta", "arroz", "sopa", "ensalada", "pollo", "carne", "pescado", "huevo", "menestra", "otro"]
RECETAS_POR_BUSQUEDA = 6
SOBRANTE_MINIMO = 0.25

class Ingrediente(BaseModel):
    nombre: str = Field(description="Ingrediente genérico, p. ej. 'Fideo spaghetti', 'Pechuga de pollo'")
    cantidad: str = Field(description="Lo que usa la receta, p. ej. '250 g', '2 unidades'")
    presentacion: str = Field(description="Cómo se compra en Ecuador, p. ej. 'funda de 500 g', 'cubeta de 30'")
    precio_presentacion_usd: float = Field(description="Precio estimado en USD de esa presentación completa")
    fraccion_usada: float = Field(description="Parte de la presentación que usa la receta, de 0 a 1")
    basico_de_despensa: bool = Field(description="True para sal, pimienta, aceite, ajo en polvo y similares")

class Receta(BaseModel):
    nombre: str
    cocina: str = Field(description="Una de las cocinas pedidas")
    descripcion: str = Field(description="Una frase apetitosa de máximo 15 palabras")
    porciones: int
    tiempo_minutos: int
    dificultad: str = Field(description="Fácil o Media")
    etiquetas: list[str] = Field(description="De los tipos pedidos u otros cortos: 'Alta en proteína', 'Rápida'...")
    ingredientes: list[Ingrediente]
    pasos: list[str]
    calorias_por_porcion: int
    proteina_g_por_porcion: int
    por_que_es_saludable: str
    busqueda_foto: str = Field(description="Nombre COMÚN del plato en INGLÉS para buscar su foto")
    icono: str = Field(description="Uno de: " + ", ".join(ICONOS))
    plato_conocido: bool = Field(default=True)
    alergenos: list[str] = Field(default_factory=list)

ECONOMICA = 1.00

def es_economica(por_porcion: float) -> bool:
    return por_porcion <= ECONOMICA

CATEGORIAS = ["Plato fuerte", "Sopas", "Ensaladas", "Desayunos", "Entradas", "Postres"]
DESCRIPCION_CATEGORIA = {
    "Plato fuerte": "plato principal de almuerzo o merienda, con proteína y acompañante",
    "Sopas": "sopas, caldos, cremas o locros",
    "Ensaladas": "ensaladas completas o de acompañante, frescas",
    "Desayunos": "desayunos o meriendas ligeras",
    "Entradas": "entradas, piqueos o bocaditos para compartir",
    "Postres": "postres sanos, con fruta y poco azúcar",
}

DIETAS = {
    "Todas": "",
    "Vegana": "VEGANA: nada de origen animal (sin carne, pescado, mariscos, huevo, lácteos ni miel)",
    "Vegetariana": "VEGETARIANA: sin carne, pollo, pescado ni mariscos; puede llevar lácteos, sin huevo",
    "Ovolactovegetariana": "OVOLACTOVEGETARIANA: sin carne, pollo, pescado ni mariscos; sí huevo y lácteos",
    "Pescetariana": "PESCETARIANA: sin carne roja ni pollo; sí pescado, mariscos, huevo y lácteos",
}

class Catalogo(BaseModel):
    recetas: list[Receta]

# INSTRUCCIÓN DE SISTEMA ENRIQUECIDA CON LA CIENCIA DE COMBINACIÓN DE SABORES
SISTEMA = (
    "Eres el cocinero experto de larefri., una app que ayuda a hogares de Ecuador a cocinar delicioso y sano con lo que ya tienen. "
    "Aplicas estrictamente los principios gastronómicos de 'La Enciclopedia de los Sabores' (Niki Segnit), 'The Flavor Bible' y 'Sal, Grasa, Ácido, Calor' "
    "para combinar alimentos con perfecta afinidad aromática y equilibrio de sabores (balanceando grasas, ácidos, umami y hierbas frescas). "
    "Adaptas todo con ingredientes reales de supermercados y mercados ecuatorianos, usando nombres locales "
    "(arroz blanco, refrito, fréjol, choclo, verde, maduro, guineo, tomate riñón, cebolla paiteña o colorada, culantro, aguacate, zapallo, arveja, maní, queso fresco)."
)

PROMPT_RECETAS = """Propón {n} recetas distintas aplicando maridaje de sabores.

PEDIDO
- Cocinas: {cocinas}
- Personas (porciones): {personas}
- Costo máximo por porción: {max_porcion:.2f} USD
- Tiempo máximo: {tiempo} minutos
- Tipo: {tipos}
{categoria}{dieta}- Ciudad: {ciudad}
- No repitas estas recetas: {excluir}
{extra}
REGLAS DE MARIDAJE Y COCINA
1. PLATOS QUE EXISTEN DE VERDAD o combinaciones con alta afinidad aromática (según The Flavor Bible y La Enciclopedia de los Sabores).
2. Saludables: con verduras o legumbres, sin frituras profundas.
3. Para cada ingrediente: presentación real ecuatoriana y su precio estimado completo.
4. PRECIOS HONESTOS en USD.
5. Pasos cortos (máximo 8)."""

EXTRA_SOBRANTES = """- PRIORIDAD: usa estos ingredientes que le sobraron al usuario esta semana: {sobrantes}."""

@dataclass
class Validacion:
    errores: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errores

def validar_busqueda(cocinas: list[str], personas: int, max_porcion: float, tiempo: int) -> Validacion:
    v = Validacion()
    if not cocinas:
        v.errores.append("Elige al menos un tipo de cocina.")
    if not personas or personas < 1:
        v.errores.append("Indica al menos 1 persona.")
    if max_porcion is None or max_porcion < 0.3:
        v.errores.append("Con menos de 0,30 USD por porción no se puede armar una receta completa.")
    if not tiempo or tiempo < 10:
        v.errores.append("Elige al menos 10 minutos de cocina.")
    return v

ALERGENOS = {
    "Gluten": r"\b(trigo|harina(?! de (maiz|arroz|yuca|platano|coco|almendra|garbanzo))|pan|panes|fideos?|spaghetti|espagueti|tallarin(es)?|macarron(es)?|lasana|pasta)\b",
    "Lácteos": r"\b(leche(?! de (coco|almendras?|soya|soja|avena|arroz))|quesos?|quesillo|yogur|yogurt|crema de leche|mantequilla)\b",
    "Huevo": r"\b(huevos?|claras?|yemas?|mayonesa)\b",
    "Maní": r"\b(mani|cacahuates?|mantequilla de mani)\b",
    "Frutos secos": r"\b(nuez|nueces|almendras?|avellanas?|pistachos?)\b",
    "Soya": r"\b(soya|soja|tofu|edamame)\b",
    "Pescado": r"\b(pescado|atun|sardinas?|tilapia|corvina|salmon)\b",
    "Mariscos": r"\b(camaron(es)?|langostinos?|conchas?|mejillon(es)?|calamar(es)?|pulpo)\b",
    "Ajonjolí": r"\b(ajonjoli|sesamo|tahini)\b",
}

def detectar_alergenos(r: Receta) -> list[str]:
    texto = " ".join(_clave(i.nombre) for i in r.ingredientes)
    encontrados = {a for a, patron in ALERGENOS.items() if re.search(patron, texto)}
    por_clave = {_clave(a): a for a in ALERGENOS}
    encontrados |= {por_clave[_clave(x)] for x in (r.alergenos or []) if _clave(x) in por_clave}
    return [a for a in ALERGENOS if a in encontrados]

NO_PERMITIDO = {"Vegana": {"Lácteos", "Huevo", "Pescado", "Mariscos"},
                "Vegetariana": {"Huevo", "Pescado", "Mariscos"},
                "Ovolactovegetariana": {"Pescado", "Mariscos"}}

def cumple_dieta(r: Receta, dieta: str) -> bool:
    return not (NO_PERMITIDO.get(dieta, set()) & set(r.alergenos or []))

LIBRA = 454
TAMANOS_REALES = [
    (r"\barroz\b", "g", [LIBRA, 1000, 2000, 5000], "funda"),
    (r"\b(fideos?|spaghetti|espagueti|tallarin(es)?|macarron(es)?|pasta corta|lasana)\b", "g", [200, 250, 400, 500, 1000], "funda"),
    (r"\b(lentejas?|frejol(es)?|frijol(es)?|garbanzos?|arveja seca|habas secas|chochos?)\b", "g", [LIBRA, 500, 1000], "funda"),
    (r"\b(azucar|harina|avena|maicena|quinua|morocho|canguil)\b", "g", [250, 400, LIBRA, 500, 1000, 2000], "funda"),
    (r"\b(leche(?! de coco)|yogur|yogurt)\b", "ml", [200, 500, 946, 1000, 2000], "envase"),
    (r"\baceite\b", "ml", [500, 900, 1000, 2000], "botella"),
    (r"\batun\b", "g", [140, 170, 354], "lata"),
    (r"\b(sardinas?)\b", "g", [155, 425], "lata"),
    (r"\b(queso|quesillo)\b", "g", [250, LIBRA, 500, 1000], "unidad"),
    (r"\b(mantequilla|margarina)\b", "g", [100, 250, 500], "barra"),
    (r"\b(pasta de tomate|salsa de tomate)\b", "g", [100, 200, 400], "envase"),
]

def _tamano(texto: str, unidad: str) -> float | None:
    t = _clave(texto).replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|kilo|g|gr|gramos|ml|cc|l|lt|litros?|lb|libras?)\b", t)
    if m:
        v, u = float(m.group(1)), m.group(2)
        if u in ("kg", "kilo", "l", "lt", "litro", "litros"):
            v *= 1000
        elif u in ("lb", "libra", "libras"):
            v *= LIBRA
        return v
    if re.search(r"\b(media libra)\b", t):
        return LIBRA / 2
    if re.search(r"\b(libra)\b", t):
        return LIBRA
    if re.search(r"\b(litro|kilo)\b", t):
        return 1000.0
    return None

def _bonito(v: float, unidad: str) -> str:
    if unidad == "g":
        if abs(v - LIBRA) < 1:
            return "1 libra"
        return f"{v / 1000:g} kg" if v >= 1000 else f"{v:g} g"
    return f"{v / 1000:g} litro" + ("s" if v > 1000 else "") if v >= 1000 else f"{v:g} ml"

def presentacion_real(i: Ingrediente) -> Ingrediente:
    nombre = _clave(i.nombre)
    for patron, unidad, tamanos, envase in TAMANOS_REALES:
        if not re.search(patron, nombre):
            continue
        actual = _tamano(i.presentacion, unidad)
        if not actual or actual <= 0:
            return i
        texto_raro = re.search(r"\b(media|medio|mitad)\b|1/2", _clave(i.presentacion))
        if any(abs(actual - t) <= t * 0.06 for t in tamanos):
            if texto_raro:
                i.presentacion = f"{envase} de {_bonito(actual, unidad)}"
            return i
        usado = actual * i.fraccion_usada
        real = next((t for t in tamanos if t >= usado), tamanos[-1])
        precio_por = i.precio_presentacion_usd / actual
        i.precio_presentacion_usd = round(precio_por * real, 2)
        i.fraccion_usada = round(usado / real, 3)
        i.presentacion = f"{envase} de {_bonito(real, unidad)}"
        return i
    return i

ECUADOR = [
    (r"\bsalteñad([oa]s?)\b", r"saltead\1"), (r"\bsalteñar\b", "saltear"),
    (r"\bcalabacín(es)?\b", r"zucchini"),
    (r"\barroz patrio\b", "arroz blanco"), (r"\bhogao\b", "refrito"), (r"\bfrijol(es)?\b", r"fréjol\1"),
    (r"\bfríjol(es)?\b", r"fréjol\1"), (r"\bpaltas?\b", "aguacate"), (r"\belotes?\b", "choclo"),
    (r"\bejotes?\b", "vainitas"), (r"\bchícharos?\b", "arveja"), (r"\bjitomates?\b", "tomate riñón"),
    (r"\bcacahuates?\b", "maní"), (r"\bcacahuetes?\b", "maní"), (r"\bbetabel\b", "remolacha"),
    (r"\bplátano macho\b", "verde"), (r"\bcalabaza\b", "zapallo"), (r"\bpimentón rojo\b", "pimiento rojo"),
    (r"\bchile\b", "ají"), (r"\bfrutilla\b", "frutilla"), (r"\bpapa criolla\b", "papa chola"),
]

def a_ecuador(texto: str) -> str:
    if not texto:
        return texto
    for patron, cambio in ECUADOR:
        def rep(m, cambio=cambio):
            nuevo = m.expand(cambio) if "\\" in cambio else cambio
            return nuevo[:1].upper() + nuevo[1:] if m.group(0)[:1].isupper() else nuevo
        texto = re.sub(patron, rep, texto, flags=re.IGNORECASE)
    return texto

def unidades_paquete(presentacion: str) -> int | None:
    t = _clave(presentacion or "")
    m = re.search(r"(\d+)\s*(unidades?|u\b)|(cubeta|docena|paquete|malla|atado|funda) de (\d+)\b(?!\s*(g|kg|ml|l|lb))", t)
    if m:
        return int(m.group(1) or m.group(4))
    if re.search(r"\bdocena\b", t):
        return 12
    if re.search(r"\b(unidad|c/u|cada uno)\b", t):
        return 1
    return None

def enteros(i: Ingrediente) -> Ingrediente:
    total = unidades_paquete(i.presentacion)
    if total and not i.basico_de_despensa:
        usadas = max(1, round(total * i.fraccion_usada))
        i.fraccion_usada = round(usadas / total, 4)
    return i

NOMBRE_INVENTADO = re.compile(r"\b(bowl|fusi[oó]n|delicias?|explosi[oó]n|sorpresa|express|exprés|de la casa|"
                              r"al estilo|estilo|toque|twist|power|fit|saludable|light|especial|m[aá]gic[oa]|"
                              r"tropical(?! fruit)|gourmet|r[aá]pid[oa]|f[aá]cil|caser[oa] de|versi[oó]n|reinventad[oa])\b",
                              re.IGNORECASE)

def nombre_inventado(nombre: str) -> bool:
    return bool(NOMBRE_INVENTADO.search(nombre or ""))

def limpiar_receta(r: Receta) -> Receta:
    r.porciones = max(1, int(r.porciones or 1))
    r.tiempo_minutos = max(1, int(r.tiempo_minutos or 1))
    buenos = []
    for i in r.ingredientes:
        if i.precio_presentacion_usd is None or i.precio_presentacion_usd < 0:
            continue
        i.fraccion_usada = min(1.0, max(0.0, float(i.fraccion_usada or 0)))
        buenos.append(i)
    r.ingredientes = buenos
    r.nombre, r.descripcion = a_ecuador(r.nombre), a_ecuador(r.descripcion)
    r.pasos = [a_ecuador(p) for p in r.pasos]
    for i in r.ingredientes:
        i.nombre, i.cantidad = a_ecuador(i.nombre), a_ecuador(i.cantidad)
    r.ingredientes = [enteros(presentacion_real(i)) for i in r.ingredientes]
    r.alergenos = detectar_alergenos(r)
    if r.icono not in ICONOS:
        r.icono = "otro"
    return r

def costo_ingrediente(i: Ingrediente) -> float:
    return round(i.precio_presentacion_usd * i.fraccion_usada, 2)

def costo_receta(r: Receta) -> float:
    return round(sum(costo_ingrediente(i) for i in r.ingredientes), 2)

def costo_porcion(r: Receta) -> float:
    return round(costo_receta(r) / max(r.porciones, 1), 2)

def ajustar_porciones(r: Receta, personas: int) -> Receta:
    if personas == r.porciones or personas < 1:
        return r
    f = personas / r.porciones
    nueva = r.model_copy(deep=True) if hasattr(r, "model_copy") else r.copy(deep=True)
    for i in nueva.ingredientes:
        i.fraccion_usada = round(i.fraccion_usada * f, 3)
        enteros(i)
    nueva.porciones = personas
    return nueva

class ErrorIA(Exception):
    """Error con un mensaje listo para mostrar."""

def _codigo(e: Exception) -> int | None:
    try:
        return int(getattr(e, "code", None) or getattr(e, "status_code", None))
    except (TypeError, ValueError):
        return None


def error_gemini(e):
    """Mensaje seguro: nunca muestra la respuesta cruda ni la clave."""
    if isinstance(e, ErrorIA):
        return e
    code = _codigo(e)
    texto = str(e).lower()
    if code == 401 or any(x in texto for x in ("api_key_invalid", "api key not valid", "api key expired")):
        return ErrorIA("La clave de Gemini no es válida o caducó. Revisa GEMINI_API_KEY en Railway.")
    if code == 403:
        return ErrorIA("Gemini denegó el acceso (403). Revisa los permisos y restricciones de la clave en Google AI Studio.")
    if code == 429:
        return ErrorIA("Gemini alcanzó su cuota (429). Revisa los límites y la facturación en Google AI Studio; esperar no resuelve una cuota diaria agotada o igual a cero.")
    if code == 402 or "billing" in texto or "failed_precondition" in texto:
        return ErrorIA("Gemini requiere revisar la facturación o los requisitos del proyecto en Google AI Studio.")
    if code == 404:
        return ErrorIA("El modelo de Gemini no está disponible (404). Revisa las variables MODELO_GEMINI y MODELO_GEMINI_IMAGEN.")
    if code == 400:
        return ErrorIA("Gemini rechazó la solicitud (400). Revisa el modelo configurado y actualiza google-genai.")
    if code and code >= 500:
        return ErrorIA("Gemini tiene un fallo temporal. Vuelve a intentarlo en unos momentos.")
    if isinstance(e, (ImportError, AttributeError)):
        return ErrorIA("Actualiza la dependencia google-genai y vuelve a desplegar la aplicación.")
    return ErrorIA("No se pudo completar la respuesta de Gemini. Comprueba la conexión y vuelve a intentar.")


def generar_con_respaldo(cliente, contenidos, modelos=None, config=None, validar=None, reintentos=1):
    from google.genai import types
    errores = []
    for modelo in dict.fromkeys(modelos or MODELOS_CASCADA):
        for intento in range(reintentos + 1):
            try:
                cfg = dict(config or {})
                if modelo.startswith("gemini-2.5-flash") and "image" not in modelo:
                    cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
                respuesta = cliente.models.generate_content(
                    model=modelo, contents=contenidos, config=types.GenerateContentConfig(**cfg))
                return (validar(respuesta) if validar else respuesta), modelo
            except Exception as e:
                errores.append(e)
                codigo = _codigo(e)
                print(f"[gemini] modelo={modelo} codigo={codigo} tipo={type(e).__name__}", flush=True)
                if codigo in (401, 403, 402) or "api_key_invalid" in str(e).lower() or "api key not valid" in str(e).lower():
                    raise error_gemini(e) from e
                if codigo in (400, 404, 429):
                    break
                if intento < reintentos:
                    time.sleep(1 + intento)
    # Un modelo retirado no debe ocultar un error de cuota previo.
    error = next((e for e in errores if _codigo(e) == 429), errores[-1] if errores else ValueError())
    raise error_gemini(error) from error


def llamar_gemini(cliente, prompt: str, esquema, modelos=MODELOS_CASCADA, reintentos: int = 1,
                  razonamiento: str = "low"):
    def validar(resp):
        obj = getattr(resp, "parsed", None)
        if isinstance(obj, esquema):
            return obj
        if obj is not None:
            return esquema.model_validate(obj)
        texto = (getattr(resp, "text", None) or "").strip()
        if not texto:
            raise ValueError("respuesta vacía")
        return esquema.model_validate_json(texto)
    return generar_con_respaldo(cliente, prompt, modelos, dict(
        system_instruction=SISTEMA, response_mime_type="application/json",
        response_schema=esquema, temperature=0.4, max_output_tokens=12000), validar, reintentos)


def mime_imagen(datos):
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if datos.startswith(b"RIFF") and datos[8:12] == b"WEBP":
        return "image/webp"
    if datos.startswith(b"\xff\xd8"):
        return "image/jpeg"
    raise ErrorIA("La imagen no es un JPG, PNG o WebP válido.")


def buscar_recetas(cliente, cocinas, personas, max_porcion, tiempo, tipos=(), ciudad="Guayaquil",
                   excluir=(), sobrantes=(), cantidad=RECETAS_POR_BUSQUEDA, categoria="", dieta="Todas"):
    prompt = PROMPT_RECETAS.format(
        n=cantidad, economica=ECONOMICA, cocinas=", ".join(cocinas), personas=personas, max_porcion=max_porcion,
        tiempo=tiempo, tipos=", ".join(tipos) or "cualquiera", ciudad=ciudad or "Guayaquil",
        excluir=", ".join(excluir) or "ninguna",
        categoria=(f"- Categoría: {categoria}.\n") if categoria else "",
        dieta=(f"- Dieta OBLIGATORIA: {DIETAS[dieta]}.\n") if DIETAS.get(dieta) else "",
        extra=EXTRA_SOBRANTES.format(sobrantes=", ".join(sobrantes)) if sobrantes else "",
    )
    cat, _ = llamar_gemini(cliente, prompt, Catalogo, razonamiento="minimal")
    validas, descartadas = [], 0
    for r in cat.recetas:
        r = ajustar_porciones(limpiar_receta(r), personas)
        if not r.ingredientes or not r.pasos:
            descartadas += 1
            continue
        if not cumple_dieta(r, dieta):
            descartadas += 1
            continue
        validas.append(r)
    if not validas:
        raise ErrorIA("No encontré recetas dentro de ese precio. Sube el precio máximo o cambia de cocina.")
    return sorted(validas, key=costo_porcion), descartadas

def _clave(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto.lower().strip())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def foto_coincide(cliente, imagen_bytes: bytes, plato: str, consulta: str = "") -> bool | None:
    """True si la foto muestra el plato pedido, False si no, None si la IA no pudo revisar.
    Se usa para filtrar candidatas de Unsplash/Commons antes de mostrarlas."""
    from google.genai import types
    prompt = (
        f"¿Esta foto muestra el plato de comida «{plato}» (o muy similar) listo para servir? "
        f"Búsqueda: {consulta or plato}. "
        "Responde SOLO con una palabra: SI o NO. "
        "SI solo si se ve el plato cocinado/servido, no ingredientes crudos solos, no mercados, no personas."
    )
    try:
        partes = [prompt, types.Part.from_bytes(data=imagen_bytes, mime_type=mime_imagen(imagen_bytes))]
        resp, _ = generar_con_respaldo(cliente, partes, config=dict(temperature=0.0, max_output_tokens=128))
        texto = _clave(getattr(resp, "text", None) or "").strip(" .!\n")
        if texto in ("si", "yes"):
            return True
        if texto == "no":
            return False
    except ErrorIA:
        pass
    return None
