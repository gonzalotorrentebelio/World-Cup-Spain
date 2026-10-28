import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st


def cargar_datos():
    eventos = pd.read_excel("eventosWC26.xlsx", index_col="index_evento")
    partidos = pd.read_excel("partidosWC26.xlsx", index_col="index_partido")
    jugadores = pd.read_excel("jugadoresWC2026.xlsx", index_col="nombre_jugador")
    return eventos, partidos, jugadores

eventos, partidos, jugadores = cargar_datos()

st.title("Análisis del Mundial 2026")


# ANÁLISIS 1 - VENTANAS DE PARTIDOS

st.header("Análisis 1. Ventanas de partidos")


st.subheader("1) Eventos de un partido")

# Etiqueta legible para cada partido: "1. Mexico - South Africa (grupos)"
etiquetas = {
    idx: f"{idx}. {fila['seleccion_local']} - {fila['seleccion_visitante']} ({fila['ronda']})"
    for idx, fila in partidos.iterrows()
}

partido_sel = st.selectbox(
    "Elige un partido",
    options=list(etiquetas.keys()),
    format_func=lambda idx: etiquetas[idx],
)

# Filtramos los eventos de ese partido y los ordenamos por minuto
ev_partido = eventos[eventos["index_partido"] == partido_sel].sort_values("minuto_evento")

# Cada evento es una barra de altura 1 colocada en su minuto;
# si coinciden varios eventos en el mismo minuto, se apilan
ev_partido = ev_partido.assign(n_eventos=1)

fig1 = px.bar(
    ev_partido,
    x="minuto_evento",
    y="n_eventos",
    color="tipo_evento",
    hover_data={
        "nombre_jugador": True,
        "seleccion_evento": True,
        "minuto_evento": True,
        "n_eventos": False,   # no mostrar la altura ficticia en el tooltip
    },
    labels={
        "minuto_evento": "Minuto de partido",
        "tipo_evento": "Tipo de evento",
        "nombre_jugador": "Jugador",
        "seleccion_evento": "Selección",
    },
    title=etiquetas[partido_sel],
)

# Eje X fijo de 0 a 120 para que todos los partidos sean comparables
fig1.update_xaxes(range=[0, 125], dtick=15)
fig1.update_yaxes(visible=False)
fig1.update_layout(bargap=0.1)

st.plotly_chart(fig1, use_container_width=True)

# Tabla de apoyo con el detalle de los eventos
st.dataframe(ev_partido[["minuto_evento", "tipo_evento", "nombre_jugador", "seleccion_evento"]])



# 2) Mapa de calor: densidad de eventos a lo largo del partido

st.subheader("2) Densidad de eventos a lo largo del partido")

tipos_sel = st.multiselect(
    "Tipo de evento",
    options=sorted(eventos["tipo_evento"].unique()),
    default=sorted(eventos["tipo_evento"].unique()),
)
rondas_sel = st.multiselect(
    "Ronda",
    options=partidos["ronda"].unique(),
    default=partidos["ronda"].unique(),
)

# La ronda y la prórroga están en 'partidos': las traemos a 'eventos'
ev = eventos.join(partidos[["ronda", "prorroga"]], on="index_partido")
ev = ev[ev["tipo_evento"].isin(tipos_sel) & ev["ronda"].isin(rondas_sel)].copy()

# El minuto 121 es la tanda de penaltis: no es tiempo de juego, se cuenta aparte
tanda = ev[ev["minuto_evento"] > 120]
ev = ev[ev["minuto_evento"] <= 120].copy()

if ev.empty:
    st.warning("No hay eventos para los filtros seleccionados.")
