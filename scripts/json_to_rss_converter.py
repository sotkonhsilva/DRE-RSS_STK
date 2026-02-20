import json
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Dict, List, Optional
import os

def extract_field_from_details(details_text: str, field_name: str) -> Optional[str]:
    """
    Extrai um campo específico do texto de detalhes usando regex
    """
    patterns = {
        'entidade_adjudicante': r'Designação da entidade adjudicante:\s*(.+?)(?:\n|$)',
        'nipc': r'NIPC:\s*(\d+)',
        'distrito': r'Distrito:\s*(.+?)(?:\n|$)',
        'concelho': r'Concelho:\s*(.+?)(?:\n|$)',
        'freguesia': r'Freguesia:\s*(.+?)(?:\n|$)',
        'site': r'Endereço da Entidade \(URL\):\s*(.+?)(?:\n|$)',
        'email': r'Endereço Eletrónico:\s*(.+?)(?:\n|$)',
        'designacao_contrato': r'Designação do contrato:\s*(.+?)(?:\n|$)',
        'descricao': r'Descrição:\s*(.+?)(?:\n|$)',
        'preco_base': r'Preço base s/IVA:\s*(.+?)(?:\n|$)',
        'prazo_execucao': r'Prazo de execução do contrato:\s*(.+?)(?:\n|$)',
        'prazo_apresentacao_propostas': r'Prazo para apresentação das propostas:\s*(.+?)(?:\n|$)',
        'fundos_eu': r'Têm fundos EU\?\s*(.+?)(?:\n|$)',
        'plataforma_eletronica': r'Plataforma eletrónica utilizada pela entidade adjudicante:\s*(.+?)(?:\n|$)',
        'url_procedimento': r'URL para Apresentação:\s*(.+?)(?:\n|$)',
        'numero_procedimento': r'Número de referência interna:\s*(.+?)(?:\n|$)',
        'autor_nome': r'28 - IDENTIFICAÇÃO DO\(S\) AUTOR\(ES\) DE ANÚNCIO\nNome:\s*(.+?)(?:\n|$)',
        'autor_cargo': r'Cargo:\s*(.+?)(?:\n|$)'
    }
    
    if field_name not in patterns:
        return None
    
    pattern = patterns[field_name]
    match = re.search(pattern, details_text, re.MULTILINE | re.DOTALL)
    
    if match:
        value = match.group(1).strip()
        # Limpar quebras de linha e espaços extras
        value = re.sub(r'\s+', ' ', value)
        # Remover caracteres especiais HTML
        value = value.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return value
    
    return None

def clean_url(url: str) -> str:
    """Limpa URLs de brancos e quebras de linha que invalidam o RSS"""
    if not url: return "https://diariodarepublica.pt"
    return str(url).strip().replace('\n', '').replace('\r', '').replace(' ', '%20')


def parse_procedimento(proc: Dict) -> Dict:
    """
    Processa um procedimento e extrai as informações específicas
    """
    # Informações básicas
    numero = proc.get('numero_procedimento', 'N/A')
    entidade = proc.get('entidade', 'N/A')
    link = proc.get('link', '')
    
    # Extrair informações dos detalhes
    detalhes_text = proc.get('detalhes_completos', '')
    
    # Se não há detalhes_completos, tentar usar os campos individuais
    if not detalhes_text:
        return {
            'numero_procedimento': numero,
            'entidade': entidade,
            'link': link,
            'nipc': proc.get('nipc', 'N/A'),
            'distrito': proc.get('distrito', 'N/A'),
            'concelho': proc.get('concelho', 'N/A'),
            'freguesia': proc.get('freguesia', 'N/A'),
            'site': proc.get('site', 'N/A'),
            'email': proc.get('email', 'N/A'),
            'designacao_contrato': proc.get('designacao_contrato', 'N/A'),
            'descricao': proc.get('descricao', 'N/A'),
            'preco_base': proc.get('preco_base', 'N/A'),
            'prazo_execucao': proc.get('prazo_execucao', 'N/A'),
            'prazo_apresentacao_propostas': proc.get('prazo_apresentacao_propostas', 'N/A'),
            'fundos_eu': proc.get('fundos_eu', 'N/A'),
            'plataforma_eletronica': proc.get('plataforma_eletronica', 'N/A'),
            'url_procedimento': proc.get('url_procedimento', 'N/A'),
            'autor_nome': proc.get('autor_nome', 'N/A'),
            'autor_cargo': proc.get('autor_cargo', 'N/A')
        }
    
    # Extrair informações específicas do texto de detalhes
    extracted_info = {}
    fields = [
        'entidade_adjudicante', 'nipc', 'distrito', 'concelho', 'freguesia',
        'site', 'email', 'designacao_contrato', 'descricao', 'preco_base',
        'prazo_execucao', 'prazo_apresentacao_propostas', 'fundos_eu', 'plataforma_eletronica', 'url_procedimento',
        'autor_nome', 'autor_cargo', 'numero_procedimento'
    ]
    
    for field in fields:
        value = extract_field_from_details(detalhes_text, field)
        extracted_info[field] = value if value else 'N/A'
    
    return {
        'numero_procedimento': numero,
        'entidade': entidade,
        'link': link,
        **extracted_info
    }

