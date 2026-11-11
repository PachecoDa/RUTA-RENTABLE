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
def cargar_costos():
    """Costo de referencia SICE-TAC (diciembre de 2025) por par dirigido de municipios."""
    d = pd.read_csv(BASE / "costos_rutas.csv")
    return {(int(r.origen), int(r.destino)): (int(r.km), int(r.horas_logisticas), int(r.costo_general),
                                              int(r.costo_refrigerada)) for r in d.itertuples(index=False)}


@st.cache_data
def cargar_mercado():
    """Pagos del RNDC (diciembre de 2025): por par de municipios y, de respaldo, por departamentos y banda de km."""
    d = pd.read_csv(BASE / "mercado_rutas.csv", dtype={"origen": str, "destino": str})
    stats = ["n", "p25", "mediana", "p75", "kg_mediana"]
    mun = d[d["nivel"] == "municipios"]
    por_mun = {(int(o), int(t)): dict(zip(stats, map(int, v)))
               for o, t, *v in mun[["origen", "destino"] + stats].itertuples(index=False)}
    por_dep = {}
    for r in d[d["nivel"] == "departamentos"].to_dict("records"):
        por_dep.setdefault((r["origen"], r["destino"]), []).append(
            {"km_min": int(r["km_min"]), "km_max": int(r["km_max"]), **{s: int(r[s]) for s in stats}})
    return por_mun, por_dep


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


# ---------------- Guía de negociación (nada de esto entra al modelo) ----------------
SICETAC_URL = "https://sicetac.mintransporte.gov.co"
MIN_VIAJES_MERCADO = 5
MARGEN_JUSTO = 0.05      # si la oferta cubre el costo por menos de 5 %, "apenas lo cubre"
SIN_COSTO = ("No hay costo de referencia para esta ruta en el SICE-TAC de diciembre de 2025; consúltalo en "
             "sicetac.mintransporte.gov.co")
SIN_MERCADO = ("No hubo 5 o más viajes parecidos en diciembre de 2025, así que no mostramos un rango de lo que se "
               "paga por esta ruta.")
ALIAS_OFERTA = {"PAGOOFRECIDO", "OFERTA", "TEOFRECEN", "VALOROFRECIDO"}


def pesos(x):
    return "$" + miles(round(x))


def _entero(v):
    try:
        return None if v is None or pd.isna(v) else int(v)
    except (TypeError, ValueError):
        return None


def a_pesos(v):
    """Valor en pesos desde un número o un texto como '$ 1.850.000'. Devuelve None si no hay un valor positivo."""
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    if isinstance(v, str):
        s = re.sub(r"[^\d,.]", "", v)
        if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
            s = re.sub(r"[.,]", "", s)
        s = s.replace(",", ".")
        try:
            v = float(s)
        except ValueError:
            return None
    v = float(v)
    return v if math.isfinite(v) and v > 0 else None


def depto_txt(d):
    return str(d).title().replace("D. C.", "D.C.")


def costo_referencia(cod_o, cod_d, naturaleza):
    """Costo de referencia SICE-TAC de la ruta: el de carga refrigerada si la carga viaja con frío y el general en
    los demás casos (igual que en el estudio). Si el par no está en ese sentido, usa el del sentido contrario.
    Devuelve dict(costo, km, horas, invertida, refrigerada) o None."""
    o, d = _entero(cod_o), _entero(cod_d)
    if o is None or d is None:
        return None
    tabla = cargar_costos()
    for par, invertida in (((o, d), False), ((d, o), True)):
        if par in tabla:
            km, horas, general, refrigerada = tabla[par]
            frio = naturaleza == "Refrigerada"
            return {"costo": refrigerada if frio else general, "km": km, "horas": horas,
                    "invertida": invertida, "refrigerada": frio}
    return None


