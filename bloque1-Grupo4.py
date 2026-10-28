# BLOQUE 1

import pandas as pd
import numpy as np
import re
from sklearn.linear_model import LinearRegression
from IPython.display import display

# APARTADO 1
# La carpeta datasetsWC26.zip dispone de varios archivos .csv con distintos datos sobre el Mundial 2026. Utilizando Pandas, impórtelos y realice una exploración
# inicial de todos ellos para entender su contenido, formato de datos y tamaño.

def resumen(df):
    display(df.head())
    print(f"NÚMERO FILAS DUPLICADAS: {df.duplicated().sum()}")
    print(f"DIMENSIONES: ({len(df)}x{len(df.columns)})")
    display(df.describe())

    df_data = pd.DataFrame({"dtypes": df.dtypes,
                           "nulos": df.isna().sum(),
                           "pct_nulos": (df.isna().mean()*100).round(2),
                           "num_distintos": df.nunique(dropna=False)
                            
                           })
    return df_data

df_2001eurocopa_fem_stats = pd.read_csv("datasetsWC26/2001eurocopa_fem_stats.csv")
display(resumen(df_2001eurocopa_fem_stats))
for i in df_2001eurocopa_fem_stats.select_dtypes(exclude="number").columns:
    display(df_2001eurocopa_fem_stats[i].value_counts(dropna=False))

# De primeras vistas, ya se pueden ver valores extraños, como NORWAY en mayusculas, 20 tarjetas roja en un único partido o valores imposibles como -2 en away_score

df_match_lineups = pd.read_csv("datasetsWC26/2026match_lineups.csv", sep =";")
display(resumen(df_match_lineups))
display(df_match_lineups["tactical_position"].value_counts())

# Se detectan ciertas anomalías en la columna de tactical positions pero por lo general hay un muy bajo porcentage de nulos y pocas filas duplicadas

df_match_register = pd.read_csv("datasetsWC26/2026match_register.csv", sep =";")
display(resumen(df_match_register))
display(df_match_register["event_type"].value_counts(dropna=False))

# Aparecen valores negativos en event_id o minute y la columna de event_type debe limpiarse para unificar valores

df_teams = pd.read_csv("datasetsWC26/2026nationalteams.csv", sep =",")
display(resumen(df_teams))

df_playerstats = pd.read_csv("datasetsWC26/2026player_stats.csv", sep =";")
display(resumen(df_playerstats))

df_squads_players = pd.read_csv("datasetsWC26/2026squads_and_players.csv", sep =";")
display(resumen(df_squads_players))
display(df_squads_players["position"].value_counts())

# solo una columna con valores nulos. No hay valores en la columna de posiciones que haya que limpiar. 

df_referees = pd.read_csv("datasetsWC26/index_referees.csv", sep =";")
display(resumen(df_referees))
display(df_referees["country"].value_counts())

# 6 filas duplicadas. No hay valores nulos. Aparecen valores anómalos como 55 tarjetas en un partido. La columna "referee_id" está repetida y tiene valores repetidos

df_matches = pd.read_csv("datasetsWC26/matches_mundial202.csv", sep =",")
display(resumen(df_matches))

df_matches26 = pd.read_csv("datasetsWC26/matches_mundial2026.csv", sep =";")
display(resumen(df_matches26))
for i in df_matches26.select_dtypes(exclude="number").columns:
    display(df_matches26[i].value_counts())

# Es necesario unificar columnas (como por ejemplo en clima: lluvia y Lluvia o Soleado y soleado). Las columnas Home_penaly_score y away_penalty_score son prácticamente nulas. También tiene valores con capacidad de estadio negativa 

df_stages = pd.read_csv("datasetsWC26/tournament_stages.csv", sep =",")
display(resumen(df_stages))
for i in ["is_knockout", "num_partidos", "fecha_inicio_fase"]:
    display(df_stages[(i)].value_counts())

df_venues = pd.read_csv("datasetsWC26/worldcup_venues.csv", sep =";")
display(resumen(df_venues))
for i in ["stadium_name", "city", "country", "superficie_cesped"]:
    display(df_venues[(i)].value_counts())