else:
    # En partidos SIN prórroga, los minutos 91+ son tiempo añadido de la 2.ª parte:
    # los llevamos al minuto 90 para que no aparezcan en la zona de prórroga
    descuento = (ev["minuto_evento"] > 90) & (ev["prorroga"] == "NO")
    ev["minuto_tramo"] = ev["minuto_evento"].mask(descuento, 90)

    # Tramo de 5 minutos: 1-5 -> 0, 6-10 -> 5, ..., 41-45 -> 40, 116-120 -> 115
    # (restamos 1 para que el minuto 45 quede en la 1.ª parte y el 90 en la 2.ª)
    ev["tramo"] = ((ev["minuto_tramo"] - 1) // 5) * 5

    # Tabla: filas = tipo de evento, columnas = tramo, valores = nº de eventos
    tabla = ev.groupby(["tipo_evento", "tramo"]).size().unstack(fill_value=0)

    # Aseguramos que aparecen todos los tramos, aunque estén vacíos
    tabla = tabla.reindex(columns=range(0, 120, 5), fill_value=0)
    tabla.columns = [f"{m}-{m + 5}'" for m in tabla.columns]

    fig2 = px.imshow(
        tabla,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="YlOrRd",
        labels={"x": "Tramo de minutos", "y": "Tipo de evento", "color": "Nº eventos"},
        title="Densidad de eventos por tramo de 5 minutos",
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(
        f"Los minutos 45' y 90' incluyen el tiempo añadido. "
        f"Tanda de penaltis (no incluida en el mapa): {len(tanda)} lanzamientos."
    )

# PREGUNTAS
# ¿En qué intervalo se producen más goles?
# En los últimos 15 minutos de partido. En tramos de 15 minutos, el de 75 a 90 tiene 76 goles,
# una cuarta parte de los 298 del tiempo reglamentario. Le siguen el de 30 a 45 (53) y el de 
# 45 a 60 (52); el que menos tiene es el de 15 a 30 (34). En tramos de 5 minutos destaca el de 
# 85 a 90, con 45 goles, casi el doble que el siguiente, que es el de 40 a 45 (25). Hay que matizarlo:
# los minutos 45 y 90 incluyen el tiempo añadido, así que esos dos tramos duran en realidad más de 5 
# minutos y salen algo inflados. Aun así, el patrón es claro: los goles se concentran al final de cada 
# parte, sobre todo del partido.

# ¿Son las segundas partes más «entretenidas» que las primeras?
# Sí. Hay 456 eventos frente a 302, un 51 % más (0,97 frente a 0,65 por cada 10 minutos). En goles la 
# diferencia es de 172 frente a 126 (+37 %), y en asistencias de 113 frente a 81. También aumentan mucho 
# las tarjetas: 151 amarillas frente a 88 y 11 rojas frente a 2. En la defensa conviene distinguir entre más goles,
# que es «entretenimiento», y más tarjetas, que indican más tensión o desgaste.

# ¿Y las prórrogas?
# Son el periodo con más eventos por minuto: 29 eventos en 9 prórrogas, es decir, 1,07 por cada 10 minutos. 
# Sin embargo, no se marcan más goles: 9 goles dan 0,33 por cada 10 minutos, una cifra entre la de la primera 
# parte (0,27) y la de la segunda (0,37). Lo que dispara la cifra son las tarjetas, con 16 (14 amarillas y 2 rojas),
# lo que supone 0,59 por cada 10 minutos, frente a 0,35 en las segundas partes. Dentro de la prórroga, 3 goles 
# llegan en la primera mitad y 6 en la segunda. 4 de las 9 prórrogas acabaron en penaltis. Conviene advertir 
# que la muestra es pequeña (9 partidos), así que la conclusión es más débil que la de las partes.


#3) Gráfico circular: eventos de una Selección a favor y en contra

st.subheader("3) Eventos de una Selección en el Mundial")

# Lista de las 48 selecciones (locales y visitantes, sin repetir)
selecciones = sorted(pd.concat([partidos["seleccion_local"], partidos["seleccion_visitante"]]).unique())
seleccion_sel = st.selectbox("Elige una Selección", options=selecciones)

# Partidos en los que ha jugado la selección elegida
partidos_sel = partidos[(partidos["seleccion_local"] == seleccion_sel) | (partidos["seleccion_visitante"] == seleccion_sel)]

# Todos los eventos de esos partidos (los suyos y los de sus rivales)
ev_sel = eventos[eventos["index_partido"].isin(partidos_sel.index)].copy()

# ¿El evento lo protagoniza la propia selección o su rival?
ev_sel["autor"] = ev_sel["seleccion_evento"].where(ev_sel["seleccion_evento"] == seleccion_sel, "Rival").replace(seleccion_sel, "Propio")

# Eventos positivos para quien los protagoniza; el resto son negativos
# (las revisiones VAR se asignan en los datos al equipo perjudicado)
positivos = ["gol", "asistencia", "penalti marcado"]
es_positivo = ev_sel["tipo_evento"].isin(positivos)
es_propio = ev_sel["autor"] == "Propio"

# A favor: algo bueno de la selección o algo malo del rival.
# En contra: algo malo de la selección o algo bueno del rival.
ev_sel["balance"] = "En contra"
ev_sel.loc[es_positivo == es_propio, "balance"] = "A favor"

# Etiqueta legible, p. ej. "gol (propio)" o "gol (rival)" = gol encajado
ev_sel["evento"] = ev_sel["tipo_evento"] + " (" + ev_sel["autor"].str.lower() + ")"

# Conteo de cada tipo de evento
resumen = (ev_sel.groupby(["balance", "evento"]).size().reset_index(name="cantidad"))

# Un solo donut: todo lo que va a favor en verde y todo lo que va en contra en rojo
resumen = resumen.sort_values(["balance", "cantidad"], ascending=[True, False])

fig3 = px.pie(
        resumen,
        names="evento",
        values="cantidad",
        color="balance",
        color_discrete_map={"A favor": "#2E8B57", "En contra": "#C0392B"},
        hole=0.5,
        title=f"Distribución de eventos de {seleccion_sel} en el Mundial",
    )
fig3.update_traces(
    textinfo="label+value",
    textposition="outside",
    sort=False,
    marker_line_color="white",
    marker_line_width=2,
)
fig3.update_layout(showlegend=False)
st.plotly_chart(fig3, use_container_width=True)


# ANALISIS 2 - RENDIMIENTO JUGADORES CLAVE
st.header("Análisis 2. Rendimiento de jugadores clave")

# 4) Dispersión: Valor de mercado vs Calificación media (mín. 180 minutos)
st.subheader("4) Valor de mercado vs calificación media")
# Solo jugadores con al menos 180 minutos jugados
# (reset_index convierte el índice nombre_jugador en columna para el hover)
jug = jugadores[jugadores["minutos_jugados"] >= 180].reset_index()

# Selectores: Selección, Partidos jugados y Posición
f1, f2, f3 = st.columns(3)
selecciones_sel = f1.multiselect(
    "Selección",
    options=sorted(jug["seleccion_nacional"].unique()),
    placeholder="Todas",
)
posiciones_sel = f2.multiselect(
    "Posición",
    options=sorted(jug["posicion"].unique()),
    placeholder="Todas",
)
pj_min, pj_max = f3.slider(
    "Partidos jugados",
    min_value=int(jug["partidos_jugados"].min()),
    max_value=int(jug["partidos_jugados"].max()),
    value=(int(jug["partidos_jugados"].min()), int(jug["partidos_jugados"].max())),
)

# Aplicamos los filtros (si un multiselect está vacío, no filtra)
jug_f = jug[jug["partidos_jugados"].between(pj_min, pj_max)]
if selecciones_sel:
    jug_f = jug_f[jug_f["seleccion_nacional"].isin(selecciones_sel)]
if posiciones_sel:
    jug_f = jug_f[jug_f["posicion"].isin(posiciones_sel)]

if jug_f.empty:
    st.info("No hay jugadores con estos filtros.")
else:
    fig4 = px.scatter(
        jug_f,
        x="valor_mercado",
        y="calificacion_media",
        color="posicion",
        hover_name="nombre_jugador",
        hover_data=["seleccion_nacional", "partidos_jugados", "minutos_jugados", "goles"],
        labels={
            "valor_mercado": "Valor de mercado (M€)",
            "calificacion_media": "Calificación media",
            "posicion": "Posición",
            "seleccion_nacional": "Selección",
            "partidos_jugados": "Partidos jugados",
            "minutos_jugados": "Minutos jugados",
            "goles": "Goles",
        },
        title="Valor de mercado vs calificación media (jugadores con ≥ 180 minutos)",
    )
    st.plotly_chart(fig4, use_container_width=True)

    # Correlación de Pearson entre ambas variables (con los filtros aplicados)
    c1, c2 = st.columns(2)
    c1.metric("Jugadores mostrados", len(jug_f))
    if len(jug_f) >= 3:
        r = jug_f["valor_mercado"].corr(jug_f["calificacion_media"])
        c2.metric("Correlación de Pearson (r)", f"{r:.2f}")