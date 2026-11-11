"""RutaRentable: riesgo de que una oferta de carga quede por debajo del costo de referencia (Streamlit)."""
import io
import json

import joblib
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import sklearn
import streamlit as st

import datos_app as datos
import estilo
from datos_app import BASE, COLS, miles, pct

MIN_FREC = 50
MAX_OFERTAS = 8
TOP_MERCANCIAS = 300

st.set_page_config(page_title="RutaRentable · ¿Te alcanza el flete?", layout="wide",
                   page_icon=str(BASE / "assets" / "logo.svg"), initial_sidebar_state="collapsed")


@st.cache_resource
def cargar():
    modelo = joblib.load(BASE / "modelo_final.joblib")
    with open(BASE / "metadatos.json", encoding="utf-8") as f:
        meta = json.load(f)
    return modelo, meta


def prob_no_rentable(modelo, X):
    return modelo.predict_proba(X[COLS])[:, 0]


def html(fragmento):
    st.markdown(fragmento, unsafe_allow_html=True)


def medidor(p, umbral):
    """Medidor semicircular de la probabilidad de no cubrir el costo, con la raya del límite."""
    color = estilo.COLOR[datos.nivel(p, umbral)]
    corte = max(0.0, umbral - datos.MARGEN_AMBAR) * 100
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=p * 100,
        number={"suffix": " %", "valueformat": ".0f",
                "font": {"size": 44, "color": color, "family": "Sora, Inter, sans-serif"}},
        gauge={"axis": {"range": [0, 100], "tickvals": [0, 25, 50, 75, 100], "ticksuffix": " %",
                        "tickfont": {"size": 11, "color": estilo.TENUE}, "tickcolor": estilo.TENUE},
               "bar": {"color": color, "thickness": 0.32},
               "bgcolor": "#141B22", "borderwidth": 0,
               "steps": [{"range": [0, corte], "color": "rgba(34,197,94,.22)"},
                         {"range": [corte, umbral * 100], "color": "rgba(245,158,11,.30)"},
                         {"range": [umbral * 100, 100], "color": "rgba(239,68,68,.24)"}],
               "threshold": {"line": {"color": estilo.AMARILLO, "width": 5}, "thickness": 0.95,
                             "value": umbral * 100}}))
    fig.update_layout(height=225, margin=dict(l=34, r=34, t=24, b=6), separators=",.",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font={"family": "Inter, sans-serif", "color": estilo.TEXTO})
    return fig


def barras_resumen(conteo):
    niveles = ["verde", "ambar", "rojo"]
    fig = go.Figure(go.Bar(
        x=[conteo.get(n, 0) for n in niveles], y=[estilo.CORTO_NIVEL[n] for n in niveles], orientation="h",
        marker_color=[estilo.COLOR[n] for n in niveles], text=[conteo.get(n, 0) for n in niveles],
        textposition="outside", textfont={"color": estilo.TEXTO, "size": 13}, hoverinfo="skip"))
    fig.update_layout(height=170, margin=dict(l=8, r=30, t=6, b=6), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font={"family": "Inter, sans-serif", "color": estilo.TEXTO},
                      xaxis={"visible": False}, yaxis={"autorange": "reversed", "tickfont": {"size": 13}})
    return fig