# APARTADO 2 y 3

# Cree tres variables de tipo DataFrame llamadas partidos, eventos y jugadores, en las que almacenará únicamente la información requerida para el análisis
# posterior.

# PARTIDOS
# Partimos de matches_mundial2026.csv (un registro por partido) y creamos las columnas con los nombres finales.
# Las columnas cuya información está en otro dataset (ronda, estadio, ciudad, país, selecciones y árbitro)
# se rellenan de momento con su id (las que en columnas_origen aparecen como algo_id).
# Después sustituimos cada id por su valor real usando la tabla auxiliar correspondiente.

partidos = pd.DataFrame()
nombres = ["index_partido", "fecha_partido", "ronda", "estadio", "ciudad_partido", "pais_partido",
           "seleccion_local", "seleccion_visitante", "marcador_local", "marcador_visitante",
           "prorroga", "penalty_local", "penalty_visitante", "arbitro_partido"]
columnas_origen = ["match_id", "date", "stage_id", "venue_id", "venue_id", "venue_id",
                   "home_team_id", "away_team_id", "home_score", "away_score",
                   "result_type", "home_penalty_score", "away_penalty_score", "referee_id"]

for nuevo, origen in zip(nombres, columnas_origen): # copiamos cada columna de origen con su nombre final   
    partidos[nuevo] = df_matches26[origen].copy()

partidos = partidos.set_index("index_partido")

# Tablas auxiliares: nos quedamos con el id y el valor que necesitamos, eliminamos ids repetidos
# (si un id se repite, map no sabe qué valor elegir) y ponemos el id como índice.
etapas = df_stages[["stage_id", "stage_name"]].drop_duplicates(subset="stage_id")  # quitamos ids repetidos para que no causen errores más adelante
etapas = etapas.set_index("stage_id")

# creamos un nuevo df 'venue' y ponemos "venue_id" como índice.
venue = df_venues[["venue_id", "stadium_name", "city", "country"]].drop_duplicates(subset="venue_id")
venue = venue.set_index("venue_id") 

# creamos un nuevo df 'equipos' y ponemos "team_id" como índice.
equipos = df_teams[["team_id", "team_name"]].dropna(subset=["team_id"]).drop_duplicates(subset="team_id")
equipos = equipos.set_index("team_id")  # quitamos también los team_id nulos

# creamos un nuevo df 'referee' y ponemos "referee_id" como índice.
referee = df_referees[["referee_id", "name"]].drop_duplicates(subset="referee_id")
referee = referee.set_index("referee_id")

# map usa cada tabla auxiliar como un diccionario id -> valor:
# cada id de partidos se sustituye por el valor que le corresponde en esa tabla.
partidos["ronda"] = partidos["ronda"].map(etapas["stage_name"])
partidos["estadio"] = partidos["estadio"].map(venue["stadium_name"])
partidos["ciudad_partido"] = partidos["ciudad_partido"].map(venue["city"])
partidos["pais_partido"] = partidos["pais_partido"].map(venue["country"])
partidos["seleccion_local"] = partidos["seleccion_local"].map(equipos["team_name"])
partidos["seleccion_visitante"] = partidos["seleccion_visitante"].map(equipos["team_name"])
partidos["arbitro_partido"] = partidos["arbitro_partido"].map(referee["name"])

# Prórroga a partir de result_type: Regular -> NO; AET (tras prórroga) y Penalties -> SI
partidos["prorroga"] = partidos["prorroga"].map({"Regular": "NO", "AET": "SI", "Penalties": "SI"})

# Traducimos ronda al español. Unificamos 'Quarter-finals' y 'Round of 16' en Cuartos
partidos["ronda"] = partidos["ronda"].map({"Group Stage":"Grupos", "Round of 32": "Dieciseisavos", 
                                           "Round of 16": "Octavos", "Quarter-finals": "Cuartos",
                                           "Semi-finals": "Semifinales", "Third-place match": "Tercer puesto",
                                           "Final": "Final"})

