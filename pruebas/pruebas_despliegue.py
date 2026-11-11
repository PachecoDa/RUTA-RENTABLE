"""Pruebas de despliegue del modelo y de la app RutaRentable, sobre el paquete entregado.
Se ejecuta con SOLO las dependencias de app/requirements.txt."""
import sys, os, json, time, platform, warnings, importlib
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

PKG = Path(sys.argv[1]); APP = PKG / "app"
os.chdir(APP); sys.path.insert(0, str(APP))
import numpy as np, pandas as pd, joblib, sklearn
from sklearn.metrics import roc_auc_score, confusion_matrix

RES = []
def chk(nombre, ok, detalle=""):
    RES.append((nombre, bool(ok), detalle)); print(f"[{'OK ' if ok else 'FALLA'}] {nombre}  {detalle}", flush=True)

COLS = ["KILOMETROS", "KILOGRAMOS", "CAPITULO", "NATURALEZACARGA", "DEPARTAMENTOORIGEN", "DEPARTAMENTODESTINO"]
meta = json.load(open(APP / "metadatos.json", encoding="utf-8"))

# 1. Entorno
vers = {m: importlib.import_module(m).__version__ for m in ["sklearn", "pandas", "numpy", "streamlit", "plotly", "pydeck", "joblib"]}
print("Python", platform.python_version(), vers)
chk("1.1 versión de scikit-learn igual a la del entrenamiento", vers["sklearn"] == meta["version_sklearn"], f"{vers['sklearn']} vs {meta['version_sklearn']}")

# 2. Integridad del artefacto
t0 = time.perf_counter(); modelo = joblib.load(APP / "modelo_final.joblib"); t_load = time.perf_counter() - t0
chk("2.1 el modelo carga", modelo is not None, f"{t_load*1000:.0f} ms, {type(modelo).__name__} con pasos {[n for n, _ in modelo.steps]}")
te = pd.read_csv(PKG / "datos" / "conjunto_prueba_reservado.csv"); X, y = te[COLS], te["RENTABLE"].values
p0 = modelo.predict_proba(X)[:, list(modelo.classes_).index(0)]
auc = roc_auc_score((y == 0).astype(int), p0)
chk("2.2 AUC en prueba igual al reportado (0,784)", abs(auc - meta["auc_prueba"]) < 1e-9 and round(auc, 3) == 0.784, f"{auc:.4f}")
cm = confusion_matrix((y == 0).astype(int), (p0 >= meta["umbral_costo"]).astype(int))
chk("2.3 matriz de confusión con umbral 0,44 igual a la del informe", cm.tolist() == [[2280, 544], [531, 818]], str(cm.tolist()))
chk("2.4 umbral de los metadatos = 0,44", abs(meta["umbral_costo"] - 0.44) < 1e-9, str(meta["umbral_costo"]))
chk("2.5 clases del modelo [0, 1] (0 = no rentable)", list(modelo.classes_) == [0, 1], str(list(modelo.classes_)))

# 3. Determinismo y consistencia
p_again = modelo.predict_proba(X)[:, 0]
chk("3.1 mismo resultado al repetir", np.array_equal(p0, p_again))
uno_a_uno = np.array([modelo.predict_proba(X.iloc[[i]])[:, 0][0] for i in range(100)])
chk("3.2 predicción fila a fila = por lote", np.allclose(uno_a_uno, p0[:100], atol=1e-12), f"dif máx {np.abs(uno_a_uno - p0[:100]).max():.1e}")
Xs = X[COLS[::-1]]
chk("3.3 orden de columnas no altera el resultado", np.allclose(modelo.predict_proba(Xs)[:, 0], p0))
chk("3.4 probabilidades en [0, 1] y sin NaN", np.isfinite(p0).all() and p0.min() >= 0 and p0.max() <= 1, f"rango {p0.min():.3f}-{p0.max():.3f}")

# 4. Robustez ante entradas raras
base = X.iloc[[0]].copy()
def pr(df): return float(modelo.predict_proba(df)[:, 0][0])
casos = {"departamento no visto (AMAZONAS)": dict(DEPARTAMENTOORIGEN="AMAZONAS"),
         "capítulo inexistente (CAP_XX)": dict(CAPITULO="CAP_XX"),
         "naturaleza desconocida": dict(NATURALEZACARGA="Otra cosa"),
         "kilómetros vacíos (NaN)": dict(KILOMETROS=np.nan),
         "kilos vacíos (NaN)": dict(KILOGRAMOS=np.nan),
         "km = 1": dict(KILOMETROS=1.0), "km = 3000 (fuera de rango)": dict(KILOMETROS=3000.0),
         "kg = 1": dict(KILOGRAMOS=1.0), "kg = 12000": dict(KILOGRAMOS=12000.0)}
