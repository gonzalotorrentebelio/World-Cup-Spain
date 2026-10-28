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



st.subheader("Densidad de evento a lo largo del partido")
tipos_sel = st.multiselect(
    "tipo de evento",
    options=sorted(eventos["tipo_evento"].unique()),
    default=sorted(eventos["tipo_evento"].unique()),    
)
rondas_sel = st.multiselect(
    "Tipo de evento",
    options=eventos["ronda"].unique(),
    default=partidos["ronda"].unique()
    )

# la ronda está en 'partidos' así que hay que unirla a 'eventos'
ev = eventos.join(partidos["ronda"], on="index_partido")
ev = ev[ev["tipo_evento"].isin(tipos_sel) & ev["ronda"].isin(rondas_sel)]
ev["eventos_interv"] = ev["minuto_evento"].rolling(window=5)
# agrupar los eventos por tramos y pintar con px.show

# Hacer git push y GIT COMMIT