def mapa_ruta(mo, md, niv, centroides):
    """Arco origen-destino sobre Colombia en mapa oscuro, coloreado por el semáforo."""
    color = estilo.RGB[niv]
    o, d = [mo["longitud"], mo["latitud"]], [md["longitud"], md["latitud"]]
    nom_o, nom_d = mo["etiqueta"].split(" (")[0], md["etiqueta"].split(" (")[0]
    todos = [{"nombre": k.title(), "lon": v[0], "lat": v[1]} for k, v in centroides.items()]
    # El texto del mapa va sin tildes: la capa de texto de deck.gl solo dibuja caracteres ASCII
    extremos = [{"nombre": datos.sin_tildes(nom_o), "lon": o[0], "lat": o[1], "color": [245, 184, 0]},
                {"nombre": datos.sin_tildes(nom_d), "lon": d[0], "lat": d[1], "color": color}]
    capas = [
        pdk.Layer("ScatterplotLayer", todos, get_position="[lon, lat]", get_fill_color=[147, 161, 176, 120],
                  get_radius=9000, radius_min_pixels=2, radius_max_pixels=5, pickable=True),
        pdk.Layer("ArcLayer", [{"o": o, "d": d, "nombre": f"{nom_o} a {nom_d}"}],
                  get_source_position="o", get_target_position="d", get_source_color=[245, 184, 0],
                  get_target_color=color, get_width=6, get_height=0.35, pickable=True),
        pdk.Layer("ScatterplotLayer", extremos, get_position="[lon, lat]", get_fill_color="color",
                  get_line_color=[17, 22, 28], stroked=True, line_width_min_pixels=2,
                  get_radius=22000, radius_min_pixels=8, radius_max_pixels=14, pickable=True),
        pdk.Layer("TextLayer", extremos, get_position="[lon, lat]", get_text="nombre", get_size=13,
                  get_color=[232, 237, 242], get_pixel_offset=[0, -22],
                  background=True, get_background_color=[17, 22, 28, 220]),
    ]
    vista = pdk.ViewState(latitude=0.5 * 4.6 + 0.5 * (o[1] + d[1]) / 2,
                          longitude=0.5 * -74.1 + 0.5 * (o[0] + d[0]) / 2, zoom=4.9, pitch=35, bearing=0)
    return pdk.Deck(layers=capas, initial_view_state=vista, map_style="dark", tooltip={"text": "{nombre}"})


def fijar_kilos(valor):
    st.session_state["kg"] = float(valor)


ENLACE_SICETAC = f'<a href="{datos.SICETAC_URL}" target="_blank">sicetac.mintransporte.gov.co</a>'
QUE_INCLUYE = """
El costo de referencia del SICE-TAC (Ministerio de Transporte) suma lo que cuesta mover un camión rígido de 2 ejes por
esa ruta:

- combustible y peajes;
- llantas, lubricantes y mantenimiento;
- salario y prestaciones del conductor;
- seguros y depreciación del vehículo;
- horas de cargue, descargue y espera (4 horas si el tránsito es de 8 horas o menos; 8 horas si es más largo).

**No incluye imprevistos:** paros o bloqueos, varadas fuera de lo normal, inseguridad, esperas excesivas. Si te
pagan apenas el costo, cualquier imprevisto es pérdida.
"""


def guia_negociacion(mo, md, origen, destino, km, nat):
    """Tarjeta 'Tu guía para negociar' de la pestaña Revisa una oferta. No usa el modelo."""
    nom_o, nom_d = mo["etiqueta"].split(" (")[0], md["etiqueta"].split(" (")[0]
    html(estilo.titulo("trato", "Tu guía para negociar"))
    html('<div class="rr-aviso"><b>El riesgo es para antes de tener precio;</b> con un precio en la mano, '
         'compáralo contra el costo de referencia.</div>')
    co = datos.costo_referencia(mo["cod_municipio"], md["cod_municipio"], nat)
    me = datos.mercado(mo["cod_municipio"], md["cod_municipio"], origen, destino, km)
    if co:
        nota = (f"Lo que cuesta hacer el viaje en condiciones normales{' con carga refrigerada' if co['refrigerada'] else ''}, por la ruta "
                f"oficial de {miles(co['km'])} km y con {co['horas']} horas de cargue, descargue y espera.")
        if co["invertida"]:
            nota += f" El SICE-TAC no trae esta ruta en este sentido; usamos la de {nom_d} a {nom_o}."
        nota += f" Valores de diciembre de 2025; consulta el valor vigente en el SICE-TAC: {ENLACE_SICETAC}."
        piso = ("Piso: costo de referencia", datos.pesos(co["costo"]), nota)
    else:
        piso = ("Piso: costo de referencia", "Sin dato",
                datos.SIN_COSTO.replace("sicetac.mintransporte.gov.co", ENLACE_SICETAC))
    if me:
        merc = ("Mercado: lo que se pagó", f"{datos.pesos(me['p25'])} a {datos.pesos(me['p75'])}",
                f"Viajes así se pagaron normalmente entre <b>{datos.pesos(me['p25'])}</b> y "
                f"<b>{datos.pesos(me['p75'])}</b> (mediana <b>{datos.pesos(me['mediana'])}</b>). {me['base']}")
    else:
        merc = ("Mercado: lo que se pagó", "Sin dato", datos.SIN_MERCADO)
    html(estilo.guia(piso, merc))
    with st.expander("¿Qué incluye el costo de referencia?"):
        st.markdown(QUE_INCLUYE)
    oferta = st.number_input("¿Cuánto te ofrecen? (opcional)", min_value=0, max_value=50_000_000, value=None,
                             step=50_000, key="oferta", placeholder="Por ejemplo: 1850000",
                             help="El valor total del flete en pesos, sin puntos. No cambia el riesgo de arriba.")
    v = datos.veredicto(oferta, co, me)
    if v:
        detalles = [f"Te ofrecen: {datos.pesos(oferta)}."]
        if v["cubre"] is not None:
            signo = "+" if v["diferencia"] >= 0 else "−"
            detalles.append(f"Frente al costo de referencia: {'cubre' if v['cubre'] else 'no cubre'} "
                            f"({signo}{datos.pesos(abs(v['diferencia']))}, {pct(v['porcentaje'])}).")
        if v["posicion"]:
            detalles.append(f"Frente al mercado: {v['posicion']} (lo normal va de {datos.pesos(me['p25'])} a "
                            f"{datos.pesos(me['p75'])}).")
        html(estilo.veredicto(v["nivel"], v["frase"], detalles))
    st.caption("Es una guía con datos de diciembre de 2025, no una garantía. El precio final lo acuerdas tú.")


