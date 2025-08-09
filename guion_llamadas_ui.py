import streamlit as st
import pandas as pd
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuración inicial de la página
st.set_page_config(page_title="Guion de Llamadas - Michigan Master", layout="centered")

# Título y encabezado
st.title("📞 Guion de Llamadas - Michigan Master")
st.markdown("Bienvenido al sistema interactivo para agentes. Sigue el guion paso a paso.")

# Variables fijas
nombre_agente = "Jonatan Diaz"
archivo_excel = "registro_llamadas.xlsx"

# Estados de sesión para navegación
if 'paso' not in st.session_state:
    st.session_state.paso = 0
if 'nombre_contacto' not in st.session_state:
    st.session_state.nombre_contacto = ''
if 'estado_llamada' not in st.session_state:
    st.session_state.estado_llamada = ''
if 'nivel_respuesta' not in st.session_state:
    st.session_state.nivel_respuesta = ''

# --- Configuración para Google Sheets ---
alcance = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

# Ruta al archivo JSON de la cuenta de servicio
ruta_json = r'C:\Users\jonat\Downloads\michigan\proyecto-michigan.json'
credenciales = ServiceAccountCredentials.from_json_keyfile_name(ruta_json, alcance)

# Autorización con Google Sheets
cliente = gspread.authorize(credenciales)

# Abre la hoja de cálculo (asegúrate que el nombre sea correcto)

# Obtener lista de pestañas disponibles en la hoja de cálculo
try:
    libro = cliente.open("FENIX 🦅✨")
    nombres_pestanas = [ws.title for ws in libro.worksheets()]
    nombre_pestana = st.selectbox("Selecciona la pestaña de la hoja de cálculo:", nombres_pestanas)
    hoja = libro.worksheet(nombre_pestana)
    st.success(f"Pestaña seleccionada: {nombre_pestana}")
    # Mostrar la hoja como tabla visual
    try:
        datos = hoja.get_all_values()
        if datos:
            encabezados = datos[0]
            # Si hay encabezados vacíos o duplicados, usa nombres genéricos
            if len(set(encabezados)) != len(encabezados) or any([h == '' for h in encabezados]):
                encabezados = [f"Columna {i+1}" for i in range(len(encabezados))]
            # Permitir editar los nombres de las columnas en la app
            if 'nombres_columnas' not in st.session_state or len(st.session_state.nombres_columnas) != len(encabezados):
                st.session_state.nombres_columnas = encabezados
            st.markdown("#### Edita los nombres de las columnas:")
            nuevos_nombres = []
            for i, nombre in enumerate(st.session_state.nombres_columnas):
                nuevo = st.text_input(f"Columna {i+1}", value=nombre, key=f"col_{i}")
                nuevos_nombres.append(nuevo if nuevo.strip() else f"Columna {i+1}")
            st.session_state.nombres_columnas = nuevos_nombres
            df = pd.DataFrame(datos[1:], columns=st.session_state.nombres_columnas)
            # Filtro de búsqueda
            st.markdown("#### Filtrar por columna:")
            columna_filtrar = st.selectbox("Selecciona columna para filtrar:", st.session_state.nombres_columnas)
            texto_filtrar = st.text_input("Texto a buscar:", "")
            if texto_filtrar:
                df_filtrado = df[df[columna_filtrar].astype(str).str.contains(texto_filtrar, case=False, na=False)]
            else:
                df_filtrado = df
        else:
            df_filtrado = pd.DataFrame()
        st.markdown("### Vista de la hoja seleccionada")
        st.dataframe(df_filtrado)

        # --- Recordatorio en la app ---
        st.markdown("#### Crear recordatorio para llamada")
        nombre_recordatorio = st.text_input("Nombre del contacto para recordar:", "", key="nombre_recordatorio")
        hora_recordatorio = st.time_input("Hora para el recordatorio:", key="hora_recordatorio")
        mensaje_recordatorio = st.text_input("Mensaje del recordatorio:", "Llamar al contacto", key="mensaje_recordatorio")
        if st.button("Guardar recordatorio"):
            st.session_state.recordatorio = {
                "nombre": nombre_recordatorio,
                "hora": hora_recordatorio,
                "mensaje": mensaje_recordatorio
            }
            st.success(f"Recordatorio guardado para {nombre_recordatorio} a las {hora_recordatorio}")

        # Mostrar alerta si es la hora del recordatorio
        import datetime
        ahora = datetime.datetime.now().time()
        if "recordatorio" in st.session_state:
            recordatorio = st.session_state["recordatorio"]
            if recordatorio["hora"] == ahora.replace(second=0, microsecond=0):
                st.warning(f"¡Recordatorio! {recordatorio['mensaje']} ({recordatorio['nombre']})")
    except Exception as e:
        st.error(f"No se pudo mostrar la hoja: {e}")
