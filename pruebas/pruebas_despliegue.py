"""Pruebas de despliegue del modelo y de la app RutaRentable, sobre el paquete entregado.
Se ejecuta con SOLO las dependencias de app/requirements.txt."""
import sys, os, json, time, platform, warnings, importlib
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

PKG = Path(sys.argv[1]).resolve(); APP = PKG / "app"
# Carpeta de datos: tercer argumento opcional; si no, <paquete>/datos; si no existe, ../3. Entrega 2 (corregida)/datos
_cand = ([Path(sys.argv[3]).resolve()] if len(sys.argv) > 3 else []) + [PKG / "datos", PKG.parent / "3. Entrega 2 (corregida)" / "datos"]
DATOS = next((p for p in _cand if (p / "conjunto_prueba_reservado.csv").exists()), _cand[0])
print("Datos:", DATOS)
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
te = pd.read_csv(DATOS / "conjunto_prueba_reservado.csv"); X, y = te[COLS], te["RENTABLE"].values
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

# 9. Guía de negociación (costo de referencia, mercado y oferta; nada de esto entra al modelo)
sic = pd.read_csv(DATOS / "sicetac_costos_c2_dic2025.csv")
def fuente(o, d):
    f = sic[(sic["ORIGEN"] == o * 1000) & (sic["DESTINO"] == d * 1000)]
    return f.iloc[0] if len(f) else None
co = da.costo_referencia(11001, 5001, "Carga Normal")
src = fuente(11001, 5001) if fuente(11001, 5001) is not None else fuente(5001, 11001)
chk("9.1 Bogotá-Medellín tiene costo de referencia = COSTO_GENERAL del SICE-TAC", co is not None and src is not None
    and co["costo"] == round(src["COSTO_GENERAL"]), f"{da.pesos(co['costo']) if co else '-'} ({co['km'] if co else '-'} km, "
    f"{co['horas'] if co else '-'} h logísticas, sentido invertido={co['invertida'] if co else '-'})")
cr = da.costo_referencia(11001, 5001, "Refrigerada")
chk("9.2 carga refrigerada usa COSTO_REFRIGERADA", cr is not None and cr["costo"] == round(src["COSTO_REFRIGERADA"])
    and cr["costo"] > co["costo"], f"{da.pesos(cr['costo']) if cr else '-'}")
me = da.mercado(11001, 5001, "BOGOTA D. C.", "ANTIOQUIA", 429)
chk("9.3 Bogotá-Medellín tiene rango de mercado con n >= 5", me is not None and me["n"] >= 5 and me["p25"] <= me["mediana"] <= me["p75"],
    f"n={me['n'] if me else '-'}, {da.pesos(me['p25']) if me else '-'} a {da.pesos(me['p75']) if me else '-'}, base={me['nivel'] if me else '-'}")
vb, va = da.veredicto(co["costo"] - 250000, co, me), da.veredicto(co["costo"] + 400000, co, me)
chk("9.4 oferta por debajo del costo -> no cubre", vb["cubre"] is False and "no cubre" in vb["frase"] and vb["nivel"] == "rojo", vb["frase"][:110])
chk("9.5 oferta por encima del costo -> cubre", va["cubre"] is True and "cubre" in va["frase"] and "no cubre" not in va["frase"], va["frase"][:110])
chk("9.6 sin oferta no hay veredicto", da.veredicto(None, co, me) is None and da.veredicto("", co, me) is None)
cost_tab = da.cargar_costos(); cods = mun["cod_municipio"].astype(int).tolist()
sin = next((o, d) for o in cods for d in cods if o != d and (o, d) not in cost_tab and (d, o) not in cost_tab)
chk("9.7 ruta sin costo -> None y mensaje de 'no hay costo'", da.costo_referencia(*sin, "Carga Normal") is None
    and "No hay costo de referencia" in da.SIN_COSTO and "sicetac.mintransporte.gov.co" in da.SIN_COSTO, f"par {sin}")
# En el SICE-TAC de diciembre de 2025 todos los pares vienen en los dos sentidos; se simula que falta uno
from unittest import mock
n_un_sentido = sum(1 for (o, d) in cost_tab if (d, o) not in cost_tab)
sin_ida = {k: v for k, v in cost_tab.items() if k != (11001, 5001)}
with mock.patch.object(da, "cargar_costos", return_value=sin_ida):
    ci = da.costo_referencia(11001, 5001, "Carga Normal")
