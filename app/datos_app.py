"""Tablas de consulta y funciones de apoyo de RutaRentable. No cambia la lógica del modelo."""
import math
import re
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st

BASE = Path(__file__).parent
COLS = ["KILOMETROS", "KILOGRAMOS", "CAPITULO", "NATURALEZACARGA",
        "DEPARTAMENTOORIGEN", "DEPARTAMENTODESTINO"]
MARGEN_AMBAR = 0.08      # franja "cerca del límite" por debajo del umbral
FACTOR_VIA = 1.3         # de línea recta a carretera
CAPACIDAD_KG = 10000
NATURALEZA_TXT = {
    "Carga Normal": "Carga normal (seca)",
    "Refrigerada": "Refrigerada (con frío)",
    "Carga Peligrosa": "Carga peligrosa",
    "Desechos Peligrosos": "Desechos peligrosos",
    "Semovientes": "Semovientes (animales vivos)",
}


def sin_tildes(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c))


def norm(s):
    """Texto comparable: sin tildes, en mayúsculas y solo letras y números."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c)).upper()
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


def miles(x, d=0):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, d=0):
    return f"{x * 100:.{d}f} %".replace(".", ",")


# ---------------- Carga de tablas ----------------
@st.cache_data
def cargar_municipios():
    return pd.read_csv(BASE / "municipios.csv", encoding="utf-8")


@st.cache_data
def cargar_mercancias():
    return pd.read_csv(BASE / "mercancias.csv", encoding="utf-8")


@st.cache_data
def cargar_distancias():
    d = pd.read_csv(BASE / "distancias_rutas.csv")
    return {(int(o), int(t)): int(k) for o, t, k in d.itertuples(index=False)}


@st.cache_data
def cargar_centroides():
    ruta = BASE / "deptos_centroides.csv"
    if not ruta.exists():
        return {}
    d = pd.read_csv(ruta)
    return {r.departamento: (float(r.longitud), float(r.latitud)) for r in d.itertuples()}


@st.cache_data
def indices():
    """Diccionarios de búsqueda: municipio por etiqueta y por texto normalizado, mercancía por nombre."""
    mun, mer = cargar_municipios(), cargar_mercancias()
    por_etiqueta = {r["etiqueta"]: r for r in mun.to_dict("records")}
    por_norm = {norm(e): e for e in mun["etiqueta"]}
    solo = mun.assign(n=mun["etiqueta"].str.split(" (", regex=False).str[0].map(norm))
    unicos = solo[~solo["n"].duplicated(keep=False)]
    for n, e in zip(unicos["n"], unicos["etiqueta"]):
        por_norm.setdefault(n, e)
    por_norm.setdefault("BOGOTA", "Bogotá, D.C.")
    mer_por_nombre = {r["mercancia"]: r for r in mer.to_dict("records")}
    mer_por_norm = {}
    for m in mer["mercancia"]:
        mer_por_norm.setdefault(norm(m), m)
    return por_etiqueta, por_norm, mer_por_nombre, mer_por_norm


def grupo_capitulo(cap):
    """Frase que explica qué es el capítulo con sus tres mercancías más frecuentes."""
    mer = cargar_mercancias()
    top = mer[(mer["capitulo"] == cap) & (~mer["mercancia"].str.startswith("Sin descripcion"))].head(3)
    nombres = [m if len(m) <= 48 else m[:48].rsplit(" ", 1)[0].rstrip(" ,") + "..." for m in top["mercancia"]]
    num = str(cap).replace("CAP_", "")
    if not nombres:
        return f"Grupo de mercancía (capítulo {num})."
    return f"Grupo de mercancía (capítulo {num}): incluye " + "; ".join(n.lower() for n in nombres) + "."


# ---------------- Distancia ----------------
def haversine(lon1, lat1, lon2, lat2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def km_ruta(mo, md):
    """Kilómetros de la ruta entre dos municipios (registros de municipios.csv).

    Devuelve (km, oficial). Oficial = distancia SICE-TAC; si no existe, línea recta entre centroides por 1,3.
    """
    dist = cargar_distancias()
    o, d = int(mo["cod_municipio"]), int(md["cod_municipio"])
    for par in ((o, d), (d, o)):
        if par in dist:
            return float(dist[par]), True
    est = haversine(mo["longitud"], mo["latitud"], md["longitud"], md["latitud"]) * FACTOR_VIA
    return float(max(10, round(est))), False


# ---------------- Lectura del resultado ----------------
def nivel(p, umbral):
    if p >= umbral:
        return "rojo"
    if p >= umbral - MARGEN_AMBAR:
        return "ambar"
    return "verde"


def de_cada_10(p):
    return int(min(10, max(0, math.floor(10 * p + 0.5))))


def frase_frecuencia(p, html=True):
    n = de_cada_10(p)
    b = (lambda t: f"<b>{t}</b>") if html else (lambda t: str(t))
    if n == 0:
        return "De cada 10 viajes como este, " + b("casi ninguno") + " se quedó sin cubrir el costo."
    if n == 1:
        return "De cada 10 viajes como este, " + b(1) + " no alcanzó a cubrir el costo."
    if n == 10:
        return "De cada 10 viajes como este, " + b("casi los 10") + " no alcanzaron a cubrir el costo."
    return "De cada 10 viajes como este, unos " + b(n) + " no alcanzaron a cubrir el costo."


def factores(km, kg, nat):
    """Dos o tres razones en palabras sencillas, según los hallazgos del estudio. Lista de (tono, texto)."""
    f = []
    if km > 450:
        f.append(("sube", f"<b>Viaje largo ({miles(km)} km).</b> Los viajes de más de 350 km suelen pagarse peor "
                          "frente a su costo: ya pasan de una jornada de 8 horas de manejo."))
    elif km > 350:
        f.append(("sube", f"<b>Distancia de {miles(km)} km.</b> Los viajes de más de 350 km suelen pagarse peor frente "
                          "a su costo. El riesgo pega el salto entre 300 y 450 km, cerca de las 8 horas de manejo."))
    elif km >= 300:
        f.append(("medio", f"<b>Distancia de {miles(km)} km.</b> Está justo donde el riesgo empieza a subir "
                           "(entre 300 y 450 km, cerca de las 8 horas de manejo)."))
    else:
        f.append(("baja", f"<b>Viaje corto ({miles(km)} km).</b> Por debajo de 300 km los viajes suelen cubrir "
                          "mejor su costo."))
    if nat == "Refrigerada":
        f.append(("sube", "<b>Carga refrigerada.</b> Mover carga con frío cuesta más y no siempre se paga: tuvo cerca "
                          "de 3,75 veces las odds de no cubrir el costo frente a la carga normal."))
    if kg <= 2000:
        f.append(("sube", f"<b>Carga liviana ({miles(kg)} kg).</b> Con poco peso el flete suele quedarse corto: "
                          "500 kg tiene 2,69 veces las odds de no cubrir el costo frente a 4.500 kg."))
    elif kg >= 8000:
        f.append(("baja", f"<b>Camión bien cargado ({miles(kg)} kg).</b> Los viajes pesados suelen pagarse mejor: "
                          "10.000 kg tiene apenas 0,15 veces las odds de 4.500 kg."))
    else:
        f.append(("medio", f"<b>Peso medio ({miles(kg)} kg).</b> No ayuda ni perjudica mucho. Si logras completar "
                           "la carga, el riesgo baja."))
    return f


# ---------------- Tablas de ofertas (comparador y archivo) ----------------
def preparar_ofertas(df):
    """Convierte una tabla de ofertas en la entrada del modelo.

    Acepta dos formatos:
      a) las 6 columnas del modelo (KILOMETROS, KILOGRAMOS, CAPITULO, NATURALEZACARGA, DEPARTAMENTOORIGEN,
         DEPARTAMENTODESTINO);
      b) formato sencillo: Origen, Destino (municipios), Kilos, Mercancia; opcionales Kilometros y Naturaleza.
    Devuelve (X, vista, errores): X con las 6 columnas, vista con columnas legibles y errores como lista de textos.
    """
    errores = []
    if df is None or df.dropna(how="all").empty:
        return None, None, ["La tabla no tiene filas."]
    df = df.dropna(how="all").reset_index(drop=True)
    cols = {norm(c): c for c in df.columns}

    if all(c in cols for c in COLS):                      # formato a)
        X = df[[cols[c] for c in COLS]].copy()
        X.columns = COLS
        for c in ("KILOMETROS", "KILOGRAMOS"):
            X[c] = pd.to_numeric(X[c], errors="coerce")
        for c in COLS[2:]:
            X[c] = X[c].astype(str).str.strip()
        vista = pd.DataFrame({
            "Ruta": X["DEPARTAMENTOORIGEN"].str.title() + " a " + X["DEPARTAMENTODESTINO"].str.title(),
            "Detalle": [f"{miles(k) if pd.notna(k) else '?'} km · {miles(g) if pd.notna(g) else '?'} kg · "
                        f"capítulo {c.replace('CAP_', '')} · {n}"
                        for k, g, c, n in zip(X["KILOMETROS"], X["KILOGRAMOS"], X["CAPITULO"], X["NATURALEZACARGA"])],
        })
        return X, vista, errores

    alias = {"ORIGEN": ["ORIGEN", "MUNICIPIO ORIGEN", "MUNICIPIOORIGEN"],
             "DESTINO": ["DESTINO", "MUNICIPIO DESTINO", "MUNICIPIODESTINO"],
             "KILOS": ["KILOS", "KILOGRAMOS", "KG", "PESO"],
             "MERCANCIA": ["MERCANCIA", "PRODUCTO", "CARGA"],
             "KM": ["KILOMETROS", "KM", "DISTANCIA"],
             "NATURALEZA": ["NATURALEZA", "NATURALEZACARGA", "NATURALEZA DE LA CARGA"]}
    col = {k: next((cols[a] for a in v if a in cols), None) for k, v in alias.items()}
    if any(col[k] is None for k in ("ORIGEN", "DESTINO", "KILOS", "MERCANCIA")):
        return None, None, ["Faltan columnas. Usa Origen, Destino, Kilos y Mercancia, o las 6 columnas del modelo: "
                            + ", ".join(COLS) + "."]

    por_etiqueta, por_norm, mer_por_nombre, mer_por_norm = indices()
    nat_norm = {norm(k): k for k in NATURALEZA_TXT} | {norm(v): k for k, v in NATURALEZA_TXT.items()}
    filas, vistas = [], []
    for i, r in df.iterrows():
        eo, ed = por_norm.get(norm(r[col["ORIGEN"]])), por_norm.get(norm(r[col["DESTINO"]]))
        em = mer_por_norm.get(norm(r[col["MERCANCIA"]]))
        kg = pd.to_numeric(r[col["KILOS"]], errors="coerce")
        malos = [t for t, v in (("el origen", eo), ("el destino", ed), ("la mercancía", em)) if v is None]
        if pd.isna(kg) or kg <= 0:
            malos.append("los kilos")
        if malos:
            errores.append(f"Fila {i + 1}: falta o no se reconoce " + ", ".join(malos) + ".")
            continue
        mo, md, m = por_etiqueta[eo], por_etiqueta[ed], mer_por_nombre[em]
        km, oficial = km_ruta(mo, md)
        if col["KM"] is not None:
            km_arch = pd.to_numeric(r[col["KM"]], errors="coerce")
            if pd.notna(km_arch) and km_arch > 0:
                km, oficial = float(km_arch), None
        nat = m["naturaleza"]
        if col["NATURALEZA"] is not None and norm(r[col["NATURALEZA"]]) in nat_norm:
            nat = nat_norm[norm(r[col["NATURALEZA"]])]
        filas.append({"KILOMETROS": km, "KILOGRAMOS": float(kg), "CAPITULO": m["capitulo"], "NATURALEZACARGA": nat,
                      "DEPARTAMENTOORIGEN": mo["departamento"], "DEPARTAMENTODESTINO": md["departamento"]})
        fuente = {True: "km oficiales", False: "km estimados", None: "km del archivo"}[oficial]
        vistas.append({"Ruta": f"{eo.split(' (')[0]} a {ed.split(' (')[0]}",
                       "Detalle": f"{miles(km)} {fuente} · {miles(kg)} kg · {em} · {NATURALEZA_TXT.get(nat, nat)}"})
    if not filas:
        return None, None, errores or ["No hay filas válidas."]
    return pd.DataFrame(filas, columns=COLS), pd.DataFrame(vistas), errores


def leer_csv(fuente):
    """Lee un CSV separado por coma o punto y coma, con o sin BOM."""
    return pd.read_csv(fuente, sep=None, engine="python", encoding="utf-8-sig")


NOMBRE_NIVEL = {"verde": "Verde", "ambar": "Amarillo", "rojo": "Rojo"}


def evaluar(modelo, X, vista, umbral):
    """Aplica el modelo y ordena de mejor a peor. Devuelve la tabla con probabilidad, semáforo y frase."""
    p = modelo.predict_proba(X[COLS])[:, 0]          # P(no cubre el costo)
    out = pd.concat([vista.reset_index(drop=True), X.reset_index(drop=True)], axis=1)
    out["prob_no_rentable"] = p.round(4)
    out["nivel"] = [nivel(v, umbral) for v in p]
    out["semaforo"] = out["nivel"].map(NOMBRE_NIVEL)
    out["de_cada_10_no_cubren"] = [de_cada_10(v) for v in p]
    out["decision"] = ["Pedir más flete o revisar" if v >= umbral else "Aceptar" for v in p]
    return out.sort_values("prob_no_rentable", kind="stable").reset_index(drop=True)