for nombre, cambio in casos.items():
    d = base.copy()
    for k, v in cambio.items(): d[k] = v
    try:
        v = pr(d); chk(f"4. {nombre}", 0 <= v <= 1, f"p = {v:.3f}")
    except Exception as e:
        chk(f"4. {nombre}", False, f"{type(e).__name__}: {e}")
try:
    pr(base.drop(columns=["CAPITULO"])); chk("4. falta una columna -> debe fallar con error claro", False, "no falló")
except Exception as e:
    chk("4. falta una columna -> el modelo la rechaza", True, type(e).__name__)

# 5. Pruebas de dirección (lo que el estudio encontró debe verse en el modelo)
def frac(cambio_a, cambio_b, sentido):
    A, B = X.copy(), X.copy()
    for k, v in cambio_a.items(): A[k] = v
    for k, v in cambio_b.items(): B[k] = v
    pa, pb = modelo.predict_proba(A)[:, 0], modelo.predict_proba(B)[:, 0]
    return float(np.mean(pa > pb) if sentido == ">" else np.mean(pa < pb)), float(np.median(pa - pb))
f, m = frac({"NATURALEZACARGA": "Refrigerada"}, {"NATURALEZACARGA": "Carga Normal"}, ">")
chk("5.1 refrigerada da más riesgo que carga normal", f > 0.95, f"en {f:.0%} de los viajes; +{m*100:.1f} pts mediana")
f, m = frac({"KILOGRAMOS": 500.0}, {"KILOGRAMOS": 9000.0}, ">")
chk("5.2 500 kg da más riesgo que 9.000 kg", f > 0.95, f"en {f:.0%}; +{m*100:.1f} pts")
f, m = frac({"KILOMETROS": 450.0}, {"KILOMETROS": 100.0}, ">")
chk("5.3 450 km da más riesgo que 100 km", f > 0.95, f"en {f:.0%}; +{m*100:.1f} pts")

# 6. Latencia
t = []
for i in range(200):
    t0 = time.perf_counter(); modelo.predict_proba(X.iloc[[i]]); t.append(time.perf_counter() - t0)
t0 = time.perf_counter(); modelo.predict_proba(pd.concat([X] * 3).iloc[:10000]); tl = time.perf_counter() - t0
chk("6.1 latencia por oferta < 100 ms", np.median(t) < 0.1, f"mediana {np.median(t)*1000:.1f} ms, p95 {np.percentile(t,95)*1000:.1f} ms")
chk("6.2 10.000 ofertas en < 5 s", tl < 5, f"{tl:.2f} s")
chk("6.3 tamaño del modelo < 5 MB", (APP / "modelo_final.joblib").stat().st_size < 5e6, f"{(APP / 'modelo_final.joblib').stat().st_size/1e3:.0f} KB")

# 7. Funciones de la app
import datos_app as da
mun = da.cargar_municipios()
def municipio(cod):
    r = mun[mun["cod_municipio"] == cod].iloc[0]; return r
bog, med = municipio(11001), municipio(5001)
km, oficial = da.km_ruta(bog, med)
chk("7.1 Bogotá-Medellín usa la distancia oficial SICE-TAC", oficial and 400 <= km <= 460, f"{km} km, oficial={oficial}")
lejos = mun.iloc[-1]
km2, of2 = da.km_ruta(bog, lejos)
chk("7.2 ruta sin distancia oficial se estima", km2 > 0, f"{lejos['nombre_municipio'] if 'nombre_municipio' in mun else ''}: {km2} km, oficial={of2}")
chk("7.3 semáforo: rojo en el umbral, ámbar justo debajo, verde lejos",
    da.nivel(0.44, 0.44) == "rojo" and da.nivel(0.40, 0.44) == "ambar" and da.nivel(0.2, 0.44) == "verde")
