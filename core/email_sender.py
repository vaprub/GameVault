# core/email_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import logging

# SMTP серверы
SMTP_SERVERS = {
    'gmail.com': ('smtp.gmail.com', 587),
    'yandex.ru': ('smtp.yandex.ru', 587),
    'ya.ru': ('smtp.yandex.ru', 587),
    'mail.ru': ('smtp.mail.ru', 587),
    'bk.ru': ('smtp.mail.ru', 587),
    'list.ru': ('smtp.mail.ru', 587),
    'inbox.ru': ('smtp.mail.ru', 587),
    'rambler.ru': ('smtp.rambler.ru', 587),
    'outlook.com': ('smtp-mail.outlook.com', 587),
    'hotmail.com': ('smtp-mail.outlook.com', 587),
    'live.com': ('smtp-mail.outlook.com', 587),
    'icloud.com': ('smtp.mail.me.com', 587),
    'yahoo.com': ('smtp.mail.yahoo.com', 587)
}

logger = logging.getLogger('GameVault.Core.email_sender')
class EmailSender:
    """Отправка email через любой SMTP"""
    
    def __init__(self, crypto):
        self.crypto = crypto
        
    def get_smtp_settings(self, email):
        """Определение SMTP настроек"""
        domain = email.split('@')[-1].lower()
        
        if domain in SMTP_SERVERS:
            return SMTP_SERVERS[domain]
        
        for key, value in SMTP_SERVERS.items():
            if key in domain:
                return value
        
        return ('smtp.gmail.com', 587)
    
    def send_email(self, to_email, subject, body, password=None, attachment=None):
        """Отправка письма"""
        try:
            smtp_server, smtp_port = self.get_smtp_settings(to_email)
            
            # Создаем сообщение
            message = MIMEMultipart()
            message["Subject"] = subject
            message["From"] = to_email
            message["To"] = to_email
            message.attach(MIMEText(body, "plain", "utf-8"))
            
            # Добавляем вложение
            if attachment and os.path.exists(attachment):
                with open(attachment, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment)}"
                )
                message.attach(part)
            
            # Отправляем
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(to_email, password)
            server.send_message(message)
            server.quit()
            
            return True, "Письмо отправлено!"
            
        except Exception as e:
            return False, str(e)