chk("9.8 si falta el sentido pedido se usa el contrario (y se marca)", ci is not None and ci["invertida"] and ci["costo"] == cost_tab[(5001, 11001)][2],
    f"Bogotá->Medellín simulado sin dato: usa Medellín->Bogotá {da.pesos(ci['costo']) if ci else '-'}; pares en un solo sentido en la tabla: {n_un_sentido}")
cober = sum(1 for o, d in cost_tab) ; mer_mun, mer_dep = da.cargar_mercado()
chk("9.9 tablas de la guía pequeñas (< 2 MB)", all((APP / f).stat().st_size < 2e6 for f in ("costos_rutas.csv", "mercado_rutas.csv")),
    f"{cober} rutas con costo, {len(mer_mun)} pares de municipios y {sum(len(v) for v in mer_dep.values())} grupos depto-km con mercado")
for f in ["ofertas_semana_transportador.csv", "ofertas_cooperativa.csv"]:
    df = da.leer_csv(APP / "ejemplos" / f); Xo, vista, err = da.preparar_ofertas(df)
    res = da.evaluar(modelo, Xo, vista, meta["umbral_costo"])
    nuevas = ["costo_referencia", "mercado_p25", "mercado_mediana", "mercado_p75", "cubre_costo", "diferencia_vs_costo", "posicion_mercado"]
    con = int(res["pago_ofrecido"].notna().sum()); vc = res["cubre_costo"].value_counts().to_dict()
    ok = (list(Xo.columns) == COLS and all(c in res.columns for c in nuevas) and con == int(df.iloc[:, -1].notna().sum())
          and {"Sí", "No"} <= set(vc) and res["costo_referencia"].notna().all() and res["prob_no_rentable"].is_monotonic_increasing
          and np.allclose(res.sort_index()["prob_no_rentable"].sort_values().values, np.sort(modelo.predict_proba(Xo)[:, 0].round(4))))
    chk(f"9.10 {f} con columna de oferta", ok, f"{con} con valor; cubre_costo {vc}; posición {res['posicion_mercado'].value_counts().to_dict()}")
ej = da.leer_csv(APP / "ejemplo_lote.csv"); Xe, ve, ee = da.preparar_ofertas(ej)
ej2 = ej.assign(PAGO_OFRECIDO=[1, 5_000_000, None, 99_999_999, 2_000_000]); Xe2, _, _ = da.preparar_ofertas(ej2)
pe, pe2 = modelo.predict_proba(Xe)[:, 0].round(3).tolist(), modelo.predict_proba(Xe2)[:, 0].round(3).tolist()
chk("9.11 ejemplo_lote.csv: mismas probabilidades, con o sin columna de oferta", pe == pe2 == [0.555, 0.619, 0.48, 0.362, 0.119]
    and list(Xe2.columns) == COLS, str(pe2))
at2 = AppTest.from_file(str(APP / "app.py"), default_timeout=120).run()
p_antes = next(m.value for m in at2.markdown if "De cada 10 viajes" in m.value)
oi = next(n for n in at2.number_input if "te ofrecen" in n.label.lower())
oi.set_value(int(co["costo"] - 250000)).run(); txt = " ".join(m.value for m in at2.markdown)
app_ok(at2, "9.12 app: oferta por debajo del costo", "dice 'no cubre'" if "no cubre el costo de referencia" in txt else "SIN veredicto")
p_despues = next(m.value for m in at2.markdown if "De cada 10 viajes" in m.value)
chk("9.13 app: la oferta no cambia el riesgo", p_antes == p_despues and "no cubre el costo de referencia" in txt and "Pide al menos" in txt)
oi.set_value(int(co["costo"] + 400000)).run(); txt = " ".join(m.value for m in at2.markdown)
app_ok(at2, "9.14 app: oferta por encima del costo", "dice 'cubre'" if "cubre el costo de referencia con" in txt else "SIN veredicto")
cmp2 = next(b for b in at2.button if b.key == "btn_comparar"); cmp2.click().run()
txt = " ".join(m.value for m in at2.markdown) + " ".join(w.value for w in at2.warning)
app_ok(at2, "9.15 comparador con valor ofrecido", "marca 'No cubre el costo'" if "No cubre el costo" in txt else "SIN marca")
chk("9.16 comparador: la fila con oferta baja queda marcada", "No cubre el costo" in txt and "no cubre (−$" in txt)

print("\nRESUMEN:", sum(ok for _, ok, _ in RES), "de", len(RES), "pruebas OK")
json.dump([{"prueba": n, "ok": o, "detalle": d} for n, o, d in RES], open(Path(sys.argv[2]), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