chk("7.4 frase de frecuencia en bordes", all(isinstance(da.frase_frecuencia(p, html=False), str) for p in [0, 0.04, 0.05, 0.62, 0.96, 1]),
    " | ".join(da.frase_frecuencia(p, html=False)[-45:] for p in [0.0, 0.619, 1.0]))
for f in ["ofertas_semana_transportador.csv", "ofertas_cooperativa.csv"]:
    df = da.leer_csv(APP / "ejemplos" / f); Xo, vista, err = da.preparar_ofertas(df)
    ok = Xo is not None and len(Xo) == len(df) and not err
    res = da.evaluar(modelo, Xo, vista, meta["umbral_costo"]) if Xo is not None else None
    chk(f"7.5 archivo de ejemplo {f}", ok and res is not None and res["prob_no_rentable"].is_monotonic_increasing,
        f"{len(df)} filas, {0 if Xo is None else len(Xo)} válidas, errores={err[:2]}; semáforos {dict(res['semaforo'].value_counts()) if res is not None else '-'}")
X2, v2, e2 = da.preparar_ofertas(pd.DataFrame({"a": [1], "b": [2]}))
chk("7.6 CSV con columnas equivocadas -> mensaje claro", X2 is None and e2 and "Faltan columnas" in e2[0], e2[0][:70] if e2 else "")
X3, v3, e3 = da.preparar_ofertas(pd.DataFrame({"Origen": ["Ciudad Inventada"], "Destino": ["Medellín (Antioquia)"], "Kilos": [5000], "Mercancia": ["Menajes"]}))
chk("7.7 municipio inexistente -> fila rechazada con mensaje", X3 is None and e3 and "origen" in e3[0], e3[0][:70] if e3 else "")
ej = da.leer_csv(APP / "ejemplo_lote.csv"); Xe, ve, ee = da.preparar_ofertas(ej)
pe = modelo.predict_proba(Xe)[:, 0].round(3).tolist()
chk("7.8 ejemplo_lote.csv da las mismas probabilidades de siempre", pe == [0.555, 0.619, 0.48, 0.362, 0.119], str(pe))

# 8. App completa con streamlit AppTest
from streamlit.testing.v1 import AppTest
def app_ok(at, nombre, extra=""):
    exc = [str(e.value)[:120] for e in at.exception]
    chk(nombre, not exc, (extra + " " + ("; ".join(exc) if exc else "sin excepciones")).strip())
t0 = time.perf_counter(); at = AppTest.from_file(str(APP / "app.py"), default_timeout=120).run(); t_app = time.perf_counter() - t0
app_ok(at, "8.1 la app abre", f"primer render {t_app:.1f} s")
textos = " ".join(m.value for m in at.markdown)
chk("8.2 muestra el resultado por defecto (semáforo y frase)", "De cada 10 viajes" in textos)
for etiqueta in at.radio[0].options:
    at.radio[0].set_value(etiqueta).run(); app_ok(at, f"8.3 umbral '{etiqueta[:28]}'")
at.radio[0].set_value(at.radio[0].options[0]).run()
sel_nat = next(s for s in at.selectbox if "carga" in s.label.lower())
sel_nat.set_value("Refrigerada").run(); app_ok(at, "8.4 carga refrigerada", "valor interno 'Refrigerada'")
txt_r = " ".join(m.value for m in at.markdown); chk("8.4b la app explica el factor refrigerada", "refrigerada" in txt_r.lower())
ni = next(n for n in at.number_input if "ilómetros" in n.label)
ni.set_value(2900.0).run(); txt = " ".join([w.value for w in at.warning] + [m.value for m in at.markdown])
app_ok(at, "8.5 km fuera de rango (2.900)", "con aviso" if ("fuera" in txt.lower() or "rango" in txt.lower() or "no vio" in txt.lower()) else "SIN aviso visible")
for b in at.button:
    if b.key in ("btn_media", "btn_completa"):
        b.click().run(); app_ok(at, f"8.6 botón {b.label}")
cmp_btn = next(b for b in at.button if b.key == "btn_comparar")
cmp_btn.click().run(); app_ok(at, "8.7 comparador de ofertas")

print("\nRESUMEN:", sum(ok for _, ok, _ in RES), "de", len(RES), "pruebas OK")
json.dump([{"prueba": n, "ok": o, "detalle": d} for n, o, d in RES], open(Path(sys.argv[2]), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
