import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email(to_email, subject, body):
    """
    Sends an email using credentials from environment variables.
    Returns True if successful, False otherwise.
    If credentials are not set, it prints the email to the console (Mock Mode).
    """
    # 1. Load config
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    try:
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
    except ValueError:
        smtp_port = 587
        
    sender_email = os.environ.get("SMTP_EMAIL")
    sender_password = os.environ.get("SMTP_PASSWORD")

    # 2. Validation / Mock Mode
    if not sender_email or not sender_password:
        print(f"\n[MOCK EMAIL SERVICE]")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print("-" * 20)
        print(body)
        print("-" * 20 + "\n")
        return False

    try:
        # 3. Construct Message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # 4. Connect and Send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False
