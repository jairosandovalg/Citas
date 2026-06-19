import streamlit as st
from datetime import datetime, timedelta

# Configuración visual de la ventana web
st.set_page_config(page_title="Taller - Reserva de Citas", page_icon="🚗", layout="centered")

st.title("🚗 Agenda de Citas - Taller Mecánico")
st.write("Selecciona el día y la hora para la atención de tu vehículo. Cada horario cuenta con un único cupo exclusivo.")

# 1. BASE DE DATOS TEMPORAL (Estructura interna con Cupo Único = 1)
if "agenda_taller" not in st.session_state:
    hoy = datetime.now().date()
    # Bloques horarios del taller
    horas_taller = ["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"]
    
    # Habilitamos una matriz de disponibilidad para los próximos 4 días de trabajo
    base_datos = {}
    for i in range(4):  
        fecha_str = str(hoy + timedelta(days=i))
        # Inicializamos cada hora con exactamente 1 cupo disponible
        base_datos[fecha_str] = {hora: 1 for hora in horas_taller}  
            
    st.session_state.agenda_taller = base_datos

# Historial para almacenar internamente lo que van registrando los clientes
if "registro_taller" not in st.session_state:
    st.session_state.registro_taller = []

# --- INTERFAZ DEL FORMULARIO ---

st.subheader("📅 1. Fecha de Atención")
fecha_sel = st.date_input(
    "Elige el día:",
    min_value=datetime.now().date(),
    max_value=datetime.now().date() + timedelta(days=3)
)
fecha_key = str(fecha_sel)

st.subheader("⏰ 2. Horarios Disponibles")
horarios_dia = st.session_state.agenda_taller.get(fecha_key, {})

# FILTRADO CRÍTICO: Creamos una lista solo con las horas cuyo cupo sea igual a 1
horas_libres = [hora for hora, cupo in horarios_dia.items() if cupo == 1]

if horas_libres:
    # Mostramos el componente selectbox pasando la lista limpia (sin textos de restantes)
    hora_elegida = st.selectbox("Selecciona la hora de ingreso de tu carro:", horas_libres)
else:
    st.error("🔴 Lo sentimos, todos los turnos para este día ya se encuentran ocupados por otros vehículos.")
    hora_elegida = None

st.subheader("📝 3. Detalles del Vehículo / Observaciones")
observacion = st.text_area(
    "Cuéntanos brevemente qué falla presenta o qué servicio requiere:",
    placeholder="Ej: Cambio de pastillas de freno, mantenimiento de los 10k, ruido en el motor..."
)

st.markdown("---")

# --- LÓGICA DE CONFIRMACIÓN ---
if hora_elegida:
    if st.button("Confirmar Cupo Exclusivo", type="primary"):
        # El cupo se bloquea inmediatamente pasando a 0 (Ocupado)
        st.session_state.agenda_taller[fecha_key][hora_elegida] = 0
        
        # Almacenamos el registro en la memoria del backend
        st.session_state.registro_taller.append({
            "Fecha": fecha_key,
            "Hora": hora_elegida,
            "Detalles": observacion if observacion else "No especificado"
        })
        
        # Mensaje de éxito en la pantalla
        st.success(f"¡Excelente! Turno reservado con éxito para el **{fecha_key}** a las **{hora_elegida}**. Te esperamos.")
        st.balloons() # Animación de celebración
        
        # Forzamos a Streamlit a recargar la página inmediatamente.
        # Al recargarse, el filtro leerá que esa hora ya vale 0 y no la dibujará en el menú.
        st.rerun()

# --- PANEL DE CONTROL INTERNO (Solo visible abajo para ver lo que se va llenando) ---
if st.session_state.registro_taller:
    with st.expander("📊 Ver órdenes registradas en el sistema (Historial del Servidor)"):
        st.dataframe(st.session_state.registro_taller)
