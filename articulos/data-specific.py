import urllib.parse

import requests
from bs4 import BeautifulSoup
import os
import json
import re

def extract_specific_article_content(url):
    """Extrae el contenido específico de la estructura del artículo dado con mejor manejo de errores."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        print("Primeros 500 caracteres de la respuesta:")
        print(response.text[:500])

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
            return {
                'content': extracted_content,
                'url': url,
                'analysis': analyzed_content
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

def extract_workflow_steps(soup):
    """Extrae los pasos típicos para implementar un flujo de trabajo en Activiti."""
    workflow_steps = []

    # Buscar listas que puedan contener los pasos del flujo de trabajo
    for ul in soup.find_all('ul'):
        list_items = ul.find_all('li')
        if len(list_items) >= 3:  # Asumimos que una lista de pasos tendrá al menos 3 elementos
            potential_steps = [li.get_text(strip=True) for li in list_items]

            # Verificar si los elementos de la lista se parecen a pasos de un flujo de trabajo
            if any(keyword in ' '.join(potential_steps).lower() for keyword in
                   ['bpmn', 'proceso', 'instancia', 'tarea']):
                workflow_steps.extend(potential_steps)

    # Si no se encuentran listas, buscar párrafos que puedan describir los pasos
    if not workflow_steps:
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if any(keyword in text.lower() for keyword in ['pasos', 'implementar', 'flujo de trabajo', 'activiti']):
                workflow_steps.append(text)

    return workflow_steps


def extract_code_examples(soup):
    """Extrae ejemplos de código para operaciones comunes en Activiti."""
    code_examples = {
        'deploy_process': [],
        'start_instance': [],
        'query_tasks': [],
        'complete_tasks': []
    }

    # Función para limpiar el texto del código
    def clean_code(code_text):
        return re.sub(r'\s+', ' ', code_text).strip()

    # Buscar bloques de código
    code_blocks = soup.find_all(['pre', 'code'])
    code_blocks += soup.find_all('span', style=lambda value: value and 'font-family:&#39;宋体&#39;' in value)
    code_blocks += soup.find_all(style=lambda value: value and re.search(r'background:rgb\([^)]+\)', value))

    for block in code_blocks:
        code_text = clean_code(block.get_text())

        # Clasificar el código según su contenido
        if 'deploymentBuilder' in code_text or 'createDeployment' in code_text:
            code_examples['deploy_process'].append(code_text)
        elif 'startProcessInstanceByKey' in code_text:
            code_examples['start_instance'].append(code_text)
        elif 'createTaskQuery' in code_text:
            code_examples['query_tasks'].append(code_text)
        elif 'complete(' in code_text:
            code_examples['complete_tasks'].append(code_text)

    return code_examples


def extract_images_and_concepts(soup):
    """Extrae imágenes y trata de vincularlas con conceptos cercanos."""
    image_concept_pairs = []

    # for img in soup.find_all('img'):
    #     # Obtener la URL de la imagen
    #     img_url = img.get('src', '')
    #     if not img_url:
    #         continue
    #
    #     # Buscar conceptos cercanos (párrafos anteriores y posteriores)
    #     prev_concept = img.find_previous(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    #     next_concept = img.find_next(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    #
    #     concepts = []
    #     if prev_concept:
    #         concepts.append(prev_concept.get_text(strip=True))
    #     if next_concept:
    #         concepts.append(next_concept.get_text(strip=True))
    #
    #     image_concept_pairs.append({
    #         'image_url': img_url,
    #         'related_concepts': concepts
    #     })
    #
    # return image_concept_pairs

def extract_images_and_concepts_2(soup, base_url):
    """Extrae imágenes y trata de vincularlas con conceptos cercanos."""
    image_concept_pairs = []

    for img in soup.find_all('img'):
        # Obtener la URL de la imagen
        img_url = img.get('src', '')
        if not img_url:
            continue

        # Convertir URL relativa a absoluta si es necesario
        if not img_url.startswith(('http://', 'https://')):
            img_url = requests.compat.urljoin(base_url, img_url)

        # Buscar conceptos cercanos (párrafos anteriores y posteriores)
        prev_concept = img.find_previous(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        next_concept = img.find_next(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        concepts = []
        if prev_concept:
            concepts.append(prev_concept.get_text(strip=True))
        if next_concept:
            concepts.append(next_concept.get_text(strip=True))

        image_concept_pairs.append({
            'image_url': img_url,
            'related_concepts': concepts
        })

    return image_concept_pairs

def create_index(soup):
    """Crea un índice basado en los encabezados del documento."""
    index = []
    for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(header.name[1])
        text = header.get_text(strip=True)
        index.append({
            'level': level,
            'text': text
        })
    return index

def analyze_content(soup, base_url):
    """Analiza el contenido extraído para obtener información adicional."""
    headers = extract_headers(soup)

    analysis = {
        'headers': headers,
        'table_of_contents': create_table_of_contents(headers),
        'code_snippets': extract_code_snippets(soup),
        'key_concepts': extract_key_concepts(soup),
        'tables': extract_tables(soup),
        'workflow_steps': extract_workflow_steps(soup),
        'code_examples': extract_code_examples(soup),
        'images_and_concepts': extract_images_and_concepts(soup),
        'images_and_concepts_2': extract_images_and_concepts_2(soup, base_url),
        'index': create_index(soup)
    }
    return analysis


# def extract_headers(soup):
#     headers = []
#     for header in soup.find_all(re.compile('^h[1-6]$')):
#         headers.append((header.name, header.text.strip()))
#     return headers
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


def extract_code_snippets(soup):
    """Extrae fragmentos de código basados en estilos CSS específicos."""
    code_snippets = []

    # Buscar elementos con font-family:'宋体'
    for element in soup.find_all(style=lambda value: value and "font-family:'宋体'" in value):
        code_snippets.append(element.get_text())

    # Buscar elementos con background:rgb()
    for element in soup.find_all(style=lambda value: value and re.search(r'background:rgb\([^)]+\)', value)):
        code_snippets.append(element.get_text())

    return code_snippets

def extract_key_concepts(soup):
    concepts = []
    for bold in soup.find_all('b'):
        if bold.text.strip():
            concepts.append(bold.text.strip())
    return concepts

def extract_tables(soup):
    tables = []
    for table in soup.find_all('table'):
        tables.append(str(table))
    return tables

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

    if soup.body is None:
        return {"error": "No se encontró el elemento body en la página"}
    return recursive_structure(soup.body)

def save_article_content(article_data, output_dir):
    """Guarda el contenido del artículo y su análisis en archivos separados."""
    if not article_data:
        return

    os.makedirs(output_dir, exist_ok=True)

    # Guardar el contenido HTML
    html_filename = f"article_{hash(article_data['url'])}.html"
    html_filepath = os.path.join(output_dir, html_filename)
    with open(html_filepath, 'w', encoding='utf-8') as f:
        f.write(f"<!-- URL: {article_data['url']} -->\n")
        f.write(article_data['content'])
    print(f"Contenido del artículo guardado en {html_filepath}")

    # Guardar el análisis en formato JSON
    analysis_filename = f"analysis_{hash(article_data['url'])}.json"
    analysis_filepath = os.path.join(output_dir, analysis_filename)
    with open(analysis_filepath, 'w', encoding='utf-8') as f:
        json.dump(article_data['analysis'], f, ensure_ascii=False, indent=2)
    print(f"Análisis del artículo guardado en {analysis_filepath}")

    # Imprimir los pasos del flujo de trabajo encontrados
    print("\nPasos del flujo de trabajo en Activiti encontrados:")
    for step in article_data['analysis']['workflow_steps']:
        print(f"- {step}")

    # Imprimir los ejemplos de código encontrados
    print("\nEjemplos de código para operaciones comunes en Activiti:")
    for operation, examples in article_data['analysis']['code_examples'].items():
        print(f"\n{operation.replace('_', ' ').title()}:")
        for i, example in enumerate(examples, 1):
            print(f"Ejemplo {i}:\n{example}\n")

    # Descargar y guardar las imágenes
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    for idx, img_data in enumerate(article_data['analysis']['images_and_concepts']):
        img_url = img_data['image_url']
        try:
            img_response = requests.get(img_url)
            img_response.raise_for_status()
            img_filename = f"image_{idx}_{hash(img_url)}.jpg"
            img_filepath = os.path.join(images_dir, img_filename)
            with open(img_filepath, 'wb') as img_file:
                img_file.write(img_response.content)
            print(f"Imagen guardada: {img_filepath}")
            print("Conceptos relacionados:")
            for concept in img_data['related_concepts']:
                print(f"- {concept}")
        except requests.RequestException as e:
            print(f"Error al descargar la imagen {img_url}: {e}")


    # Imprimir el índice
    print("\nÍndice del documento:")
    for item in article_data['analysis']['index']:
        print(f"{'  ' * (item['level'] - 1)}- {item['text']}")

    # Imprimir información sobre las imágenes
    print("\nImágenes encontradas 2:")
    for i, img in enumerate(article_data['analysis']['images'], 1):
        print(f"\nImagen {i}:")
        print(f"URL: {img['url']}")
        print(f"Alt: {img['alt']}")
        print(f"Concepto: {img['concept']}")

    # Imprimir la tabla de contenidos
    print("\nTabla de Contenidos:")
    for item in article_data['analysis']['table_of_contents']:
        print(f"{'  ' * (item['level'] - 1)}- {item['text']}")

    print("\nCódigo extraído:")
    for snippet in article_data['analysis']['code_snippets']:
        print(snippet)
        print("-" * 40)


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