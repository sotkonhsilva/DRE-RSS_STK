import requests
from lxml import etree

try:
    r = requests.get('https://files.diariodarepublica.pt/rss/serie2&parte=l-html.xml', timeout=30)
    r.raise_for_status()
    root = etree.fromstring(r.content)
    items = root.xpath('//item')
    print(f"Total items in remote feed: {len(items)}")
    for item in items[:5]:
        title = item.xpath('title/text()')[0] if item.xpath('title/text()') else "No title"
        print(f" - {title}")
except Exception as e:
    print(f"Error: {e}")
