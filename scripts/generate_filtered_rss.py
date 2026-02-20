import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict
import html

def load_seeds() -> List[Dict]:
    """Carrega as seeds do arquivo JSON"""
    seeds_file = os.path.join("data", "seeds.json")
    if not os.path.exists(seeds_file):
        return []
    try:
        with open(seeds_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def procedure_matches_seed(proc: Dict, seed: Dict) -> bool:
    """Verifica se um procedimento corresponde a uma seed"""
    if seed.get('district'):
        proc_district = proc.get('distrito', '').lower()
        seed_district = seed['district'].lower()
        if proc_district != seed_district:
            return False

    title_text = (proc.get('descricao') or proc.get('designacao_contrato') or '').lower()
    
    other_fields = [
        proc.get('entidade', ''),
        proc.get('entidade_adjudicante', ''),
        proc.get('plataforma_eletronica', ''),
        proc.get('nipc', ''),
        proc.get('concelho', ''),
        proc.get('freguesia', '')
    ]
    other_text = " ".join([str(f) for f in other_fields if f]).lower()
    full_text = f"{title_text} {other_text}"

    title_tags = seed.get('titleTags', [])
    if title_tags:
        if not any(tag.lower() in title_text for tag in title_tags):
            return False

    global_tags = seed.get('tags', [])
    if global_tags:
        if not any(tag.lower() in full_text for tag in global_tags):
            return False
            
    return True

def generate_filtered_rss():
    """Gera um arquivo RSS contendo apenas procedimentos que dão match com as seeds"""
    print("📡 Gerando RSS filtrado personalizado...")
    
    ativos_json = os.path.join("data", "ativos.json")
    if not os.path.exists(ativos_json):
        print("Arquivo ativos.json não encontrado.")
        return

    try:
        with open(ativos_json, 'r', encoding='utf-8') as f:
            procedimentos = json.load(f)
    except:
        return

    seeds = load_seeds()
    filtered_items = []

    for item in procedimentos:
        for seed in seeds:
            if procedure_matches_seed(item, seed):
                item['matched_seed'] = seed.get('name', seed.get('code'))
                filtered_items.append(item)
                break

    # Criar estrutura XML do RSS
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    
    ET.SubElement(channel, "title").text = "DRE Procedimentos Filtrados (Seeds)"
    ET.SubElement(channel, "link").text = "https://github.com/sotkonhsilva/DRE-RSS_STK"
    ET.SubElement(channel, "description").text = "Feed RSS automatizado com base nas sementes de pesquisa parametrizadas."
    ET.SubElement(channel, "language").text = "pt-PT"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")

    for item in filtered_items:
        rss_item = ET.SubElement(channel, "item")
        
        # Título amigável
        title = item.get('descricao') or item.get('designacao_contrato') or "Procedimento sem título"
        ET.SubElement(rss_item, "title").text = f"[{item.get('matched_seed', 'SEED')}] {title}"
        
        ET.SubElement(rss_item, "link").text = item.get('link', '')
        
        # Descrição rica
        desc_text = f"""
        Entidade: {item.get('entidade', 'N/A')}
        Preço Base: {item.get('preco_base', 'N/A')}
        Distrito: {item.get('distrito', 'N/A')}
        Prazo: {item.get('prazo_apresentacao_propostas', 'N/A')}
        Seed: {item.get('matched_seed', 'N/A')}
        """
        ET.SubElement(rss_item, "description").text = desc_text.strip()
        
        # Guid único
        ET.SubElement(rss_item, "guid", isPermaLink="false").text = item.get('link', '')

    # Salvar o arquivo
    output_path = os.path.join("RSS", "feed_filtros_seeds.xml")
    os.makedirs("RSS", exist_ok=True)
    
    tree = ET.ElementTree(rss)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ RSS filtrado gerado em: {output_path} ({len(filtered_items)} itens)")

if __name__ == "__main__":
    generate_filtered_rss()
