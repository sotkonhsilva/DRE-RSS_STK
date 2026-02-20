import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict
import html
import re
from xml.dom import minidom

def load_seeds() -> List[Dict]:
    """Carrega as seeds do arquivo JSON"""
    # Tentar encontrar a pasta de dados
    possible_paths = [
        'data/seeds.json',
        '../data/seeds.json',
        'public/data/seeds.json',
        '../public/data/seeds.json',
        'seeds.json'
    ]
    
    seeds_file = None
    for path in possible_paths:
        if os.path.exists(path):
            seeds_file = path
            break
            
    if not seeds_file:
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
    
    # Tentar encontrar a pasta de dados
    possible_paths = [
        'data/ativos.json',
        '../data/ativos.json',
        'public/data/ativos.json',
        '../public/data/ativos.json',
        'ativos.json'
    ]
    
    ativos_json = None
    for path in possible_paths:
        if os.path.exists(path):
            ativos_json = path
            break
            
    if not ativos_json:
        print("Arquivo ativos.json não encontrado.")
        return

    try:
        with open(ativos_json, 'r', encoding='utf-8') as f:
            procedimentos = json.load(f)
    except Exception as e:
        print(f"Erro ao ler ativos.json: {e}")
        return

    seeds = load_seeds()
    filtered_items = []

    for item in procedimentos:
        for seed in seeds:
            if procedure_matches_seed(item, seed):
                item['matched_seed'] = seed.get('name', seed.get('code'))
                filtered_items.append(item)
                break

    # Criar elemento raiz do RSS
    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
    rss = ET.Element('rss', version='2.0')
    
    # Criar canal
    channel = ET.SubElement(rss, 'channel')
    
    ET.SubElement(channel, "title").text = "DRE Procedimentos Filtrados (Seeds)"
    ET.SubElement(channel, "link").text = "https://sotkonhsilva.github.io/DRE-RSS_STK/"
    ET.SubElement(channel, "description").text = "Feed RSS automatizado com base nas sementes de pesquisa parametrizadas."
    ET.SubElement(channel, "language").text = "pt-PT"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Adicionar tag do gerador
    ET.SubElement(channel, "generator").text = "Antigravity RSS Generator 1.0"

    # Link atom para auto-descoberta
    atom_link = ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link')
    atom_link.set('href', 'https://sotkonhsilva.github.io/DRE-RSS_STK/RSS/feed_filtros_seeds.xml')
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')

    for i, item in enumerate(filtered_items):
        rss_item = ET.SubElement(channel, "item")
        
        nipc = str(item.get('nipc', 'N/A')).strip()
        entidade = str(item.get('entidade_adjudicante', item.get('entidade', 'N/A'))).strip()
        designacao = str(item.get('descricao') or item.get('designacao_contrato') or "Procedimento sem título").strip()
        matched_seed = str(item.get('matched_seed', 'SEED')).strip()
        
        # Escapar e limpar texto básico
        def clean_text(t):
            t = str(t)
            # Remover caracteres de controle
            t = "".join(ch for ch in t if ord(ch) >= 32 or ch in "\n\r\t")
            return t

        title_text = clean_text(f"[{matched_seed}] [{nipc}] {entidade} - {designacao}")
        ET.SubElement(rss_item, "title").text = title_text
        
        link = clean_url(item.get('link', ''))
        ET.SubElement(rss_item, "link").text = link
        
        # pubDate é CRITICO para Outlook
        pub_date_elem = ET.SubElement(rss_item, "pubDate")
        detalhes = item.get('detalhes_completos', '')
        envio_match = re.search(r'Data de Envio do Anúncio:\s*(\d{2}-\d{2}-\d{4})', detalhes)
        if envio_match:
            try:
                dt = datetime.strptime(envio_match.group(1), '%d-%m-%Y')
                pub_date_elem.text = dt.strftime("%a, %d %b %Y 00:00:00 GMT")
            except:
                pub_date_elem.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        else:
            pub_date_elem.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")

        # Placeholder para descrição
        ET.SubElement(rss_item, "description").text = f"DESCRIPTION_CDATA_PLACEHOLDER_{i}"
        
        # GUID único (adiciona índice para evitar duplicatas se o link for igual)
        guid = ET.SubElement(rss_item, "guid", isPermaLink="false")
        guid.text = f"{link}#{i}"

    # Gerar XML com minidom para formatação limpa
    rough_string = ET.tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    xml_str = reparsed.toxml(encoding='UTF-8').decode('utf-8')
    
    # Processar CDATAs (em ordem inversa para evitar problemas com índices como 1 e 11)
    reconstructed = xml_str
    for i in range(len(filtered_items) - 1, -1, -1):
        item = filtered_items[i]
        nipc = item.get('nipc', 'N/A')
        entidade = item.get('entidade_adjudicante', item.get('entidade', 'N/A'))
        designacao = item.get('descricao') or item.get('designacao_contrato') or "Procedimento sem título"
        matched_seed = item.get('matched_seed', 'SEED')
        price_val = item.get('preco_base', 'N/A')
        plataforma = item.get('plataforma_eletronica', 'N/A')
        concelho = item.get('concelho', 'N/A')
        prazo = item.get('prazo_execucao', 'N/A')
        
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
                <div style="font-size:11px;">CONCELHO: {concelho}</div>
            </td>
            <td width="33%" valign="top" style="background:#ffffff; padding:10px; border:1px solid #d1d9e6; border-radius:8px;">
                <h4 style="color:#2a5298; margin:0 0 10px 0; font-size:12px;">CONTRATO</h4>
                <div style="font-size:11px;">PRAZO: {prazo}</div>
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
        reconstructed = reconstructed.replace(f"DESCRIPTION_CDATA_PLACEHOLDER_{i}", f"<![CDATA[{desc_html}]]>")

    # Salvar o arquivo
    # Tentar determinar as pastas de destino
    targets = []
    
    # Root paths
    is_root = os.path.exists('package.json') or os.path.exists('RSS')
    is_parent_root = os.path.exists('../package.json') or os.path.exists('../RSS')

    if is_root:
        targets.append('RSS')
    elif is_parent_root:
        targets.append('../RSS')
        
    # Public paths
    if os.path.exists('public'):
        p = 'public/RSS'
        if p not in targets: targets.append(p)
    elif os.path.exists('../public'):
        p = '../public/RSS'
        if p not in targets: targets.append(p)

    if not targets:
        targets = ['RSS']

    for rss_dir in targets:
        output_path = os.path.join(rss_dir, "feed_filtros_seeds.xml")
        try:
            os.makedirs(rss_dir, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(reconstructed)
            print(f"✅ Feed filtrado salvo em: {output_path}")
        except Exception as e:
            print(f"❌ Erro ao salvar em {rss_dir}: {e}")
        
    print(f"✅ RSS filtrado gerado em: {output_path} ({len(filtered_items)} itens)")

if __name__ == "__main__":
    generate_filtered_rss()
