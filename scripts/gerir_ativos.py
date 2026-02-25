import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict

# Procedimentos sem prazo extraído expiram após este número de dias desde a publicação
FALLBACK_DAYS_ACTIVE = 60

def parse_date(date_str: str) -> datetime:
    """
    Converte string de data no formato DD-MM-YYYY HH:MM para datetime
    """
    try:
        return datetime.strptime(date_str, '%d-%m-%Y %H:%M')
    except ValueError:
        try:
            return datetime.strptime(date_str, '%d-%m-%Y')
        except ValueError:
            return datetime(1900, 1, 1)

def get_publication_date(procedure: Dict) -> datetime:
    """
    Tenta extrair a data de publicação do campo detalhes_completos.
    Retorna None se não encontrar.
    """
    detalhes = procedure.get('detalhes_completos', '') or ''
    match = re.search(r'Data de Envio do Anúncio:\s*(\d{2}-\d{2}-\d{4})', detalhes)
    if match:
        try:
            return datetime.strptime(match.group(1), '%d-%m-%Y')
        except:
            pass
    return None

def is_procedure_active(procedure: Dict) -> bool:
    """
    Verifica se um procedimento está ativo (prazo de apresentação ainda válido).
    Quando o prazo não está disponível, usa a data de publicação como fallback:
    considera ativo por FALLBACK_DAYS_ACTIVE dias após a publicação.
    """
    prazo_str = procedure.get('prazo_apresentacao_propostas')
    current_date = datetime.now()

    if prazo_str and prazo_str != 'N/A':
        try:
            prazo_date = parse_date(prazo_str)
            if prazo_date.year > 1900:  # data válida
                return prazo_date >= current_date
        except:
            pass

    # Fallback 1: usar data de publicação extraída dos detalhes
    pub_date = get_publication_date(procedure)
    if pub_date:
        expiry = pub_date + timedelta(days=FALLBACK_DAYS_ACTIVE)
        return current_date <= expiry

    # Fallback 2: usar data de extração se disponível (para itens ainda não processados)
    ext_date_str = procedure.get('data_extracao')
    if ext_date_str:
        try:
            # Tentar vários formatos comuns
            ext_date = parse_date(ext_date_str)
            if ext_date.year > 1900:
                expiry = ext_date + timedelta(days=FALLBACK_DAYS_ACTIVE)
                return current_date <= expiry
        except:
            pass

    # Se não tem detalhes_completos, é um item novo que ainda não foi processado.
    # Devemos mantê-lo ativo para que apareça nos feeds básicos até ser processado.
    if not procedure.get('detalhes_completos'):
        # Como não sabemos a data, assumimos que é novo. 
        # Para evitar acumular lixo, se o procedimento já é conhecido mas continua sem detalhes 
        # após muito tempo, eventualmente expirará aqui se guardarmos a data de extração.
        return True

    # Sem data de publicação, sem data de extração, mas tem detalhes (e falhou nos checks acima):
    # assumir expirado para não acumular indefinidamente
    return False

def get_all_data_dirs():
    """
    Retorna todos os caminhos possíveis para o diretório data/
    """
    targets = []
    
    # 1. Root data/ (Prioridade para GitHub Pages)
    # Se existe package.json ou pasta data
    is_root = os.path.exists('package.json') or os.path.exists('data')
    is_parent_root = os.path.exists('../package.json') or os.path.exists('../data')
    
    if is_root:
        if 'data' not in targets: targets.append('data')
    elif is_parent_root:
        if '../data' not in targets: targets.append('../data')
            
    # 2. Public paths (para Next.js local)
    # Se existe a pasta public, devemos garantir que data/ existe lá dentro
    if os.path.exists('public'):
        p = 'public/data'
        if p not in targets: targets.append(p)
    elif os.path.exists('../public'):
        p = '../public/data'
        if p not in targets: targets.append(p)
            
    if not targets:
        targets = ['data']
        
    return targets

def get_data_dir():
    """
    Retorna o primeiro caminho encontrado para o diretório data/
    """
    return get_all_data_dirs()[0]