# Penaltis: 0 cuando no hubo tanda (NaN). Usamos Int64, el tipo entero de pandas que admite nulos.
partidos["penalty_local"] = partidos["penalty_local"].fillna(0).astype("Int64")
partidos["penalty_visitante"] = partidos["penalty_visitante"].fillna(0).astype("Int64")


display(partidos.dtypes)

# JUGADORES
# Combinamos 2026squads_and_players.csv (datos del jugador) y 2026player_stats.csv (estadísticas del torneo),
# emparejados por player_id. player_id se usa solo como llave y se elimina al final.
jugadores = pd.DataFrame()
nombres_squads = ["player_id", "nombre_jugador", "seleccion_nacional", "club_jugador", "partidos_seleccion", "posicion", "valor_mercado"]
columnas_squads = ["player_id", "player_name", "team_id", "club_team", "caps", "position", "market_value_eur"]

# Copiamos las columnas de squads con su nombre final (el nombre se toma de squads porque en player_stats
# tiene errores de codificación). seleccion_nacional contiene de momento el team_id.
for nuevo, viejo in zip(nombres_squads, columnas_squads): 
    jugadores[nuevo] = df_squads_players[viejo].copy()

# Sustituimos el team_id por el nombre de la selección (tabla equipos creada en la celda de partidos)
jugadores["seleccion_nacional"] = jugadores["seleccion_nacional"].map(equipos["team_name"])  

# Traducimos la posición al español
jugadores["posicion"] = jugadores["posicion"].map({"GK": "portero", "DEF": "defensa", "MID": "centrocampista", "FWD": "delantero"})

# Tabla de estadísticas con player_id como índice, sin ids repetidos para evitar errores en el map
stats = df_playerstats.drop_duplicates(subset="player_id")  
stats = stats.set_index("player_id")

nombres_stats = ["partidos_jugados", "minutos_jugados", "goles", "asistencias", "tiros",
                 "tarjetas_amarillas", "tarjetas_rojas", "paradas", "goles_concedidos", "calificacion_media"]
columnas_stats = ["matches_played", "minutes_played", "goals", "assists", "shots",
                  "yellow_cards", "red_cards", "saves", "goals_conceded", "average_rating"]

# Para cada estadística, buscamos el valor de cada jugador en stats a través de su player_id
for nuevo, viejo in zip(nombres_stats, columnas_stats):
    jugadores[nuevo] = jugadores["player_id"].map(stats[viejo])

jugadores = jugadores.drop(columns="player_id")
jugadores = jugadores.set_index("nombre_jugador")

display(jugadores)
# Pasamos a entero las columnas de conteo. Usamos Int64 porque admite nulos.
for i in ["tiros", "goles", "asistencias", "tarjetas_amarillas", "paradas", "tarjetas_rojas", "goles_concedidos"]:
    jugadores[i] = jugadores[i].astype("Int64")
display(jugadores.dtypes)

# EVENTOS
# Partimos de 2026match_register.csv (un registro por evento) y creamos las columnas con los nombres finales.
# nombre_jugador y seleccion_evento contienen de momento el player_id y el team_id.

eventos = pd.DataFrame()
nombres_eventos = ["index_evento", "minuto_evento", "index_partido", "nombre_jugador", "tipo_evento", "seleccion_evento"]
columnas_eventos = ["event_id", "minute", "match_id", "player_id", "event_type", "team_id"]

for nuevo, viejo in zip(nombres_eventos, columnas_eventos):
    eventos[nuevo] = df_match_register[viejo].copy()

# Jugador: tabla auxiliar player_id -> nombre (desde squads), sin ids repetidos
nombres_jug = df_squads_players[["player_id", "player_name"]].drop_duplicates(subset="player_id")
nombres_jug = nombres_jug.set_index("player_id")
eventos["nombre_jugador"] = eventos["nombre_jugador"].map(nombres_jug["player_name"]) # sustituimos el player_id por el nombre

# Selección: sustituimos el team_id por el nombre usando la tabla equipos (celda de partidos)
eventos["seleccion_evento"] = eventos["seleccion_evento"].map(equipos["team_name"]) # sustituimos el team_id por la columna "team_name"

