import os
from typing import Any
import pandas as pd
import streamlit as st
print("ENV-CHECK POLLINATIONS:", "OK" if os.environ.get("sk_E2kVdvA4QZGNrjzIZhDowvkKjvoTrdIK") else "FALTA", flush=True)


st.set_page_config(
    page_title="larefri · Ranking de Recetas por Ingredientes",
    page_icon="🍳",
    layout="wide",
)

INGREDIENTES_BASICOS = {
    "sal",
    "agua",
    "aceite",
    "aceite de oliva",
    "pimienta",
    "azucar",
    "azúcar",
}

RECETAS_EJEMPLO: list[dict[str, Any]] = [
    {
        "nombre": "Tortilla rápida de huevo, tomate y ajo",
        "tiempo_min": 12,
        "ingredientes": ["huevo", "tomate", "ajo", "sal", "aceite"],
        "pasos": [
            "Pica el tomate y el ajo en trozos pequeños.",
            "Bate los huevos con una pizca de sal.",
            "Sofríe el ajo y el tomate en aceite, incorpora el huevo y cocina hasta cuajar.",
        ],
    },
    {
        "nombre": "Huevo revuelto al ajillo",
        "tiempo_min": 8,
        "ingredientes": ["huevo", "ajo", "sal", "aceite", "pimienta"],
        "pasos": [
            "Lamina el ajo y dóralo suavemente en aceite.",
            "Vierte los huevos batidos y remueve a fuego medio hasta que queden jugosos.",
        ],
    },
    {
        "nombre": "Ensalada fresca de tomate y aguacate",
        "tiempo_min": 10,
        "ingredientes": ["tomate", "aguacate", "cebolla", "limon", "sal", "aceite de oliva"],
        "pasos": [
            "Corta el tomate, el aguacate y la cebolla en cubos.",
            "Aliña con jugo de limón, aceite de oliva y sal.",
        ],
    },
    {
        "nombre": "Shakshuka exprés en sartén",
        "tiempo_min": 20,
        "ingredientes": ["huevo", "tomate", "ajo", "cebolla", "pimenton", "comino", "sal", "aceite"],
        "pasos": [
            "Prepara una salsa rápida con ajo, cebolla, pimentón y tomate.",
            "Haz huecos en la salsa, casca los huevos y tapa hasta que la clara esté lista.",
        ],
    },
    {
        "nombre": "Arroz salteado con huevo y verduras",
        "tiempo_min": 18,
        "ingredientes": ["arroz", "huevo", "zanahoria", "cebolla larga", "salsa de soya", "aceite", "sal"],
        "pasos": [
            "Saltea las verduras picadas en un sartén o wok caliente.",
            "Incorpora el arroz cocido y el huevo revuelto, mezclando bien con salsa de soya.",
        ],
    },
]


def normalizar_ingrediente(texto: str) -> str:
    return " ".join(texto.strip().lower().split())


def parsear_ingredientes(raw_input: str) -> set[str]:
    partes = raw_input.replace("\n", ",").split(",")
    return {normalizar_ingrediente(p) for p in partes if normalizar_ingrediente(p)}


def evaluar_recetas(
    recetas: list[dict[str, Any]],
    ingredientes_usuario: set[str],
    basicos: set[str],
    w_aprovechamiento: float = 0.55,
    w_eficiencia: float = 0.25,
    bono_todos: float = 0.20,
    w_penalizacion: float = 0.20,
) -> pd.DataFrame:
    n_usuario = len(ingredientes_usuario)
    basicos_norm = {normalizar_ingrediente(b) for b in basicos}
    filas: list[dict[str, Any]] = []

    for receta in recetas:
        ing_receta = {normalizar_ingrediente(i) for i in receta.get("ingredientes", [])}
        if not ing_receta:
            continue

        coinciden = ing_receta & ingredientes_usuario
        faltan_total = ing_receta - ingredientes_usuario
        faltan_no_basicos = faltan_total - basicos_norm

        aprovechamiento = (len(coinciden) / n_usuario) if n_usuario > 0 else 0.0
        eficiencia = len(coinciden) / len(ing_receta)
        usa_todos = (n_usuario > 0) and (len(coinciden) == n_usuario)
        bono = bono_todos if usa_todos else 0.0
        penalizacion_extras = len(faltan_no_basicos) / len(ing_receta)

        score = (
            (w_aprovechamiento * aprovechamiento)
            + (w_eficiencia * eficiencia)
            + bono
            - (w_penalizacion * penalizacion_extras)
        )

        filas.append(
            {
                "receta": receta["nombre"],
                "tiempo_min": receta.get("tiempo_min", 15),
                "coinciden_cnt": len(coinciden),
                "usuario_cnt": n_usuario,
                "usa_todos": usa_todos,
                "aprovechamiento": aprovechamiento,
                "eficiencia": eficiencia,
                "score": score,
                "coinciden": sorted(coinciden),
                "faltan_extras": sorted(faltan_no_basicos),
                "faltan_basicos": sorted(faltan_total & basicos_norm),
                "pasos": receta.get("pasos", []),
            }
        )

    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(filas).sort_values(
        by=["score", "aprovechamiento", "eficiencia"],
        ascending=[False, False, False],
    )
    return df.reset_index(drop=True)


