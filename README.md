# RutaRentable · Riesgo de que una oferta de carga no cubra su costo (Colombia)

**App en línea:** https://ruta-rentable.streamlit.app


Machine Learning I, Universidad Externado de Colombia. Entrega final: modelo final, evaluación en prueba, interpretación y despliegue.
Integrantes: Daniel Pacheco y Harold Burgos.

## Qué hay en este repositorio

| Carpeta | Contenido |
|---|---|
| `informe/` | Informe final en PDF, su fuente LaTeX y las figuras que usa. |
| `notebooks/` | Los cuatro notebooks del flujo, ya ejecutados (01 a 03 vienen de la entrega 2; el 04 es nuevo). |
| `datos/` | Datos crudos (RNDC y SICE-TAC, diciembre de 2025) y los archivos que producen los notebooks 01 a 03. |
| `resultados/` | Tablas y figuras de la entrega 2 y de la entrega final (notebook 04). |
| `app/` | Aplicación de Streamlit "RutaRentable" con el modelo final exportado. Ver `app/README.md`. |
| `presentacion/` | Presentación de la sustentación en HTML interactivo (`sustentacion_rutarentable.html`, se abre con doble clic). Teclas: → avanza, ← retrocede, F pantalla completa, P modo presentador con notas, O vista general. |
| `video/` | Animación de 30 segundos (`promo_rutarentable.html`) para grabar como video de propuesta de valor. |
| `pruebas/` | Pruebas de reproducibilidad (notebooks 01 a 04 desde los crudos, resultados idénticos) y de despliegue de la app (46 de 46 correctas). Ver `pruebas/README.md`. |

## Cómo reproducir

Los notebooks se corren en orden y cada uno lee solo lo que produjo el anterior. Semilla 42 en todo el flujo. Los notebooks 01 a 03 leen sus archivos de la misma carpeta (o de `/content` en Colab): copie allí los de `datos/` que indica cada uno.

1. `01_limpieza.ipynb`: lee `RNDC_202512_crudo.csv.gz` y `SICETAC_202512_crudo.csv.gz`.
2. `02_cruce_rndc_sicetac.ipynb`: produce `dataset_modelo_dic2025.csv` (lo único que lee el modelo) y `dataset_auditoria_dic2025.csv` (pago y costo, solo para revisión).
3. `03_modelamiento.ipynb`: comparación de modelos de la entrega 2; separa `conjunto_prueba_reservado.csv`.
4. `04_modelo_final.ipynb`: decide logaritmo frente a splines, elige el umbral por costo en pesos, evalúa una sola vez en la prueba reservada, interpreta en odds ratios y exporta `app/modelo_final.joblib` y `app/metadatos.json`. Tarda unos cinco minutos.

**En Google Colab:** corra primero la celda de instalación del notebook 04 (fija `scikit-learn==1.8.0`, la versión con la que se exportó el modelo) y suba a `/content` los archivos que indica cada notebook. Fuera de Colab, instale `requirements.txt` y corra los notebooks desde su carpeta; el 04 busca los datos en `../datos/`.

**Aplicación en local:**

```bash
pip install -r app/requirements.txt
streamlit run app/app.py
```

**Despliegue:** la app está publicada en Streamlit Community Cloud desde este repositorio (archivo principal `app/app.py`, Python 3.12, dependencias en `app/requirements.txt`).

## Resultados principales

- Modelo final: regresión logística con splines en kilómetros y kilogramos (6 nodos, C = 0,1). Supera a la versión con logaritmo en los 10 folds agrupados por ruta.
- Prueba reservada (4.173 viajes, rutas nunca vistas): AUC 0,784 (IC 95 % por ruta: 0,766 a 0,801). Artículo de referencia: 0,81.
- Umbral 0,44, elegido minimizando el costo en pesos de los errores (α = 0,5). En prueba reduce 48,7 % las pérdidas frente a aceptar todas las ofertas (Youden: 39,2 %).

## Fuentes de los datos

- RNDC, Ministerio de Transporte, Portal Logístico de Colombia: https://plc.mintransporte.gov.co
- SICE-TAC, Ministerio de Transporte: https://sicetac.mintransporte.gov.co
- DIVIPOLA (centroides para el mapa de la app), DANE.

## Entorno

Python 3.12, pandas, numpy, scikit-learn 1.8.0, statsmodels 0.15, scipy, matplotlib, patsy, joblib; la app además usa streamlit 1.67, plotly y pydeck. Uso de IA generativa declarado en el informe.