# Traducimos al español los tipos de evento y unificamos "VAR Review" y "Review VAR"
eventos["tipo_evento"] = eventos["tipo_evento"].map({"Goal": "gol", "Assist": "asistencia",  
                                                    "Yellow Card": "tarjeta amarilla", "Red Card": "tarjeta roja",
                                                    "Penalty Shootout Goal": "penalti marcado",
                                                    "Penalty Shootout Miss": "penalti fallado",
                                                    "VAR Review": "revision VAR", "Review VAR": "revision VAR"})

eventos = eventos.set_index("index_evento")


# Pasamos a entero las columnas que lo permiten. Usamos Int64 porque admite nulos.
eventos["minuto_evento"] = eventos["minuto_evento"].astype("Int64")
eventos["index_partido"] = eventos["index_partido"].astype("Int64")
display(eventos.dtypes)
display(eventos)



# APARTADO 4

# Utilizando las técnicas de clase, lleve a cabo la limpieza de los datasets y realice un tratamiento correcto de los valores duplicados, nulos y anómalos que pudieran
# contener. Justifique las medidas adoptadas (Consejo: antes de aplicar las medidas, es conveniente entender bien el contenido de los datasets, con apoyo, si hace
# falta, a través de algún gráfico de barras, histograma o métodos de análisis como .describe o .info. También es recomendable aplicar estas técnicas una vez
# seleccionadas únicamente las columnas de interés).

#PARTIDOS
#Visualizamos datos 
display(resumen(partidos))
for i in partidos.select_dtypes(exclude="number").columns:
    display(partidos[i].value_counts(dropna=False))

# Duplicados: había 6 filas repetidas (110 filas para 104 partidos). Son copias exactas, así que se eliminan.
partidos = partidos.drop_duplicates()
print("Partidos:", len(partidos), "| index_partido repetidos:", partidos.index.duplicated().sum())  # 104 | 0

# País: unificamos "usa" -> "USA"
partidos["pais_partido"] = partidos["pais_partido"].replace("usa", "USA")

# Ronda: los 4 NaN son los cuartos de final. En tournament_stages.csv el nombre aparece como "Quarter-finals "
# (con un espacio al final), por lo que no coincidió con la traducción y quedó vacío.
partidos["ronda"] = partidos["ronda"].fillna("Cuartos")
display(partidos["ronda"].value_counts())  # Grupos 72, Dieciseisavos 16, Octavos 8, Cuartos 4, Semifinales 2, Tercer puesto 1, Final 1

# Penaltis: los valores 20, 30 y 40 solo aparecen en los 4 partidos con result_type "Penalties" y son múltiplos de 10.
# Es un error de escala: dividiendo entre 10 se recuperan resultados de tanda válidos (3-4, 2-3, 2-4, 4-3).
partidos["penalty_visitante"] = partidos["penalty_visitante"] // 10
partidos["penalty_local"] = partidos["penalty_local"] // 10

# Árbitro: un partido (53) no tiene referee_id en el dataset original, así que no se puede recuperar
partidos["arbitro_partido"] = partidos["arbitro_partido"].fillna("Desconocido")

#JUGADORES
#Visualizamos datos 
display(resumen(jugadores))
for i in jugadores.select_dtypes(exclude="number").columns:
    display(jugadores[i].value_counts(dropna=False))



#hay 1241 nombres distintos para 1248 jugadores
mascara = jugadores.index.duplicated()

display(jugadores[mascara])
# Nombres truncados ("Mc"): tomamos el nombre completo de player_stats (mismo orden de filas que squads)
nombres_completos = df_squads_players["player_id"].map(stats["player_name"]).values
jugadores.index = np.where(jugadores.index == "Mc", nombres_completos, jugadores.index)

# Homónimos (Ali Ahmed): añadimos la selección al nombre
mascara_rep = jugadores.index.duplicated(keep=False)
jugadores.index = np.where(mascara_rep, jugadores.index + " (" + jugadores["seleccion_nacional"] + ")", jugadores.index)

jugadores.index.name = "nombre_jugador"   # np.where pierde el nombre del índice, lo volvemos a poner