def main() -> None:
    st.title("🍳 larefri — Priorización Estadística de Recetas")
    st.caption(
        "Ordena recetas priorizando usar **todos o la mayoría** de los ingredientes seleccionados "
        "y reduciendo ingredientes extra no básicos."
    )

    with st.sidebar:
        st.header("Parámetros estadísticos")
        w_aprovechamiento = st.slider(
            "Peso aprovechamiento (ingredientes del usuario usados)",
            min_value=0.0,
            max_value=1.0,
            value=0.55,
            step=0.05,
        )
        w_eficiencia = st.slider(
            "Peso eficiencia (coincidencia frente al total de la receta)",
            min_value=0.0,
            max_value=1.0,
            value=0.25,
            step=0.05,
        )
        bono_todos = st.slider(
            "Bono por incluir el 100% de ingredientes elegidos",
            min_value=0.0,
            max_value=0.50,
            value=0.20,
            step=0.05,
        )
        w_penalizacion = st.slider(
            "Penalización por ingredientes extra no básicos",
            min_value=0.0,
            max_value=1.0,
            value=0.20,
            step=0.05,
        )

        # Variables de entorno disponibles en despliegue (Railway / Streamlit Cloud)
        tiene_gemini = bool(os.getenv("GEMINI_API_KEY"))
        tiene_spoonacular = bool(os.getenv("SPOONACULAR_API_KEY"))
        tiene_hf = bool(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN"))
        st.divider()
        st.caption(
            f"APIs configuradas → Gemini: {'✅' if tiene_gemini else '—'} | "
            f"Spoonacular: {'✅' if tiene_spoonacular else '—'} | "
            f"Hugging Face: {'✅' if tiene_hf else '—'}"
        )

    entrada_raw = st.text_input(
        "Ingredientes que tienes disponibles (separados por coma)",
        value="huevo, tomate, ajo",
        placeholder="Ej.: huevo, tomate, ajo, cebolla",
    )
    ingredientes_usuario = parsear_ingredientes(entrada_raw)

    if not ingredientes_usuario:
        st.warning("Ingresa al menos un ingrediente para calcular el ranking.")
        return

    df_ranking = evaluar_recetas(
        recetas=RECETAS_EJEMPLO,
        ingredientes_usuario=ingredientes_usuario,
        basicos=INGREDIENTES_BASICOS,
        w_aprovechamiento=w_aprovechamiento,
        w_eficiencia=w_eficiencia,
        bono_todos=bono_todos,
        w_penalizacion=w_penalizacion,
    )

    if df_ranking.empty:
        st.info("No hay recetas disponibles para evaluar.")
        return

    # Métricas estadísticas resumidas de la búsqueda actual
    cobertura_promedio = df_ranking["aprovechamiento"].mean() * 100
    recetas_completas = int(df_ranking["usa_todos"].sum())
    mejor_receta = df_ranking.iloc[0]

    m1, m2, m3 = st.columns(3)
    m1.metric("Mejor coincidencia", mejor_receta["receta"])
    m2.metric("Aprovechamiento promedio", f"{cobertura_promedio:.1f}%")
    m3.metric("Usan 100% de tus ingredientes", f"{recetas_completas} / {len(df_ranking)}")

    st.subheader("Ranking de recetas")
    for idx, fila in df_ranking.iterrows():
        etiqueta_top = "⭐ " if idx == 0 else ""
        badge_todos = " · 100% de tus ingredientes" if fila["usa_todos"] else ""
        titulo = (
            f"{etiqueta_top}#{idx + 1} {fila['receta']} "
            f"— Score: {fila['score']:.3f} "
            f"(Usa {fila['coinciden_cnt']}/{fila['usuario_cnt']} tuyos{badge_todos})"
        )
        with st.expander(titulo, expanded=(idx == 0)):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Aprovechamiento:** {fila['aprovechamiento'] * 100:.0f}%")
            c2.write(f"**Eficiencia:** {fila['eficiencia'] * 100:.0f}%")
            c3.write(f"**Tiempo estimado:** {fila['tiempo_min']} min")

            st.write(
                "**Ingredientes usados de tu búsqueda:** "
                + (", ".join(fila["coinciden"]) if fila["coinciden"] else "ninguno")
            )
            st.write(
                "**Extras no básicos necesarios:** "
                + (", ".join(fila["faltan_extras"]) if fila["faltan_extras"] else "ninguno")
            )
            if fila["pasos"]:
                st.markdown("**Preparación rápida:**")
                for paso_num, paso in enumerate(fila["pasos"], start=1):
                    st.write(f"{paso_num}. {paso}")

    st.subheader("Tabla estadística comparativa")
    tabla_visible = pd.DataFrame(
        {
            "Receta": df_ranking["receta"],
            "Score": df_ranking["score"].round(3),
            "Aprovechamiento (%)": (df_ranking["aprovechamiento"] * 100).round(1),
            "Eficiencia (%)": (df_ranking["eficiencia"] * 100).round(1),
            "Usa todos": df_ranking["usa_todos"].map({True: "Sí", False: "No"}),
            "Extras no básicos": df_ranking["faltan_extras"].apply(
                lambda x: ", ".join(x) if x else "—"
            ),
        }
    )
    st.dataframe(tabla_visible, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
