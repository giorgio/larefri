# larefri.

**¿Hay algo en la refri? Cocina con eso. Gasto: $0.** Le dices qué tienes en casa y te da recetas para hoy **sin comprar nada**.
Hermana de **canastas.** y **sazona.**

- Marcas lo que tienes (o lo escribes) y los básicos de cocina.
- La IA (Google Gemini) propone recetas **solo** con eso; la app revisa cada ingrediente y descarta las que traen algo que no tienes.
- Cada receta muestra **$0 · No compras nada** y cuánto te ahorras por no salir a comprar.
- Opcional: recetas a las que les falta **un** ingrediente barato (apagado por defecto).
- Dietas (vegana, vegetariana, ovolactovegetariana, pescetariana), alérgenos y tipo de plato.

## Ejecutar
```
pip install -r requirements.txt
streamlit run app.py
```
Claves en `.streamlit/secrets.toml` (local) o en **Secrets** de Streamlit Cloud: `GEMINI_API_KEY` y, opcional, `PEXELS_API_KEY`.
Nunca escribas las claves en el código.

## Pruebas
```
python tests/test_casa.py
```

Autor: Jorge Recabarren

## Railway
`railway.json` (y `Procfile`) le dicen a Railway cómo arrancar la app:
`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`.
Las claves van en **Variables** del servicio en Railway: `GEMINI_API_KEY` y, opcional, `PEXELS_API_KEY`.

Se publica sola en Railway con cada cambio en la rama `main`.
