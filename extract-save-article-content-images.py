import os
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
import re
import json

def extract_headers(soup):
    headers = []
    for header in soup.find_all(re.compile('^h[1-6]$')):
        level = int(header.name[1])
        headers.append({
            'level': level,
            'text': header.get_text(strip=True),
            'id': header.get('id', '')
        })
    return headers

def create_table_of_contents(headers):
    toc = []
    for header in headers:
        toc.append({
            'level': header['level'],
            'text': header['text'],
            'link': f"#{header['id']}" if header['id'] else ''
        })
    return toc

def extract_content(content):
    # Implementa la lógica para extraer el contenido del elemento
    # return element.get_text(strip=True)
    return content.get_text()

def analyze_content(content, url):
    # Implementa la lógica para analizar el contenido
    # Por ejemplo, contar palabras, identificar temas principales, etc.
    word_count = len(content.get_text(strip=True).split())
    return {
        'word_count': word_count,
        "links": len(content.find_all('a')),
        # Agrega más análisis aquí
    }

def structure_overview(soup):
    # Implementa la lógica para proporcionar una visión general de la estructura de la página
    # return {tag.name: len(soup.find_all(tag.name)) for tag in soup.find_all()}
    return {
        "title": soup.title.string if soup.title else "No title",
        "meta_tags": len(soup.find_all('meta')),
        # Agrega más información estructural según sea necesario
    }

def create_folder_from_url(url):
    """Crea una carpeta basada en el dominio de la URL."""
    domain = urlparse(url).netloc
    folder_name = re.sub(r'[^\w\-_\. ]', '_', domain)
    os.makedirs(folder_name, exist_ok=True)
    return folder_name


def download_image(img_url, folder_path):
    """Descarga una imagen y la guarda en la carpeta especificada."""
    try:
        response = requests.get(img_url, stream=True)
        response.raise_for_status()

        # Extraer el nombre del archivo de la URL
        filename = os.path.join(folder_path, os.path.basename(urlparse(img_url).path))

        # Asegurarse de que el nombre del archivo sea válido
        filename = re.sub(r'[^\w\-_\. ]', '_', filename)

        with open(filename, 'wb') as out_file:
            out_file.write(response.content)
        return filename
    except Exception as e:
        print(f"Error al descargar la imagen {img_url}: {e}")
        return None

def extract_and_download_images(soup, base_url, folder_path):
    """Extrae todas las imágenes de la página y las descarga."""
    downloaded_images = []
    for img in soup.find_all('img'):
        img_url = img.get('src')
        if img_url:
            # Convertir URL relativa a absoluta si es necesario
            img_url = urljoin(base_url, img_url)
            downloaded_file = download_image(img_url, folder_path)
            if downloaded_file:
                downloaded_images.append(downloaded_file)
    return downloaded_images


def save_content_as_html(content, folder_name, url):
    """Guarda el contenido en un archivo HTML."""
    file_name = re.sub(r'[^\w\-_\. ]', '_', url.split('/')[-1]) + '.html'
    file_path = os.path.join(folder_name, file_name)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Artículo extraído de {url}</title>
    </head>
    <body>
        <h1>Artículo extraído de <a href="{url}">{url}</a></h1>
        <div class="article-content">
            {content}
        </div>
    </body>
    </html>
    """

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return file_path

def extract_specific_article_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        selectors = [
            ('div', 'article_content'),
            ('div', 'htmledit_views'),
            ('article', None),
            ('div', 'post-content'),
            ('div', 'entry-content')
        ]

        content = None
        for tag, class_name in selectors:
            if class_name:
                content = soup.find(tag, class_=class_name)
            else:
                content = soup.find(tag)
            if content:
                break

        if content:
            extracted_content = extract_content(content)
            analyzed_content = analyze_content(content, url)

            # Crear una nueva carpeta para guardar los archivos
            folder_name = create_folder_from_url(url)

            # Descargar imágenes
            downloaded_images = extract_and_download_images(content, url, folder_name)

            # Guardar el contenido en un archivo HTML
            file_path = save_content_as_html(extracted_content, folder_name, url)

            return {
                'content': extracted_content,
                'url': url,
                'analysis': analyzed_content,
                'saved_file_path': file_path,
                'downloaded_images': downloaded_images
            }
        else:
            print(f"No se encontró el contenido del artículo en {url}")
            print("Estructura de la página:")
            print(json.dumps(structure_overview(soup), indent=2))
            return None
    except requests.RequestException as e:
        print(f"Error al acceder a {url}: {e}")
        return None

# Ejemplo de uso
if __name__ == "__main__":
    url = "https://blog.csdn.net/qq877507054/article/details/60143099"
    result = extract_specific_article_content(url)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("No se pudo extraer el contenido del artículo.")