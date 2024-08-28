import requests
from bs4 import BeautifulSoup
import os
import json


def extract_specific_article_content(url):
    """Extrae el contenido específico de la estructura del artículo dado con mejor manejo de errores."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Imprimir los primeros 500 caracteres de la respuesta para depuración
        print("Primeros 500 caracteres de la respuesta:")
        print(response.text[:500])

        soup = BeautifulSoup(response.text, 'html.parser')

        # Intentar diferentes selectores
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
            # Extraer el contenido del artículo
            extracted_content = extract_content(content)

            return {
                'content': extracted_content,
                'url': url
            }
        else:
            print(f"No se encontró el contenido del artículo en {url}")
            print("Estructura de la página:")
            print(json.dumps(structure_overview(soup), indent=2))
            return None
    except requests.RequestException as e:
        print(f"Error al acceder a {url}: {e}")
        return None


def extract_content(element):
    """Extrae el contenido recursivamente, manteniendo la estructura pero limpiando estilos."""
    if element is None:
        return ""
    if isinstance(element, str):
        return element

    content = []
    for child in element.children:
        if isinstance(child, str):
            content.append(child)
        elif child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            content.append(f"<{child.name}>{child.get_text().strip()}</{child.name}>")
        elif child.name == 'img':
            content.append(str(child))
        elif child.name in ['b', 'strong', 'i', 'em', 'u', 'a']:
            content.append(str(child))
        else:
            content.append(extract_content(child))

    if element.name == 'div' and 'class' in element.attrs:
        class_str = ' '.join(element['class'])
        return f'<div class="{class_str}">{"".join(content)}</div>'
    elif element.name:
        return f"<{element.name}>{''.join(content)}</{element.name}>"
    else:
        return ''.join(content)


def structure_overview(soup):
    """Genera una visión general de la estructura de la página."""

    def recursive_structure(element, max_depth=3, current_depth=0):
        if current_depth >= max_depth or element is None:
            return "..."

        if isinstance(element, str):
            return element if len(element.strip()) > 0 else ""

        result = {
            "name": element.name,
            "class": element.get("class", None),
            "id": element.get("id", None)
        }

        children = [recursive_structure(child, max_depth, current_depth + 1)
                    for child in element.children
                    if not isinstance(child, str) or child.strip()]

        if children:
            result["children"] = children

        return result

    # Manejar el caso donde soup.body es None
    if soup.body is None:
        return {"error": "No se encontró el elemento body en la página"}

    return recursive_structure(soup.body)


def save_article_content(article_data, output_dir):
    """Guarda el contenido del artículo en un archivo HTML."""
    if not article_data:
        return

    os.makedirs(output_dir, exist_ok=True)

    filename = f"article_{hash(article_data['url'])}.html"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"<!-- URL: {article_data['url']} -->\n")
        f.write(article_data['content'])

    print(f"Contenido del artículo guardado en {filepath}")


# URL del blog para procesar
blog_url = "https://blog.csdn.net/qq877507054/article/details/60143099"

output_directory = "article_contents"

print(f"Procesando: {blog_url}")
article_data = extract_specific_article_content(blog_url)
if article_data:
    save_article_content(article_data, output_directory)
else:
    print(f"No se pudo extraer el contenido del artículo de {blog_url}")

print("\nProceso completado.")
