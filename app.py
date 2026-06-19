import streamlit as st
from datetime import datetime, timedelta

# Configuración de la página web (Genera el HTML/HTTP básico)
st.set_page_config(page_title="Reserva de Citas", page_icon="📅", layout="centered")

st.title("📅 Sistema de Reserva de Citas")
st.write("Selecciona una fecha, una hora disponible y déjanos tus comentarios para agendar tu cita.")

# 1. SIMULACIÓN DE BASE DE DATOS (Se ejecuta en el servidor)
# Inicializamos las horas y cupos disponibles si no existen en la sesión
if "agenda" not in st.session_state:
    # Vamos a crear citas disponibles para los próximos 3 días
    hoy = datetime.now().date()
    horas_permitidas = ["09:00 AM", "10:00 AM", "11:00 AM", "03:00 PM", "04:00 PM", "05:00 PM"]
    
    base_datos = {}
    for i in range(3):
        fecha_str = str(hoy + timedelta(days=i))
        base_datos[fecha_str] = {}
        for hora in horas_permitidas:
            # Inicializamos cada horario con 3 cupos disponibles
            base_datos[fecha_str][hora] = 3 
            
    st.session_state.agenda = base_datos

if "historial_reservas" not in st.session_state:
    st.session_state.historial_reservas = []

# --- INTERFAZ DE USUARIO ---

# 2. Selección de Fecha
st.subheader("1. Elige la Fecha")
fecha_seleccionada = st.date_input(
    "Selecciona el día de tu cita:",
    min_value=datetime.now().date(),
    max_value=datetime.now().date() + timedelta(days=2)
)
fecha_key = str(fecha_seleccionada)

# 3. Selección de Hora según disponibilidad
st.subheader("2. Elige la Hora")

# Obtenemos los horarios para la fecha seleccionada
horarios_del_dia = st.session_state.agenda.get(fecha_key, {})

# Filtrar solo las horas que aún tienen cupos (> 0)
horas_disponibles = [hora for hora, cupos in horarios_del_dia.items() if cupos > 0]

if horas_disponibles:
    # Mostramos un selector con las horas y cuántos cupos quedan marcados al lado
    opciones_selector = [f"{hora} ({horarios_del_dia[hora]} cupos restantes)" for hora in horas_disponibles]
    seleccion_usuario = st.selectbox("Horarios disponibles:", opciones_selector)
    
    # Extraer la hora limpia elegida (quitando el texto de los cupos)
    hora_elegida = seleccion_usuario.split(" (")[0]
else:
    st.error("🔴 Lo sentimos, no quedan horarios disponibles para esta fecha. Por favor, elige otro día.")
    hora_elegida = None

# 4. Campo de Observación
st.subheader("3. Información Adicional")
observacion = st.text_area(
    "Escribe alguna observación o requerimiento especial:",
    placeholder="Ej. Deseo que la reunión sea virtual / Tengo una consulta específica sobre..."
)

# 5. Botón para confirmar y restar cupo
st.markdown("---")
if hora_elegida:
    if st.button("Confirmar y Agendar Cita", type="primary"):
        # Restar 1 cupo de la "base de datos" en memoria
        st.session_state.agenda[fecha_key][hora_elegida] -= 1
        
        # Guardar el registro de la reserva
        nueva_reserva = {
            "Fecha": fecha_key,
            "Hora": hora_elegida,
            "Observación": observacion if observacion else "Ninguna"
        }
        st.session_state.historial_reservas.append(nueva_reserva)
        
        # Mensaje de éxito HTTP renderizado en pantalla
        st.success(f"¡Cita confirmada con éxito para el **{fecha_key}** a las **{hora_elegida}**!")
        st.balloons() # Animación gráfica de celebración
        
        # Forzar recarga corta para actualizar los cupos visualmente al instante
        st.rerun()

# --- VISTA DE ADMINISTRADOR / HISTORIAL (Opcional, abajo en la página) ---
if st.session_state.historial_reservas:
    with st.expander("📊 Ver Reservas Registradas (Historial del Servidor)"):
        st.write(st.session_state.historial_reservas)