def texto_guia(r):
    """Línea de costo, mercado y oferta para una tarjeta del comparador."""
    partes = [f"Costo de referencia: <b>{'sin dato' if pd.isna(r['costo_referencia']) else datos.pesos(r['costo_referencia'])}</b>",
              f"Mercado (mediana): <b>{'sin dato' if pd.isna(r['mercado_mediana']) else datos.pesos(r['mercado_mediana'])}</b>"]
    if pd.notna(r["pago_ofrecido"]):
        t = f"Te ofrecen <b>{datos.pesos(r['pago_ofrecido'])}</b>"
        if r["cubre_costo"] == "Sí":
            t += f": cubre (+{datos.pesos(r['diferencia_vs_costo'])})"
        elif r["cubre_costo"] == "No":
            t += f": no cubre (−{datos.pesos(-r['diferencia_vs_costo'])})"
        partes.append(t)
    return " · ".join(partes)


def mostrar_ranking(res, umbral):
    filas = [{"nivel": r["nivel"], "ruta": r["Ruta"], "detalle": r["Detalle"],
              "frase": datos.frase_frecuencia(r["prob_no_rentable"], html=False), "guia": texto_guia(r),
              "alerta": "No cubre el costo" if r["cubre_costo"] == "No" else ""} for r in res.to_dict("records")]
    html(estilo.ranking(filas))
    if res.iloc[0]["nivel"] == "rojo":
        st.warning("Ojo: hasta la mejor de la lista sale con riesgo alto. Pide más flete o busca otra oferta.")
    n_no = int((res["cubre_costo"] == "No").sum())
    if n_no:
        st.warning(f"{n_no} {'oferta no cubre' if n_no == 1 else 'ofertas no cubren'} el costo de referencia. "
                   "Antes de aceptar, pide al menos ese valor.")
    html('<p class="rr-nota">Orden por riesgo (modelo, sin precio). El costo de referencia y el mercado son datos de '
         'diciembre de 2025: una guía, no una garantía.</p>')


