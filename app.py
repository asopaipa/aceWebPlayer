from flask import Flask, render_template, request, redirect, url_for, send_from_directory, Response, abort, send_file
from getLinks import generar_m3u_from_url, decode_default_url
import re
import os
import json
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import requests
import io
import threading
import time
import shutil
from pathlib import Path
from werkzeug.utils import safe_join
from operator import itemgetter


app = Flask(__name__)

EPG_XML_PATH = os.getenv("EPG_XML_PATH", 'https://epgshare01.online/epgshare01/epg_ripper_ES1.xml.gz')

# Define las credenciales
USERNAME = "" #si está vacía, no se requerirá autenticación
PASSWORD = ""  

# Ruta del archivo donde se guardarán los datos persistidos
DATA_FILE = "urls.json"

def save_to_file(textarea1, textarea2, checkbox, file_input):
    """
    Guarda los datos de los dos textareas y el estado del checkbox en un archivo JSON.
    
    :param textarea1: Contenido del primer textarea (cadena).
    :param textarea2: Contenido del segundo textarea (cadena).
    :param checkbox: Estado del checkbox (True o False).
    :param file_input: Ruta del archivo donde se guardarán los datos.
    """
    data = {
        "textarea1": textarea1 if textarea1 is not None else "",
        "textarea2": textarea2 if textarea2 is not None else "",
        "checkbox": checkbox
    }
    
    with open(file_input, "w") as file:
        json.dump(data, file)

def load_from_file(file_input):
    """
    Carga los datos de los dos textareas y el estado del checkbox desde un archivo JSON.
    
    :param file_input: Ruta del archivo desde donde se cargarán los datos.
    :return: Una tupla con el contenido de textarea1, textarea2 y el estado del checkbox.
    """
    if os.path.exists(file_input):
        with open(file_input, "r") as file:
            try:
                data = json.load(file)
                textarea1 = data.get("textarea1", "")
                textarea2 = data.get("textarea2", "")
                checkbox = data.get("checkbox", False)
                return textarea1, textarea2, checkbox
            except json.JSONDecodeError:
                # En caso de error al leer el JSON, devolver valores por defecto
                return "", "", False
    # Si el archivo no existe, devolver valores por defecto
    return "", "", False

    
def requires_auth(f):
    def decorated(*args, **kwargs):
        # Si el usuario está vacío, no aplica la autenticación
        if not USERNAME:
            return f(*args, **kwargs)

        auth = request.authorization
        if not auth or auth.username != USERNAME or auth.password != PASSWORD:
            return Response(
                "Necesitas autenticarte para acceder.\n",
                401,
                {"WWW-Authenticate": 'Basic realm="Login Required"'},
            )
        return f(*args, **kwargs)
    # Hacer el decorador compatible con Flask
    decorated.__name__ = f.__name__
    return decorated


class Channel:
    def __init__(self, name, id, logo, group, tvg_id):
        self.name = name
        self.id = id
        self.logo = logo
        self.group = group
        self.tvg_id = tvg_id
        self.current_program = None
        self.current_program_time = None
        self.next_program = None
        self.next_program_time = None

