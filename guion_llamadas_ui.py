import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import datetime
import sqlite3

# --- Variables de sesión ---
if 'paso' not in st.session_state:
    st.session_state.paso = 0
if 'nombre_contacto' not in st.session_state:
    st.session_state.nombre_contacto = ''
if 'estado_llamada' not in st.session_state:
    st.session_state.estado_llamada = ''
if 'nivel_respuesta' not in st.session_state:
    st.session_state.nivel_respuesta = ''
if 'recordatorio' not in st.session_state:
    st.session_state.recordatorio = None

# --- Nombre del agente ---
nombre_agente = "Jonatan Diaz"

# --- Configuración para Google Sheets ---
alcance = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

# --- Seguridad en credenciales ---
try:
    if hasattr(st, "secrets") and "gcp" in st.secrets:
        credentials_info = dict(st.secrets["gcp"])
        credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=alcance)
    else:
        json_file_path = r'C:\Users\jonat\Downloads\michigan\proyecto-michigan.json'
        credentials = service_account.Credentials.from_service_account_file(json_file_path, scopes=alcance)
except Exception as e:
    st.error(f"No se pudo cargar las credenciales: {e}")
    st.stop()

# --- Autorización con Google Sheets ---
cliente = gspread.authorize(credentials)

# --- Conexión y creación de base de datos SQLite ---
conn = sqlite3.connect('michigan.db', check_same_thread=False)
cursor = conn.cursor()

# Crear tablas si no existen
cursor.execute('''
CREATE TABLE IF NOT EXISTS agentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS llamadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agente_id INTEGER,
    contacto TEXT,
    estado TEXT,
    fecha TEXT,
    hora TEXT,
    observaciones TEXT,
    FOREIGN KEY (agente_id) REFERENCES agentes(id)
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS recordatorios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agente_id INTEGER,
    contacto TEXT,
    mensaje TEXT,
    fecha TEXT,
    hora TEXT,
    creado TEXT,
    FOREIGN KEY (agente_id) REFERENCES agentes(id)
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS encabezados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_pestana TEXT,
    encabezados TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS columnas_visibles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_pestana TEXT,
    columnas TEXT
)
''')
conn.commit()

