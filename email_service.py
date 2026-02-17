import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import streamlit as st

def get_config(key, default=None):
    """
    Helper to get config from Streamlit secrets (priority) or Environment variables.
    """
    # 1. Check Streamlit Secrets (Best for Cloud)
    if hasattr(st, "secrets") and key in st.secrets:
        return st.secrets[key]
    
    # 2. Check Environment Variables (Best for Local .env)
    return os.environ.get(key, default)

def send_email(to_email, subject, body):
    """
    Sends an email using credentials from Streamlit secrets or environment variables.
    Returns True if successful, False otherwise.
    If credentials are not set, it prints the email to the console (Mock Mode).
    """
    # 1. Load config
    smtp_server = get_config("SMTP_SERVER", "smtp.gmail.com")
    try:
        smtp_port = int(get_config("SMTP_PORT", 587))
    except (ValueError, TypeError):
        smtp_port = 587
        
    sender_email = get_config("SMTP_EMAIL")
    sender_password = get_config("SMTP_PASSWORD")

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