def mercado(cod_o, cod_d, dep_o, dep_d, km):
    """Rango de lo que se pagó en diciembre de 2025 (RNDC) por viajes parecidos, con al menos 5 viajes.

    Primero el mismo par de municipios; si no alcanza, el mismo par de departamentos y la misma banda de km.
    Devuelve dict(n, p25, mediana, p75, kg_mediana, nivel, base) o None."""
    por_mun, por_dep = cargar_mercado()
    o, d = _entero(cod_o), _entero(cod_d)
    if o is not None and d is not None:
        m = por_mun.get((o, d))
        if m and m["n"] >= MIN_VIAJES_MERCADO:
            return {**m, "nivel": "municipios",
                    "base": f"Basado en {miles(m['n'])} viajes de camión rígido de 2 ejes entre estos municipios en "
                            f"diciembre de 2025, de distintos pesos (peso típico: {miles(m['kg_mediana'])} kg)."}
    km = pd.to_numeric(km, errors="coerce")
    if pd.notna(km):
        for b in por_dep.get((str(dep_o), str(dep_d)), []):
            if b["km_min"] <= km < b["km_max"] and b["n"] >= MIN_VIAJES_MERCADO:
                extra = " Entre estos dos municipios hubo menos de 5 viajes." if o is not None and d is not None else ""
                return {**{k: v for k, v in b.items() if k not in ("km_min", "km_max")}, "nivel": "departamentos",
                        "base": f"Basado en {miles(b['n'])} viajes de camión rígido de 2 ejes de {depto_txt(dep_o)} a "
                                f"{depto_txt(dep_d)}, de {miles(b['km_min'])} a {miles(b['km_max'])} km, en diciembre "
                                f"de 2025, de distintos pesos (peso típico: {miles(b['kg_mediana'])} kg).{extra}"}
    return None


def posicion_mercado(oferta, merc):
    if oferta is None or merc is None:
        return None
    if oferta < merc["p25"]:
        return "debajo de lo usual"
    if oferta > merc["p75"]:
        return "por encima de lo usual"
    return "dentro de lo usual"


def veredicto(oferta, costo, merc):
    """Compara un valor ofrecido contra el costo de referencia y contra el mercado.

    Devuelve dict(cubre, diferencia, porcentaje, posicion, nivel, frase) o None si no hay valor ofrecido.
    nivel: verde, ambar, rojo o neutro (sin costo para comparar)."""
    oferta = a_pesos(oferta)
    if oferta is None:
        return None
    pos = posicion_mercado(oferta, merc)
    if costo is None:
        if pos is None:
            return {"cubre": None, "diferencia": None, "porcentaje": None, "posicion": None, "nivel": "neutro",
                    "frase": "No hay costo de referencia ni datos de mercado para esta ruta. Compara la oferta con el "
                             "valor del SICE-TAC antes de aceptarla."}
        return {"cubre": None, "diferencia": None, "porcentaje": None, "posicion": pos,
                "nivel": "ambar" if pos.startswith("debajo") else "neutro",
                "frase": f"No hay costo de referencia para comparar. Frente a lo que se pagó por viajes así, esta "
                         f"oferta está {pos}."}
    c = costo["costo"]
    dif = oferta - c
    por = abs(dif) / c
    if dif < 0:
        pide = math.ceil(c / 10000) * 10000
        frase = (f"Esta oferta no cubre el costo de referencia: te faltan {pesos(-dif)} ({pct(por)}). "
                 f"Pide al menos {pesos(pide)}.")
        if merc is not None and merc["mediana"] > pide:
            frase += f" Viajes así se pagaron normalmente cerca de {pesos(merc['mediana'])}."
        nivel_v = "rojo"
    elif por < MARGEN_JUSTO:
        frase = (f"Esta oferta apenas cubre el costo de referencia (te quedan {pesos(dif)}, {pct(por)}): cualquier "
                 "imprevisto te deja en pérdida.")
        if merc is not None and merc["mediana"] > oferta:
            frase += f" Viajes así se pagaron normalmente cerca de {pesos(merc['mediana'])}: pide más."
        nivel_v = "ambar"
    else:
        frase = f"Esta oferta cubre el costo de referencia con {pesos(dif)} de margen ({pct(por)})."
        nivel_v = "verde"
        if pos == "debajo de lo usual":
            frase += (f" Pero está por debajo de lo usual para viajes así: puedes pedir cerca de "
                      f"{pesos(merc['mediana'])}.")
            nivel_v = "ambar"
        elif pos == "dentro de lo usual":
            frase += " Además está dentro de lo usual para viajes así."
        elif pos == "por encima de lo usual":
            frase += " Además está por encima de lo usual para viajes así: es una buena oferta."
    return {"cubre": dif >= 0, "diferencia": dif, "porcentaje": por, "posicion": pos, "nivel": nivel_v,
            "frase": frase}