except Exception as e:
    st.error(f"No se pudo acceder a la hoja de cálculo: {e}")

# --- Fin de configuración para Google Sheets ---

# --- Prueba de acceso y edición a la hoja de cálculo ---
try:
    valores = hoja.get_all_values()
    st.write("Valores actuales en la hoja:", valores)
except Exception as e:
    st.error(f"No se pudo acceder a la hoja de cálculo: {e}")

# Función para guardar el estado del contacto en Google Sheets
def guardar_estado_contacto_google_sheets(estado, referido_nombre="", referido_telefono=""):
    nuevo_registro = [
        datetime.now().strftime("%Y-%m-%d"),  # Fecha
        datetime.now().strftime("%H:%M:%S"),  # Hora
        nombre_agente,  # Agente
        st.session_state.nombre_contacto,  # Nombre del contacto
        estado,  # Estado
        referido_nombre,  # Nombre referido
        referido_telefono,  # Teléfono referido
        ""  # Observaciones
    ]
    
    hoja.append_row(nuevo_registro)  # Añadir el nuevo registro a la hoja

    st.success(f"Estado guardado: {estado}")

# Paso 0: Configurar contacto
if st.session_state.paso == 0:
    with st.form("contacto_form"):
        nombre = st.text_input("👤 Nombre del contacto:")
        submitted = st.form_submit_button("Iniciar llamada")
        if submitted and nombre.strip():
            st.session_state.nombre_contacto = nombre.strip()
            st.session_state.paso = 1

# Paso 1: Estado de llamada
elif st.session_state.paso == 1:
    st.subheader(f"Llamando a: {st.session_state.nombre_contacto}")
    opcion = st.radio("¿Qué pasó con la llamada?", [
        "Contestó",
        "No contestó",
        "Teléfono apagado",
        "Rechazó la llamada"
    ])
    if st.button("Registrar estado"):
        if opcion == "Contestó":
            st.session_state.estado_llamada = "contesto"
            st.session_state.paso = 2
        else:
            estados_map = {
                "No contestó": "NO_CONTESTO",
                "Teléfono apagado": "TELEFONO_APAGADO",
                "Rechazó la llamada": "RECHAZO_LLAMADA"
            }
            guardar_estado_contacto_google_sheets(estados_map[opcion])  # Usar Google Sheets en lugar de Excel
            st.info("Fin de la llamada.")
            st.stop()

# Paso 2: Saludo
elif st.session_state.paso == 2:
    saludo = f"Buenos días/tardes, por favor... hoooolaaa mucho gusto hablas con {nombre_agente} de Michigan Master, ¿cómo estás {st.session_state.nombre_contacto}? "
    st.markdown("### 🗣️ Saludo inicial:")
    st.info(saludo)
    if st.button("Continuar con el guion"):
        st.session_state.paso = 3

