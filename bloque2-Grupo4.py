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



# -----------------------------------------------------------------------------
# 2) Mapa de calor: densidad de eventos a lo largo del partido
# -----------------------------------------------------------------------------
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
ev = ev[ev["tipo_evento"].isin(tipos_sel) & ev["ronda"].isin(rondas_sel)]

if ev.empty:
    st.warning("No hay eventos para los filtros seleccionados.")
else:
    # Tramo de 5 minutos al que pertenece cada evento (0, 5, 10, ..., 115)
    ev["tramo"] = (ev["minuto_evento"].astype(int) // 5) * 5
    ev["tramo"] = ev["tramo"].clip(upper=115)   # el minuto 120 entra en el último tramo

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

    # --- Respuestas a las preguntas del enunciado ---------------------------
    goles = ev[ev["tipo_evento"] == "gol"]

    if not goles.empty:
        tramo_max = goles.groupby("tramo").size().idxmax()
        st.write(f"**Tramo con más goles:** minuto {tramo_max}-{tramo_max + 5}")

    # Prórroga = minutos > 90 SOLO en partidos que la tuvieron
    # (en el resto, los minutos 91+ son tiempo añadido de la segunda parte)
    en_prorroga = (ev["minuto_evento"] > 90) & (ev["prorroga"] == "SI")
    primera = ev[ev["minuto_evento"] <= 45]
    segunda = ev[(ev["minuto_evento"] > 45) & ~en_prorroga]
    prorroga = ev[en_prorroga]

    col1, col2, col3 = st.columns(3)
    col1.metric("1.ª parte", len(primera))
    col2.metric("2.ª parte", len(segunda))
    col3.metric("Prórroga", len(prorroga))

