# RutaRentable: ¿te alcanza el flete? (despliegue Streamlit)

Aplicación del Proyecto Integrador de Machine Learning I (Universidad Externado de Colombia). Estima la probabilidad de que un viaje de carga (camión rígido de 2 ejes, Colombia) termine pagado por debajo del costo de referencia SICE-TAC, usando solo lo que se conoce al recibir la oferta. No usa el pago ni el costo como entradas. Aparte del modelo, una guía para negociar muestra el costo de referencia SICE-TAC de la ruta en pesos, el rango que se pagó en el RNDC por viajes parecidos y, si el usuario escribe cuánto le ofrecen, si esa oferta cubre el costo; nada de eso entra al modelo. Datos: RNDC y SICE-TAC, diciembre de 2025.

## Ejecutar en local

```
pip install -r requirements.txt
streamlit run app.py
```

Con uv, desde esta carpeta:

```
uv run --no-project --python 3.12 --with "streamlit==1.67.0,scikit-learn==1.8.0,pandas,numpy,scipy,joblib,plotly,pydeck" -- streamlit run app.py
```

Se requiere scikit-learn 1.8.0 (la versión con la que se ajustó el modelo); la app avisa si la versión instalada es distinta.

## Pestañas

1. **Revisa una oferta.** El transportador elige municipio de origen y destino, kilos, mercancía y cómo viaja la carga.
   - Los kilómetros se llenan solos: distancia oficial SICE-TAC si la ruta existe (7.512 pares de municipios); si no, línea recta entre centroides por 1,3. Siempre se pueden cambiar.
   - La mercancía se busca por su nombre real (982 descripciones del RNDC). La app deriva el capítulo, explica qué incluye ese grupo y sugiere la naturaleza de carga más común.
   - Botones rápidos de kilos: media carga (5.000 kg) y carga completa (9.000 kg).
   - Resultado: semáforo (verde si p < límite − 0,08; amarillo entre límite − 0,08 y el límite; rojo desde el límite), frase "de cada 10 viajes como este, unos N no alcanzaron a cubrir el costo" con 10 camiones, medidor con la raya del límite, "qué está pesando en esta oferta", mapa de la ruta y tres indicadores. Las odds aparecen como dato técnico secundario.
   - Avisos: kilómetros o kilos fuera del rango p1 a p99 de entrenamiento, y categorías con menos de 50 viajes (el modelo las trata como "infrecuente").
   - **Tu guía para negociar** (debajo del resultado; no usa el modelo): piso = costo de referencia SICE-TAC de la ruta (refrigerada si la carga viaja con frío, general en los demás casos; si falta el sentido pedido se usa el contrario y se avisa), con lo que incluye y lo que no; mercado = percentiles 25 a 75 y mediana de lo pagado en el RNDC por el mismo par de municipios (5 o más viajes) o, si no alcanza, por el mismo par de departamentos y banda de km; y un campo opcional "¿Cuánto te ofrecen?" que dice si cubre el costo (diferencia en pesos y %) y si está debajo, dentro o por encima de lo usual.
2. **Compara tus ofertas.** Tabla editable (origen, destino, kilos, mercancía y, opcional, cuánto te ofrecen; hasta 8 filas, con 3 de ejemplo). El botón Comparar las ordena por riesgo de mejor a peor, resalta la mejor y en cada tarjeta muestra costo de referencia, mediana del mercado y si la oferta cubre el costo (las que no, quedan marcadas "No cubre el costo").
3. **Para empresas (archivo CSV).** Sube un CSV y descarga el resultado. Acepta dos formatos:
   - Sencillo: `Origen`, `Destino` (municipios, por ejemplo "Medellín (Antioquia)" o "Medellin"), `Kilos`, `Mercancia`; opcionales `Kilometros` y `Naturaleza`.
   - Técnico: `KILOMETROS, KILOGRAMOS, CAPITULO, NATURALEZACARGA, DEPARTAMENTOORIGEN, DEPARTAMENTODESTINO`; opcionales `CODMUNICIPIOORIGEN` y `CODMUNICIPIODESTINO` (DIVIPOLA) para el costo y el mercado de la ruta exacta.
   - En los dos, columna opcional con el valor ofrecido: `PAGO_OFRECIDO`, `OFERTA`, `TE_OFRECEN` o `VALOR_OFRECIDO` (sin importar mayúsculas ni tildes).
   Muestra cuántas ofertas quedan en verde, amarillo y rojo, cuántas con valor ofrecido no cubren el costo, una gráfica de barras y la tabla ordenada. La descarga agrega `pago_ofrecido`, `costo_referencia`, `mercado_p25`, `mercado_mediana`, `mercado_p75`, `mercado_viajes`, `cubre_costo` (Sí/No/sin dato), `diferencia_vs_costo` y `posicion_mercado`.

