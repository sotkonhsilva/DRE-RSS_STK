import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict

# Configurações de Email (Devem ser configuradas como Secrets no GitHub ou env vars locais)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "jhsilva@sotkon.com")

def load_seeds() -> List[Dict]:
    """Carrega as seeds do arquivo JSON de forma robusta"""
    # Tentar encontrar a pasta data independente de onde o script é corrido
    possible_paths = [
        os.path.join("data", "seeds.json"),
        os.path.join("..", "data", "seeds.json"),
        "seeds.json"
    ]
    
    for seeds_file in possible_paths:
        if os.path.exists(seeds_file):
            try:
                with open(seeds_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
    return []

def procedure_matches_seed(proc: Dict, seed: Dict) -> bool:
    """Verifica se um procedimento corresponde a uma seed (Lógica idêntica ao scripts.js)"""
    
    # 1. Distrito
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

    # 2. Title Tags (Obrigatórias no título/descrição)
    title_tags = seed.get('titleTags', [])
    if title_tags:
        if not any(tag.lower() in title_text for tag in title_tags):
            return False

    # 3. Global Tags (Pelo menos uma em qualquer lugar)
    global_tags = seed.get('tags', [])
    if global_tags:
        if not any(tag.lower() in full_text for tag in global_tags):
            return False
            
    return True

def send_notification(new_items: List[Dict]):
    """Envia email com os novos itens encontrados"""
    if not EMAIL_RECEIVER or not SMTP_USER or not SMTP_PASSWORD:
        print("⚠️ Configurações de email ausentes. Notificação ignorada.")
        return

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"🔔 Novos Procedimentos DRE Encontrados - {datetime.now().strftime('%d/%m/%Y')}"

    # Construir corpo HTML
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2a5298;">Novos Procedimentos Detectados</h2>
        <p>Foram encontrados {len(new_items)} novos procedimentos correspondentes às suas seeds:</p>
        <hr>
    """

    for item in new_items:
        html += f"""
        <div style="margin-bottom: 20px; padding: 15px; border-radius: 8px; background-color: #f9f9f9; border-left: 5px solid #2a5298;">
            <h3 style="margin-top: 0; color: #2a5298;">{item.get('descricao') or item.get('designacao_contrato', 'Sem descrição')}</h3>
            <p><strong>Entidade:</strong> {item.get('entidade') or item.get('entidade_adjudicante', 'N/A')}</p>
            <p><strong>Preço Base:</strong> {item.get('preco_base', 'N/A')}</p>
            <p><strong>Prazo:</strong> {item.get('prazo_apresentacao_propostas', 'N/A')}</p>
            <p><strong>Local:</strong> {item.get('distrito', 'N/A')} - {item.get('concelho', 'N/A')}</p>
            <p><a href="{item.get('link', '#')}" style="display: inline-block; padding: 10px 20px; background-color: #2a5298; color: white; text-decoration: none; border-radius: 5px;">Ver Detalhes no DRE</a></p>
        </div>
        """

    html += """
        <p style="font-size: 0.8em; color: #777;">Este é um email automático enviado pelo Portal de Procedimentos DRE-RSS.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"📧 Email enviado com sucesso para {EMAIL_RECEIVER}")
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")

def notify_new_items(current_items: List[Dict]):
    """Compara com os itens anteriores e notifica sobre os novos que dão match com as seeds"""
    
    # Localizar ativos.json de forma robusta
    ativos_json = None
    possible_ativos = [
        os.path.join("data", "ativos.json"),
        os.path.join("..", "data", "ativos.json")
    ]
    
    for p in possible_ativos:
        if os.path.exists(p):
            ativos_json = p
            break

    if not ativos_json:
        print("Aviso: ativos.json não encontrado. Ignorando notificações.")
        return

    try:
        with open(ativos_json, 'r', encoding='utf-8') as f:
            old_items = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar ativos anteriores: {e}")
        old_items = []

    old_links = {item.get('link') for item in old_items if item.get('link')}
    
    # Identificar itens que são realmente novos (não estavam no arquivo anterior)
    brand_new_items = [item for item in current_items if item.get('link') not in old_links]
    
    if not brand_new_items:
        print("Nenhum item novo encontrado em relação ao ativos.json anterior.")
        return

    # Carregar seeds e filtrar os novos itens
    seeds = load_seeds()
    items_to_notify = []

    for item in brand_new_items:
        for seed in seeds:
            if procedure_matches_seed(item, seed):
                # Adicionar informação de qual seed deu match (opcional)
                item['matched_seed'] = seed.get('name', seed.get('code'))
                items_to_notify.append(item)
                break # Notificar uma vez se der match em qualquer seed

    if items_to_notify:
        print(f"🎯 Foram encontrados {len(items_to_notify)} novos itens com match nas seeds!")
        send_notification(items_to_notify)
    else:
        print("Novos itens encontrados, mas nenhum deu match com as seeds parametrizadas.")