def resumen_y_tabla(res, umbral, nombre_descarga):
    conteo = res["nivel"].value_counts().to_dict()
    a, b = st.columns([1.3, 1], gap="medium")
    with a:
        html(estilo.kpis([
            ("semaforo", "Riesgo bajo", miles(conteo.get("verde", 0)), "buenas ofertas"),
            ("semaforo", "Cerca del límite", miles(conteo.get("ambar", 0)), "revisar con cuidado"),
            ("semaforo", "Riesgo alto", miles(conteo.get("rojo", 0)), "pedir más flete"),
        ]))
        html(f'<p class="rr-nota" style="margin-top:8px">{miles(len(res))} ofertas evaluadas, ordenadas de mejor a '
             f'peor. Límite usado: {pct(umbral, 1)}.</p>')
    with b:
        st.plotly_chart(barras_resumen(conteo), config={"displayModeBar": False}, key=f"barras_{nombre_descarga}")
    # Guía de negociación: ofertas con valor que no cubren el costo de referencia
    con_valor = int(res["pago_ofrecido"].notna().sum())
    n_no, n_si = int((res["cubre_costo"] == "No").sum()), int((res["cubre_costo"] == "Sí").sum())
    sin_costo = int(res["costo_referencia"].isna().sum())
    if con_valor:
        html(estilo.kpis([
            ("trato", "Con valor ofrecido", miles(con_valor), f"de {miles(len(res))} ofertas"),
            ("semaforo", "No cubren el costo", miles(n_no), "pedir al menos el costo de referencia"),
            ("semaforo", "Sí cubren el costo", miles(n_si), "comparar con el mercado"),
        ]))
        if n_no:
            st.warning(f"{miles(n_no)} de las {miles(con_valor)} ofertas con valor ofrecido no cubren el costo de "
                       "referencia (columna cubre_costo = No).")
    else:
        html('<p class="rr-nota">Si agregas una columna con el valor ofrecido (PAGO_OFRECIDO, OFERTA, TE_OFRECEN o '
             'VALOR_OFRECIDO), te decimos cuáles no cubren el costo de referencia.</p>')
    if sin_costo:
        html(f'<p class="rr-nota">{miles(sin_costo)} ofertas sin costo de referencia: la ruta no está en el SICE-TAC '
             'de diciembre de 2025 o el archivo no trae los municipios.</p>')
    tabla = res.drop(columns=["nivel"]).rename(columns={
        "prob_no_rentable": "Probabilidad de no cubrir el costo", "semaforo": "Semáforo",
        "de_cada_10_no_cubren": "De cada 10 no cubren", "decision": "Qué hacer"})
    color = {"Verde": estilo.VERDE, "Amarillo": estilo.AMBAR, "Rojo": estilo.ROJO}
    plata = {c: (lambda v: "" if pd.isna(v) else datos.pesos(v)) for c in
             ("pago_ofrecido", "costo_referencia", "mercado_p25", "mercado_mediana", "mercado_p75")}
    plata["diferencia_vs_costo"] = lambda v: "" if pd.isna(v) else ("+" if v >= 0 else "−") + datos.pesos(abs(v))
    st.dataframe(tabla.style.map(lambda v: f"color:{color.get(v, estilo.TEXTO)};font-weight:700",
                                 subset=["Semáforo"])
                 .map(lambda v: f"color:{estilo.ROJO};font-weight:700" if v == "No" else "", subset=["cubre_costo"])
                 .format({"Probabilidad de no cubrir el costo": "{:.3f}", **plata}),
                 width="stretch", hide_index=True)
    buf = io.StringIO()
    res.drop(columns=["nivel"]).to_csv(buf, index=False)
    st.download_button("Descargar resultados (CSV)", buf.getvalue().encode("utf-8-sig"),
                       file_name=nombre_descarga, mime="text/csv", key=f"desc_{nombre_descarga}")


# =====================================================================================
modelo, meta = cargar()
cats, rangos = meta["categorias"], meta["rangos"]
mun, mer = datos.cargar_municipios(), datos.cargar_mercancias()
por_etiqueta, por_norm, mer_por_nombre, mer_por_norm = datos.indices()
centroides = datos.cargar_centroides()
etiquetas = mun["etiqueta"].tolist()
mercancias = mer["mercancia"].tolist()
por_codigo = dict(zip(mun["cod_municipio"], mun["etiqueta"]))

html(estilo.CSS)
html(estilo.hero([
    "Camión rígido de <b>2 ejes</b>",
    "<b>20.868</b> viajes reales de diciembre de 2025",
    "Datos del <b>RNDC</b> y <b>SICE-TAC</b>",
]))
if sklearn.__version__ != meta["version_sklearn"]:
    st.warning(f"Versión de scikit-learn instalada ({sklearn.__version__}) distinta a la del modelo "
               f"({meta['version_sklearn']}). Las predicciones podrían no ser fiables.")
html(estilo.PORQUE)

cuerpo = st.container()          # pestañas (se llenan después de leer los ajustes)
zona_ajustes = st.container()    # se dibuja debajo, pero se ejecuta primero