def parse_time(time_str):
    try:
        # Remove spaces and handle timezone offset
        time_str = time_str.replace(' ', '')
        date_part = time_str[:14]  # YYYYMMDDHHMMSS
        tz_part = time_str[14:]    # +HHMM or -HHMM
        
        # Parse the base datetime
        dt = datetime.strptime(date_part, '%Y%m%d%H%M%S')
        
        # Handle timezone offset
        if tz_part:
            sign = 1 if tz_part[0] == '+' else -1
            hours = int(tz_part[1:3])
            minutes = int(tz_part[3:5]) if len(tz_part) >= 5 else 0
            offset = sign * (hours * 60 + minutes) * 60  # Convert to seconds
            
            # Create timezone aware datetime
            return dt.replace(tzinfo=pytz.FixedOffset(offset // 60))
        
        return dt.replace(tzinfo=pytz.UTC)
    except Exception as e:
        print(f"Error parsing time {time_str}: {e}")
        return None

def parse_epg(epg_url):
    epg_data = {}
    try:
        print(f"Downloading EPG data from {epg_url}...")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br'
        })

        response = session.get(epg_url, stream=True, timeout=30)
        response.raise_for_status()
        
        print("Download completed. Parsing XML...")
        
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
            tree = ET.parse(f)
            root = tree.getroot()

        # Debug information
        channels = root.findall('.//channel')
        programmes = root.findall('.//programme')
        print(f"Found {len(channels)} channels and {len(programmes)} programmes")

        for programme in root.findall('.//programme'):
            channel_id = programme.get('channel')
            if not channel_id:
                continue

            start_time = parse_time(programme.get('start'))
            stop_time = parse_time(programme.get('stop'))
            
            if not start_time or not stop_time:
                continue
                
            title_elem = programme.find('title')
            title = title_elem.text if title_elem is not None else 'No Title'

            if channel_id not in epg_data:
                epg_data[channel_id] = []

            epg_data[channel_id].append({
                'start': start_time,
                'stop': stop_time,
                'title': title
            })

        # Sort programs by start time
        for channel_id in epg_data:
            epg_data[channel_id].sort(key=lambda x: x['start'])

        print(f"EPG parsing completed. Found {len(epg_data)} channels")
        # Debug: Print some channel IDs
        print("Sample channel IDs:", list(epg_data.keys())[:5])
        return epg_data

    except Exception as e:
        print(f"Error in parse_epg: {e}")
        return {}

def get_current_and_next_program(programs, now):
    """Get current and next program based on current time"""
    current_program = None
    next_program = None
    
    # Convert now to UTC if it's not already timezone aware
    if now.tzinfo is None:
        now = pytz.UTC.localize(now)
    
    # Sort programs by start time
    sorted_programs = sorted(programs, key=lambda x: x['start'])
    
    # Find current program
    for i, program in enumerate(sorted_programs):
        program_start = program['start']
        program_end = program['stop']
        
        # Convert to UTC for comparison
        if program_start.tzinfo != pytz.UTC:
            program_start = program_start.astimezone(pytz.UTC)
        if program_end.tzinfo != pytz.UTC:
            program_end = program_end.astimezone(pytz.UTC)
            
        if program_start <= now < program_end:
            current_program = program
            if i + 1 < len(sorted_programs):
                next_program = sorted_programs[i + 1]
            break
    
    return current_program, next_program

def parse_m3u(content):
    channels = []
    current_channel = None
    
    for line in content.splitlines():
        if line.startswith('#EXTINF:'):
            tvg_id_match = re.search('tvg-id="(.*?)"', line)
            logo_match = re.search('tvg-logo="(.*?)"', line)
            group_match = re.search('group-title="(.*?)"', line)
            name = line.split(',')[-1].strip()
            
            current_channel = Channel(
                name=name,
                id=None,
                logo=logo_match.group(1) if logo_match else "",
                group=group_match.group(1) if group_match else "Sin categoría",
                tvg_id=tvg_id_match.group(1) if tvg_id_match else None
            )
        elif line.startswith('acestream://') and current_channel:
            current_channel.id = line.replace('acestream://', '').strip()
            channels.append(current_channel)
            current_channel = None
            
    return channels

# Global EPG cache
epg_data_cache = {}
epg_last_updated = None

def update_epg_data():
    global epg_data_cache, epg_last_updated
    while True:
        try:
            print("Updating EPG data...")
            epg_data_cache = parse_epg(EPG_XML_PATH)
            epg_last_updated = datetime.now(pytz.UTC)
            print("EPG update completed")
        except Exception as e:
            print(f"Error updating EPG: {e}")
        time.sleep(6 * 60 * 60)  # Update every 6 hours