Debajo están "Ajustes avanzados" (límite de decisión) y "Sobre el modelo" (qué usa, qué no, factores, alcance, limitaciones).

## Archivos de ejemplo (simulados, semilla 42)

- `ejemplos/ofertas_semana_transportador.csv`: 8 ofertas que recibe un transportador en una semana (formato sencillo).
- `ejemplos/ofertas_cooperativa.csv`: 40 ofertas de una cooperativa pequeña (formato técnico).
- `ejemplo_lote.csv`: 5 filas en formato técnico (ejemplo de la versión anterior; mismas predicciones).

Los dos primeros se descargan desde la pestaña "Para empresas".

## Límite de decisión (Ajustes avanzados)

- Recomendado (costo del negocio): 0,44. Minimiza el costo esperado: aceptar un viaje malo cuesta el faltante; marcar uno bueno cuesta α veces el margen, con α = 0,5.
- Youden (artículo): 0,319.
- Personalizado: control deslizante.

## Organización del código

- `app.py`: flujo de la aplicación, carga del modelo (`@st.cache_resource`) y gráficos.
- `estilo.py`: tema oscuro, CSS, logo, escena animada de la carretera y fragmentos HTML. Las animaciones se apagan si el sistema pide reducir movimiento.
- `datos_app.py`: tablas de consulta, distancia de la ruta, semáforo, frases y lectura de tablas de ofertas (`preparar_ofertas`, `evaluar`).
- `construir_tablas.py`: se ejecuta una sola vez para generar `municipios.csv` (DIVIPOLA, 1.122 municipios), `mercancias.csv` (RNDC), `distancias_rutas.csv` (solo los kilómetros de SICE-TAC), `costos_rutas.csv` (costo de referencia SICE-TAC por par dirigido de municipios: 7.512 rutas, 248 KB), `mercado_rutas.csv` (lo pagado en el RNDC: 1.255 pares de municipios y 555 grupos de departamentos y banda de km con 5 o más viajes, 111 KB) y los ejemplos (con una columna de valor ofrecido simulado alrededor del costo de referencia). Las dos tablas de la guía solo se muestran; nunca entran al modelo.
  `uv run --no-project --python 3.12 --with pandas,numpy -- python construir_tablas.py`
- `.streamlit/config.toml`: tema oscuro base. `deptos_centroides.csv`: puntos de referencia del mapa.

## Modelo

`modelo_final.joblib` es exactamente el que se evaluó en el conjunto de prueba reservado en el notebook 04 (AUC en prueba y su IC 95 % en `metadatos.json`). La app le entrega las columnas `KILOMETROS, KILOGRAMOS, CAPITULO, NATURALEZACARGA, DEPARTAMENTOORIGEN, DEPARTAMENTODESTINO` y lee `predict_proba(X)[:, 0]` como la probabilidad de no cubrir el costo.

Limitaciones: solo diciembre de 2025, solo camiones C2, etiqueta basada en una aproximación del costo por tipo de carrocería, y cerca del límite el resultado es incierto. El mapa base no usa token; sin internet se ven solo los puntos y el arco. Los nombres sobre el mapa van sin tildes por una limitación de la capa de texto.
