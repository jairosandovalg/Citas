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
HORARIOS_MAESTROS = ["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"]

@app.route('/')
def home():
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    # Renderiza la web de forma limpia sin pasar marcas ficticias
    return render_template('pdf_template.html', fecha=fecha_hoy)

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
        return jsonify(HORARIOS_MAESTROS)

# --- RUTA ÚNICA PARA PROCESAR Y AGENDAR LA CITA ---
@app.route('/reservar-cita', methods=['POST'])
def reservar_cita():
    try:
        # Capturamos todos los datos que el usuario llenó en el formulario HTML
        datos_form = request.form.to_dict()

        # 1. RENDERIZAR PLANTILLA PARA EL PDF
        html = render_template(
            'pdf_template.html',
            es_pdf=True,
            nombre=datos_form.get('nombre', ''),
            apellido=datos_form.get('apellido', ''),
            correo=datos_form.get('correo', ''),
            telefono=datos_form.get('telefono', ''),
            orden=datos_form.get('orden', ''),
            placa=datos_form.get('placa', ''),
            fecha=datos_form.get('fecha', ''),
            hora=datos_form.get('hora', ''),
            observacion=datos_form.get('observacion', '')
        )

        # 2. GENERAR ARCHIVO PDF TEMPORAL
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        HTML(string=html, base_url=os.path.dirname(os.path.abspath(__file__))).write_pdf(pdf_file.name)

        n_orden = datos_form.get('orden', 'SIN_ORDEN').strip()
        placa = datos_form.get('placa', 'SIN_PLACA').strip()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo_pdf = f"{n_orden}_{placa}_{timestamp}.pdf"
        
        # 3. SUBIR PDF AL STORAGE DE SUPABASE
        url_publica = None
        try:
            with open(pdf_file.name, 'rb') as archivo_pdf:
                supabase.storage.from_('pdfs_formularios').upload(
                    file=archivo_pdf,
                    path=nombre_archivo_pdf,
                    file_options={"content-type": "application/pdf"}
                )
            url_publica = supabase.storage.from_('pdfs_formularios').get_public_url(nombre_archivo_pdf)
        except Exception as e:
            print(f"Alerta Storage: No se pudo subir el archivo: {e}")

        # Añadimos la URL del PDF a los datos que irán a la tabla
        if url_publica:
            datos_form['url_pdf'] = url_publica

        # 4. GUARDAR EN LA BASE DE DATOS DE SUPABASE (Ya no requiere limpiar sufijos de marcas)
        supabase.table("inspecciones").insert(datos_form).execute()

        # 5. RETORNAR EL ARCHIVO PDF PARA DESCARGA AUTOMÁTICA DEL CLIENTE
        return send_file(pdf_file.name, as_attachment=True, download_name=f"Cita_{n_orden}_{placa}.pdf")

    except Exception as e:
        return f"<h1>Error Interno al Procesar Cita:</h1><pre>{traceback.format_exc()}</pre>", 500

if __name__ == '__main__':
    app.run(debug=True)