# ---------------- Ajustes avanzados (límite de decisión) ----------------
with zona_ajustes, st.expander("Ajustes avanzados"):
    st.markdown("**Límite para considerar que el riesgo es alto.** Si no sabes qué elegir, deja el recomendado.")
    opcion = st.radio("Criterio del límite",
                      ["Recomendado (costo del negocio)", "Youden (artículo)", "Personalizado"],
                      horizontal=True, key="criterio")
    if opcion.startswith("Recomendado"):
        umbral = float(meta["umbral_costo"])
    elif opcion.startswith("Youden"):
        umbral = float(meta["umbral_youden"])
    else:
        umbral = st.slider("Límite personalizado", 0.05, 0.95, float(meta["umbral_costo"]), 0.01, key="umbral_pers")
    html(estilo.caja_umbral(f"{umbral:.3f}".replace(".", ",")))
    st.caption(
        "Recomendado: el límite que menos plata hace perder en promedio, si marcar de más una oferta buena cuesta "
        "la mitad de su margen (α = 0,5). Youden: el criterio del artículo de referencia, que marca más ofertas. "
        "Un límite más bajo marca más viajes en rojo; uno más alto deja pasar más."
    )

with cuerpo:
    tab1, tab2, tab3 = st.tabs(["Revisa una oferta", "Compara tus ofertas", "Para empresas (archivo CSV)"])

