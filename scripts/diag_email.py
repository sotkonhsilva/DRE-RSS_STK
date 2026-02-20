import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_config(server, port, user, password, receiver, use_ssl=False):
    print(f"--- Testando {server}:{port} (SSL: {use_ssl}) ---")
    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = receiver
    msg['Subject'] = "Teste de Conexão Portal DRE"
    msg.attach(MIMEText("Este é um teste para validar as configurações de email.", 'plain'))

    try:
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
            smtp.starttls()
        
        smtp.login(user, password)
        smtp.send_message(msg)
        smtp.quit()
        return True, "Sucesso!"
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    user = os.environ.get("SMTP_USER", "comercial@mail2portugal.com")
    password = os.environ.get("SMTP_PASSWORD", "Comercial@2026")
    receiver = os.environ.get("EMAIL_RECEIVER", "jhsilva@sotkon.com")
    
    # Lista de servidores e portas para tentar
    configs = [
        ("smtp.mail2world.com", 587, False),
        ("smtp.mail2world.com", 465, True),
        ("publicms2.mail2world.com", 587, False),
        ("publicms2.mail2world.com", 25, False),
        ("mail2portugal.com", 587, False),
    ]
    
    for server, port, ssl in configs:
        success, msg = test_config(server, port, user, password, receiver, ssl)
        if success:
            print(f"✅ FUNCIONOU: {server}:{port}")
            break
        else:
            print(f"❌ Falhou: {msg}")