def create_rss_feed(procedimentos: List[Dict]) -> str:
    """
    Cria um feed RSS a partir dos procedimentos processados
    """
    # Criar elemento raiz do RSS
    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
    rss = ET.Element('rss', version='2.0')
    
    # Criar canal
    channel = ET.SubElement(rss, 'channel')
    
    # Informações do canal
    title = ET.SubElement(channel, 'title')
    title.text = 'Feed RSS - Procedimentos DRE'
    
    description = ET.SubElement(channel, 'description')
    description.text = 'Feed RSS com procedimentos do Diário da República - Série II - Parte L'
    
    link = ET.SubElement(channel, 'link')
    link.text = 'https://sotkonhsilva.github.io/DRE-RSS_STK/'
    
    # Adicionar tag do gerador
    ET.SubElement(channel, "generator").text = "Antigravity RSS Generator 1.0"
    
    # Link atom para auto-descoberta
    atom_link = ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link')
    atom_link.set('href', 'https://sotkonhsilva.github.io/DRE-RSS_STK/RSS/feed_rss_procedimentos.xml')
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    language = ET.SubElement(channel, 'language')
    language.text = 'pt-PT'
    
    pub_date = ET.SubElement(channel, 'lastBuildDate')
    pub_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # Adicionar cada procedimento como item
    for i, proc in enumerate(procedimentos):
        item = ET.SubElement(channel, 'item')
        
        nipc = str(proc.get('nipc', 'N/A')).strip()
        entidade = str(proc.get('entidade_adjudicante', proc.get('entidade', 'N/A'))).strip()
        designacao = str(proc.get('designacao_contrato', proc.get('descricao', 'N/A'))).strip()
        if designacao == 'N/A' or not designacao:
            designacao = "Procedimento sem título"
            
        item_title = ET.SubElement(item, 'title')
        item_title.text = f"[{nipc}] {entidade} - {designacao}"
        
        c_link = clean_url(proc.get('link', ''))
        ET.SubElement(item, 'link').text = c_link
        
        # GUID único
        guid = ET.SubElement(item, 'guid')
        guid.text = f"{c_link}#{i}"
        guid.set('isPermaLink', 'false')
        
        pub_date_item = ET.SubElement(item, 'pubDate')
        detalhes = proc.get('detalhes_completos', '')
        envio_match = re.search(r'Data de Envio do Anúncio:\s*(\d{2}-\d{2}-\d{4})', detalhes)
        if envio_match:
            try:
                dt = datetime.strptime(envio_match.group(1), '%d-%m-%Y')
                pub_date_item.text = dt.strftime("%a, %d %b %Y 00:00:00 GMT")
            except:
                pub_date_item.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        else:
            pub_date_item.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Placeholder
        item_description = ET.SubElement(item, 'description')
        item_description.text = f"DESCRIPTION_CDATA_PLACEHOLDER_{i}"
        
    # Converter para string XML formatada usando minidom
    rough_string = ET.tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    xml_str = reparsed.toxml(encoding='UTF-8').decode('utf-8')
    
    # Processar CDATAs (em ordem inversa para evitar problemas com índices como 1 e 11)
    reconstructed = xml_str
    
    for i in range(len(procedimentos) - 1, -1, -1):
        proc = procedimentos[i]
        nipc = proc.get('nipc', 'N/A')
        entidade = proc.get('entidade_adjudicante', proc.get('entidade', 'N/A'))
        designacao = proc.get('designacao_contrato', proc.get('descricao', 'N/A'))
        price_val = proc.get('preco_base', 'N/A')
        plataforma = proc.get('plataforma_eletronica', 'N/A')
        c_link = clean_url(proc.get('link', ''))
        c_url_proc = clean_url(proc.get('url_procedimento', ''))
        
        desc_html = f"""
<div style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 15px; border: 1px solid #e0e6ed; border-radius: 8px;">
    <div style="background-color: #ffffff; padding: 12px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #2a5298;">
        <div style="font-size: 11px; color: #2a5298; font-weight: bold; text-transform: uppercase;">{entidade}</div>
        <div style="font-size: 15px; font-weight: bold; color: #1e293b; margin: 4px 0;">{designacao}</div>
        <div style="font-size: 10px; color: #64748b;"><span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px;">PLATAFORMA: {plataforma}</span></div>
    </div>
    <table width="100%" cellpadding="0" cellspacing="5" border="0">
        <tr>
            <td width="50%" valign="top" style="background:#ffffff; padding:10px; border:1px solid #d1d9e6; border-radius:8px;">
                <div style="font-size:11px;">NIPC: <b>{nipc}</b></div>
                <div style="font-size:11px;">PREÇO: <b>{price_val}</b></div>
            </td>
            <td width="50%" valign="top" style="background:#ffffff; padding:10px; border:1px solid #d1d9e6; border-radius:8px;">
                <div style="font-size:11px;"><a href="{c_link}">Anúncio DRE</a></div>
                <div style="font-size:11px;"><a href="{c_url_proc}">Procedimento</a></div>
            </td>
        </tr>
    </table>
</div>
""".strip()
        reconstructed = reconstructed.replace(f"DESCRIPTION_CDATA_PLACEHOLDER_{i}", f"<![CDATA[{desc_html}]]>")

    return reconstructed