# ---------------- Revisa una oferta ----------------
with tab1:
    col_in, col_mapa = st.columns([1.2, 1], gap="medium")
    with col_in, st.container(key="tarjeta_entradas"):
        html(estilo.titulo("caja", "Cuéntanos la oferta"))
        c1, c2 = st.columns(2)
        with c1:
            e_origen = st.selectbox("¿De dónde sales?", etiquetas, index=etiquetas.index(por_codigo.get(11001, etiquetas[0])),
                                    key="origen", help="Escribe el nombre del municipio para buscarlo.")
        with c2:
            e_destino = st.selectbox("¿Para dónde vas?", etiquetas, index=etiquetas.index(por_codigo.get(5001, etiquetas[0])),
                                     key="destino", help="Escribe el nombre del municipio para buscarlo.")
        mo, md = por_etiqueta[e_origen], por_etiqueta[e_destino]
        origen, destino = mo["departamento"], md["departamento"]
        km_def, km_oficial = datos.km_ruta(mo, md)
        km_def = min(km_def, 3000.0)

        c3, c4 = st.columns(2)
        with c3:
            km = st.number_input("Kilómetros del viaje", min_value=1.0, max_value=3000.0, value=km_def, step=5.0,
                                 key=f"km_{mo['cod_municipio']}_{md['cod_municipio']}")
            if km_oficial:
                html(estilo.pista(f"<b>Distancia oficial de la ruta (SICE-TAC):</b> {miles(km_def)} km. "
                                  "Puedes cambiarla.", "ok"))
            else:
                html(estilo.pista(f"<b>Distancia estimada: ajústala si la conoces.</b> Calculamos unos "
                                  f"{miles(km_def)} km por carretera.", "est"))
        with c4:
            st.session_state.setdefault("kg", 4500.0)
            kg = st.number_input("¿Cuántos kilos llevas?", min_value=1.0, max_value=12000.0, step=100.0, key="kg")
            st.button("Media carga (5.000 kg)", on_click=fijar_kilos, args=(5000,), key="btn_media", width="stretch")
            st.button("Carga completa (9.000 kg)", on_click=fijar_kilos, args=(9000,), key="btn_completa",
                      width="stretch")
            html(estilo.pista("Un camión rígido de 2 ejes carga hasta unos 10.000 kg."))

        i_def = mercancias.index("Productos varios") if "Productos varios" in mercancias else 0
        mercancia = st.selectbox("¿Qué vas a llevar?", mercancias, index=i_def, key="mercancia",
                                 help="Escribe una palabra (por ejemplo: arroz, cemento, pollo) para buscar.")
        m = mer_por_nombre[mercancia]
        cap = m["capitulo"]
        html(estilo.pista(datos.grupo_capitulo(cap)))
        nats = list(datos.NATURALEZA_TXT)
        nat = st.selectbox("¿Cómo viaja la carga?", nats, index=nats.index(m["naturaleza"]) if m["naturaleza"] in nats else 0,
                           format_func=datos.NATURALEZA_TXT.get, key=f"nat_{mercancias.index(mercancia)}",
                           help="Te sugerimos la forma más común para esa mercancía. Puedes cambiarla.")

        # Advertencias
        for nombre, val, unidad in (("Los kilómetros", km, "km"), ("Los kilos", kg, "kg")):
            col = "KILOMETROS" if unidad == "km" else "KILOGRAMOS"
            p1, p99 = rangos[col][1], rangos[col][2]
            if val < p1 or val > p99:
                st.warning(f"{nombre} ({miles(val)} {unidad}) están fuera del rango que el modelo vio al entrenar "
                           f"({miles(p1)} a {miles(p99)} {unidad}). La estimación es poco fiable.")
        for etiqueta, col, valor in (("grupo de mercancía", "CAPITULO", cap), ("tipo de carga", "NATURALEZACARGA", nat),
                                     ("departamento de origen", "DEPARTAMENTOORIGEN", origen),
                                     ("departamento de destino", "DEPARTAMENTODESTINO", destino)):
            n = cats[col].get(valor, 0)
            if n < MIN_FREC:
                st.info(f"El {etiqueta} elegido tiene solo {n} viajes en los datos de entrenamiento: el modelo lo "
                        "trata como 'infrecuente' y el resultado es menos preciso.")

    X = pd.DataFrame([{"KILOMETROS": km, "KILOGRAMOS": kg, "CAPITULO": cap, "NATURALEZACARGA": nat,
                       "DEPARTAMENTOORIGEN": origen, "DEPARTAMENTODESTINO": destino}])
    p = float(prob_no_rentable(modelo, X)[0])
    odds = p / (1 - p) if p < 1 else float("inf")
    niv = datos.nivel(p, umbral)

    with col_mapa, st.container(key="tarjeta_mapa"):
        html(estilo.titulo("mapa", f"{e_origen.split(' (')[0]} a {e_destino.split(' (')[0]}"))
        try:
            st.pydeck_chart(mapa_ruta(mo, md, niv, centroides), height=400)
            html('<p class="rr-nota">Línea de referencia entre los dos municipios, con el color del semáforo en el '
                 'destino. No es el trazado de la vía.</p>')
        except Exception:
            st.info("No se pudo dibujar el mapa de esta ruta. La estimación no cambia.")

    with st.container(key="tarjeta_resultado"):
        html(estilo.titulo("semaforo", "Resultado de la oferta"))
        r1, r2 = st.columns([1.5, 1], gap="medium")
        with r1:
            html(estilo.semaforo(niv, datos.frase_frecuencia(p), datos.de_cada_10(p)))
        with r2:
            st.plotly_chart(medidor(p, umbral), config={"displayModeBar": False}, key="medidor")
            html(estilo.leyenda(pct(umbral)))
        st.caption(f"Probabilidad de no cubrir el costo: {pct(p, 1)}. La raya amarilla del medidor es el límite "
                   f"({pct(umbral)}): de ahí en adelante el riesgo se considera alto. Es una probabilidad, no una certeza.")
        f1, f2 = st.columns([1.5, 1], gap="medium")
        with f1:
            html(estilo.titulo("lupa", "Qué está pesando en esta oferta"))
            html(estilo.factores(datos.factores(km, kg, nat)))
        with f2:
            nota_km = ("distancia oficial SICE-TAC" if km_oficial and km == km_def
                       else "distancia estimada" if km == km_def else "distancia que tú pusiste")
            html(estilo.kpis([
                ("ruta", "Distancia", f"{miles(km)} km", nota_km),
                ("peso", "Peso", f"{miles(kg)} kg", f"{pct(min(kg / datos.CAPACIDAD_KG, 1))} de la capacidad"),
                ("medidor", "Nivel de riesgo", estilo.CORTO_NIVEL[niv].replace("Riesgo ", "").capitalize(),
                 f"límite en uso: {pct(umbral)}"),
            ]))
            html('<div class="rr-odds">Dato técnico (odds): por cada viaje como este que sí cubre el costo, hay '
                 f"<b>{f'{odds:.2f}'.replace('.', ',')}</b> que no lo cubren. Las odds son p / (1 − p); no son una "
                 "probabilidad.</div>")

    # Guía para negociar: costo de referencia, mercado y la oferta. Nada de esto entra al modelo.
    with st.container(key="tarjeta_guia"):
        guia_negociacion(mo, md, origen, destino, km, nat)

