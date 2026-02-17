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
    Sends an email using credentials.
    Returns tuple: (success: bool, message: str)
    """
    # 1. Load config
    smtp_server = get_config("SMTP_SERVER", "smtp.gmail.com")
    try:
        smtp_port = int(get_config("SMTP_PORT", 587))
    except (ValueError, TypeError):
        smtp_port = 587
        
    sender_email = get_config("SMTP_EMAIL")
    sender_password = get_config("SMTP_PASSWORD")

    # 2. Mock Mode (No credentials)
    if not sender_email or not sender_password:
        print(f"\n[MOCK EMAIL SERVICE]")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        return False, "Mock Mode (Credentials missing)"

    server = None
    try:
        # 3. Construct Message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # 4. Connect and Send (Robust Handling)
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=15) # 15s timeout
        server.ehlo() # Identify to server
        server.starttls() # Encrypt
        server.ehlo() # Re-identify after encryption
        server.login(sender_email, sender_password)
        
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        
        return True, "Email Sent Successfully"
        
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication Failed. Check App Password."
    except smtplib.SMTPConnectError:
        return False, "Connection Failed. Check Server/Port."
    except Exception as e:
        print(f"Email Error: {e}")
        return False, str(e)
    finally:
        # 5. CRITICAL: Always close connection to prevent blocking
        if server:
            try:
                server.quit()
            except Exception:
                pass
