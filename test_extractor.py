#!/usr/bin/env python3
"""
Quick test of content extraction
"""
from bs4 import BeautifulSoup
import html2text

# Sample HTML content from Nebrija
html_sample = """
<!DOCTYPE html>
<html lang="es">
<head>
  <title>Universidad en Madrid Presencial y Online | Nebrija</title>
</head>
<body id="home">
  <header>
    <div class="logoNebrija">
      <a title="Universidad Nebrija" href="/">Universidad Nebrija</a>
    </div>
  </header>
  
  <main>
    <section class="hero">
      <h1>Grados Universitarios</h1>
      <p>Tu carrera universitaria comienza en Nebrija, comprometida con la excelencia académica y la empleabilidad.</p>
      <a href="/carreras-universitarias/carreras.php">Ver listado de grados</a>
      <a href="https://admisiones.nebrija.com/s/formulario-admision">SOLICITA TU ADMISIÓN</a>
    </section>
    
    <section class="programs">
      <h2>Oferta Académica</h2>
      <ul>
        <li>Carreras Universitarias</li>
        <li>Dobles Grados</li>
        <li>Nebrija Postgrado</li>
      </ul>
    </section>
  </main>
  
  <nav id="menuPrincipal">
    <ul>
      <li><a href="/la_universidad/">La Universidad</a></li>
      <li><a href="/estudios/">Estudios</a></li>
    </ul>
  </nav>
  
  <script>
    // Some JavaScript
    console.log('test');
  </script>
  
  <style>
    /* Some CSS */
    body { margin: 0; }
  </style>
</body>
</html>
"""

def test_clean_text_extraction():
    """Test the clean text extraction logic"""
    soup = BeautifulSoup(html_sample, 'html.parser')
    
    # Create a copy to avoid modifying original
    content_soup = soup.__copy__()
    
    # Remove unwanted elements
    unwanted_tags = [
        'script', 'style', 'nav', 'header', 'footer', 
        'aside', 'noscript', 'iframe', 'object', 'embed',
        'button', 'input', 'select', 'textarea', 'form'
    ]
    
    for tag_name in unwanted_tags:
        for element in content_soup.find_all(tag_name):
            element.decompose()
    
    print("After removing unwanted tags:")
    print(content_soup.get_text(strip=True)[:200])
    print("\n" + "="*50 + "\n")
    
    # Try to find main content area
    main_content = (
        content_soup.find('main') or 
        content_soup.find('article') or
        content_soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'main' in x.lower() or 'body' in x.lower())) or
        content_soup.find('div', id=lambda x: x and ('content' in x.lower() or 'main' in x.lower() or 'body' in x.lower())) or
        content_soup.find('body') or
        content_soup
    )
    
    if main_content:
        # Extract text and clean whitespace
        text = main_content.get_text(separator=' ', strip=True)
        print("Raw extracted text:")
        print(repr(text))
        print("\nText length:", len(text))
        print("\nFormatted text:")
        print(text)
        
        # Normalize whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        print("\nAfter normalizing whitespace:")
        print(repr(text))
        print("Length:", len(text))
        
        # Check minimum length
        if len(text.strip()) > 50:
            print("\n✅ PASS: Text is longer than 50 characters")
            return text.strip()
        else:
            print("\n❌ FAIL: Text is too short (< 50 characters)")
            return None
    else:
        print("❌ FAIL: No main content found")
        return None

def test_markdown_conversion():
    """Test markdown conversion"""
    soup = BeautifulSoup(html_sample, 'html.parser')
    
    # Configure html2text for markdown conversion
    html_converter = html2text.HTML2Text()
    html_converter.ignore_links = False
    html_converter.ignore_images = False
    html_converter.body_width = 0  # Don't wrap lines
    html_converter.unicode_snob = True
    html_converter.ignore_emphasis = False
    
    # Create a copy and clean it similar to text extraction
    markdown_soup = soup.__copy__()
    
    # Remove unwanted elements (same as clean text but preserve more structure)
    unwanted_tags = [
        'script', 'style', 'nav', 'header', 'footer', 
        'aside', 'noscript', 'iframe', 'object', 'embed'
    ]
    
    for tag_name in unwanted_tags:
        for element in markdown_soup.find_all(tag_name):
            element.decompose()
    
    # Try to find main content for markdown conversion
    main_content = (
        markdown_soup.find('main') or 
        markdown_soup.find('article') or
        markdown_soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'main' in x.lower() or 'body' in x.lower())) or
        markdown_soup.find('body') or
        markdown_soup
    )
    
    if main_content:
        # Convert to markdown
        markdown = html_converter.handle(str(main_content))
        
        print("Raw markdown:")
        print(repr(markdown))
        print("\nFormatted markdown:")
        print(markdown)
        print("\nLength:", len(markdown.strip()))
        
        return markdown.strip()
    
    return None

if __name__ == "__main__":
    print("Testing Clean Text Extraction:")
    print("="*60)
    clean_result = test_clean_text_extraction()
    
    print("\n\nTesting Markdown Conversion:")
    print("="*60)
    markdown_result = test_markdown_conversion()
    
    print("\n\nSummary:")
    print("="*30)
    print("Clean text result:", "✅ Success" if clean_result else "❌ Failed")
    print("Markdown result:", "✅ Success" if markdown_result else "❌ Failed")