# ---------------- Compara tus ofertas ----------------
with tab2, st.container(key="tarjeta_comparar"):
    html(estilo.titulo("lista", "¿Te llegaron varias ofertas? Mira cuál te conviene"))
    st.write("Anota las ofertas que te llegaron por WhatsApp, por una aplicación o de una empresa (hasta "
             f"{MAX_OFERTAS}). Los kilómetros se calculan solos. Luego toca **Comparar**.")
    top_mer = mercancias[:TOP_MERCANCIAS]
    ejemplo = pd.DataFrame({
        "Origen": [por_codigo.get(c, etiquetas[0]) for c in (11001, 11001, 11001)],
        "Destino": [por_codigo.get(c, etiquetas[1]) for c in (5001, 8001, 15001)],
        "Kilos": [9000, 3000, 5000],
        "Mercancía": [x if x in top_mer else top_mer[0] for x in ("Productos varios", "Mudanzas", "Avena")],
        "Te ofrecen ($)": pd.array([1_700_000, None, None], dtype="Int64"),
    })
    tabla = st.data_editor(
        ejemplo, num_rows="dynamic", width="stretch", hide_index=True, key="editor_ofertas",
        column_config={
            "Origen": st.column_config.SelectboxColumn("Origen", options=etiquetas, required=True),
            "Destino": st.column_config.SelectboxColumn("Destino", options=etiquetas, required=True),
            "Kilos": st.column_config.NumberColumn("Kilos", min_value=1, max_value=12000, step=100, required=True),
            "Mercancía": st.column_config.SelectboxColumn("Mercancía", options=top_mer, required=True),
            "Te ofrecen ($)": st.column_config.NumberColumn(
                "Te ofrecen ($)", min_value=0, max_value=50_000_000, step=50_000, format="$%d",
                help="Opcional. Valor total del flete en pesos. No cambia el riesgo; se compara con el costo de referencia."),
        })
    html(estilo.pista("Para agregar otra oferta usa la última fila de la tabla. El tipo de carga (normal, "
                      "refrigerada...) se toma del más común para cada mercancía. La columna \"Te ofrecen\" es "
                      "opcional: si la llenas, te decimos si cubre el costo de referencia."))
    if st.button("Comparar", type="primary", key="btn_comparar"):
        st.session_state["ofertas_cmp"] = pd.DataFrame(tabla).copy()
    if "ofertas_cmp" in st.session_state:
        ofertas = st.session_state["ofertas_cmp"]
        if len(ofertas) > MAX_OFERTAS:
            st.info(f"Se comparan solo las primeras {MAX_OFERTAS} ofertas.")
            ofertas = ofertas.head(MAX_OFERTAS)
        Xc, vista, errores = datos.preparar_ofertas(ofertas)
        for e in errores:
            st.warning(e)
        if Xc is not None:
            mostrar_ranking(datos.evaluar(modelo, Xc, vista, umbral), umbral)

# ---------------- Para empresas ----------------
with tab3, st.container(key="tarjeta_lote"):
    html(estilo.titulo("edificio", "Evalúa muchas ofertas de una sola vez"))
    st.markdown(
        "Sube un archivo CSV en cualquiera de estos dos formatos:\n"
        "- **Sencillo:** columnas `Origen`, `Destino` (municipios), `Kilos` y `Mercancia`. Los kilómetros se "
        "calculan solos; `Kilometros` y `Naturaleza` son opcionales.\n"
        "- **Técnico:** las 6 columnas del modelo: " + ", ".join(f"`{c}`" for c in COLS) + ". Opcionales "
        "`CODMUNICIPIOORIGEN` y `CODMUNICIPIODESTINO` (código DIVIPOLA) para el costo de referencia y el mercado de "
        "la ruta exacta.\n"
        "- **Opcional en los dos:** una columna con el valor ofrecido en pesos (`PAGO_OFRECIDO`, `OFERTA`, "
        "`TE_OFRECEN` o `VALOR_OFRECIDO`). El resultado dice si cubre el costo de referencia y dónde queda frente "
        "al mercado. Ese valor no entra al modelo."
    )
    d1, d2, _ = st.columns([1, 1, 1])
    for colu, nombre, texto in ((d1, "ofertas_semana_transportador.csv", "Ejemplo: 8 ofertas de una semana"),
                                (d2, "ofertas_cooperativa.csv", "Ejemplo: 40 ofertas de una cooperativa")):
        ruta = BASE / "ejemplos" / nombre
        if ruta.exists():
            colu.download_button(texto, ruta.read_bytes(), file_name=nombre, mime="text/csv", key=f"ej_{nombre}",
                                 width="stretch")
    archivo = st.file_uploader("Archivo CSV con tus ofertas", type="csv", key="archivo")
    if archivo is not None:
        try:
            df = datos.leer_csv(archivo)
        except Exception as e:
            st.error(f"No se pudo leer el archivo: {e}")
            df = None
        if df is not None:
            Xl, vista, errores = datos.preparar_ofertas(df)
            if Xl is None:
                for e in errores:
                    st.error(e)
            else:
                if errores:
                    st.warning(f"{len(errores)} filas no se pudieron leer y se dejaron por fuera. "
                               + " ".join(errores[:5]))
                resumen_y_tabla(datos.evaluar(modelo, Xl, vista, umbral), umbral, "resultados_ofertas.csv")
                st.caption("Si faltan kilómetros o kilos en una fila, el modelo usa el valor típico (mediana).")

