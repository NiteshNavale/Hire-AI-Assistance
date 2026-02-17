import os
import streamlit as st
import json
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

    # Debugging: Print to console to ensure the correct email is being picked up
    if from_email:
        print(f"[Email Service] Attempting to send from: {from_email}")
    else:
        print(f"[Email Service] FROM_EMAIL is missing in configuration.")

    # 2. Mock Mode (No credentials)
    if not api_key or not from_email:
        print(f"\n[MOCK EMAIL SERVICE - SENDGRID]")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        return False, "Mock Mode (Credentials missing in .env or secrets.toml)"

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
        print(f"Full SendGrid Exception: {e}")
        
        clean_error = "Email failed to send."
        
        # Handle SendGrid specific error bodies (often bytes)
        if hasattr(e, 'body'):
            try:
                # Decode bytes to string if needed
                body_content = e.body
                if isinstance(body_content, bytes):
                    body_content = body_content.decode('utf-8')
                
                # Parse JSON
                error_json = json.loads(body_content)
                
                # Extract the specific message from SendGrid's error format
                if "errors" in error_json and isinstance(error_json["errors"], list):
                    first_error = error_json["errors"][0]
                    if "message" in first_error:
                        clean_error = first_error["message"]
                    else:
                         clean_error = str(error_json)
                else:
                    clean_error = str(body_content)
                    
            except Exception as parse_err:
                print(f"Error parsing SendGrid error response: {parse_err}")
                clean_error = str(e)
        else:
             clean_error = str(e)
        
        # --- FALLBACK LOGIC ---
        # If the error is due to unverified Sender Identity, we treat it as a "Soft Fail".
        # We print the email to console and return True so the user flow continues.
        if "Sender Identity" in clean_error or "verified" in clean_error or "403" in str(e):
            print(f"\n{'='*40}")
            print(f"[/!\\ SIMULATION MODE] SendGrid Sender Identity Invalid")
            print(f"Actual email could not be sent. Printing to console:")
            print(f"{'='*40}")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body:\n{body}")
            print(f"{'='*40}\n")
            return True, "Simulated (Sender Identity Invalid - Check Console)"

        return False, f"SendGrid Error: {clean_error}"
