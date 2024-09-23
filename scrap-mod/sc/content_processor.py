from .utils import print_progress

def extract_headers(soup):
    print_progress(1, 5, "Extrayendo encabezados...")
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
    print_progress(2, 5, "Creando tabla de contenidos...")
    toc = []
    for header in headers:
        toc.append({
            'level': header['level'],
            'text': header['text'],
            'link': f"#{header['id']}" if header['id'] else ''
        })
    return toc

def extract_content(content):
    print_progress(3, 5, "Extrayendo contenido principal...")
    return content.get_text(strip=True)

def analyze_content(content):
    print_progress(4, 5, "Analizando contenido...")
    word_count = len(content.split())
    return {
        'word_count': word_count,
        "links": len(content.find_all('a')),
    }