# ---------------- Sobre el modelo ----------------
with st.expander("Sobre el modelo"):
    lo, hi = meta["auc_prueba_ic95"]
    st.markdown(
        f"""
**Qué usa.** Solo lo que sabes cuando te ofrecen el viaje: origen, destino, kilómetros, kilos, tipo de mercancía y
naturaleza de la carga (normal, refrigerada, peligrosa...).

**Qué NO usa.** No conoce el precio que te ofrecen. Estima el riesgo de ese tipo de viaje **antes de negociar**,
comparando con lo que pasó en viajes reales parecidos: cuántos se pagaron por debajo del costo de referencia del
Ministerio de Transporte (SICE-TAC).

**Qué pesa más.**
- La distancia: el riesgo sube fuerte entre 300 y 450 km, cerca de las 8 horas de manejo.
- La carga refrigerada: cerca de 3,75 veces las odds de no cubrir el costo frente a la carga normal.
- El peso: las cargas livianas tienen más riesgo (500 kg: 2,69 veces las odds de 4.500 kg) y las pesadas menos
  (10.000 kg: 0,15 veces).

**El modelo y el SICE-TAC.** El SICE-TAC dice cuánto cuesta el viaje; el flete es lo que se pagó; RutaRentable
dice, antes de negociar, qué tan seguido viajes como este se pagan por debajo de ese costo. El costo de referencia, el
rango del mercado y el valor que te ofrecen se muestran como guía, pero nunca entran al modelo.

**Qué tanto creerle a la frase "de cada 10".** Se apoya en que el modelo está razonablemente calibrado: en validación,
la diferencia entre lo que predijo y lo que pasó fue de máximo 3,7 puntos por decil. Es una guía, no una probabilidad
exacta.

**Para qué casos sirve.** Camión rígido de 2 ejes, en Colombia, viajes de un solo trayecto. Se entrenó con
20.868 viajes del RNDC y los costos SICE-TAC de diciembre de 2025.

**Qué tan bien acierta.** En viajes que el modelo nunca había visto, si se toma uno que no cubrió el costo y otro
que sí, le da más riesgo al primero en unas {round(meta['auc_prueba'] * 100)} de cada 100 parejas
(AUC = {f"{meta['auc_prueba']:.3f}".replace(".", ",")}; IC 95 %: {f"{lo:.3f}".replace(".", ",")} a {f"{hi:.3f}".replace(".", ",")}).
Modelo: regresión logística con splines, semilla {meta['semilla']}.

**Cómo se eligió el límite recomendado ({pct(meta['umbral_costo'])}).** Hay dos formas de equivocarse: aceptar un
viaje malo (pierdes lo que le faltó al flete para cubrir el costo) o marcar en rojo un viaje bueno (pierdes parte de
la ganancia por rechazarlo o demorarlo). El límite recomendado es el que hace perder menos plata en promedio,
suponiendo que marcar de más cuesta la mitad del margen del viaje (α = {str(meta['alpha_base']).replace(".", ",")}).

**Limitaciones.**
- Solo un mes de datos (diciembre de 2025): no recoge temporadas ni cambios de precios.
- En el RNDC solo están los viajes que sí se hicieron. Las ofertas que los transportadores rechazaron (seguramente
  las peores) no aparecen, así que el riesgo y el rango del mercado pueden verse mejores de lo que son.
- El costo de referencia se aproximó según el tipo de carrocería, no con los costos de cada camión.
- Cerca del límite el resultado es incierto: muchos viajes se pagan casi igual al costo. Por eso existe el amarillo.
- Es una probabilidad, no una certeza. No reemplaza tu experiencia ni la negociación.
"""
    )

html(estilo.PIE)
