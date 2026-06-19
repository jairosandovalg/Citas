from flask import Flask, render_template, request, send_file, jsonify
from datetime import datetime
from weasyprint import HTML
import os
import tempfile
import traceback
from supabase import create_client, Client

app = Flask(__name__)

# Configuración de variables de entorno para Render
SUPABASE_URL = os.environ.get("SUPABASE_URL", "TU_SUPABASE_URL_AQUI")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "TU_SUPABASE_ANON_KEY_AQUI")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Lista maestra global de bloques horarios del taller
HORARIOS_MAESTROS = ["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"]

@app.route('/')
def home():
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    # Carga inicial por defecto con marca audi
    return render_template('pdf_template.html', es_pdf=False, fecha=fecha_hoy, marca='audi')

# --- RUTA DE DISPONIBILIDAD EN TIEMPO REAL ---
@app.route('/obtener-horarios', methods=['GET'])
def obtener_horarios():
    fecha = request.args.get('fecha')
    if not fecha:
        return jsonify([])

    try:
        # Consultamos en Supabase qué registros ya existen exactamente para esa fecha
        respuesta = supabase.table("inspecciones").select("hora").eq("fecha", fecha).execute()
        
        # Almacenamos en una lista las horas que ya fueron tomadas
        horas_ocupadas = [registro['hora'] for registro in respuesta.data]
        
        # Filtramos la lista maestra dejando únicamente las horas Libres
        horas_disponibles = [hora for hora in HORARIOS_MAESTROS if hora not in horas_ocupadas]
        
        return jsonify(horas_disponibles)
    except Exception as e:
        print(f"Error al consultar disponibilidad: {e}")
        # Retorno de seguridad en caso de fallo de conexión externa
        return jsonify(HORARIOS_MAESTROS)

# --- PROCESADOR CENTRAL DE FORMULARIOS ---
def procesar_inspeccion(sufijo_marca):
    datos_html = request.form.to_dict()

    if 'km' in datos_html and datos_html['km']:
        try:
            datos_html['km'] = int(datos_html['km'])
        except ValueError:
            datos_html['km'] = 0

    # Renderizado dinámico de la plantilla in