def get_agente_id(nombre_agente):
    cursor.execute('SELECT id FROM agentes WHERE nombre=?', (nombre_agente,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('INSERT INTO agentes (nombre) VALUES (?)', (nombre_agente,))
    conn.commit()
    return cursor.lastrowid

def guardar_llamada(nombre_agente, contacto, estado, fecha, hora, observaciones):
    agente_id = get_agente_id(nombre_agente)
    cursor.execute('''
        INSERT INTO llamadas (agente_id, contacto, estado, fecha, hora, observaciones)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (agente_id, contacto, estado, fecha, hora, observaciones))
    conn.commit()

def guardar_recordatorio(nombre_agente, contacto, mensaje, fecha, hora, creado):
    agente_id = get_agente_id(nombre_agente)
    cursor.execute('''
        INSERT INTO recordatorios (agente_id, contacto, mensaje, fecha, hora, creado)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (agente_id, contacto, mensaje, fecha, hora, creado))
    conn.commit()

def obtener_llamadas(nombre_agente):
    agente_id = get_agente_id(nombre_agente)
    df = pd.read_sql_query('SELECT * FROM llamadas WHERE agente_id=?', conn, params=(agente_id,))
    return df

def obtener_recordatorios(nombre_agente):
    agente_id = get_agente_id(nombre_agente)
    df = pd.read_sql_query('SELECT * FROM recordatorios WHERE agente_id=?', conn, params=(agente_id,))
    return df

def guardar_encabezados(nombre_pestana, encabezados_lista):
    encabezados_str = ','.join(encabezados_lista)
    cursor.execute('DELETE FROM encabezados WHERE nombre_pestana=?', (nombre_pestana,))
    cursor.execute('INSERT INTO encabezados (nombre_pestana, encabezados) VALUES (?, ?)', (nombre_pestana, encabezados_str))
    conn.commit()

def obtener_encabezados(nombre_pestana):
    cursor.execute('SELECT encabezados FROM encabezados WHERE nombre_pestana=?', (nombre_pestana,))
    row = cursor.fetchone()
    if row:
        return row[0].split(',')
    return None

def guardar_columnas_visibles(nombre_pestana, columnas_visibles):
    columnas_str = ','.join(columnas_visibles)
    cursor.execute('DELETE FROM columnas_visibles WHERE nombre_pestana=?', (nombre_pestana,))
    cursor.execute('INSERT INTO columnas_visibles (nombre_pestana, columnas) VALUES (?, ?)', (nombre_pestana, columnas_str))
    conn.commit()

def obtener_columnas_visibles(nombre_pestana):
    cursor.execute('SELECT columnas FROM columnas_visibles WHERE nombre_pestana=?', (nombre_pestana,))
    row = cursor.fetchone()
    if row:
        return row[0].split(',')
    return None

# --- Selector de pestaña dinámico con cache en sesión ---
libro = cliente.open("FENIX 🦅✨")
nombres_pestanas = [ws.title for ws in libro.worksheets()]

if 'pestana_seleccionada' not in st.session_state:
    st.session_state.pestana_seleccionada = nombres_pestanas[0]

nombre_pestana = st.selectbox(
    "Selecciona la pestaña que quieres usar:",
    nombres_pestanas,
    index=nombres_pestanas.index(st.session_state.pestana_seleccionada)
)

if nombre_pestana != st.session_state.pestana_seleccionada:
    st.session_state.pestana_seleccionada = nombre_pestana

hoja = libro.worksheet(nombre_pestana)
st.success(f"Pestaña seleccionada: {nombre_pestana}")

# --- Mostrar la hoja como tabla visual ---
datos = hoja.get_all_values()
if datos:
    encabezados = datos[0]
    encabezados = [
        nombre if nombre.strip() else f"Columna_{i+1}"
        for i, nombre in enumerate(encabezados)
    ]
    vistos = {}
    for i, nombre in enumerate(encabezados):
        if nombre in vistos:
            vistos[nombre] += 1
            encabezados[i] = f"{nombre}_{vistos[nombre]}"
        else:
            vistos[nombre] = 1

    encabezados_db = obtener_encabezados(nombre_pestana)
    if encabezados_db:
        if len(encabezados) > len(encabezados_db):
            encabezados_db += [f"Columna_{i+1}" for i in range(len(encabezados_db), len(encabezados))]
        encabezados_mostrar = encabezados_db
    else:
        encabezados_mostrar = encabezados

    # Cargar columnas visibles desde la base de datos
    columnas_visibles_db = obtener_columnas_visibles(nombre_pestana)
    if columnas_visibles_db:
        columnas_visibles = [col for col in columnas_visibles_db if col in encabezados_mostrar]
    else:
        columnas_visibles = encabezados_mostrar

    st.markdown("### Vista de la hoja seleccionada")
    columnas_visibles = st.multiselect(
        "Selecciona las columnas que quieres ver:",
        options=list(encabezados_mostrar),
        default=list(columnas_visibles)
    )
    df = pd.DataFrame(datos[1:], columns=encabezados_mostrar)
    st.dataframe(df[columnas_visibles])

    # Editar solo los nombres de las columnas visibles
    st.markdown("#### Edita los nombres de las columnas visibles:")
    nuevos_nombres = []
    for i, nombre in enumerate(columnas_visibles):
        key_col = f"col_{i}_{nombre_pestana}"
        if key_col not in st.session_state:
            st.session_state[key_col] = nombre
        nuevo = st.text_input(f"Columna {i+1}", value=st.session_state[key_col], key=key_col)
        nuevos_nombres.append(nuevo if nuevo.strip() else f"Columna_{i+1}")

    guardar_columnas = st.button("Guardar nombres y selección de columnas en la base de datos")
    if guardar_columnas:
        guardar_encabezados(nombre_pestana, nuevos_nombres)
        guardar_columnas_visibles(nombre_pestana, columnas_visibles)
        st.success("¡Nombres y selección de columnas guardados en la base de datos!")
        st.rerun()

    st.markdown("#### Filtrar por columna:")
    columna_filtrar = st.selectbox("Selecciona columna para filtrar:", columnas_visibles)
    texto_filtrar = st.text_input("Texto a buscar:", "")
    if texto_filtrar:
        df_filtrado = df[df[columna_filtrar].astype(str).str.contains(texto_filtrar, case=False, na=False)]
    else:
        df_filtrado = df

else:
    df_filtrado = pd.DataFrame()
    st.markdown("### Vista de la hoja seleccionada")
    st.dataframe(df_filtrado)

# --- Flujo del guion ---
if st.session_state.paso == 0:
    contactos_lista = df_filtrado[df_filtrado.columns[0]].tolist() if not df_filtrado.empty else []
    nombre = st.selectbox("👤 Selecciona el contacto a llamar:", contactos_lista)
    submitted = st.button("Iniciar llamada")
    if submitted and nombre:
        st.session_state.nombre_contacto = nombre
        st.session_state.paso = 1
        st.rerun()

elif st.session_state.paso == 1:
    st.subheader(f"Llamando a: {st.session_state.nombre_contacto}")
    opcion = st.radio("¿Qué pasó con la llamada?", [
        "Contestó",
        "No contestó",
        "Teléfono apagado",
        "Rechazó la llamada"
    ])
    if st.button("Registrar estado"):
        fecha = datetime.now().strftime("%Y-%m-%d")
        hora = datetime.now().strftime("%H:%M:%S")
        if opcion == "Contestó":
            st.session_state.estado_llamada = "contesto"
            guardar_llamada(nombre_agente, st.session_state.nombre_contacto, "CONTESTO", fecha, hora, "")
            st.session_state.paso = 2
            st.rerun()
        else:
            estados_map = {
                "No contestó": "NO_CONTESTO",
                "Teléfono apagado": "TELEFONO_APAGADO",
                "Rechazó la llamada": "RECHAZO_LLAMADA"
            }
            guardar_llamada(nombre_agente, st.session_state.nombre_contacto, estados_map[opcion], fecha, hora, "")
            st.info("Fin de la llamada.")
            st.stop()

elif st.session_state.paso == 2:
    saludo = f"Buenos días/tardes, por favor... hoooolaaa mucho gusto hablas con {nombre_agente} de Michigan Master, ¿cómo estás {st.session_state.nombre_contacto}? "
    st.markdown("### 🗣️ Saludo inicial:")
    st.info(saludo)
    if st.button("Continuar con el guion"):
        st.session_state.paso = 3
        st.rerun()

elif st.session_state.paso == 3:
    intro = """Yo te estoy llamando porque mi empresa está apoyando una estrategia publicitaria y estamos seleccionando algunas personas para otorgarles un beneficio académico y financiero y se puedan capacitar en el idioma inglés.

Cuéntame, ¿tú ya hablas inglés fluidamente?"""
    st.markdown("### ❄️ Introducción (Contactos fríos)")
    st.warning(intro)
    st.markdown("#### ¿La persona está ocupada y desea que la llames después?")
    if st.checkbox("Agendar recordatorio para este contacto", key="recordatorio_intro"):
        fecha_recordatorio = st.date_input("Fecha para el recordatorio:", key="fecha_recordatorio_intro")
        hora_recordatorio = st.time_input("Hora para el recordatorio:", key="hora_recordatorio_intro")
        mensaje_recordatorio = st.text_input("Mensaje del recordatorio:", "Llamar al contacto", key="mensaje_recordatorio_intro")
        if st.button("Guardar recordatorio", key="btn_recordatorio_intro"):
            guardar_recordatorio(
                nombre_agente,
                st.session_state.nombre_contacto,
                mensaje_recordatorio,
                str(fecha_recordatorio),
                str(hora_recordatorio),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            st.success(f"Recordatorio guardado para {st.session_state.nombre_contacto} el {fecha_recordatorio} a las {hora_recordatorio}")
    if st.button("Continuar"):
        st.session_state.paso = 4
        st.rerun()

elif st.session_state.paso == 4:
    st.markdown("### 📊 Nivel de inglés del contacto")
    nivel = st.radio("Selecciona una opción:", [
        "No habla inglés",
        "Habla inglés fluidamente",
        "Nivel intermedio o básico",
        "Pregunta por qué lo llaman"
    ])
    st.session_state.nivel_respuesta = nivel
    st.markdown("#### ¿La persona está ocupada y desea que la llames después?")
    if st.checkbox("Agendar recordatorio para este contacto", key="recordatorio_nivel"):
        fecha_recordatorio = st.date_input("Fecha para el recordatorio:", key="fecha_recordatorio_nivel")
        hora_recordatorio = st.time_input("Hora para el recordatorio:", key="hora_recordatorio_nivel")
        mensaje_recordatorio = st.text_input("Mensaje del recordatorio:", "Llamar al contacto", key="mensaje_recordatorio_nivel")
        if st.button("Guardar recordatorio", key="btn_recordatorio_nivel"):
            guardar_recordatorio(
                nombre_agente,
                st.session_state.nombre_contacto,
                mensaje_recordatorio,
                str(fecha_recordatorio),
                str(hora_recordatorio),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            st.success(f"Recordatorio guardado para {st.session_state.nombre_contacto} el {fecha_recordatorio} a las {hora_recordatorio}")

    if st.button("Continuar con el guion"):
        st.session_state.paso = 5
        st.rerun()

elif st.session_state.paso == 5:
    if st.session_state.nivel_respuesta == "Habla inglés fluidamente":
        st.markdown("### ¿Quiere perfeccionar su inglés?")
        perfeccion = st.radio("", ["Sí, quiere perfeccionar", "No, no quiere perfeccionar"])
        if perfeccion == "Sí, quiere perfeccionar":
            if st.button("Procesar respuesta"):
                texto = f"""INVESTIGACIÓN: Bueno, te cuento qué estamos haciendo, en este momento la academia está apoyando una estrategia publicitaria, y está dispuesta a apoyar económicamente con una parte del costo total del programa a cambio de publicidad con el resultado del estudiante.

Cuéntame {st.session_state.nombre_contacto} ¿por qué te gustaría aprender inglés en este momento, es decir qué te motiva a hacerlo?"""
                st.info(texto)
                st.session_state.paso = 6
                st.rerun()
        else:
            referido_nombre = st.text_input("Nombre del referido:")
            referido_tel = st.text_input("Teléfono del referido:")
            if st.button("Guardar referido"):
                fecha = datetime.now().strftime("%Y-%m-%d")
                hora = datetime.now().strftime("%H:%M:%S")
                guardar_llamada(nombre_agente, referido_nombre, "REFERIDO", fecha, hora, referido_tel)
                st.success("Referido registrado.")
                st.stop()
    elif st.session_state.nivel_respuesta == "No habla inglés":
        st.markdown("### ¿Desea aprender inglés?")
        aprender = st.radio("", ["Sí, quiere aprender", "No, no quiere aprender"])
        if aprender == "Sí, quiere aprender":
            if st.button("Procesar respuesta"):
                texto = f"""INVESTIGACIÓN: Bueno, te cuento qué estamos haciendo, en este momento la academia está apoyando una estrategia publicitaria, y está dispuesta a apoyar económicamente con una parte del costo total del programa a cambio de publicidad con el resultado del estudiante.

Cuéntame {st.session_state.nombre_contacto} ¿por qué te gustaría aprender inglés en este momento, es decir qué te motiva a hacerlo?"""
                st.info(texto)
                st.session_state.paso = 6
                st.rerun()
        else:
            referido_nombre = st.text_input("Nombre del referido:")
            referido_tel = st.text_input("Teléfono del referido:")
            if st.button("Guardar referido"):
                fecha = datetime.now().strftime("%Y-%m-%d")
                hora = datetime.now().strftime("%H:%M:%S")
                guardar_llamada(nombre_agente, referido_nombre, "REFERIDO", fecha, hora, referido_tel)
                st.success("Referido registrado.")
                st.stop()
    elif st.session_state.nivel_respuesta == "Nivel intermedio o básico":
        fecha = datetime.now().strftime("%Y-%m-%d")
        hora = datetime.now().strftime("%H:%M:%S")
        guardar_llamada(nombre_agente, st.session_state.nombre_contacto, "NIVEL_MEDIO_INTERES", fecha, hora, "")
        st.success("Interés registrado. Puedes continuar según el guion interno.")
        st.stop()

elif st.session_state.paso == 6:
    seguimiento = f"Teniendo en cuenta, que para ti es importante aprender inglés, {st.session_state.nombre_contacto}, ¿por qué no estás estudiándolo en este momento? Tal vez el tiempo, metodología, presupuesto u horarios. ¿Qué ha pasado?"
    st.markdown("### 🔍 Seguimiento a la motivación")
    st.info(seguimiento)
    inconveniente = st.selectbox("Selecciona el principal inconveniente:", [
        "TIEMPO",
        "DINERO",
        "METODOLOGÍA",
        "HORARIOS",
        "SIN INCONVENIENTES"
    ])
    if st.button("Registrar inconveniente"):
        fecha = datetime.now().strftime("%Y-%m-%d")
        hora = datetime.now().strftime("%H:%M:%S")
        if inconveniente == "SIN INCONVENIENTES":
            st.session_state.paso = 7
            st.rerun()
        else:
            guardar_llamada(nombre_agente, st.session_state.nombre_contacto, f"INCONVENIENTE_{inconveniente}", fecha, hora, "")
            st.success(f"Inconveniente registrado: {inconveniente}")
            st.stop()

elif st.session_state.paso == 7:
    presentacion = """Ok… Te comento cómo funciona Michigan. Somos un programa de primera categoría, cumplimos con los estándares educativos con la Secretaría de Educación y podemos certificarte nivel a nivel hasta un nivel B2. El programa tiene una duración máxima de 16 meses, es conversacional, semi personalizado y con horarios programables.

Las clases son en tiempo real con docentes, de lunes a viernes de 6am a 9pm y sábados de 8am a 5pm. Debes disponer de al menos 30 minutos para práctica libre. Al finalizar, puedes prepararte para exámenes como TOEFL, IELTS, MET o TOEIC, y obtener una certificación internacional APTIS o GEP. ¿Cómo te parece?"""
    st.markdown("### 🧾 Presentación del programa")
    st.info(presentacion)
    fecha = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M:%S")
    guardar_llamada(nombre_agente, st.session_state.nombre_contacto, "PRESENTACION_PROGRAMA", fecha, hora, "")
    st.success("Presentación registrada. Llamada finalizada.")
    st.stop()

# --- Mostrar historial de llamadas y recordatorios del agente ---
st.markdown("## Historial de llamadas")
llamadas_hist = obtener_llamadas(nombre_agente)
st.dataframe(llamadas_hist)

st.markdown("## Recordatorios del agente")
recordatorios_hist = obtener_recordatorios(nombre_agente)
st.dataframe(recordatorios_hist)