@app.route('/download/<filename>')
@requires_auth
def download_file(filename):
    # Directorio donde están los archivos
    directory = "resources"
    try:
        # Descargar el archivo
    
        # Lista de nombres permitidos
        archivos_permitidos = ["acestream_directos.m3u", "web_directos.m3u", "acestream_pelis.m3u", "web_pelis.m3u"]
    
        # Validar si el archivo es permitido
        if filename not in archivos_permitidos:
            abort(403, description="Archivo no autorizado para la descarga.")
        
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        return f"El archivo {filename} no existe.", 404



@app.route('/', methods=['GET', 'POST'])
@requires_auth
def index():
    channels = []
    groups = set()
    
    if request.method == 'POST':
        if request.form.get('default_list') == 'true':
            direccion_bytes, direccion_pelis_bytes = decode_default_url()
            direccion = direccion_bytes.decode("utf-8")
            direccion_pelis = direccion_pelis_bytes.decode("utf-8")
            save_to_file(direccion, direccion_pelis, False, DATA_FILE)       
            # Procesar cada línea como una URL
            urls = [direccion]
            urls_pelis = [direccion_pelis]
            generar_m3u_from_url(request.host, urls, "directos")
            generar_m3u_from_url(request.host, urls_pelis, "pelis")
            textarea_content = direccion
            textarea_content_pelis = direccion_pelis
            export_strm = False
        elif request.form.get('submit_url') == 'true':
            # Obtener los datos enviados desde el formulario
            textarea_content = request.form.get('urlInput', '').strip()      
            textarea_content_pelis = request.form.get('urlInputPelis', '').strip()   
            export_strm = False
            export_strm = 'export_strm' in request.form
            # Guardar los datos en el archivo
            save_to_file(textarea_content,textarea_content_pelis,export_strm,DATA_FILE)       
            # Procesar cada línea como una URL
            urls = [url.strip() for url in textarea_content.splitlines() if url.strip()]
            urls_pelis = [url.strip() for url in textarea_content_pelis.splitlines() if url.strip()]
            generar_m3u_from_url(request.host, urls, "directos")
            generar_m3u_from_url(request.host, urls_pelis, "pelis")
    else:
        # Cargar los datos persistidos desde el archivo
        textarea_content, textarea_content_pelis, export_strm  =  load_from_file(DATA_FILE)

    if export_strm:
        
        # Procesar directos y películas
        procesar_directos("resources/acestream_directos.m3u", "output_strm/acestream")
        procesar_peliculas("resources/acestream_pelis.m3u", "output_strm/acestream")

        procesar_directos("resources/web_directos.m3u", "output_strm/web")
        procesar_peliculas("resources/web_pelis.m3u", "output_strm/web")
    else:
        if os.path.exists("output_strm/acestream"):
            shutil.rmtree("output_strm/acestream")

        if os.path.exists("output_strm/web"):
            shutil.rmtree("output_strm/web")
    if os.path.exists("resources/acestream_directos.m3u") and os.stat("resources/acestream_directos.m3u").st_size > 5:
        with open("resources/acestream_directos.m3u", 'r', encoding='utf-8') as file:
            content = file.read()
            channels = parse_m3u(content)
    
    if channels:  # Verifica si 'channels' no está vacío
        now = datetime.now(pytz.UTC)
        local_tz = pytz.timezone('Europe/Madrid')  # Change this to your timezone
        
        for channel in channels:
            if channel.tvg_id and channel.tvg_id in epg_data_cache:
                print(f"Processing EPG for channel {channel.name} (ID: {channel.tvg_id})")
                current, next = get_current_and_next_program(epg_data_cache[channel.tvg_id], now)
                
                if current:
                    channel.current_program = current['title']
                    channel.current_program_time = current['start'].astimezone(local_tz)
                    print(f"Current program: {channel.current_program} at {channel.current_program_time}")
                if next:
                    channel.next_program = next['title']
                    channel.next_program_time = next['start'].astimezone(local_tz)
                    print(f"Next program: {channel.next_program} at {channel.next_program_time}")

        groups = {channel.group for channel in channels}
        groups = sorted(list(groups))


    if os.path.exists("resources/acestream_pelis.m3u") and os.stat("resources/acestream_pelis.m3u").st_size > 5:
        with open("resources/acestream_pelis.m3u", 'r', encoding='utf-8') as file:
            content = file.read()
            channels2 = parse_m3u(content)
            channels.extend(channels2)
    
    if channels:  # Verifica si 'channels' no está vacío
        groups = {channel.group for channel in channels}
        groups = sorted(list(groups))
    
    return render_template('index.html', channels=channels, groups=groups, textarea_content=textarea_content, export_strm=export_strm, textarea_content_pelis=textarea_content_pelis)

