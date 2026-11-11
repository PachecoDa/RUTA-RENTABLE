"""Construye una sola vez las tablas de consulta de la app (no usa pagos ni costos).

Ejecutar desde la carpeta app:
    uv run --no-project --python 3.12 --with pandas,numpy -- python construir_tablas.py

Salidas: municipios.csv, mercancias.csv, distancias_rutas.csv y ejemplos/*.csv
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
for f in ("municipios.csv", "mercancias.csv", "distancias_rutas.csv"):
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
pd.DataFrame({"Origen": s["o"].map(et), "Destino": s["d"].map(et), "Kilos": s["kg"],
              "Mercancia": s["mercancia"]}).to_csv(APP / "ejemplos" / "ofertas_semana_transportador.csv",
                                                   index=False, encoding="utf-8-sig")
c = simular(40)
pd.DataFrame({"KILOMETROS": c["km"], "KILOGRAMOS": c["kg"], "CAPITULO": c["capitulo"],
              "NATURALEZACARGA": c["naturaleza"], "DEPARTAMENTOORIGEN": c["o"].map(dep),
              "DEPARTAMENTODESTINO": c["d"].map(dep)}).to_csv(APP / "ejemplos" / "ofertas_cooperativa.csv", index=False)
print("ejemplos listos:", len(s), len(c))
