from sc import extract_specific_article_content
import json


def main():
    url = "https://blog.csdn.net/qq877507054/article/details/60143099"
    result = extract_specific_article_content(url)
    if result:
        print("\nResumen del contenido extraído:")
        print(f"URL: {result['url']}")
        print(f"Análisis: {json.dumps(result['analysis'], indent=2, ensure_ascii=False)}")
        print(f"Contenido guardado en: {result['saved_file_path']}")

        # Mostrar las primeras líneas del contenido extraído
        with open(result['saved_file_path'], 'r', encoding='utf-8') as f:
            print("\nPrimeras líneas del contenido extraído:")
            print(f.read(500) + "...")
    else:
        print("No se pudo extraer el contenido del artículo")


if __name__ == "__main__":
    main()
