import streamlit as st
import pandas as pd
import os
from datetime import datetime

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

# Función para guardar contacto
def guardar_estado_contacto(estado, referido_nombre="", referido_telefono=""):
    nuevo_registro = {
        'Fecha': datetime.now().strftime("%Y-%m-%d"),
        'Hora': datetime.now().strftime("%H:%M:%S"),
        'Agente': nombre_agente,
        'Contacto': st.session_state.nombre_contacto,
        'Estado': estado,
        'Referido_Nombre': referido_nombre,
        'Referido_Telefono': referido_telefono,
        'Observaciones': ""
    }

    if os.path.exists(archivo_excel):
        df_existente = pd.read_excel(archivo_excel)
        df_nuevo = pd.DataFrame([nuevo_registro])
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = pd.DataFrame([nuevo_registro])

    df_final.to_excel(archivo_excel, index=False)
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
            guardar_estado_contacto(estados_map[opcion])
            st.info("Fin de la llamada.")
            st.stop()

# Paso 2: Saludo
elif st.session_state.paso == 2:
    saludo = f"Buenos días/tardes, por favor... hoooolaaa mucho gusto hablas con {nombre_agente} de Michigan Master, ¿cómo estás {st.session_state.nombre_contacto}?"
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
                    guardar_estado_contacto("REFERIDO", referido_nombre, referido_tel)
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
                    guardar_estado_contacto("REFERIDO", referido_nombre, referido_tel)
                    st.success("Referido registrado.")
                    st.stop()

    elif st.session_state.nivel_respuesta == "Nivel intermedio o básico":
        guardar_estado_contacto("NIVEL_MEDIO_INTERES")
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
            guardar_estado_contacto(f"INCONVENIENTE_{inconveniente}")
            st.success(f"Inconveniente registrado: {inconveniente}")
            st.stop()

# Paso 7: Presentación del programa
elif st.session_state.paso == 7:
    presentacion = """Ok… Te comento cómo funciona Michigan. Somos un programa de primera categoría, cumplimos con los estándares educativos con la Secretaría de Educación y podemos certificarte nivel a nivel hasta un nivel B2. El programa tiene una duración máxima de 16 meses, es conversacional, semi personalizado y con horarios programables.

Las clases son en tiempo real con docentes, de lunes a viernes de 6am a 9pm y sábados de 8am a 5pm. Debes disponer de al menos 30 minutos para práctica libre. Al finalizar, puedes prepararte para exámenes como TOEFL, IELTS, MET o TOEIC, y obtener una certificación internacional APTIS o GEP. ¿Cómo te parece?"""
    st.markdown("### 🧾 Presentación del programa")
    st.info(presentacion)
    guardar_estado_contacto("PRESENTACION_PROGRAMA")
    st.success("Presentación registrada. Llamada finalizada.")
    st.stop()
