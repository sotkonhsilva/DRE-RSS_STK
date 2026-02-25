import requests
from bs4 import BeautifulSoup

url = "https://diariodarepublica.pt/dr/detalhe/contrato-publico/4216-105750617"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

try:
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Print page title
    print(f"Title: {soup.title.string if soup.title else 'No title'}")
    
    # Print all div texts that might contain the identification
    print("\nSearching for headers...")
    search_texts = ["IDENTIFICAÇÃO", "ENTIDADE ADJUDICANTE", "Prazo"]
    for div in soup.find_all(['div', 'span', 'h1', 'h2', 'h3']):
        text = div.get_text(strip=True)
        if any(st in text for st in search_texts):
            print(f"Match found in <{div.name}>: {text[:100]}...")

    # Get the whole text to see structure
    with open('dre_source.txt', 'w', encoding='utf-8') as f:
        f.write(soup.get_text(separator='\n'))
    print("\nSaved full text to dre_source.txt")

except Exception as e:
    print(f"Error: {e}")