def procesar_directos(m3u_directos, directorio_salida):
    """
    Procesa el archivo M3U de directos y crea archivos .strm en una única carpeta.
    """
    carpeta_directos = os.path.join(directorio_salida, "Directos")
    os.makedirs(carpeta_directos, exist_ok=True)

    with open(m3u_directos, "r", encoding="utf-8") as f:
        contenido = f.readlines()

    for i, linea in enumerate(contenido):
        linea = linea.strip()
        if linea.startswith("#EXTINF"):
            # Extraer el nombre del canal
            match = re.search(r',(.+)$', linea)
            nombre_canal = match.group(1).strip() if match else f"Directo_{i}"
            nombre_canal=nombre_canal.replace(" ", "_")
        elif linea.startswith("acestream://") or linea.startswith("http"):
            # Crear el archivo STRM con el enlace
            archivo_strm = os.path.join(carpeta_directos, f"{nombre_canal}.strm")
            with open(archivo_strm, "w", encoding="utf-8") as f:
                f.write(linea)



def procesar_peliculas(m3u_peliculas, directorio_salida):
    """
    Procesa el archivo M3U de películas y crea una estructura de carpetas con subcarpetas y archivos .strm.
    """
    carpeta_peliculas = os.path.join(directorio_salida, "Peliculas")
    os.makedirs(carpeta_peliculas, exist_ok=True)

    with open(m3u_peliculas, "r", encoding="utf-8") as f:
        contenido = f.readlines()

    pelicula_actual = None
    for i, linea in enumerate(contenido):
        linea = linea.strip()
        if linea.startswith("#EXTINF"):
            # Extraer el nombre de la película y la calidad
            match = re.search(r',(.+)$', linea)
            if match:
                info = match.group(1).strip()
                # Separar título y calidad
                titulo_match = re.match(r'(.+?)\s+\((\d{4})\)\s+(.+)', info)
                if titulo_match:
                    titulo_pre = titulo_match.group(1).strip()
                    titulo = titulo_pre.replace("/", "_").replace("\\", "_").replace("-", "_").replace(" ", "_").replace("+", "_").replace("*", "_").replace(".", "_").replace("(", "_").replace(")", "_")
                    calidad = titulo_match.group(3).strip().replace(" ", "_").replace("[", "_").replace("]", "_").replace("*", "_").replace(".", "_").replace("(", "_").replace(")", "_")
                else:
                    titulo_pre = info
                    titulo = titulo_pre.replace("/", "_").replace("\\", "_").replace("-", "_").replace(" ", "_").replace("+", "_").replace("*", "_").replace(".", "_").replace("(", "_").replace(")", "_")
                    calidad = "Desconocida"
                # Crear carpeta para la película
                pelicula_actual = os.path.join(carpeta_peliculas, titulo)
                os.makedirs(pelicula_actual, exist_ok=True)
        elif linea.startswith("acestream://") or linea.startswith("http"):
            # Crear el archivo STRM con el enlace
            if pelicula_actual:
                archivo_strm = os.path.join(pelicula_actual, f"{titulo}-{calidad}.strm")
                with open(archivo_strm, "w", encoding="utf-8") as f:
                    f.write(linea)


