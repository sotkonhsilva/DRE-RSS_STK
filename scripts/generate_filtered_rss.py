import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict
import html

def load_seeds() -> List[Dict]:
    """Carrega as seeds do arquivo JSON"""
    seeds_file = os.path.join("..", "public", "data", "seeds.json")
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

def clean_url(url: str) -> str:
    """Limpa URLs de brancos e quebras de linha que invalidam o RSS"""
    if not url: return "https://diariodarepublica.pt"
    return str(url).strip().replace('\n', '').replace('\r', '').replace(' ', '%20')

def generate_filtered_rss():
    """Gera um arquivo RSS contendo apenas procedimentos que dão match com as seeds"""
    print("📡 Gerando RSS filtrado personalizado...")
    
    ativos_json = os.path.join("..", "public", "data", "ativos.json")
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
        
        nipc = item.get('nipc', 'N/A')
        entidade = item.get('entidade_adjudicante', item.get('entidade', 'N/A'))
        designacao = item.get('descricao') or item.get('designacao_contrato') or "Procedimento sem título"
        matched_seed = item.get('matched_seed', 'SEED')
        
        ET.SubElement(rss_item, "title").text = f"[{matched_seed}] [{nipc}] {entidade} - {designacao}"
        
        link = clean_url(item.get('link', ''))
        ET.SubElement(rss_item, "link").text = link
        
        # Placeholder para descrição que será substituído por CDATA
        ET.SubElement(rss_item, "description").text = "DESCRIPTION_CDATA_PLACEHOLDER"
        
        ET.SubElement(rss_item, "guid", isPermaLink="false").text = link

    # Gerar XML final com substituição manual de CDATA para melhor compatibilidade com Outlook
    xml_str = ET.tostring(rss, encoding='utf-8').decode('utf-8')
    
    # Adicionar cabeçalho XML
    final_xml = '<?xml version="1.0" encoding="utf-8" ?>\n' + xml_str
    
    # Processar CDATAs
    parts = final_xml.split("DESCRIPTION_CDATA_PLACEHOLDER")
    reconstructed = parts[0]
    
    for i, item in enumerate(filtered_items):
        nipc = item.get('nipc', 'N/A')
        entidade = item.get('entidade_adjudicante', item.get('entidade', 'N/A'))
        designacao = item.get('descricao') or item.get('designacao_contrato') or "Procedimento sem título"
        matched_seed = item.get('matched_seed', 'SEED')
        pub_date_val = item.get('data_publicacao', datetime.now().strftime('%d/%m/%Y'))
        deadline_val = item.get('prazo_apresentacao_propostas', 'N/A')
        price_val = item.get('preco_base', 'N/A')
        plataforma = item.get('plataforma_eletronica', 'N/A')
        
        c_link = clean_url(item.get('link', ''))
        c_url_proc = clean_url(item.get('url_procedimento', ''))
        
        desc_html = f"""
<div style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 15px; border: 1px solid #e0e6ed; border-radius: 8px;">
    <div style="background-color: #ffffff; padding: 12px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #2a5298;">
        <div style="font-size: 11px; color: #2a5298; font-weight: bold; text-transform: uppercase;">{entidade}</div>
        <div style="font-size: 15px; font-weight: bold; color: #1e293b; margin: 4px 0;">{designacao}</div>
        <div style="font-size: 10px; color: #64748b;">
            <span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px; margin-right: 8px;">PLATAFORMA: {plataforma}</span>
            <span style="background: #2a5298; color: #ffffff; padding: 2px 6px; border-radius: 4px;">MATCH: {matched_seed}</span>
        </div>
    </div>
    <table width="100%" cellpadding="0" cellspacing="5" border="0">
        <tr>
            <td width="33%" valign="top" style="background:#ffffff; padding:10px; border:1px solid #d1d9e6; border-radius:8px;">
                <h4 style="color:#2a5298; margin:0 0 10px 0; font-size:12px;">ENTIDADE</h4>
                <div style="font-size:11px;">NIPC: <b>{nipc}</b></div>
                <div style="font-size:11px;">CONCELHO: {item.get('concelho', 'N/A')}</div>
            </td>
            <td width="33%" valign="top" style="background:#ffffff; padding:10px; border:1px solid #d1d9e6; border-radius:8px;">
                <h4 style="color:#2a5298; margin:0 0 10px 0; font-size:12px;">CONTRATO</h4>
                <div style="font-size:11px;">PRAZO: {item.get('prazo_execucao', 'N/A')}</div>
                <div style="font-size:11px;">PREÇO: <b>{price_val}</b></div>
            </td>
            <td width="33%" valign="top" style="background:#ffffff; padding:10px; border:1px solid #d1d9e6; border-radius:8px;">
                <h4 style="color:#2a5298; margin:0 0 10px 0; font-size:12px;">LINKS</h4>
                <div style="font-size:11px;"><a href="{c_link}">Anúncio DRE</a></div>
                <div style="font-size:11px;"><a href="{c_url_proc}">Procedimento</a></div>
            </td>
        </tr>
    </table>
    <div style="margin-top: 15px; padding: 10px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 12px; line-height: 1.4;">
        <b>DESCRIÇÃO:</b><br/>{item.get('descricao', 'N/A')}
    </div>
</div>
""".strip()
        reconstructed += f"<![CDATA[{desc_html}]]>" + parts[i+1]

    # Salvar o arquivo
    output_path = os.path.join("..", "public", "RSS", "feed_filtros_seeds.xml")
    os.makedirs(os.path.join("..", "public", "RSS"), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(reconstructed)
        
    print(f"✅ RSS filtrado gerado em: {output_path} ({len(filtered_items)} itens)")

if __name__ == "__main__":
    generate_filtered_rss()
