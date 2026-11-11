# Pruebas del modelo y de la aplicación

Dos pruebas que respaldan que lo entregado funciona y es reproducible. Se ejecutaron el 10 de noviembre de 2026 sobre el paquete `entrega_final/`.

## 1. Reproducibilidad (`repro.py`)

Ejecuta los notebooks 01 a 04 desde los datos crudos, en una carpeta nueva, y compara lo que producen con lo entregado.

```bash
uv run --no-project --python 3.12 --with "pandas,numpy,scikit-learn==1.8.0,statsmodels,scipy,matplotlib,joblib,patsy,nbclient,ipykernel,nbformat" -- python repro.py <ruta a entrega_final> <carpeta temporal>
```

Resultado (`salida_reproducibilidad.txt`): los cuatro notebooks corren sin error (unos 6 minutos en total). Los datos limpios, el conjunto de modelamiento, la prueba reservada y las bitácoras salen idénticos. Las tablas del notebook 04 y el modelo exportado salen idénticos (diferencia 0). En la tabla de comparación de la entrega 2, KNN y LDA difieren en el cuarto decimal (máximo 0,0023) por desempates numéricos entre versiones de librerías; no afecta al modelo final.

## 2. Despliegue (`pruebas_despliegue.py`)

Se ejecuta en un entorno limpio con solo las dependencias de la aplicación:

```bash
uv run --no-project --isolated --python 3.12 --with-requirements ../app/requirements.txt -- python -I pruebas_despliegue.py <ruta a entrega_final> resultado_pruebas.json [carpeta de datos]
```

La carpeta de datos (con `conjunto_prueba_reservado.csv` y `sicetac_costos_c2_dic2025.csv`) es opcional: si no se da, se usa `<ruta>/datos` y, si no existe, `../3. Entrega 2 (corregida)/datos`.

Resultado (`salida_pruebas_despliegue.txt`, corrida del 11 de noviembre de 2026 sobre `5. Entrega final/`): **63 de 63 pruebas correctas**, en nueve grupos:

| Grupo | Qué comprueba |
|---|---|
| 1. Entorno | La versión de scikit-learn instalada es la misma con la que se entrenó el modelo. |
| 2. Integridad | El modelo guardado reproduce el AUC de prueba (0,784), la matriz de confusión del informe y el umbral 0,44. |
| 3. Consistencia | Mismo resultado al repetir, fila a fila igual que por lote, el orden de columnas no importa, probabilidades válidas. |
| 4. Robustez | Departamento, capítulo o naturaleza no vistos, valores vacíos y extremos: el modelo responde sin fallar; una columna faltante se rechaza. |
| 5. Dirección | Lo que encontró el estudio se ve en el modelo: refrigerada, poco peso y más de 350 km suben el riesgo en el 100 % de los casos probados. |
| 6. Desempeño | Unos 7 ms por oferta, 10.000 ofertas en 0,05 s, modelo de 12 KB. |
| 7. Funciones de la app | Distancia oficial, semáforo, frases, archivos de ejemplo, mensajes ante CSV mal formados, predicciones estables. |
| 8. App completa | Con `streamlit.testing`: abre sin errores, los tres umbrales, carga refrigerada, km fuera de rango con aviso, botones de kilos y comparador. |
| 9. Guía de negociación | Costo de referencia de Bogotá a Medellín igual al COSTO_GENERAL del SICE-TAC ($1.900.050) y COSTO_REFRIGERADA para carga con frío; uso del sentido contrario si falta uno; mensaje cuando la ruta no tiene costo; rango de mercado con 5 o más viajes (79 viajes); oferta por debajo = no cubre, por encima = cubre; los dos ejemplos con columna de oferta; el valor ofrecido no cambia las predicciones de `ejemplo_lote.csv`; en la app, llenar la oferta no cambia el riesgo y el comparador marca la oferta que no cubre el costo. |