FolderPath = r"output_strm"



def getReadableByteSize(num, suffix='B') -> str:
    # Si el número es menor que 1024 (en bytes), devolver el valor entero sin sufijo "B"
    if abs(num) < 1024.0:
        return "%d" % num  # No muestra decimales ni sufijo "B"
    
    # Para unidades mayores a 1024, aplicamos el formato con sufijos y sin decimales
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%d%s%s" % (num, unit, suffix)  # No decimales para "K", "M", etc.
        num /= 1024.0
    
    return "%d%s%s" % (num, 'Y', suffix)  # Para valores grandes, se omiten decimales

def getTimeStampString(tSec: float) -> str:
    tObj = datetime.fromtimestamp(tSec)
    tStr = tObj.strftime('%d-%m-%Y %H:%M:%S')
    return tStr

def getIconClassForFilename(fName):
    fileExt = Path(fName).suffix
    fileExt = fileExt[1:] if fileExt.startswith(".") else fileExt
    fileTypes = ["aac", "ai", "bmp", "cs", "css", "csv", "doc", "docx", "exe", "gif", "heic", "html", "java", "jpg", "js", "json", "jsx", "key", "m4p", "md", "mdx", "mov", "mp3",
                 "mp4", "otf", "pdf", "php", "png", "pptx", "psd", "py", "raw", "rb", "sass", "scss", "sh", "sql", "svg", "tiff", "tsx", "ttf", "txt", "wav", "woff", "xlsx", "xml", "yml"]
    fileIconClass = f"bi bi-filetype-{fileExt}" if fileExt in fileTypes else "bi bi-file-earmark"
    return fileIconClass

# route handler
@app.route('/output_strm/', defaults={'reqPath': ''})
@app.route('/output_strm/<path:reqPath>')
def getFiles(reqPath):
    # Join the base and the requested path
    # could have done os.path.join, but safe_join ensures that files are not fetched from parent folders of the base folder
    absPath = safe_join(FolderPath, reqPath)

    # Return 404 if path doesn't exist
    if not os.path.exists(absPath):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(absPath):
        return send_file(absPath)

    # Show directory contents
    def fObjFromScan(x):
        fileStat = x.stat()
        # return file information for rendering
        if os.path.isdir(x.path):
            nombre = x.name + "/"
        else:
            nombre = x.name
        return {'name': nombre[:50],
                'espacios_nombre': "".ljust(51 - len(nombre[:50])),
                'fIcon': "bi bi-folder-fill" if os.path.isdir(x.path) else getIconClassForFilename(x.name),
                'relPath': nombre.replace("\\", "/"),
                'mTime': getTimeStampString(fileStat.st_mtime),
                'espacios_fecha': "       " if os.path.isdir(x.path) else "".ljust(7 - len(getReadableByteSize(fileStat.st_size)[:6])),
                'size': "-" if os.path.isdir(x.path) else getReadableByteSize(fileStat.st_size)[:6]}
        
    #fileObjs = [fObjFromScan(x) for x in os.scandir(absPath)]
    fileObjs = sorted(
        [fObjFromScan(x) for x in os.scandir(absPath)],
        key=itemgetter('name')
    )
    # get parent directory url
    parentFolderPath = os.path.relpath(
        Path(absPath).parents[0], FolderPath).replace("\\", "/")
    return render_template('files.html.j2', data={'files': fileObjs,
                                                 'parentFolder': parentFolderPath})
    
    
if __name__ == '__main__':
    # Start EPG updater thread
    updater_thread = threading.Thread(target=update_epg_data)
    updater_thread.daemon = True
    updater_thread.start()
    
    app.run(host='0.0.0.0')