# Codificación rota en los nombres de club (p. ej. "Be ş ikta ş  JK" -> "Beşiktaş JK")
jugadores["club_jugador"] = jugadores["club_jugador"].str.replace(" ş ", "ş", regex=False) # texto litearal, no expresion regular
jugadores["club_jugador"] = jugadores["club_jugador"].str.replace(" ń ", "ń", regex=False)

# Jugadores que no juegan (0 partidos y 0 minutos): sus estadísticas de conteo son 0, no un dato desconocido
mascara_no_jugo = jugadores["minutos_jugados"] == 0
for i in ["goles", "asistencias", "tiros", "tarjetas_amarillas", "tarjetas_rojas"]:
    jugadores.loc[mascara_no_jugo, i] = 0

# Paradas y goles concedidos solo aplican a porteros: en el resto ponemos 0
mascara_campo = jugadores["posicion"] != "portero"
jugadores.loc[mascara_campo, "paradas"] = 0
jugadores.loc[mascara_campo, "goles_concedidos"] = 0

# Calificación 0: son jugadores con 1-2 minutos sin valoración real -> nulo (se imputa en el aprtado 7)
jugadores.loc[jugadores["calificacion_media"] == 0, "calificacion_media"] =np.nan

# Valor de mercado 0: un jugador internacional no vale 0 -> nulo (se imputa en el apartado 7)
jugadores.loc[jugadores["valor_mercado"] == 0, "valor_mercado"] = np.nan

# Incoherencia: jugadores con más goles que tiros (un gol exige al menos un tiro)
mascara_tiros = jugadores["goles"] > jugadores["tiros"]
jugadores.loc[mascara_tiros, "tiros"] = jugadores.loc[mascara_tiros, "goles"]
# Comprobaciones
display(jugadores[jugadores.index.duplicated()])   # debe salir vacío
display(resumen(jugadores))

#EVENTOS
#Visualizamos datos 
display(resumen(eventos))
for i in eventos.select_dtypes(exclude="number").columns:
    display(eventos[i].value_counts(dropna=False))

#EVENTOS
# Eliminamos filas duplicadas
# En eventos hay 864 registros pero solo 835 valores distintos de index_evento
# 20 son copias exactas del mismo evento (todas las columnas coinciden)
# 9 son copias corruptas: o bien repiten el evento con un minuto imposible (999, 301, 350, 420, 500)
unic_index = (~eventos.index.duplicated())
eventos = eventos[unic_index]
# eliminamos las filas que son todo nulas (ej: -5,,,,,,,). Da la casualidad que esas filas también eran las que
# tenían un índice fuera del rango 1-829, ej -5
eventos = eventos.dropna(how="all")

# Nombres truncados ("Mc") y homónimos: usamos los nombres ya corregidos de jugadores.
# jugadores tiene el mismo orden de filas que squads, así que podemos emparejar cada player_id con su nombre corregido.
nombre_por_id = pd.Series(jugadores.index, index=df_squads_players["player_id"])
# Recuperamos el player_id de cada evento desde el dataset original a través de index_evento
id_por_evento = df_match_register.drop_duplicates(subset="event_id").set_index("event_id")["player_id"]
eventos["nombre_jugador"] = eventos.index.map(id_por_evento).map(nombre_por_id)


jugadores.index.name = "nombre_jugador"   # np.where pierde el nombre del índice, lo volvemos a poner

eventos.to_csv("eventos.csv")

# APARTADO 5
# Identifique en el dataset eventos los valores anómalos que deben excluirse, teniendo en cuenta los minutos anómalos o incorrectos y la consistencia en los tipos
# de eventos. No elimine los registros sin minuto asociado ya que se imputarán más adelante.

# la columna de minuto_evento contiene valores nulos o negativos, que obviamente no pueden darse
# estos eventos, en principio, deberían excluirse
anomalos = eventos["minuto_evento"] < 0
display(eventos[anomalos])

# por otro lado, las tandas de penalties se muestran asociadas al minuto 121. 

tanda_pen = eventos["minuto_evento"] == 121
display(eventos[tanda_pen].head())

