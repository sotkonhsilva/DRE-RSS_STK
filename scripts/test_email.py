import os
import sys

# Adicionar o diretório atual ao path para importar notify_new_items
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from notify_new_items import send_notification

def test_email():
    print("🧪 Iniciando envio de email de teste...")
    
    # Criar um item de exemplo fictício
    test_items = [
        {
            "descricao": "TESTE: Aquisição de Contentores de Resíduos",
            "entidade": "Município de Exemplo",
            "preco_base": "125.000,00 €",
            "prazo_apresentacao_propostas": "25-02-2026 18:00",
            "distrito": "Lisboa",
            "concelho": "Lisboa",
            "link": "https://diariodarepublica.pt/"
        }
    ]
    
    print(f"SMTP_USER: {os.environ.get('SMTP_USER')}")
    print(f"EMAIL_RECEIVER: {os.environ.get('EMAIL_RECEIVER')}")
    
    send_notification(test_items)
    print("✅ Processo de teste concluído.")

if __name__ == "__main__":
    test_email()
