import requests
from bs4 import BeautifulSoup
import os
import json
import re
from urllib.parse import urlparse, urljoin
from typing import Dict, Optional, Any


def extract_specific_article_content(url: str) -> Optional[Dict[str, Any]]:
    """
    Extrae el contenido específico de la estructura del artículo dado,
    lo guarda en un archivo HTML en una nueva carpeta y devuelve un diccionario con la información.
    """
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

        content = next((soup.find(tag, class_=class_name) if class_name else soup.find(tag)
                        for tag, class_name in selectors if
                        (class_name and soup.find(tag, class_=class_name)) or (not class_name and soup.find(tag))),
                       None)

        if content:
            extracted_headers = extract_headers(soup)
            extracted_content = str(content)
            analyzed_content = analyze_content(content, url)

            # Crear una nueva carpeta para guardar los archivos
            folder_name = create_folder_from_url(url)

            return {
                'content': extracted_content,
                'url': url,
                'analysis': analyzed_content,
                'headers': extracted_headers,
                'folder_name': folder_name
            }
        else:
            print(f"No se encontró el contenido del artículo en {url}")
            print("Estructura de la página:")
            print(json.dumps(structure_overview(soup), indent=2))
            return None
    except requests.RequestException as e:
        print(f"Error al acceder a {url}: {e}")
        return None


def extract_headers(soup: BeautifulSoup) -> list:
    return [{'level': int(header.name[1]),
             'text': header.get_text(strip=True),
             'id': header.get('id', '')}
            for header in soup.find_all(re.compile('^h[1-6]$'))]


def analyze_content(content: BeautifulSoup, url: str) -> Dict[str, int]:
    return {
        "word_count": len(content.get_text(strip=True).split()),
        "links": len(content.find_all('a'))
    }


def structure_overview(soup: BeautifulSoup) -> Dict[str, Any]:
    return {
        "title": soup.title.string if soup.title else "No title",
        "meta_tags": len(soup.find_all('meta'))
    }


def create_folder_from_url(url: str) -> str:
    domain = urlparse(url).netloc
    folder_name = re.sub(r'[^\w\-_\. ]', '_', domain)
    os.makedirs(folder_name, exist_ok=True)
    return folder_name


def save_article_content(article_data: Dict[str, Any], output_dir: str) -> str:
    """Guarda el contenido del artículo en un archivo HTML."""
    filepath = os.path.join(output_dir, f"{urlparse(article_data['url']).netloc.replace('.', '_')}.html")

    html_content = f"""
    <html>
    <head>
        <title>{article_data['url']}</title>
    </head>
    <body>
        <h1>Artículo extraído de {article_data['url']}</h1>
        <h2>Contenido</h2>
        {article_data['content']}
        <h2>Análisis</h2>
        <p>Número de palabras: {article_data['analysis']['word_count']}</p>
        <p>Número de enlaces: {article_data['analysis']['links']}</p>
    </body>
    </html>
    """

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Artículo guardado en: {filepath}")
    return filepath


def download_images(article_data: Dict[str, Any], output_dir: str) -> None:
    """Descarga y guarda las imágenes del artículo."""
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    soup = BeautifulSoup(article_data['content'], 'html.parser')
    images = soup.find_all('img')

    for idx, img in enumerate(images):
        img_url = img.get('src')
        if img_url:
            img_url = urljoin(article_data['url'], img_url)
            try:
                img_response = requests.get(img_url)
                img_response.raise_for_status()
                img_filename = f"image_{idx}_{hash(img_url)}.jpg"
                img_filepath = os.path.join(images_dir, img_filename)
                with open(img_filepath, 'wb') as img_file:
                    img_file.write(img_response.content)
                print(f"Imagen guardada: {img_filepath}")
            except requests.RequestException as e:
                print(f"Error al descargar la imagen {img_url}: {e}")


if __name__ == "__main__":
    url = "https://blog.csdn.net/qq877507054/article/details/60143099"

    result = extract_specific_article_content(url)
    if result:
        saved_file_path = save_article_content(result, result['folder_name'])
        download_images(result, result['folder_name'])
        print(f"Artículo guardado en: {saved_file_path}")
        print(json.dumps(result['analysis'], indent=2, ensure_ascii=False))
    else:
        print("No se pudo extraer el contenido del artículo.")