# Minutos imposibles: negativos (-1, -2, -5, -10, -45) y 103 en un partido sin prórroga.
#    El evento es real, lo erróneo es el minuto: lo excluimos (NaN) para imputarlo en el apartado 7.
prorroga_evento = eventos["index_partido"].map(partidos["prorroga"])
minuto_negativo = eventos["minuto_evento"] < 0
minuto_excesivo = (eventos["minuto_evento"] > 100) & (eventos["minuto_evento"] != 121) & (prorroga_evento == "NO")
display(eventos[minuto_negativo | minuto_excesivo])
eventos.loc[minuto_negativo | minuto_excesivo, "minuto_evento"] = pd.NA

# Tandas de penaltis: se registran en el minuto 121. Los que no tienen minuto se ponen a 121 por coherencia.
tanda = eventos["tipo_evento"].isin(["penalti marcado", "penalti fallado"])
mascara = (eventos["minuto_evento"].isna()) & tanda
eventos.loc[mascara, "minuto_evento"] = 121

# Asistencias sin un gol de su equipo en el mismo partido y minuto: son inconsistentes y se excluyen.
#    (solo las que tienen minuto; las que no lo tienen no se pueden comprobar)
# En cada partido, la asistencia se registra justo después de su gol: miramos el evento anterior del mismo partido.
anterior_tipo = eventos.groupby("index_partido")["tipo_evento"].shift(1)
anterior_minuto = eventos.groupby("index_partido")["minuto_evento"].shift(1)
mascara = (eventos["tipo_evento"] == "asistencia") & (eventos["minuto_evento"].notna()) & \
          ((anterior_tipo != "gol") | (anterior_minuto != eventos["minuto_evento"]))
display(eventos[mascara])
eventos = eventos[~mascara]

# APARTADO 6. La fecha de los partidos aparece en distintos formatos. Utilizando expresiones regulares, identifique el patrón correspondiente a cada registro y reconstruya una columna “fecha_partido” homogénea con el día mes y año.

def corregir_fechas(fecha):
    # Diccionario para transformar los meses escritos a formato numérico
    meses = {"june":"06", "jun":"06", "junio":"06", "july":"07", "jul":"07", "julio":"07"}

    # Quitamos posibles espacios al principio o al final
    fecha = fecha.strip()

    # Caso: 20260614
    if re.fullmatch(r"\d{8}", fecha):
        año = fecha[0:4]
        mes = fecha[4:6]
        dia = fecha[6:8]

    # Caso: 2026-06-16T19:00:00Z
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}T.+", fecha):
        año = fecha[0:4]
        mes = fecha[5:7]
        dia = fecha[8:10]

    # Caso: 14 de junio de 2026
    elif re.fullmatch(r"\d{1,2}\s+de\s+(junio|julio)\s+de\s+\d{4}", fecha, re.IGNORECASE):
        partes = fecha.split()
        dia = partes[0].zfill(2)
        mes = meses[partes[2].lower()]
        año = partes[4]

    # Caso: June 13, 2026 o Jun 14 2026
    elif re.fullmatch(r"(June|Jun|July|Jul)\s+\d{1,2},?\s+\d{4}", fecha, re.IGNORECASE):
        partes = fecha.replace(",", "").split()
        mes = meses[partes[0].lower()]
        dia = partes[1].zfill(2)
        año = partes[2]

    # Caso: 12 June 2026
    elif re.fullmatch(r"\d{1,2}\s+(June|Jun|July|Jul)\s+\d{4}", fecha, re.IGNORECASE):
        partes = fecha.split()
        dia = partes[0].zfill(2)
        mes = meses[partes[1].lower()]
        año = partes[2]

    # Caso: 13-jun-26
    elif re.fullmatch(r"\d{1,2}-(jun|jul)-\d{2}", fecha, re.IGNORECASE):
        partes = fecha.split("-")
        dia = partes[0].zfill(2)
        mes = meses[partes[1].lower()]
        año = "20" + partes[2]

    # Casos numéricos con separadores: 11/06/2026, 06-15-2026, 14.06.2026...
    elif re.fullmatch(r"\d{1,2}[./-]\d{1,2}[./-]\d{4}", fecha):
        partes = re.split(r"[./-]", fecha)
        primero = int(partes[0])
        segundo = int(partes[1])
        año = partes[2]

        # Como sabemos que los meses solo pueden ser junio o julio,
        # si el primer valor es 6 o 7 y el segundo no, interpretamos primero como mes
        if primero in [6, 7] and segundo not in [6, 7]:
            mes = str(primero).zfill(2)
            dia = str(segundo).zfill(2)

        # En caso contrario interpretamos el primer valor como día y el segundo como mes
        else:
            dia = str(primero).zfill(2)
            mes = str(segundo).zfill(2)

    # Si no reconocemos el formato, dejamos la fecha como estaba
    else:
        print("Fecha no reconocida:", fecha)
        return fecha

    return dia + "/" + mes + "/" + año