def load_existing_ativos() -> List[Dict]:
    """
    Carrega o arquivo ativos.json existente se existir
    """
    data_dir = get_data_dir()
    ativos_file = os.path.join(data_dir, 'ativos.json')
    
    if os.path.exists(ativos_file):
        try:
            with open(ativos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar {ativos_file}: {e}")
            return []
    return []

def save_ativos(procedimentos_ativos: List[Dict]) -> str:
    """
    Salva a lista de procedimentos ativos no arquivo ativos.json em todas as localizações encontradas
    """
    targets = get_all_data_dirs()
    last_file = ""
    
    for data_dir in targets:
        try:
            os.makedirs(data_dir, exist_ok=True)
            ativos_file = os.path.join(data_dir, 'ativos.json')
            with open(ativos_file, 'w', encoding='utf-8') as f:
                json.dump(procedimentos_ativos, f, ensure_ascii=False, indent=2)
            print(f"✅ Arquivo ativos.json atualizado em: {ativos_file}")
            last_file = ativos_file
        except Exception as e:
            print(f"❌ Erro ao salvar ativos.json em {data_dir}: {e}")
            
    return last_file

def update_ativos_from_date_file(date_file_path: str) -> List[Dict]:
    """
    Atualiza o arquivo ativos.json baseado no arquivo de data específico
    """
    print(f"📅 Atualizando ativos.json a partir de {date_file_path}...")
    
    # Carregar procedimentos do arquivo de data
    try:
        with open(date_file_path, 'r', encoding='utf-8') as f:
            procedimentos = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar {date_file_path}: {e}")
        return []
    
    print(f"Carregados {len(procedimentos)} procedimentos do arquivo de data")
    
    # Filtrar apenas procedimentos ativos
    procedimentos_ativos = []
    procedimentos_expirados = 0
    
    for proc in procedimentos:
        if is_procedure_active(proc):
            procedimentos_ativos.append(proc)
        else:
            procedimentos_expirados += 1
    
    print(f"✅ Procedimentos ativos: {len(procedimentos_ativos)}")
    print(f"❌ Procedimentos expirados: {procedimentos_expirados}")
    
    return procedimentos_ativos

def merge_with_existing_ativos(procedimentos_ativos: List[Dict]) -> List[Dict]:
    """
    Combina novos procedimentos ativos com os existentes, removendo duplicados
    """
    existing_ativos = load_existing_ativos()
    
    if not existing_ativos:
        return procedimentos_ativos
    
    print(f"Combinando com {len(existing_ativos)} procedimentos ativos existentes...")
    
    # Criar um set de links para verificar duplicados
    existing_links = {proc.get('link', '') for proc in existing_ativos}
    
    # Adicionar apenas procedimentos que não existem
    novos_procedimentos = []
    for proc in procedimentos_ativos:
        if proc.get('link', '') not in existing_links:
            novos_procedimentos.append(proc)
    
    # Combinar existentes + novos
    todos_ativos = existing_ativos + novos_procedimentos
    
    # Verificar novamente quais estão ativos (pode ter expirado desde a última verificação)
    ativos_finais = []
    for proc in todos_ativos:
        if is_procedure_active(proc):
            ativos_finais.append(proc)
    
    print(f"✅ Total de procedimentos ativos após merge: {len(ativos_finais)}")
    print(f"📈 Novos procedimentos adicionados: {len(novos_procedimentos)}")
    
    return ativos_finais

def main():
    """
    Função principal para testar o script com dados reais
    """
    print("🔍 Testando gestão de procedimentos ativos com dados reais...")
    
    # Testar com o arquivo real criado pela consulta inicial
    data_dir = get_data_dir()
    date_file_path = os.path.join(data_dir, '31-07-2025.json')
    
    print(f"📁 Diretório de dados: {data_dir}")
    print(f"📄 Procurando arquivo: {date_file_path}")
    
    if os.path.exists(date_file_path):
        print(f"✅ Arquivo encontrado: {date_file_path}")
        
        # Atualizar ativos a partir do arquivo real
        procedimentos_ativos = update_ativos_from_date_file(date_file_path)
        
        # Combinar com existentes (se houver)
        ativos_finais = merge_with_existing_ativos(procedimentos_ativos)
        
        # Salvar arquivo ativos.json
        ativos_file_path = save_ativos(ativos_finais)
        
        if ativos_file_path:
            print(f"\n✅ Teste concluído com sucesso!")
            print(f"📊 Total de procedimentos ativos: {len(ativos_finais)}")
            
            # Mostrar alguns exemplos
            print(f"\n📋 Exemplos de procedimentos ativos:")
            for i, proc in enumerate(ativos_finais[:5]):  # Mostrar apenas os primeiros 5
                entidade = proc.get('entidade', 'N/A')
                prazo = proc.get('prazo_apresentacao_propostas', 'N/A')
                print(f"  {i+1}. {entidade[:50]}... - Prazo: {prazo}")
            
            if len(ativos_finais) > 5:
                print(f"  ... e mais {len(ativos_finais) - 5} procedimentos")
        else:
            print("❌ Erro ao salvar arquivo ativos.json")
    else:
        print(f"❌ Arquivo {date_file_path} não encontrado!")
        print("Execute primeiro o script rss_dre_extractor.py para gerar dados reais")
        
        # Mostrar arquivos disponíveis no diretório
        if os.path.exists(data_dir):
            print(f"\n📂 Arquivos disponíveis em {data_dir}:")
            for file in os.listdir(data_dir):
                if file.endswith('.json'):
                    print(f"  - {file}")

if __name__ == "__main__":
    main() 