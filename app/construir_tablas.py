"""Construye una sola vez las tablas de consulta de la app.

Las tablas que usa el modelo (municipios, mercancías, distancias) no usan pagos ni costos. Las de la guía de
negociación (costos_rutas.csv y mercado_rutas.csv) sí los usan, pero solo se muestran al usuario: nunca entran
al modelo.

Ejecutar desde la carpeta app:
    uv run --no-project --python 3.12 --with pandas,numpy -- python construir_tablas.py

Salidas: municipios.csv, mercancias.csv, distancias_rutas.csv, costos_rutas.csv, mercado_rutas.csv y ejemplos/*.csv
"""
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

APP = Path(__file__).parent
RAIZ = APP.parent.parent


def buscar(nombre, *alternativas):
    """Busca primero en ../datos (estructura del repositorio) y luego en la del proyecto original."""
    for p in (APP.parent / "datos" / nombre, *alternativas):
        if p.exists():
            return p
    raise FileNotFoundError(f"No se encontró {nombre}; póngalo en la carpeta datos/.")


F_AUDITORIA = buscar("dataset_auditoria_dic2025.csv", RAIZ / "3. Entrega 2 (corregida)" / "datos" / "dataset_auditoria_dic2025.csv")
F_SICETAC = buscar("sicetac_costos_c2_dic2025.csv", RAIZ / "3. Entrega 2 (corregida)" / "datos" / "sicetac_costos_c2_dic2025.csv")
F_DIVIPOLA = buscar("divipola_centroides.csv", RAIZ / "2. Entrega 1" / "Base de datos" / "divipola_centroides.csv")
MENORES = {"De", "Del", "La", "Las", "Los", "Y", "El", "En"}


def sin_tildes(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c))


def depto_modelo(nombre):
    """Nombre del departamento como lo conoce el modelo: sin tildes, mayúsculas, 'BOGOTA D. C.'."""
    d = re.sub(r"\s+", " ", sin_tildes(nombre).upper().strip())
    if d.startswith("BOGOTA"):
        return "BOGOTA D. C."
    return d


def bonito(nombre):
    pal = str(nombre).strip().title().split()
    pal = [p.lower() if (i > 0 and p in MENORES) else p for i, p in enumerate(pal)]
    return " ".join(pal).replace("D.c.", "D.C.")


def limpiar_mercancia(m, largo=80):
    m = re.sub(r"\s*;\s*", ", ", str(m))
    m = re.sub(r"\s+", " ", m).strip(" ,.;")
    m = m.replace("( ", "(").replace(" )", ")")
    if len(m) > largo:
        m = m[:largo].rsplit(" ", 1)[0].rstrip(" ,;(") + "..."
    return m[:1].upper() + m[1:].lower()


def moda(s):
    return s.value_counts().index[0]


# ---------------- Municipios ----------------
div = pd.read_csv(F_DIVIPOLA, encoding="utf-8")
div["departamento"] = div["nombre_depto"].map(depto_modelo)
div["depto_bonito"] = div["nombre_depto"].map(bonito)
div.loc[div["departamento"] == "BOGOTA D. C.", "depto_bonito"] = "Bogotá, D.C."
div.loc[div["departamento"].str.startswith("ARCHIPIELAGO"), "depto_bonito"] = "San Andrés y Providencia"
# Nombres de uso común en carretera en lugar del nombre oficial largo
COMUNES = {76001: "Cali", 13001: "Cartagena", 54001: "Cúcuta", 76111: "Buga", 52835: "Tumaco",
           73443: "Mariquita", 70820: "Tolú", 25843: "Ubaté"}
div["municipio"] = [COMUNES.get(c, bonito(m)) for c, m in zip(div["cod_municipio"], div["nombre_municipio"])]
div["etiqueta"] = [f"{m} ({d})" for m, d in zip(div["municipio"], div["depto_bonito"])]
div.loc[div["departamento"] == "BOGOTA D. C.", "etiqueta"] = "Bogotá, D.C."
assert div["etiqueta"].is_unique, div[div["etiqueta"].duplicated(keep=False)]
mun = div[["cod_municipio", "etiqueta", "departamento", "longitud", "latitud"]].copy()
mun["longitud"] = mun["longitud"].round(5)
mun["latitud"] = mun["latitud"].round(5)
mun = mun.sort_values("etiqueta", key=lambda s: s.map(sin_tildes)).reset_index(drop=True)
mun.to_csv(APP / "municipios.csv", index=False, encoding="utf-8")

# ---------------- Mercancías ----------------
aud = pd.read_csv(F_AUDITORIA, usecols=["MERCANCIA", "CAPITULO", "NATURALEZACARGA",
                                        "CODMUNICIPIOORIGEN", "CODMUNICIPIODESTINO"], low_memory=False)
aud["mercancia"] = aud["MERCANCIA"].map(limpiar_mercancia)
mer = (aud.groupby("mercancia")
       .agg(capitulo=("CAPITULO", moda), naturaleza=("NATURALEZACARGA", moda), viajes=("CAPITULO", "size"))
       .reset_index().sort_values(["viajes", "mercancia"], ascending=[False, True]).reset_index(drop=True))