# Paso 3: Intro FRIOS
elif st.session_state.paso == 3:
    intro = """Yo te estoy llamando porque mi empresa está apoyando una estrategia publicitaria y estamos seleccionando algunas personas para otorgarles un beneficio académico y financiero y se puedan capacitar en el idioma inglés.

Cuéntame, ¿tú ya hablas inglés fluidamente?"""
    st.markdown("### ❄️ Introducción (Contactos fríos)")
    st.warning(intro)
    # Opción para agendar recordatorio si la persona está ocupada
    st.markdown("#### ¿La persona está ocupada y desea que la llames después?")
    if st.checkbox("Agendar recordatorio para este contacto", key="recordatorio_intro"):
        numero_contacto = st.text_input("Número de contacto:", value=st.session_state.nombre_contacto, key="num_recordatorio_intro")
        fecha_recordatorio = st.date_input("Fecha para el recordatorio:", key="fecha_recordatorio_intro")
        hora_recordatorio = st.time_input("Hora para el recordatorio:", key="hora_recordatorio_intro")
        observacion_recordatorio = st.text_area("Observación (opcional):", key="obs_recordatorio_intro")
        if st.button("Guardar recordatorio", key="btn_recordatorio_intro"):
            st.session_state.recordatorio = {
                "nombre": st.session_state.nombre_contacto,
                "numero": numero_contacto,
                "fecha": fecha_recordatorio,
                "hora": hora_recordatorio,
                "observacion": observacion_recordatorio
            }
            st.success(f"Recordatorio guardado para {st.session_state.nombre_contacto} el {fecha_recordatorio} a las {hora_recordatorio}")
    
    if st.button("Continuar"):
        st.session_state.paso = 4

# Paso 4: Nivel de inglés
elif st.session_state.paso == 4:
    st.markdown("### 📊 Nivel de inglés del contacto")
    nivel = st.radio("Selecciona una opción:", [
        "No habla inglés",
        "Habla inglés fluidamente",
        "Nivel intermedio o básico",
        "Pregunta por qué lo llaman"
    ])
    # Opción para agendar recordatorio si la persona está ocupada
    st.markdown("#### ¿La persona está ocupada y desea que la llames después?")
    if st.checkbox("Agendar recordatorio para este contacto", key="recordatorio_nivel"):
        numero_contacto = st.text_input("Número de contacto:", value=st.session_state.nombre_contacto, key="num_recordatorio_nivel")
        fecha_recordatorio = st.date_input("Fecha para el recordatorio:", key="fecha_recordatorio_nivel")
        hora_recordatorio = st.time_input("Hora para el recordatorio:", key="hora_recordatorio_nivel")
        observacion_recordatorio = st.text_area("Observación (opcional):", key="obs_recordatorio_nivel")
        if st.button("Guardar recordatorio", key="btn_recordatorio_nivel"):
            st.session_state.recordatorio = {
                "nombre": st.session_state.nombre_contacto,
                "numero": numero_contacto,
                "fecha": fecha_recordatorio,
                "hora": hora_recordatorio,
                "observacion": observacion_recordatorio
            }
            st.success(f"Recordatorio guardado para {st.session_state.nombre_contacto} el {fecha_recordatorio} a las {hora_recordatorio}")
# Mostrar contador visual para el recordatorio
import datetime
if "recordatorio" in st.session_state:
    recordatorio = st.session_state["recordatorio"]
    fecha_hora_obj = datetime.datetime.combine(recordatorio["fecha"], recordatorio["hora"])
    ahora = datetime.datetime.now()
    tiempo_restante = fecha_hora_obj - ahora
    if tiempo_restante.total_seconds() > 0:
        st.info(f"⏳ Tiempo restante para llamar a {recordatorio['nombre']}: {str(tiempo_restante).split('.')[0]}")
    else:
        st.warning(f"¡Es momento de llamar a {recordatorio['nombre']}! Observación: {recordatorio['observacion']}")
        # Aquí podrías agregar el envío de correo automático
    if st.button("Responder"):
        if nivel == "Pregunta por qué lo llaman":
            explicacion = "La base de datos se construye con recomendaciones anónimas de estudiantes y solicitudes de información."
            st.info(explicacion)
        else:
            preguntas = {
                "No habla inglés": "¿Te gustaría aprenderlo en este momento?",
                "Habla inglés fluidamente": "¿Qué nivel de inglés? ¿Te gustaría perfeccionarlo?",
                "Nivel intermedio o básico": "Entonces, ¿sí te interesa aprender inglés en este momento?"
            }
            st.session_state.nivel_respuesta = nivel
            st.success(preguntas[nivel])
            st.session_state.paso = 5