partidos["fecha_partido"] = partidos["fecha_partido"].apply(corregir_fechas)

partidos["fecha_partido"]

# APARTADO 7. Observará que hay datos faltantes en algunas filas. Complete la información faltante utilizando las siguientes Técnicas de Imputación:

# Calculamos la media agrupada por seleccion y usamos map que funciona como indice = seleccion, valor = media, como si fuese un dicc
jugadores_seleccion_media = jugadores.groupby("seleccion_nacional")["valor_mercado"].mean()
jugadores["valor_mercado"] = jugadores["valor_mercado"].fillna(jugadores["seleccion_nacional"].map(jugadores_seleccion_media))

# Quedan valores nulos?
jugadores["valor_mercado"].isna().sum()

# REGRESIÓN PARA PORTEROS

train_porteros = jugadores[jugadores["posicion"] == "portero"].dropna(subset=["calificacion_media", "paradas", "goles_concedidos"])

modelo_porteros = LinearRegression().fit(
    train_porteros[["paradas", "goles_concedidos"]],
    train_porteros["calificacion_media"]
)

mask_porteros = (jugadores["posicion"] == "portero") & jugadores["calificacion_media"].isna() & jugadores["paradas"].notna() & jugadores["goles_concedidos"].notna()

jugadores.loc[mask_porteros, "calificacion_media"] = modelo_porteros.predict(
    jugadores.loc[mask_porteros, ["paradas", "goles_concedidos"]]
)


# REGRESIÓN PARA EL RESTO

train_jugadores = jugadores[jugadores["posicion"] != "portero"].dropna(subset=["calificacion_media", "goles", "asistencias", "tarjetas_amarillas", "tarjetas_rojas"])

modelo_jugadores = LinearRegression().fit(
    train_jugadores[["goles", "asistencias", "tarjetas_amarillas", "tarjetas_rojas"]],
    train_jugadores["calificacion_media"]
)

mask_jugadores = (jugadores["posicion"] != "portero") & jugadores["calificacion_media"].isna() & jugadores["goles"].notna() & jugadores["asistencias"].notna() & jugadores["tarjetas_amarillas"].notna() & jugadores["tarjetas_rojas"].notna()

jugadores.loc[mask_jugadores, "calificacion_media"] = modelo_jugadores.predict(
    jugadores.loc[mask_jugadores, ["goles", "asistencias", "tarjetas_amarillas", "tarjetas_rojas"]]
)
# Quedan valores nulos?
jugadores["calificacion_media"].isna().sum()

# interpolación + redondear y poner en int
eventos["minuto_evento"] = eventos.groupby("index_partido")["minuto_evento"].transform(lambda x: x.interpolate("linear", limit_direction="both")).round().astype(int) 

# Quedan valores nulos?

print(eventos["minuto_evento"].isna().sum())
print("Parece que no queda ningún valor sin rellenar")

# APARTADO 8. Finalmente, exporte los tres DataFrames a tres documentos Excel: partidosWC26.xlsx, eventosWC26.xlsx y jugadoresWC2026.xlsx

eventos.to_excel("eventosWC26.xlsx")
partidos.to_excel("partidosWC26.xlsx")
jugadores.to_excel("jugadoresWC2026.xlsx")