mer.to_csv(APP / "mercancias.csv", index=False, encoding="utf-8")

# ---------------- Distancias oficiales (solo km) ----------------
sic = pd.read_csv(F_SICETAC, usecols=["ORIGEN", "DESTINO", "KM_SICETAC"], low_memory=False).dropna()
sic["origen"] = (sic["ORIGEN"] // 1000).astype(int)
sic["destino"] = (sic["DESTINO"] // 1000).astype(int)
sic["km"] = sic["KM_SICETAC"].round().astype(int)
dist = (sic[sic["km"] > 0].groupby(["origen", "destino"], as_index=False)["km"].median()
        .astype(int).sort_values(["origen", "destino"]))
dist.to_csv(APP / "distancias_rutas.csv", index=False)

cods = set(mun["cod_municipio"])
print("municipios:", len(mun), "| deptos:", mun["departamento"].nunique())
print("mercancias:", len(mer), "| capitulos:", mer["capitulo"].nunique())
print("rutas con km oficial:", len(dist),
      "| codigos SICE-TAC sin municipio DIVIPOLA:", len((set(dist.origen) | set(dist.destino)) - cods))
par = dist.set_index(["origen", "destino"])["km"]
print("Bogota-Medellin:", par.get((11001, 5001)), "| Medellin-Bogota:", par.get((5001, 11001)))
print("codigos RNDC sin municipio:", len((set(aud.CODMUNICIPIOORIGEN // 1000) | set(aud.CODMUNICIPIODESTINO // 1000)) - cods))

# ---------------- Guía de negociación (solo se muestra; nunca entra al modelo) ----------------
# Costo de referencia SICE-TAC por par dirigido de municipios (códigos DIVIPOLA de 5 dígitos)
# El SICE-TAC trae algunos centros poblados (código que no termina en 000). Se usa la fila de las cabeceras
# municipales; si un par solo tiene centros poblados, se toma la mediana de esas filas.
cos = pd.read_csv(F_SICETAC, usecols=["ORIGEN", "DESTINO", "KM_SICETAC", "HORAS_LOGISTICAS",
                                      "COSTO_GENERAL", "COSTO_REFRIGERADA"]).dropna()
cos["origen"], cos["destino"] = (cos["ORIGEN"] // 1000).astype(int), (cos["DESTINO"] // 1000).astype(int)
cos["cabecera"] = (cos["ORIGEN"] % 1000 == 0) & (cos["DESTINO"] % 1000 == 0)
VAL = ["KM_SICETAC", "HORAS_LOGISTICAS", "COSTO_GENERAL", "COSTO_REFRIGERADA"]
cab = cos[cos["cabecera"]].drop_duplicates(["origen", "destino"])
resto = cos[~cos["cabecera"]].groupby(["origen", "destino"], as_index=False)[VAL].median()
resto = resto[~resto.set_index(["origen", "destino"]).index.isin(cab.set_index(["origen", "destino"]).index)]
cos = pd.concat([cab[["origen", "destino"] + VAL], resto], ignore_index=True)
costos = pd.DataFrame({"origen": cos["origen"], "destino": cos["destino"],
                       "km": cos["KM_SICETAC"].round().astype(int), "horas_logisticas": cos["HORAS_LOGISTICAS"].round().astype(int),
                       "costo_general": cos["COSTO_GENERAL"].round().astype(int),
                       "costo_refrigerada": cos["COSTO_REFRIGERADA"].round().astype(int)})
costos = costos.sort_values(["origen", "destino"]).reset_index(drop=True)
costos.to_csv(APP / "costos_rutas.csv", index=False)

# Mercado: lo que de verdad se pagó (RNDC) por par de municipios y, de respaldo, por par de departamentos y banda de km
MIN_VIAJES = 5
BANDAS_KM = [0, 50, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1500, 3000]
pag = pd.read_csv(F_AUDITORIA, usecols=["CODMUNICIPIOORIGEN", "CODMUNICIPIODESTINO", "DEPARTAMENTOORIGEN",
                                        "DEPARTAMENTODESTINO", "KILOMETROS", "KILOGRAMOS", "VALORESPAGADOS"],
                  low_memory=False)
pag["o"] = (pag["CODMUNICIPIOORIGEN"] // 1000).astype(int).astype(str)
pag["d"] = (pag["CODMUNICIPIODESTINO"] // 1000).astype(int).astype(str)
pag["banda"] = pd.cut(pag["KILOMETROS"], BANDAS_KM, right=False, labels=False)
RESUMEN = dict(n=("VALORESPAGADOS", "size"), p25=("VALORESPAGADOS", lambda v: v.quantile(.25)),
               mediana=("VALORESPAGADOS", "median"), p75=("VALORESPAGADOS", lambda v: v.quantile(.75)),
               kg_mediana=("KILOGRAMOS", "median"))
m_mun = pag.groupby(["o", "d"]).agg(**RESUMEN).reset_index().rename(columns={"o": "origen", "d": "destino"})
m_mun["nivel"], m_mun["km_min"], m_mun["km_max"] = "municipios", np.nan, np.nan
m_dep = (pag.dropna(subset=["banda"]).groupby(["DEPARTAMENTOORIGEN", "DEPARTAMENTODESTINO", "banda"])
         .agg(**RESUMEN).reset_index()
         .rename(columns={"DEPARTAMENTOORIGEN": "origen", "DEPARTAMENTODESTINO": "destino"}))
m_dep["nivel"] = "departamentos"
m_dep["km_min"] = [BANDAS_KM[int(b)] for b in m_dep["banda"]]
m_dep["km_max"] = [BANDAS_KM[int(b) + 1] for b in m_dep["banda"]]
mercado = pd.concat([m_mun, m_dep.drop(columns="banda")], ignore_index=True)
mercado = mercado[mercado["n"] >= MIN_VIAJES]
for c in ("p25", "mediana", "p75", "kg_mediana"):
    mercado[c] = mercado[c].round().astype(int)
mercado = mercado[["nivel", "origen", "destino", "km_min", "km_max", "n", "p25", "mediana", "p75", "kg_mediana"]]
mercado.to_csv(APP / "mercado_rutas.csv", index=False)

print("rutas con costo de referencia:", len(costos))
n_mun = (mercado["nivel"] == "municipios")
print("mercado: pares de municipios con >= 5 viajes:", int(n_mun.sum()), "(", round(mercado.loc[n_mun, "n"].sum() / len(pag) * 100, 1),
      "% de los viajes) | grupos departamento y banda de km:", int((~n_mun).sum()), "(",
      round(mercado.loc[~n_mun, "n"].sum() / len(pag) * 100, 1), "% de los viajes)")
for f in ("municipios.csv", "mercancias.csv", "distancias_rutas.csv", "costos_rutas.csv", "mercado_rutas.csv"):
    print(f, round((APP / f).stat().st_size / 1024), "KB")

# ---------------- Archivos de ejemplo (simulados, semilla 42) ----------------
rng = np.random.default_rng(42)
(APP / "ejemplos").mkdir(exist_ok=True)
CIUDADES = [11001, 5001, 76001, 8001, 13001, 68001, 54001, 66001, 17001, 73001, 50001, 15001, 41001,
            52001, 23001, 47001, 20001, 63001, 76109, 25473, 5360, 76520, 25269, 15238, 68081]
CIUDADES = [c for c in CIUDADES if c in cods]
et = mun.set_index("cod_municipio")["etiqueta"]
dep = mun.set_index("cod_municipio")["departamento"]
pares = [(o, d) for o in CIUDADES for d in CIUDADES if o != d and (o, d) in par.index]
top = mer[~mer["mercancia"].str.startswith("Sin descripcion")].head(60).reset_index(drop=True)
KILOS = [500, 1200, 2000, 3000, 4500, 5000, 6000, 7500, 9000, 10000]


def simular(n):
    filas = []
    for i in rng.choice(len(pares), size=n, replace=False):
        o, d = pares[i]
        m = top.iloc[int(rng.integers(len(top)))]
        filas.append({"o": o, "d": d, "km": int(par[(o, d)]), "kg": int(rng.choice(KILOS)),
                      "mercancia": m["mercancia"], "capitulo": m["capitulo"], "naturaleza": m["naturaleza"]})
    return pd.DataFrame(filas)


s = simular(8)
c = simular(40)
costo_par = costos.set_index(["origen", "destino"])


def ofertas(t, con_valor):
    """Valor ofrecido simulado alrededor del costo de referencia de la ruta (unas por debajo y otras por encima).
    Se sortea después de las ofertas para no cambiar las filas de los ejemplos."""
    factor = np.clip(rng.normal(1.08, 0.18, len(t)), 0.7, 1.5)
    usar = rng.random(len(t)) < con_valor
    out = []
    for (o, d, nat), f, u in zip(t[["o", "d", "naturaleza"]].itertuples(index=False), factor, usar):
        fila = costo_par.loc[(o, d)]
        base = fila["costo_refrigerada"] if nat == "Refrigerada" else fila["costo_general"]
        out.append(int(round(base * f / 10000) * 10000) if u else None)
    return pd.array(out, dtype="Int64")


pd.DataFrame({"Origen": s["o"].map(et), "Destino": s["d"].map(et), "Kilos": s["kg"],
              "Mercancia": s["mercancia"], "Te ofrecen": ofertas(s, 0.75)}).to_csv(
    APP / "ejemplos" / "ofertas_semana_transportador.csv", index=False, encoding="utf-8-sig")
pd.DataFrame({"KILOMETROS": c["km"], "KILOGRAMOS": c["kg"], "CAPITULO": c["capitulo"],
              "NATURALEZACARGA": c["naturaleza"], "DEPARTAMENTOORIGEN": c["o"].map(dep),
              "DEPARTAMENTODESTINO": c["d"].map(dep), "CODMUNICIPIOORIGEN": c["o"], "CODMUNICIPIODESTINO": c["d"],
              "PAGO_OFRECIDO": ofertas(c, 0.7)}).to_csv(APP / "ejemplos" / "ofertas_cooperativa.csv", index=False)
print("ejemplos listos:", len(s), len(c))