# Paso 5: Procesar interés o cesión
elif st.session_state.paso == 5:
    if st.session_state.nivel_respuesta == "Habla inglés fluidamente":
        st.markdown("### ¿Quiere perfeccionar su inglés?")
        perfeccion = st.radio("", ["Sí, quiere perfeccionar", "No, no quiere perfeccionar"])
        if st.button("Procesar respuesta"):
            if perfeccion == "Sí, quiere perfeccionar":
                texto = """INVESTIGACIÓN: Bueno, te cuento qué estamos haciendo, en este momento la academia está apoyando una estrategia publicitaria, y está dispuesta a apoyar económicamente con una parte del costo total del programa a cambio de publicidad con el resultado del estudiante.

Cuéntame {0} ¿por qué te gustaría aprender inglés en este momento, es decir qué te motiva a hacerlo?""".format(st.session_state.nombre_contacto)
                st.info(texto)
                st.session_state.paso = 6
            else:
                referido_nombre = st.text_input("Nombre del referido:")
                referido_tel = st.text_input("Teléfono del referido:")
                if st.button("Guardar referido"):
                    guardar_estado_contacto_google_sheets("REFERIDO", referido_nombre, referido_tel)
                    st.success("Referido registrado.")
                    st.stop()

    elif st.session_state.nivel_respuesta == "No habla inglés":
        st.markdown("### ¿Desea aprender inglés?")
        aprender = st.radio("", ["Sí, quiere aprender", "No, no quiere aprender"])
        if st.button("Procesar respuesta"):
            if aprender == "Sí, quiere aprender":
                texto = """INVESTIGACIÓN: Bueno, te cuento qué estamos haciendo, en este momento la academia está apoyando una estrategia publicitaria, y está dispuesta a apoyar económicamente con una parte del costo total del programa a cambio de publicidad con el resultado del estudiante.

Cuéntame {0} ¿por qué te gustaría aprender inglés en este momento, es decir qué te motiva a hacerlo?""".format(st.session_state.nombre_contacto)
                st.info(texto)
                st.session_state.paso = 6
            else:
                referido_nombre = st.text_input("Nombre del referido:")
                referido_tel = st.text_input("Teléfono del referido:")
                if st.button("Guardar referido"):
                    guardar_estado_contacto_google_sheets("REFERIDO", referido_nombre, referido_tel)
                    st.success("Referido registrado.")
                    st.stop()

    elif st.session_state.nivel_respuesta == "Nivel intermedio o básico":
        guardar_estado_contacto_google_sheets("NIVEL_MEDIO_INTERES")
        st.success("Interés registrado. Puedes continuar según el guion interno.")
        st.stop()

# Paso 6: Seguimiento de investigación
elif st.session_state.paso == 6:
    seguimiento = "Teniendo en cuenta, que para ti es importante aprender inglés, {0}, ¿por qué no estás estudiándolo en este momento? Tal vez el tiempo, metodología, presupuesto u horarios. ¿Qué ha pasado?".format(st.session_state.nombre_contacto)
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
        if inconveniente == "SIN INCONVENIENTES":
            st.session_state.paso = 7
        else:
            guardar_estado_contacto_google_sheets(f"INCONVENIENTE_{inconveniente}")
            st.success(f"Inconveniente registrado: {inconveniente}")
            st.stop()

# Paso 7: Presentación del programa
elif st.session_state.paso == 7:
    presentacion = """Ok… Te comento cómo funciona Michigan. Somos un programa de primera categoría, cumplimos con los estándares educativos con la Secretaría de Educación y podemos certificarte nivel a nivel hasta un nivel B2. El programa tiene una duración máxima de 16 meses, es conversacional, semi personalizado y con horarios programables.

Las clases son en tiempo real con docentes, de lunes a viernes de 6am a 9pm y sábados de 8am a 5pm. Debes disponer de al menos 30 minutos para práctica libre. Al finalizar, puedes prepararte para exámenes como TOEFL, IELTS, MET o TOEIC, y obtener una certificación internacional APTIS o GEP. ¿Cómo te parece?"""
    st.markdown("### 🧾 Presentación del programa")
    st.info(presentacion)
    guardar_estado_contacto_google_sheets("PRESENTACION_PROGRAMA")
    st.success("Presentación registrada. Llamada finalizada.")
    st.stop()
