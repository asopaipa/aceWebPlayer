import re
import requests

# URL de la que quieres obtener los datos
url = 'https://ipfs.io/ipns/elcano.top'

# Realizar la solicitud HTTP
response = requests.get(url)
if response.status_code == 200:
    content = response.text

    # Expresión regular para extraer el nombre y el enlace acestream
    matches = re.findall(r'{"name": "(.*?)", "url": "acestream://([a-f0-9]{40})"}', content)

    # Guardar en un archivo .txt
    with open('output.txt', 'w') as f:
        for name, acestream_hash in matches:
            f.write(f"{name}\n{acestream_hash}\n")
    print("Archivo 'ace_ids.txt' creado con éxito.")
else:
    print(f"Error al realizar la solicitud: {response.status_code}")
