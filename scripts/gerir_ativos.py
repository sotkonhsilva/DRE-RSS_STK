import json
import os
from datetime import datetime
from typing import List, Dict

def parse_date(date_str: str) -> datetime:
    """
    Converte string de data no formato DD-MM-YYYY HH:MM para datetime
    """
    try:
        # Formato esperado: "08-08-2025 18:00"
        return datetime.strptime(date_str, '%d-%m-%Y %H:%M')
    except ValueError:
        # Se não conseguir fazer parse, retornar uma data muito antiga
        return datetime(1900, 1, 1)

def is_procedure_active(procedure: Dict) -> bool:
    """
    Verifica se um procedimento está ativo (prazo de apresentação ainda válido)
    """
    prazo_str = procedure.get('prazo_apresentacao_propostas')
    
    if not prazo_str or prazo_str == 'N/A':
        return False
    
    try:
        prazo_date = parse_date(prazo_str)
        current_date = datetime.now()
        
        # Procedimento está ativo se o prazo for >= data atual
        return prazo_date >= current_date
    except:
        return False

def get_all_data_dirs():
    """
    Retorna todos os caminhos possíveis para o diretório data/
    """
    current_dir = os.getcwd()
    targets = []
    
    # Prioridade para Root data/ (para GitHub Pages)
    root_paths = ['data', '../data']
    for p in root_paths:
        if os.path.exists(p) or os.path.exists(os.path.join(p, '..', 'package.json')):
            if p not in targets: targets.append(p)
            
    # Public paths (para Next.js local)
    public_paths = ['public/data', '../public/data']
    for p in public_paths:
        if os.path.exists(p):
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