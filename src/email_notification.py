import smtplib
from email.message import EmailMessage

def send_backup_email(backup_details):
    msg = EmailMessage()
    body = "Backup Details:\n\n"
    for key, value in backup_details.items():
        body += f"{key}: {value}\n"
    
    msg.set_content(body)
    msg['Subject'] = "Backup Completed"
    msg['From'] = "your_email@example.com"
    msg['To'] = "recipient@example.com"

    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "your_email@example.com"
    password = "your_password"

    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(sender_email, password)
    server.send_message(msg)
    server.quit()