import os
import streamlit as st
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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
    Sends an email using SendGrid API.
    Returns tuple: (success: bool, message: str)
    """
    # 1. Load config
    api_key = get_config("SENDGRID_API_KEY")
    from_email = get_config("FROM_EMAIL")

    # 2. Mock Mode (No credentials)
    if not api_key or not from_email:
        print(f"\n[MOCK EMAIL SERVICE - SENDGRID]")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        return False, "Mock Mode (Credentials missing)"

    try:
        # 3. Construct Message
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )
        
        # 4. Send via API
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        # Check for 2xx status code
        if 200 <= response.status_code < 300:
            return True, "Email Sent Successfully"
        else:
            return False, f"Failed with status: {response.status_code}"

    except Exception as e:
        # SendGrid specific exceptions usually contain a body
        error_msg = str(e)
        if hasattr(e, 'body'):
            error_msg += f" Details: {e.body}"
            
        print(f"SendGrid Error: {error_msg}")
        return False, error_msg
