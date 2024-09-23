import os
import re
from bs4 import BeautifulSoup

def print_progress(step, total_steps, message):
    """Imprime el progreso actual del proceso."""
    print(f"[{step}/{total_steps}] {message}")



def save_content_as_html(content, folder_name, url):
    print_progress(6, 7, "Guardando contenido como texto plano...")
    file_name = re.sub(r'[^\w\-_\. ]', '_', url.split('/')[-1]) + '.txt'
    file_path = os.path.join(folder_name, file_name)

    # Usar BeautifulSoup para extraer solo el texto
    soup = BeautifulSoup(content, 'html.parser')

    # Extraer solo el texto, eliminando todos los scripts y estilos
    for script in soup(["script", "style"]):
        script.decompose()

    text_content = soup.get_text()

    # Limpiar el texto: eliminar líneas en blanco y espacios extra
    lines = (line.strip() for line in text_content.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text_content = '\n'.join(chunk for chunk in chunks if chunk)

    # Agregar información sobre la fuente
    text_content = f"Contenido extraído de: {url}\n\n" + text_content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text_content)

    return file_path