def agregar_guia(out):
    """Agrega costo de referencia, mercado y veredicto a la tabla de resultados (después de usar el modelo)."""
    filas = []
    for r in out.to_dict("records"):
        co = costo_referencia(r.get("cod_origen"), r.get("cod_destino"), r["NATURALEZACARGA"])
        me = mercado(r.get("cod_origen"), r.get("cod_destino"), r["DEPARTAMENTOORIGEN"], r["DEPARTAMENTODESTINO"],
                     r["KILOMETROS"])
        of = a_pesos(r.get("pago_ofrecido"))
        v = veredicto(of, co, me)
        filas.append({
            "pago_ofrecido": None if of is None else round(of),
            "costo_referencia": None if co is None else co["costo"],
            "mercado_p25": None if me is None else me["p25"],
            "mercado_mediana": None if me is None else me["mediana"],
            "mercado_p75": None if me is None else me["p75"],
            "mercado_viajes": None if me is None else me["n"],
            "cubre_costo": "sin dato" if v is None or v["cubre"] is None else ("Sí" if v["cubre"] else "No"),
            "diferencia_vs_costo": None if v is None or v["diferencia"] is None else round(v["diferencia"]),
            "posicion_mercado": "sin dato" if v is None or v["posicion"] is None else v["posicion"],
        })
    g = pd.DataFrame(filas, index=out.index)
    for c in ("pago_ofrecido", "costo_referencia", "mercado_p25", "mercado_mediana", "mercado_p75", "mercado_viajes",
              "diferencia_vs_costo"):
        g[c] = pd.array(g[c].tolist(), dtype="Int64")
    base = out.drop(columns=[c for c in ("cod_origen", "cod_destino", "pago_ofrecido") if c in out.columns])
    return pd.concat([base, g], axis=1)


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
    # Valor ofrecido (opcional): solo para la guía de negociación, nunca entra al modelo
    col_oferta = next((c for n, c in cols.items() if n.replace(" ", "") in ALIAS_OFERTA), None)
    ofertas = [a_pesos(v) for v in df[col_oferta]] if col_oferta is not None else [None] * len(df)

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
        # Municipios opcionales (código DIVIPOLA o nombre) para el costo de referencia y el mercado de la ruta exacta
        for lado, alias in (("cod_origen", ("CODMUNICIPIOORIGEN", "MUNICIPIOORIGEN", "ORIGEN")),
                            ("cod_destino", ("CODMUNICIPIODESTINO", "MUNICIPIODESTINO", "DESTINO"))):
            c = next((cols[a] for a in alias if a in cols), None)
            vista[lado] = pd.array([codigo_municipio(v) for v in df[c]] if c is not None else [None] * len(df),
                                   dtype="Int64")
        vista["pago_ofrecido"] = ofertas
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
                       "Detalle": f"{miles(km)} {fuente} · {miles(kg)} kg · {em} · {NATURALEZA_TXT.get(nat, nat)}",
                       "cod_origen": int(mo["cod_municipio"]), "cod_destino": int(md["cod_municipio"]),
                       "pago_ofrecido": ofertas[i]})
    if not filas:
        return None, None, errores or ["No hay filas válidas."]
    return pd.DataFrame(filas, columns=COLS), pd.DataFrame(vistas), errores


def codigo_municipio(v):
    """Código DIVIPOLA de 5 dígitos desde un código (5 u 8 dígitos) o un nombre de municipio. None si no existe."""
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    mun = cargar_municipios()
    num = pd.to_numeric(v, errors="coerce")
    if pd.notna(num):
        cod = int(num) // 1000 if num > 99999 else int(num)
        return cod if cod in set(mun["cod_municipio"]) else None
    por_etiqueta, por_norm, _, _ = indices()
    e = por_norm.get(norm(v))
    return int(por_etiqueta[e]["cod_municipio"]) if e else None


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
    out = out.sort_values("prob_no_rentable", kind="stable").reset_index(drop=True)
    return agregar_guia(out)          # costo, mercado y oferta: se agregan después del modelo, no lo alimentan