def main():
    """
    Função principal
    """
    # Carregar dados do JSON
    possible_paths = [
        'RSS/procedimentos_completos.json',
        '../RSS/procedimentos_completos.json',
        'public/RSS/procedimentos_completos.json',
        '../public/RSS/procedimentos_completos.json',
        'procedimentos_completos.json'
    ]
    
    json_file = None
    for path in possible_paths:
        if os.path.exists(path):
            json_file = path
            break
            
    if not json_file:
        print(f"❌ Arquivo procedimentos_completos.json não encontrado!")
        print("Caminhos tentados:", possible_paths)
        print("Execute primeiro o script rss_dre_extractor.py")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar {json_file}: {e}")
        return
    
    print(f"Carregados {len(dados)} procedimentos do JSON")
    
    # Processar cada procedimento
    procedimentos_processados = []
    for i, proc in enumerate(dados):
        print(f"Processando procedimento {i+1}/{len(dados)}...")
        proc_processado = parse_procedimento(proc)
        procedimentos_processados.append(proc_processado)
        
        # Mostrar exemplo do primeiro procedimento
        if i == 0:
            print(f"  Exemplo - Entidade: {proc_processado.get('entidade', 'N/A')}")
            print(f"  Exemplo - NIPC: {proc_processado.get('nipc', 'N/A')}")
            print(f"  Exemplo - Preço: {proc_processado.get('preco_base', 'N/A')}")
    
    # Criar feed RSS
    print("\nCriando feed RSS...")
    rss_content = create_rss_feed(procedimentos_processados)
    
    # Salvar feed RSS
    # Tentar determinar as pastas de destino (Prioridade para ROOT/RSS para o GitHub Pages)
    targets = []
    
    # Root paths
    if os.path.exists('RSS') or os.path.exists('package.json'):
        targets.append('RSS')
    elif os.path.exists('../RSS') or os.path.exists('../package.json'):
        targets.append('../RSS')
        
    # Public paths (for local dev dev next.js)
    if os.path.exists('public/RSS'):
        if 'public/RSS' not in targets and '../public/RSS' not in targets:
            targets.append('public/RSS')
    elif os.path.exists('../public/RSS'):
        if 'public/RSS' not in targets and '../public/RSS' not in targets:
            targets.append('../public/RSS')

    if not targets:
        # Fallback para criar na raiz
        targets = ['RSS']

    for rss_dir in targets:
        output_file = os.path.join(rss_dir, 'feed_rss_procedimentos.xml')
        try:
            os.makedirs(rss_dir, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(rss_content)
            print(f"✅ Feed RSS salvo em: {output_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar em {rss_dir}: {e}")
        
    print(f"\nFeed RSS criado com sucesso em {len(targets)} localizações.")
    print(f"Total de procedimentos processados: {len(procedimentos_processados)}")
    
    # Estatísticas
    print("\nEstatísticas:")
    print(f"- Procedimentos com entidade: {len([p for p in procedimentos_processados if p.get('entidade') != 'N/A'])}")
    print(f"- Procedimentos com NIPC: {len([p for p in procedimentos_processados if p.get('nipc') != 'N/A'])}")
    print(f"- Procedimentos com preço: {len([p for p in procedimentos_processados if p.get('preco_base') != 'N/A'])}")
    print(f"- Procedimentos com fundos EU: {len([p for p in procedimentos_processados if p.get('fundos_eu') and p.get('fundos_eu') != 'N/A'])}")

if __name__ == "__main__":
    main() 