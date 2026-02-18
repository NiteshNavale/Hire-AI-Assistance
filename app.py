import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import time
from datetime import datetime, timedelta
import random
import string
import uuid
import importlib
from google import genai
from google.genai import types
from dotenv import load_dotenv  # Import dotenv
import database  # Import the shared database module
import email_service # Import email service

# --- LOAD ENVIRONMENT VARIABLES ---
# This ensures it works on local machines, VPS, and hosting panels using .env files
load_dotenv()

# Note: Removed importlib.reload(database) as it was causing ImportError in some environments.
# Streamlit automatically watches for file changes in development.

# --- PREMIUM UI CONFIGURATION ---
st.set_page_config(
    page_title="HireAI | Intelligent Recruitment",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
        
        /* Base App Styling */
        .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] { 
            background-color: #ffffff !important; 
            border-right: 1px solid #e2e8f0;
        }
        
        /* Sidebar Content */
        section[data-testid="stSidebar"] .stMarkdown, 
        section[data-testid="stSidebar"] .stRadio label {
            color: #0f172a !important;
        }
        
        /* Headings */
        h1, h2, h3 { font-weight: 700 !important; color: #0f172a !important; }
        
        /* Custom Button Styling override */
        .stButton>button {
            border-radius: 8px; font-weight: 600;
        }
        
        /* Popover styling tweaks */
        div[data-testid="stPopoverBody"] {
            border-radius: 12px;
        }

        /* Hide default Streamlit chrome */
        #MainMenu {visibility: hidden;} 
        footer {visibility: hidden;} 
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- INITIALIZATION ---
database.init_db()
# Load candidates from DB. 
candidates = database.get_candidates()
# Load jobs from DB
jobs = database.get_jobs()

if 'active_user' not in st.session_state:
    st.session_state.active_user = None

# HR Auth State
if 'hr_authenticated' not in st.session_state:
    st.session_state.hr_authenticated = False
if 'hr_username' not in st.session_state:
    st.session_state.hr_username = None

# --- API CLIENT ---
def get_client():
    # Priority: 1. Streamlit Secrets (Cloud), 2. Environment Variable (VPS/Heroku/.env)
    api_key = st.secrets.get("API_KEY") if hasattr(st, "secrets") else os.environ.get("API_KEY")
    
    if not api_key:
        st.error("Missing API_KEY. Please set it in .env file or Environment Variables.")
        st.stop()
    return genai.Client(api_key=api_key)

client = get_client()

# --- HELPERS ---
def generate_key():
    return f"{''.join(random.choices(string.ascii_uppercase, k=4))}-{''.join(random.choices(string.digits, k=4))}"

def generate_meeting_link():
    # Using Jitsi Meet ensures links are valid and working immediately without OAuth
    # Format: https://meet.jit.si/HireAI-{random_uuid}
    unique_id = uuid.uuid4().hex[:12]
    return f"https://meet.jit.si/HireAI-Interview-{unique_id}"

def set_generated_link_callback(key):
    """Callback to update session state with a new meeting link before render."""
    st.session_state[key] = generate_meeting_link()

def check_email_config():
    """Checks if SendGrid credentials are present."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    if hasattr(st, "secrets") and "SENDGRID_API_KEY" in st.secrets:
        api_key = st.secrets["SENDGRID_API_KEY"]
    return api_key is not None

def get_test_duration():
    """Returns test duration in minutes from config, default 20."""
    try:
        val = os.environ.get("APTITUDE_TEST_DURATION_MINUTES")
        if hasattr(st, "secrets") and "APTITUDE_TEST_DURATION_MINUTES" in st.secrets:
            val = st.secrets["APTITUDE_TEST_DURATION_MINUTES"]
        return int(val) if val else 20
    except:
        return 20

def save_uploaded_doc(uploaded_file, candidate_id, doc_type):
    """Saves uploaded documents to a local uploads folder."""
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    file_ext = uploaded_file.name.split('.')[-1]
    file_name = f"{candidate_id}_{doc_type}.{file_ext}"
    file_path = os.path.join("uploads", file_name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def resend_candidate_email(c):
    """
    Reconstructs and resends the last relevant email based on candidate status.
    Returns: (success: bool, msg: str)
    """
    subject = ""
    body = ""
    status = c.get('status', 'Screening')
    
    if status == 'Screening':
        subject = f"Application Received: {c['role']}"
        body = f"""
Dear {c['name']},

Thank you for applying for the position of {c['role']} at HireAI.

Your application has been received and screened by our AI system.
To track your status or take assessments, please login to the Candidate Portal.

Your Access Key: {c.get('access_key', 'N/A')}

Best regards,
HireAI Recruiting Team
"""
    elif status == 'Aptitude Scheduled':
        subject = "Aptitude Assessment Scheduled - HireAI"
        body = f"""
Dear {c['name']},

You have been shortlisted for the Aptitude Assessment for the {c['role']} position.

Date: {c.get('aptitudeDate', 'TBD')}
Time: {c.get('aptitudeTime', 'TBD')}

Please login to the Candidate Portal using your Access Key: {c.get('access_key', 'N/A')}

Best regards,
HireAI Recruiting Team
"""
    elif status == 'Aptitude Completed':
        score = c.get('aptitude_score', 0)
        if score >= 50:
            subject = "Aptitude Test Passed - HireAI"
            body = f"Dear {c['name']},\n\nCongratulations! You have passed the aptitude assessment with a score of {score}%.\n\nOur team will review your profile and schedule the final interview shortly.\n\nBest regards,\nHireAI Recruiting Team"
        else:
            subject = "Application Update - HireAI"
            body = f"Dear {c['name']},\n\nThank you for completing the aptitude assessment.\n\nUnfortunately, your score of {score}% did not meet the required threshold for this role.\n\nWe encourage you to apply again after 6 months.\n\nBest regards,\nHireAI Recruiting Team"
    
    elif status == 'Interview Scheduled':
        round_num = c.get('interview_round', 1)
        round_name = "First Round" if round_num == 1 else "Second Round"
        subject = f"{round_name} Interview - HireAI"
        body = f"""
Dear {c['name']},

We are pleased to invite you to the {round_name} Interview for the {c['role']} position.

Date: {c.get('round2Date', 'TBD')}
Time: {c.get('round2Time', 'TBD')}
Meeting Link: {c.get('round2Link', '#')}

Please join the link at the scheduled time.

Best regards,
HireAI Recruiting Team
"""
    elif status == 'Selected':
        subject = "Congratulations! You have been Selected - HireAI"
        body = f"""
Dear {c['name']},

Congratulations! We are pleased to inform you that you have cleared the final interview round for the position of {c['role']}.

We are currently preparing your formal offer. A confirmation letter will be shared with you shortly.

Action Required:
Please login to the candidate portal and submit the following documents for verification:
1. Valid Government ID Proof (Passport/Aadhaar/Driver's License)
2. Current Address Proof

Once verified, we will issue your formal Joining Letter.

Best regards,
HireAI HR Team
"""
    elif status == 'Joining Scheduled':
        subject = "Official Joining Letter - HireAI"
        body = f"""
Dear {c['name']},

We are delighted to formally offer you the position of {c['role']} at HireAI!

We have verified your documents and everything looks in order.

**Joining Date:** {c.get('joining_date', 'To Be Discussed')}

Please arrive at our office by 9:30 AM on your joining date for orientation.
We are excited to have you onboard.

Welcome to the family!

Best regards,
HireAI HR Team
"""
    elif status == 'Rejected':
        round_num = c.get('interview_round', 1)
        round_name = "First Round" if round_num == 1 else "Second Round"
        subject = "Update on your Application - HireAI"
        body = f"""
Dear {c['name']},

Thank you for giving us the opportunity to get to know you during the {round_name} of interviews for the {c['role']} position.

We appreciate the time and effort you put into the process. However, after careful consideration, we have decided to move forward with other candidates who more closely match our current requirements for this specific role.

We encourage you to apply again after 6 months as our needs and roles continue to evolve.

We wish you the very best in your future endeavors.

Best regards,
HireAI Recruiting Team
"""
    else:
        return False, "No email template found for current status."

    # Send
    email_sent, email_msg = email_service.send_email(c['email'], subject, body)
    
    # Update DB with new email status
    c['email_status'] = "Sent" if email_sent else "Failed"
    c['email_error'] = email_msg if not email_sent else None
    database.save_candidate(c)
    
    return email_sent, email_msg

# --- AI LOGIC ---
def verify_candidate_identity(resume_text, input_name):
    """
    Verifies if the name entered by the user matches the name found in the resume.
    """
    prompt = f"""
    You are an identity verification system.
    
    1. Analyze the top section of the provided RESUME TEXT to extract the candidate's name.
    2. Compare the extracted name with the USER INPUT NAME.
    3. Determine if they represent the same person.
       - Allow for case-insensitive matches.
       - Allow for minor variations (e.g., "John Doe" matches "John A. Doe").
       - Allow for common nicknames if obvious (e.g. "Dave" for "David").
       - If the names are completely different, return false.
    
    USER INPUT NAME: "{input_name}"
    
    RESUME TEXT (First 2000 chars):
    "{resume_text[:2000]}"
    
    Return a JSON object:
    {{
        "match": boolean,
        "name_on_resume": "string",
        "reason": "string"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema={
                    'type': 'OBJECT',
                    'properties': {
                        'match': {'type': 'BOOLEAN'},
                        'name_on_resume': {'type': 'STRING'},
                        'reason': {'type': 'STRING'}
                    },
                    'required': ['match', 'name_on_resume', 'reason']
                }
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Identity check failed: {e}")
        # Fail safe: if AI fails, we might want to warn or just pass. 
        # Here we return False to be strict, or True to be lenient. 
        # Let's return error so user knows.
        raise e

def screen_resume_ai(text, role_title, job_description, skills_required, min_experience):
    """
    Screens resume with temperature=0.0 and a fixed seed for deterministic results.
    """
    
    seed_str = f"{text[:100]}{job_description[:100]}{len(text)}"
    seed = sum(ord(char) for char in seed_str)

    prompt = f"""
    You are a strict technical recruiter. 
    Evaluate the following Resume against the Job Requirements.
    
    JOB TITLE: {role_title}
    
    MANDATORY REQUIREMENTS:
    1. Minimum Experience Required: {min_experience} years.
    2. Mandatory Skills: {skills_required}
    
    JOB DESCRIPTION:
    {job_description}
    
    CANDIDATE RESUME:
    {text}
    
    EVALUATION INSTRUCTIONS:
    1. Extract the total years of relevant experience from the resume as an integer.
    2. Check if the candidate matches the Minimum Experience. If they have less than {min_experience} years, the Score MUST be below 40.
    3. Check if the candidate has the Mandatory Skills ({skills_required}). If they miss key skills, deduct points significantly.
    4. Score from 0-100 based on strict evidence in the text.
    5. Provide a summary explaining the score, specifically mentioning if they met the experience and skill requirements.
    """
    
    max_retries = 3
    base_delay = 20 

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0, 
                    seed=seed,       
                    response_mime_type='application/json',
                    response_schema={
                        'type': 'OBJECT',
                        'properties': {
                            'overallScore': {'type': 'INTEGER'},
                            'years_experience': {'type': 'INTEGER', 'description': 'Total relevant years of experience extracted from resume'},
                            'summary': {'type': 'STRING'},
                            'technicalMatch': {'type': 'INTEGER'}
                        },
                        'required': ['overallScore', 'years_experience', 'summary', 'technicalMatch']
                    }
                )
            )
            return json.loads(response.text)
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (attempt + 1)
                    print(f"Quota exceeded (Attempt {attempt+1}/{max_retries}). Retrying in {wait_time}s...")
                    st.toast(f"High AI Traffic. Retrying in {wait_time}s...", icon="⏳")
                    time.sleep(wait_time)
                    continue
            raise e

def generate_aptitude_questions(role):
    prompt = f"""
    Generate a 20-question multiple-choice aptitude test for a {role} candidate.
    
    Structure the questions into these 4 sections (5 questions each):
    1. Logical Reasoning (IQ & Patterns)
    2. Quantitative Aptitude (Math)
    3. Verbal Ability (Language)
    4. Domain Knowledge (specific to {role})

    Format the output as a JSON array of objects with keys: 
    - 'id' (integer)
    - 'question' (string)
    - 'options' (list of 4 strings)
    - 'correct_index' (integer 0-3)
    - 'category' (string)
    """
    
    max_retries = 3
    base_delay = 20

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema={
                        'type': 'ARRAY',
                        'items': {
                            'type': 'OBJECT',
                            'properties': {
                                'id': {'type': 'INTEGER'},
                                'question': {'type': 'STRING'},
                                'options': {'type': 'ARRAY', 'items': {'type': 'STRING'}},
                                'correct_index': {'type': 'INTEGER'},
                                'category': {'type': 'STRING'}
                            },
                            'required': ['id', 'question', 'options', 'correct_index', 'category']
                        }
                    }
                )
            )
            return json.loads(response.text)
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (attempt + 1)
                    print(f"Quota exceeded (Attempt {attempt+1}/{max_retries}). Retrying in {wait_time}s...")
                    st.toast(f"High AI Traffic. Retrying in {wait_time}s...", icon="⏳")
                    time.sleep(wait_time)
                    continue
            raise e

# --- UI COMPONENTS ---
def render_candidate_details(c):
    """
    Renders a detailed view of the candidate inside a Popover/Expander.
    """
    st.markdown(f"### {c['name']}")
    st.caption(f"Role: {c['role']} | ID: {c['id'][:8]}")
    
    # 1. Scores & Key Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Score", f"{c.get('score', 0)}/100")
    col2.metric("Tech Match", f"{c.get('technical', 0)}/100")
    col3.metric("Experience", f"{c.get('years_experience', 0)} Years")
    
    st.divider()
    
    # 2. AI Summary
    st.markdown("**🤖 AI Resume Analysis:**")
    st.info(c.get('summary', 'No summary available.'))
    
    # 3. Assessment Details
    if c.get('aptitude_score') is not None:
        st.markdown("**📝 Aptitude Results:**")
        score = c.get('aptitude_score', 0)
        color = "green" if score >= 50 else "red"
        st.markdown(f"**Score:** :{color}[{score}%]")
        if c.get('aptitudeDate'):
             st.caption(f"Scheduled: {c['aptitudeDate']} {c['aptitudeTime']}")
    
    # 4. Interview Details
    if c.get('round2Date'):
        st.markdown(f"**🤝 Interview (Round {c.get('interview_round', 1)}):**")
        st.markdown(f"- **Date:** {c['round2Date']}")
        st.markdown(f"- **Time:** {c['round2Time']}")
        st.markdown(f"- **Link:** [Join Meeting]({c.get('round2Link', '#')})")
        
        # Show Recruiter Owner
        recruiter = c.get('recruiter', 'Unassigned')
        st.markdown(f"**👤 Interviewer:** {recruiter}")
    
    st.divider()
    
    # 5. Admin Info
    st.markdown("**🔐 Admin Details:**")
    st.text_input("Access Key (Candidate Login)", value=c.get('access_key', 'N/A'), disabled=True, key=f"ak_{c['id']}")
    st.text_input("Email", value=c['email'], disabled=True, key=f"em_{c['id']}")
    
    email_st = c.get('email_status', 'Unknown')
    st.markdown(f"**Last Email Status:** {email_st}")
    if c.get('email_error'):
        st.error(f"Error: {c['email_error']}")

# --- VIEWS ---
def sidebar_nav():
    with st.sidebar:
        col_logo, col_title = st.columns([1, 4])
        with col_logo:
             st.markdown("### 🎯")
        with col_title:
             st.markdown("### HireAI")
        
        choice = st.radio("Navigation", 
                         ["Candidate Portal", "Candidate Login", "HR Dashboard"],
                         key="nav_radio")
        
        st.divider()
        st.caption("SYSTEM STATUS")
        
        is_email_configured = check_email_config()
        if is_email_configured:
            st.markdown("📧 **Email Service**: :green[Active] (SendGrid)")
        else:
            st.markdown("📧 **Email Service**: :red[Mock Mode]")
            st.caption("Set SENDGRID_API_KEY in .env")

        if choice == "HR Dashboard" and st.session_state.hr_authenticated:
            upcoming_meetings = []
            now = datetime.now()
            for c in candidates:
                if c.get('round2Date') and c.get('round2Time'):
                    try:
                        meeting_dt = datetime.strptime(f"{c['round2Date']} {c['round2Time']}", "%Y-%m-%d %H:%M")
                        diff = meeting_dt - now
                        if timedelta(minutes=0) < diff <= timedelta(minutes=5):
                            upcoming_meetings.append(c['name'])
                    except:
                        pass
            
            if upcoming_meetings:
                 st.error(f"🔔 Meeting Starting: {', '.join(upcoming_meetings)}")

        if st.session_state.hr_authenticated:
            st.markdown(f"👤 **{st.session_state.hr_username}**")
            if st.button("Logout HR", key="logout_hr", type="secondary"):
                st.session_state.hr_authenticated = False
                st.session_state.hr_username = None
                st.rerun()

        if st.session_state.active_user:
            if st.button("Logout Candidate", type="primary"):
                st.session_state.active_user = None
                if 'aptitude_questions' in st.session_state:
                    del st.session_state.aptitude_questions
                st.rerun()
                
    return choice

def view_candidate_portal():
    st.title("Join HireAI Pipeline")
    st.markdown("Submit your profile for instant AI screening.")
    
    current_jobs = database.get_jobs()
    
    if not current_jobs:
        st.warning("No positions are currently open. Please check back later.")
        return

    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader("Application Form")
            
            if 'cp_name' not in st.session_state: st.session_state.cp_name = ""
            if 'cp_email' not in st.session_state: st.session_state.cp_email = ""
            if 'cp_uploader_key' not in st.session_state: st.session_state.cp_uploader_key = 0

            name = st.text_input("Full Name", placeholder="John Doe", key="cp_name")
            email = st.text_input("Email Address", placeholder="john@example.com", key="cp_email")
            
            job_options = {j['title']: j for j in current_jobs}
            selected_role_title = st.selectbox("Apply for Role", list(job_options.keys()))
            
            selected_job = job_options[selected_role_title]
            
            with st.expander("View Job Requirements"):
                st.markdown(f"**Required Experience:** {selected_job.get('min_experience', 0)}+ Years")
                if selected_job.get('skills'):
                    st.markdown(f"**Must-Have Skills:**")
                    for s in selected_job['skills'].split(','):
                        st.markdown(f"- {s}")
                st.markdown("---")
                st.write(selected_job['description'])

            resume = st.file_uploader(
                "Upload Resume (TXT/PDF)", 
                type=['txt', 'pdf'],
                key=f"resume_uploader_{st.session_state.cp_uploader_key}"
            )
            
            if st.button("Submit Application", type="primary"):
                if name and email and resume:
                    with st.spinner("AI is rigorously analyzing your profile against specific job requirements..."):
                        try:
                            resume_text = resume.read().decode("utf-8", errors="ignore")
                            
                            # --- 1. IDENTITY VERIFICATION ---
                            st.caption("Verifying identity...")
                            identity_check = verify_candidate_identity(resume_text, name)
                            
                            if not identity_check['match']:
                                st.error(f"Identity Mismatch Error: {identity_check.get('reason', 'Name in resume does not match entered name.')}")
                                st.warning(f"Resume Name Detected: {identity_check.get('name_on_resume', 'Unknown')}")
                                return # STOP EXECUTION HERE
                            
                            # --- 2. RESUME SCREENING ---
                            st.caption("Identity Verified. Analyzing qualifications...")
                            analysis = screen_resume_ai(
                                resume_text, 
                                selected_role_title, 
                                selected_job['description'],
                                selected_job.get('skills', ''),
                                selected_job.get('min_experience', 0)
                            )
                            
                            access_key = generate_key()
                            c_id = str(uuid.uuid4())
                            
                            # Initial Object
                            new_candidate = {
                                "id": c_id,
                                "name": name,
                                "email": email,
                                "role": selected_role_title,
                                "status": "Screening",
                                "score": analysis['overallScore'],
                                "technical": analysis['technicalMatch'],
                                "years_experience": analysis.get('years_experience', 0),
                                "summary": analysis['summary'],
                                "access_key": access_key,
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "aptitude_score": None,
                                "aptitude_details": None,
                                "aptitudeDate": None,
                                "aptitudeTime": None,
                                "round2Date": None,
                                "round2Time": None,
                                "round2Link": None,
                                "interview_round": 1,
                                "email_status": "Pending", 
                                "email_error": None,
                                "archived": False,
                                "recruiter": None, # Initially unassigned
                                "documents_uploaded": False,
                                "documents": {}
                            }
                            
                            database.save_candidate(new_candidate) # Save first to use helper
                            email_sent, email_msg = resend_candidate_email(new_candidate)
                            
                            # Reload to get updated status
                            new_candidate['email_status'] = "Sent" if email_sent else "Failed"
                            new_candidate['email_error'] = email_msg if not email_sent else None
                            
                            st.balloons()
                            if email_sent:
                                if "Simulated" in email_msg:
                                    st.warning(f"Profile Screened! {email_msg} - Credentials logged to Console")
                                else:
                                    st.success(f"Profile Screened! Email sent to {email}")
                            else:
                                st.error(f"Profile Screened, but email failed: {email_msg}")
                            
                            st.session_state.last_submitted = new_candidate
                            st.session_state.submission_time = time.time()
                            
                            del st.session_state.cp_name
                            del st.session_state.cp_email
                            st.session_state.cp_uploader_key += 1
                            
                            st.rerun()

                        except Exception as e:
                            st.error(f"Error processing application: {e}")
                else:
                    st.warning("Please fill all fields.")

    with col2:
        if 'last_submitted' in st.session_state:
            if 'submission_time' not in st.session_state:
                del st.session_state.last_submitted
                st.rerun()
                return

            elapsed = time.time() - st.session_state.submission_time
            if elapsed > 60:
                del st.session_state.last_submitted
                if 'submission_time' in st.session_state:
                    del st.session_state.submission_time
                st.rerun()
                return

            c = st.session_state.last_submitted
            remaining = int(60 - elapsed)
            
            with st.container(border=True):
                st.info("Please save your credentials")
                st.markdown(f"## {c['access_key']}")
                st.caption("Use this Access Key to login to the interview portal.")
                st.markdown(f"**Role:** {c['role']}")
                st.markdown(f"**Experience:** {c.get('years_experience', 0)} Years")
                st.markdown(f"**AI Score:** {c['score']}/100")
                
                st.divider()
                st.error(f"This screen will close in {remaining} seconds.")
                
                if st.button("✅ I have copied the secret code", type="primary"):
                     del st.session_state.last_submitted
                     if 'submission_time' in st.session_state:
                        del st.session_state.submission_time
                     st.rerun()
            
            time.sleep(1)
            st.rerun()

def view_hr_dashboard():
    if not st.session_state.hr_authenticated:
        st.title("Recruiter Login")
        col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
        with col_c2:
            with st.container(border=True):
                st.markdown("### 🔐 Secure Access")
                with st.form("hr_login_form"):
                    username = st.text_input("Username", placeholder="admin")
                    password = st.text_input("Password", type="password", placeholder="••••••")
                    
                    if st.form_submit_button("Login to Dashboard", type="primary"):
                        if database.login_user(username, password):
                            st.session_state.hr_authenticated = True
                            st.session_state.hr_username = username
                            st.toast(f"Welcome back, {username}!", icon="👋")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                st.caption("Default Admin: `admin` / `admin123`")
        return

    st.title(f"Recruiter Command Center")
    st.caption(f"Logged in as: {st.session_state.hr_username}")
    
    current_hr = st.session_state.hr_username
    is_super_admin = current_hr == "admin"
    active_candidates = [c for c in candidates if not c.get('archived')]
    archived_candidates = [c for c in candidates if c.get('archived')]
    
    tab_pipeline, tab_jobs, tab_team, tab_archived = st.tabs([
        f"Active Pipeline ({len(active_candidates)})", 
        "Manage Jobs / JDs",
        "Manage Team",
        f"Archived ({len(archived_candidates)})"
    ])
    
    with tab_pipeline:
        df_active = pd.DataFrame(active_candidates)
        m1, m2, m3 = st.columns(3)
        with m1:
            with st.container(border=True):
                st.metric("Total Candidates", len(active_candidates))
        with m2:
            with st.container(border=True):
                if not df_active.empty and 'aptitude_score' in df_active.columns:
                    aptitude_takers = df_active[df_active['aptitude_score'].notnull()]
                    avg_apt = int(aptitude_takers['aptitude_score'].mean()) if not aptitude_takers.empty else 0
                else:
                    avg_apt = 0
                st.metric("Avg Aptitude Score", f"{avg_apt}%")
        with m3:
            with st.container(border=True):
                upcoming = "None"
                for c in active_candidates:
                        if c.get('round2Date'): 
                            upcoming = f"{c['round2Date']} {c['round2Time']}"
                st.metric("Next Interview", upcoming)
        
        st.divider()

        if not active_candidates:
            st.info("No active candidates in the pipeline.")
        else:
            stage_screening = [c for c in active_candidates if c['status'] == 'Screening']
            stage_aptitude = [c for c in active_candidates if c['status'] in ['Aptitude Scheduled', 'Aptitude Completed']]
            stage_interview = [c for c in active_candidates if c['status'] == 'Interview Scheduled']
            stage_selected = [c for c in active_candidates if c['status'] in ['Selected', 'Joining Scheduled']]
            
            subtab_1, subtab_2, subtab_3, subtab_4 = st.tabs([
                f"📋 Screening ({len(stage_screening)})",
                f"📝 Aptitude ({len(stage_aptitude)})",
                f"🤝 Interviews ({len(stage_interview)})",
                f"🎉 Offers & Joining ({len(stage_selected)})"
            ])
            
            # --- SCREENING TAB ---
            with subtab_1:
                if not stage_screening:
                    st.info("No candidates pending screening.")
                else:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 2])
                        c1.markdown("**Candidate**")
                        c2.markdown("**AI Match**")
                        c3.markdown("**Action**")
                    
                    for c in stage_screening:
                        with st.container(border=True):
                            c1, c2, c3 = st.columns([3, 2, 2])
                            with c1:
                                st.markdown(f"**{c['name']}**")
                                st.caption(f"{c['role']}")
                                exp_years = c.get('years_experience', 0)
                                st.caption(f"📅 Exp: {exp_years} Years")
                                
                                email_status = c.get('email_status', 'Unknown')
                                color = "green" if email_status == "Sent" else "red" if email_status == "Failed" else "grey"
                                st.markdown(f"📧 Email: :{color}[{email_status}]")

                                # Check Ownership
                                assigned = c.get('recruiter')
                                is_owner = not assigned or assigned == current_hr or is_super_admin
                                
                                if is_owner:
                                    if st.button("🔄 Resend Email", key=f"rs_{c['id']}"):
                                        sent, msg = resend_candidate_email(c)
                                        if sent: st.toast(f"Email resent to {c['email']}")
                                        else: st.error(f"Failed: {msg}")
                                        time.sleep(1)
                                        st.rerun()
                                else:
                                    st.caption(f"🔒 Locked by {assigned}")

                            with c2:
                                st.markdown(f"**{c.get('score', 0)}/100**")
                                
                                # NEW: View Profile Popover (Open to all)
                                with st.popover("📄 View Profile"):
                                    render_candidate_details(c)
                                    
                            with c3:
                                # Check Ownership for Actions
                                assigned = c.get('recruiter')
                                is_owner = not assigned or assigned == current_hr or is_super_admin

                                if not is_owner:
                                    st.warning(f"Owned by {assigned}")
                                else:
                                    exp_years = c.get('years_experience', 0)
                                    if exp_years > 2:
                                        st.success("Senior Candidate")
                                        with st.popover("Schedule Interview"):
                                            st.markdown("### 📅 First Round Interview")
                                            r2d = st.date_input("Interview Date", key=f"r2d_s_{c['id']}")
                                            r2t = st.time_input("Start Time", key=f"r2t_s_{c['id']}")
                                            st.divider()
                                            
                                            col_l1, col_l2 = st.columns([3, 1.5])
                                            with col_l1:
                                                meet_link = st.text_input("Meeting Link", key=f"lnk_s_{c['id']}", placeholder="https://meet.jit.si/...")
                                            with col_l2:
                                                st.button("⚡ Generate", key=f"btn_gen_s_{c['id']}", on_click=set_generated_link_callback, args=(f"lnk_s_{c['id']}",))
                                            
                                            if st.button("Confirm Interview", key=f"btn_int_s_{c['id']}", type="primary"):
                                                final_link = meet_link if meet_link else generate_meeting_link()
                                                
                                                c['round2Date'] = r2d.strftime("%Y-%m-%d")
                                                c['round2Time'] = r2t.strftime("%H:%M")
                                                c['round2Link'] = final_link
                                                c['status'] = 'Interview Scheduled'
                                                c['interview_round'] = 1
                                                c['recruiter'] = current_hr # CLAIM OWNERSHIP
                                                database.save_candidate(c)
                                                
                                                # Send Email
                                                resend_candidate_email(c)
                                                st.toast(f"Interview Scheduled. You are now the assigned recruiter.")
                                                st.rerun()
                                    else:
                                        with st.popover("Schedule Exam"):
                                            st.info("Junior: Aptitude Mandatory")
                                            d = st.date_input("Date", key=f"d_{c['id']}")
                                            t = st.time_input("Time", key=f"t_{c['id']}")
                                            if st.button("Confirm Schedule", key=f"btn_{c['id']}", type="primary"):
                                                c['aptitudeDate'] = d.strftime("%Y-%m-%d")
                                                c['aptitudeTime'] = t.strftime("%H:%M")
                                                c['status'] = 'Aptitude Scheduled'
                                                # Aptitude doesn't strictly lock ownership yet, but scheduling interview will
                                                database.save_candidate(c)
                                                
                                                # Send Email
                                                resend_candidate_email(c)
                                                st.toast(f"Scheduled for {c['name']}")
                                                st.rerun()
                                    
                                    if st.button("Archive", key=f"arc_{c['id']}"):
                                        c['archived'] = True
                                        database.save_candidate(c)
                                        st.rerun()
            
            # --- APTITUDE TAB ---
            with subtab_2:
                if not stage_aptitude:
                    st.info("No candidates in aptitude stage.")
                else:
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([2.5, 1.5, 1, 2])
                        c1.markdown("**Candidate**")
                        c2.markdown("**Status**")
                        c3.markdown("**Score**")
                        c4.markdown("**Action**")
                    
                    for c in stage_aptitude:
                        with st.container(border=True):
                            c1, c2, c3, c4 = st.columns([2.5, 1.5, 1, 2])
                            with c1:
                                st.markdown(f"**{c['name']}**")
                                st.caption(c['role'])
                                
                                email_status = c.get('email_status', 'Unknown')
                                color = "green" if email_status == "Sent" else "red" if email_status == "Failed" else "grey"
                                st.markdown(f"📧 Email: :{color}[{email_status}]")
                                
                                assigned = c.get('recruiter')
                                is_owner = not assigned or assigned == current_hr or is_super_admin

                                if is_owner:
                                    if st.button("🔄 Resend Email", key=f"rs_apt_{c['id']}"):
                                        sent, msg = resend_candidate_email(c)
                                        if sent: st.toast(f"Email resent to {c['email']}")
                                        else: st.error(f"Failed: {msg}")
                                        time.sleep(1)
                                        st.rerun()
                                else:
                                    st.caption(f"🔒 Locked by {assigned}")

                            with c2:
                                if c['status'] == 'Aptitude Scheduled':
                                    st.markdown(":orange[Scheduled]")
                                    st.caption(f"{c.get('aptitudeDate')} {c.get('aptitudeTime')}")
                                else:
                                    st.markdown(":green[Completed]")
                            with c3:
                                if c.get('aptitude_score') is not None:
                                    sc = c['aptitude_score']
                                    res = "PASS" if sc >= 50 else "FAIL"
                                    clr = "green" if sc >= 50 else "red"
                                    st.markdown(f":{clr}[{sc}%]")
                                else:
                                    st.markdown("--")
                            with c4:
                                # View Profile
                                with st.popover("📄 View Profile"):
                                    render_candidate_details(c)
                                
                                # Ownership Check
                                assigned = c.get('recruiter')
                                is_owner = not assigned or assigned == current_hr or is_super_admin

                                if not is_owner:
                                    st.warning(f"Owned by {assigned}")
                                else:
                                    if c['status'] == 'Aptitude Completed':
                                        if (c.get('aptitude_score') or 0) >= 50:
                                            with st.popover("Schedule Round 1"):
                                                st.markdown("### 📅 Setup First Round")
                                                r2d = st.date_input("Interview Date", key=f"r2d_{c['id']}")
                                                r2t = st.time_input("Start Time", key=f"r2t_{c['id']}")
                                                st.divider()
                                                
                                                col_l1, col_l2 = st.columns([3, 1.5])
                                                with col_l1:
                                                    meet_link = st.text_input("Meeting Link", key=f"lnk_a_{c['id']}", placeholder="https://meet.jit.si/...")
                                                with col_l2:
                                                    st.button("⚡ Generate", key=f"btn_gen_a_{c['id']}", on_click=set_generated_link_callback, args=(f"lnk_a_{c['id']}",))

                                                if st.button("Send Invite", key=f"inv_{c['id']}", type="primary"):
                                                    final_link = meet_link if meet_link else generate_meeting_link()
                                                    
                                                    c['round2Date'] = r2d.strftime("%Y-%m-%d")
                                                    c['round2Time'] = r2t.strftime("%H:%M")
                                                    c['round2Link'] = final_link
                                                    c['status'] = 'Interview Scheduled'
                                                    c['interview_round'] = 1
                                                    c['recruiter'] = current_hr # CLAIM OWNERSHIP
                                                    database.save_candidate(c)
                                                    
                                                    # Send Email
                                                    resend_candidate_email(c)
                                                    st.toast(f"Invite Sent! Assigned to you.", icon="📨")
                                                    time.sleep(1)
                                                    st.rerun()
                                        else:
                                            st.error("Low Score")
                                    else:
                                        st.caption("Waiting for exam...")
                                    
                                    if st.button("Archive", key=f"arc_{c['id']}_apt"):
                                        c['archived'] = True
                                        database.save_candidate(c)
                                        st.rerun()

            # --- INTERVIEW TAB ---
            with subtab_3:
                if not stage_interview:
                    st.info("No candidates scheduled for interviews.")
                else:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 3, 2])
                        c1.markdown("**Candidate**")
                        c2.markdown("**Meeting Details**")
                        c3.markdown("**Action**")
                    
                    for c in stage_interview:
                         with st.container(border=True):
                            c1, c2, c3 = st.columns([3, 3, 2])
                            with c1:
                                st.markdown(f"**{c['name']}**")
                                st.caption(c['role'])
                                
                                # Ownership Check
                                assigned = c.get('recruiter')
                                is_owner = not assigned or assigned == current_hr or is_super_admin
                                
                                email_status = c.get('email_status', 'Unknown')
                                color = "green" if email_status == "Sent" else "red" if email_status == "Failed" else "grey"
                                st.markdown(f"📧 Email: :{color}[{email_status}]")
                                
                                if is_owner:
                                    if st.button("🔄 Resend Email", key=f"rs_int_{c['id']}"):
                                        sent, msg = resend_candidate_email(c)
                                        if sent: st.toast(f"Email resent to {c['email']}")
                                        else: st.error(f"Failed: {msg}")
                                        time.sleep(1)
                                        st.rerun()
                                else:
                                    st.caption(f"🔒 Locked by {assigned}")

                            with c2:
                                round_num = c.get('interview_round', 1)
                                st.markdown(f"📌 **Round {round_num}**")
                                st.markdown(f"📅 **{c['round2Date']}**")
                                st.markdown(f"⏰ **{c['round2Time']}**")
                                st.caption(f"🔗 {c['round2Link']}")
                                
                                # Display Recruiter Badge
                                recruiter_display = c.get('recruiter', 'Unassigned')
                                if recruiter_display == current_hr:
                                    st.markdown(f"**👤 Interviewer:** :green[{recruiter_display} (You)]")
                                else:
                                    st.markdown(f"**👤 Interviewer:** :orange[{recruiter_display}]")

                            with c3:
                                st.link_button("Join Meeting", c['round2Link'])
                                
                                # View Profile
                                with st.popover("📄 View Profile"):
                                    render_candidate_details(c)
                                
                                # SUPER ADMIN CONTROLS
                                if is_super_admin:
                                    with st.popover("⚡ Admin Controls"):
                                        st.markdown("### Super Admin Override")
                                        
                                        # 1. Reassign Recruiter
                                        all_users = [u['username'] for u in database.get_users()]
                                        current_idx = 0
                                        if assigned in all_users:
                                            current_idx = all_users.index(assigned)
                                            
                                        new_owner = st.selectbox("Assign Interviewer", all_users, index=current_idx, key=f"own_{c['id']}")
                                        if st.button("Reassign Ownership", key=f"btn_own_{c['id']}"):
                                            c['recruiter'] = new_owner
                                            database.save_candidate(c)
                                            st.toast(f"Reassigned to {new_owner}")
                                            st.rerun()
                                        
                                        st.divider()
                                        
                                        # 2. Force Reschedule / Update Link
                                        st.markdown("**Force Reschedule / Update Link**")
                                        admin_date = st.date_input("Date", value=datetime.strptime(c['round2Date'], "%Y-%m-%d"), key=f"ad_d_{c['id']}")
                                        admin_time = st.time_input("Time", value=datetime.strptime(c['round2Time'], "%H:%M"), key=f"ad_t_{c['id']}")
                                        
                                        col_l1, col_l2 = st.columns([3, 1.5])
                                        with col_l1:
                                            admin_link = st.text_input("Meeting Link", value=c.get('round2Link', ''), key=f"ad_l_{c['id']}")
                                        with col_l2:
                                            st.button(
                                                "⚡ Generate", 
                                                key=f"gen_{c['id']}", 
                                                help="Generate new video meeting link",
                                                on_click=set_generated_link_callback,
                                                args=(f"ad_l_{c['id']}",)
                                            )

                                        if st.button("Update & Notify Candidate", type="primary", key=f"ad_upd_{c['id']}"):
                                            c['round2Date'] = admin_date.strftime("%Y-%m-%d")
                                            c['round2Time'] = admin_time.strftime("%H:%M")
                                            # Use the value from the text input state if available
                                            c['round2Link'] = st.session_state.get(f"ad_l_{c['id']}", c.get('round2Link', ''))
                                            database.save_candidate(c)
                                            
                                            # Send Email
                                            resend_candidate_email(c)
                                            st.toast("Updated & Email Sent!")
                                            st.rerun()

                                # Actions restricted to owner (or admin who is now also an owner effectively)
                                assigned = c.get('recruiter')
                                is_owner = not assigned or assigned == current_hr or is_super_admin

                                if not is_owner:
                                    st.error(f"Locked by {assigned}")
                                else:
                                    current_round = c.get('interview_round', 1)
                                    if current_round == 1:
                                        with st.popover("Schedule Round 2"):
                                            st.markdown("### 📅 Setup Round 2")
                                            r3d = st.date_input("Date", key=f"r3d_{c['id']}")
                                            r3t = st.time_input("Time", key=f"r3t_{c['id']}")
                                            
                                            st.divider()
                                            
                                            col_l1, col_l2 = st.columns([3, 1.5])
                                            with col_l1:
                                                meet_link = st.text_input("Meeting Link", key=f"lnk_r2_{c['id']}", placeholder="https://meet.jit.si/...")
                                            with col_l2:
                                                st.button("⚡ Generate", key=f"btn_gen_r2_{c['id']}", on_click=set_generated_link_callback, args=(f"lnk_r2_{c['id']}",))
                                            
                                            if st.button("Confirm Round 2", key=f"btn_r3_{c['id']}", type="primary"):
                                                # Use input link if provided, otherwise generate random
                                                new_link = meet_link if meet_link else generate_meeting_link()
                                                
                                                c['round2Date'] = r3d.strftime("%Y-%m-%d")
                                                c['round2Time'] = r3t.strftime("%H:%M")
                                                c['round2Link'] = new_link
                                                c['interview_round'] = 2
                                                # Only set recruiter if not already set, or if admin is taking over normal flow
                                                if not c.get('recruiter'):
                                                    c['recruiter'] = current_hr 
                                                database.save_candidate(c)
                                                
                                                # Send Email
                                                resend_candidate_email(c)
                                                st.toast(f"Round 2 Scheduled!")
                                                time.sleep(1)
                                                st.rerun()
                                    
                                    # --- Selection Action for Round 2 ---
                                    if current_round == 2:
                                        st.markdown("**Selection Decision**")
                                        if st.button("✅ Select Candidate", key=f"sel_{c['id']}", type="primary"):
                                            c['status'] = 'Selected'
                                            database.save_candidate(c)
                                            
                                            # Send Selection Email (Request Docs)
                                            resend_candidate_email(c)
                                            st.balloons()
                                            st.toast(f"Candidate Selected! Document Request Sent.")
                                            time.sleep(2)
                                            st.rerun()

                                    st.divider()
                                    # --- Rejection Action (Available in both rounds) ---
                                    with st.popover("❌ Reject Candidate"):
                                        st.markdown("### Rejection Details")
                                        st.info("This action is irreversible. The candidate will be notified and archived.")
                                        
                                        rej_reason = st.text_area("Internal Rejection Reason", placeholder="e.g., Lack of depth in System Design...", key=f"rej_r_{c['id']}")
                                        
                                        if st.button("Confirm Rejection", key=f"btn_rej_{c['id']}", type="primary"):
                                            if rej_reason:
                                                c['status'] = 'Rejected'
                                                c['rejection_reason'] = rej_reason
                                                c['archived'] = True
                                                database.save_candidate(c)
                                                
                                                # Send Rejection Email (Generic, no reason included)
                                                resend_candidate_email(c)
                                                st.toast("Candidate Rejected & Archived")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("Please provide a reason for internal reference.")

                                    # Simple Archive (No email trigger, just hide)
                                    if st.button("Archive (No Email)", key=f"arc_{c['id']}_int"):
                                        c['archived'] = True
                                        database.save_candidate(c)
                                        st.rerun()

            # --- OFFERS & JOINING TAB ---
            with subtab_4:
                if not stage_selected:
                    st.info("No selected candidates waiting for joining.")
                else:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 3, 2])
                        c1.markdown("**Candidate**")
                        c2.markdown("**Status / Docs**")
                        c3.markdown("**Action**")
                    
                    for c in stage_selected:
                         with st.container(border=True):
                            c1, c2, c3 = st.columns([3, 3, 2])
                            with c1:
                                st.markdown(f"**{c['name']}**")
                                st.caption(c['role'])
                                
                                email_status = c.get('email_status', 'Unknown')
                                color = "green" if email_status == "Sent" else "red" if email_status == "Failed" else "grey"
                                st.markdown(f"📧 Email: :{color}[{email_status}]")
                            
                            with c2:
                                if c['status'] == 'Selected':
                                    if c.get('documents_uploaded'):
                                        st.success("Docs Uploaded")
                                        
                                        # Show download buttons
                                        docs = c.get('documents', {})
                                        col_d1, col_d2 = st.columns(2)
                                        with col_d1:
                                            if docs.get('id_proof') and os.path.exists(docs['id_proof']):
                                                with open(docs['id_proof'], "rb") as f:
                                                    st.download_button("⬇️ ID Proof", f, file_name=os.path.basename(docs['id_proof']), key=f"dl_id_{c['id']}")
                                        with col_d2:
                                            if docs.get('address_proof') and os.path.exists(docs['address_proof']):
                                                with open(docs['address_proof'], "rb") as f:
                                                    st.download_button("⬇️ Addr Proof", f, file_name=os.path.basename(docs['address_proof']), key=f"dl_ad_{c['id']}")
                                    else:
                                        st.warning("Waiting for Documents")
                                        st.caption("Requested: ID, Address")
                                elif c['status'] == 'Joining Scheduled':
                                    st.success(f"Joining: {c.get('joining_date')}")
                                    st.caption("Joining Letter Sent")
                            
                            with c3:
                                with st.popover("📄 View Profile"):
                                    render_candidate_details(c)
                                
                                # Ownership Check
                                assigned = c.get('recruiter')
                                is_owner = not assigned or assigned == current_hr or is_super_admin
                                
                                if is_owner:
                                    if c['status'] == 'Selected':
                                        with st.popover("Send Joining Letter"):
                                            st.markdown("### 📅 Finalize Joining")
                                            j_date = st.date_input("Joining Date", key=f"jd_{c['id']}")
                                            
                                            st.info("This will trigger the official Joining Letter email.")
                                            
                                            # Disable if documents not uploaded
                                            btn_disabled = not c.get('documents_uploaded')
                                            
                                            if btn_disabled:
                                                st.error("Cannot send letter: Documents Pending")
                                            
                                            if st.button("Confirm & Send Letter", key=f"btn_join_{c['id']}", type="primary", disabled=btn_disabled):
                                                c['joining_date'] = j_date.strftime("%Y-%m-%d")
                                                c['status'] = 'Joining Scheduled'
                                                database.save_candidate(c)
                                                
                                                # Send Joining Email
                                                resend_candidate_email(c)
                                                st.toast(f"Joining Letter Sent!")
                                                time.sleep(1)
                                                st.rerun()
                                    elif c['status'] == 'Joining Scheduled':
                                        if st.button("🔄 Resend Letter", key=f"rs_join_{c['id']}"):
                                            sent, msg = resend_candidate_email(c)
                                            if sent: st.toast("Joining Letter Resent")
                                            else: st.error(f"Failed: {msg}")

                                else:
                                    st.caption(f"Locked by {assigned}")

    # --- JOB MANAGEMENT TAB ---
    with tab_jobs:
        st.subheader("Manage Job Descriptions")
        st.markdown("Add roles with specific skills and experience requirements. The AI will strictly use these for screening.")
        
        common_skills = [
            "Python", "Java", ".NET", ".NET Core", "C#", "JavaScript", "TypeScript", "React", "Angular", "Vue.js",
            "Node.js", "Django", "Flask", "FastAPI", "Spring Boot", "SQL", "PostgreSQL", "MongoDB", "AWS", "Azure",
            "GCP", "Docker", "Kubernetes", "CI/CD", "Git", "Machine Learning", "Data Analysis"
        ]

        if 'new_job_title' not in st.session_state: st.session_state.new_job_title = ""
        if 'new_job_exp' not in st.session_state: st.session_state.new_job_exp = 2
        if 'new_job_skills' not in st.session_state: st.session_state.new_job_skills = []
        if 'new_job_desc' not in st.session_state: st.session_state.new_job_desc = ""

        with st.form("add_job_form"):
            col_j1, col_j2 = st.columns([1, 1])
            with col_j1:
                new_title = st.text_input("Job Title", placeholder="e.g. Senior Backend Engineer", key="new_job_title")
            with col_j2:
                new_exp = st.number_input("Minimum Experience (Years)", min_value=0, max_value=20, step=1, key="new_job_exp")

            new_skills = st.multiselect("Required Skills (Select all that apply)", options=common_skills, key="new_job_skills")
            
            new_desc = st.text_area("Detailed Job Description", height=200, placeholder="Paste the full job description here. Include culture, soft skills, and day-to-day responsibilities.", key="new_job_desc")
            
            if st.form_submit_button("Create Job Posting", type="primary"):
                if st.session_state.new_job_title and st.session_state.new_job_desc and st.session_state.new_job_skills:
                    database.save_job(
                        st.session_state.new_job_title, 
                        st.session_state.new_job_desc, 
                        st.session_state.new_job_skills, 
                        st.session_state.new_job_exp
                    )
                    st.success(f"Job '{st.session_state.new_job_title}' created successfully!")
                    
                    del st.session_state.new_job_title
                    del st.session_state.new_job_exp
                    del st.session_state.new_job_skills
                    del st.session_state.new_job_desc
                    
                    st.rerun()
                else:
                    st.error("Please fill in Job Title, Skills, and Description.")
        
        st.divider()
        st.markdown("### Active Jobs")
        
        current_jobs = database.get_jobs()
        if not current_jobs:
            st.info("No jobs defined yet. Create one above.")
        else:
            for job in current_jobs:
                with st.container(border=True):
                    col_j1, col_j2 = st.columns([5, 1])
                    with col_j1:
                        st.markdown(f"**{job['title']}**")
                        st.markdown(f"**Experience:** {job.get('min_experience', 0)}+ Years")
                        if job.get('skills'):
                            skills_list = job['skills'].split(',')
                            tags_html = " ".join([f"<span style='background-color:#e0f2fe; color:#0284c7; padding:2px 8px; border-radius:12px; font-size:12px; font-weight:600; margin-right:4px;'>{s}</span>" for s in skills_list])
                            st.markdown(tags_html, unsafe_allow_html=True)
                        
                        with st.expander("Show Detailed Description"):
                            st.write(job['description'])
                            
                    with col_j2:
                        with st.popover("Edit"):
                            st.markdown("### Edit Job")
                            edit_title = st.text_input("Title", value=job['title'], key=f"edit_t_{job['id']}")
                            edit_exp = st.number_input("Min Exp", value=job.get('min_experience', 0), min_value=0, key=f"edit_e_{job['id']}")
                            
                            existing_skills = job.get('skills', '').split(',') if job.get('skills') else []
                            valid_default_skills = [s for s in existing_skills if s in common_skills]
                            
                            edit_skills = st.multiselect(
                                "Skills", 
                                options=common_skills, 
                                default=valid_default_skills, 
                                key=f"edit_s_{job['id']}"
                            )
                            
                            edit_desc = st.text_area("Description", value=job['description'], height=150, key=f"edit_d_{job['id']}")
                            
                            if st.button("Update Job", key=f"btn_upd_{job['id']}", type="primary"):
                                database.update_job(job['id'], edit_title, edit_desc, edit_skills, edit_exp)
                                st.success("Job updated!")
                                st.rerun()

                        if st.button("Delete", key=f"del_job_{job['id']}"):
                            database.delete_job(job['id'])
                            st.rerun()

    with tab_team:
        st.subheader("Manage HR Team")
        is_super_admin = st.session_state.hr_username == "admin"
        
        if is_super_admin:
            st.markdown("Create accounts for other recruiters. The system will simulate sending credentials via email.")
            with st.container(border=True):
                st.markdown("### Add New Recruiter")
                
                if 'new_u_input' not in st.session_state: st.session_state.new_u_input = ""
                if 'new_e_input' not in st.session_state: st.session_state.new_e_input = ""
                if 'new_p_input' not in st.session_state: st.session_state.new_p_input = ""

                with st.form("add_hr_form"):
                    c1, c2, c3 = st.columns(3)
                    new_u = c1.text_input("Username", placeholder="j.doe", key="new_u_input")
                    new_e = c2.text_input("Email", placeholder="j.doe@company.com", key="new_e_input")
                    new_p = c3.text_input("Password", type="password", placeholder="Secret123", key="new_p_input")
                    
                    if st.form_submit_button("Create User & Send Email", type="primary"):
                        if st.session_state.new_u_input and st.session_state.new_p_input and st.session_state.new_e_input:
                            if database.create_user(st.session_state.new_u_input, st.session_state.new_p_input, st.session_state.new_e_input):
                                email_body = f"""
Hello {st.session_state.new_u_input},

You have been granted recruiter access to the HireAI platform.

Username: {st.session_state.new_u_input}
Password: {st.session_state.new_p_input}

Please login securely at the HR Portal.

Best regards,
HireAI Admin
"""
                                sent, msg = email_service.send_email(st.session_state.new_e_input, "HireAI Recruiter Access", email_body)
                                
                                st.success(f"User '{st.session_state.new_u_input}' created successfully.")
                                if sent:
                                    st.toast(f"📧 Credentials sent to {st.session_state.new_e_input}", icon="✅")
                                else:
                                    st.error(f"Failed to send email: {msg}")
                                
                                del st.session_state.new_u_input
                                del st.session_state.new_e_input
                                del st.session_state.new_p_input
                                
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Username '{st.session_state.new_u_input}' already exists.")
                        else:
                            st.warning("All fields are required.")
        else:
             st.info("Team management is restricted to Super Admin. You have read-only access to the team list.")

        st.markdown("### Existing Users")
        
        users = database.get_users()
        c1, c2, c3 = st.columns([2, 3, 2])
        c1.markdown("**Username**")
        c2.markdown("**Email**")
        c3.markdown("**Actions**")
        
        for u in users:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 3, 2])
                c1.markdown(f"👤 **{u['username']}**")
                c2.caption(u.get('email', 'No Email'))
                
                with c3:
                    if is_super_admin:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            with st.popover("Edit"):
                                st.markdown(f"**Edit {u['username']}**")
                                ed_email = st.text_input("Email", value=u.get('email', ''), key=f"e_{u['username']}")
                                ed_pass = st.text_input("New Password", type="password", key=f"p_{u['username']}", help="Leave blank to keep current")
                                if st.button("Update", key=f"upd_{u['username']}"):
                                    final_pass = ed_pass if ed_pass else u['password']
                                    database.update_user(u['username'], ed_email, final_pass)
                                    st.success("Updated!")
                                    st.rerun()
                        
                        with col_b:
                            if u['username'] != 'admin':
                                if st.button("🗑️", key=f"del_{u['username']}", help="Delete User"):
                                    database.delete_user(u['username'])
                                    st.rerun()
                            elif u['username'] == 'admin':
                                st.caption("Super Admin")
                    else:
                        st.caption("View Only")

    with tab_archived:
        if not archived_candidates:
            st.info("No archived candidates.")
        else:
            with st.form("archive_management"):
                st.write("Select candidates to manage.")
                selected_for_delete = []
                col_h1, col_h2, col_h3 = st.columns([0.5, 4, 1.5])
                col_h1.markdown("**Select**")
                col_h2.markdown("**Candidate**")
                col_h3.markdown("**Stats**")
                
                for c in archived_candidates:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([0.5, 4, 1.5])
                        with c1:
                            if st.checkbox("", key=f"del_{c['id']}"):
                                selected_for_delete.append(c['id'])
                        with c2:
                            st.markdown(f"**{c['name']}**")
                            st.caption(f"{c['role']}")
                            
                            # SHOW REJECTION REASON IF EXISTS (Internal Only)
                            if c.get('rejection_reason'):
                                st.error(f"🛑 Rejection Reason: {c['rejection_reason']}")

                        with c3:
                            st.caption(f"Score: {c.get('score', 0)}")
                            status = c['status']
                            color = "red" if status == "Rejected" else "grey"
                            st.markdown(f":{color}[{status}]")
                
                st.divider()
                col_actions_1, col_actions_2 = st.columns([1, 1])
                with col_actions_1:
                    restore_pressed = st.form_submit_button("Restore Selected")
                with col_actions_2:
                    delete_pressed = st.form_submit_button("Delete Selected (Permanent)", type="primary")

                if restore_pressed and selected_for_delete:
                    for cid in selected_for_delete:
                        cand = next((x for x in candidates if x['id'] == cid), None)
                        if cand:
                            cand['archived'] = False
                            database.save_candidate(cand)
                    st.success(f"Restored {len(selected_for_delete)} candidates.")
                    st.rerun()
                
                if delete_pressed and selected_for_delete:
                     database.bulk_delete_candidates(selected_for_delete)
                     st.success(f"Permanently deleted {len(selected_for_delete)} records.")
                     st.rerun()

def view_interview_room():
    if not st.session_state.active_user:
        st.title("Candidate Login")
        col_c, _ = st.columns([1, 1])
        with col_c:
            with st.container(border=True):
                key_input = st.text_input("Enter your 8-digit Access Key", placeholder="XXXX-0000")
                if st.button("Login to Portal", type="primary"):
                    match = next((c for c in candidates if c.get('access_key') == key_input and not c.get('archived')), None)
                    if match:
                        st.session_state.active_user = match
                        st.rerun()
                    else:
                        st.error("Invalid key or account archived.")
    else:
        user = st.session_state.active_user
        
        # --- SELECTED / DOCUMENT SUBMISSION STAGE ---
        if user.get('status') == 'Selected':
            st.title(f"🎉 Congratulations, {user['name']}!")
            
            # If documents are already uploaded
            if user.get('documents_uploaded'):
                 with st.container(border=True):
                     st.success("✅ Documents Submitted Successfully")
                     st.info("Your profile is currently under verification by the HR team. We will contact you shortly with your Joining Letter.")
                     st.caption("If you need to update your documents, please contact HR directly.")
                 return

            st.balloons()
            with st.container(border=True):
                st.success("You have been selected for the role! Please submit your documents to proceed.")
                
                st.markdown("### 📂 Document Submission")
                st.write("Please upload clear copies of the following documents.")
                
                id_proof = st.file_uploader("Upload ID Proof (Passport/Aadhaar/License) - PDF/Image", type=['pdf', 'png', 'jpg', 'jpeg'], key="up_id")
                addr_proof = st.file_uploader("Upload Address Proof - PDF/Image", type=['pdf', 'png', 'jpg', 'jpeg'], key="up_addr")
                
                if st.button("Submit Documents for Verification", type="primary"):
                    if id_proof and addr_proof:
                        # Save files
                        p1 = save_uploaded_doc(id_proof, user['id'], "ID_Proof")
                        p2 = save_uploaded_doc(addr_proof, user['id'], "Address_Proof")
                        
                        user['documents'] = {
                            "id_proof": p1,
                            "address_proof": p2
                        }
                        user['documents_uploaded'] = True
                        database.save_candidate(user)
                        
                        st.toast("Documents submitted successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Please upload both documents to proceed.")
            return

        if user.get('status') == 'Interview Scheduled':
            round_label = "First Round" if user.get('interview_round', 1) == 1 else "Second Round"
            st.title(f"{round_label} Interview: {user['name']}")
            with st.container(border=True):
                st.success(f"You are scheduled for the {round_label} Interview.")
                st.markdown(f"### Interview Time: {user['round2Date']} at {user['round2Time']}")
                st.link_button("JOIN VIDEO MEETING NOW", user['round2Link'])
                st.caption("HR has been notified of your readiness.")
            return

        st.title(f"Aptitude Portal: {user['name']}")
        
        if not user.get('aptitudeDate'):
            st.info("Your exam has not been scheduled by HR yet. Please check back later.")
            return

        scheduled_datetime_str = f"{user['aptitudeDate']} {user['aptitudeTime']}"
        scheduled_dt = datetime.strptime(scheduled_datetime_str, "%Y-%m-%d %H:%M")
        now = datetime.now()
        
        if now < scheduled_dt:
            diff = scheduled_dt - now
            mins, secs = divmod(diff.seconds, 60)
            hours, mins = divmod(mins, 60)
            
            with st.container(border=True):
                st.warning("Exam Locked")
                st.markdown(f"### Starts in: {diff.days}d {hours}h {mins}m")
                st.write(f"Scheduled for: **{scheduled_datetime_str}**")
                if st.button("Refresh Timer"):
                    st.rerun()
            return

        if user.get('aptitude_score') is not None:
             with st.container(border=True):
                 st.header("Exam Results")
                 score = user['aptitude_score']
                 is_passed = score >= 50
                 col1, col2 = st.columns(2)
                 with col1:
                     st.metric("Final Score", f"{score}%")
                 with col2:
                     if is_passed:
                         st.success("Result: PASS")
                         st.caption("You have qualified for the next round.")
                     else:
                         st.error("Result: FAIL")
                         st.caption("You did not meet the required threshold.")
                 
                 st.divider()
                 st.subheader("Detailed Review")
                 
                 details = user.get('aptitude_details')
                 if details:
                     questions_data = details.get('questions', [])
                     answers_data = details.get('answers', {})
                     answers_data = {int(k): v for k, v in answers_data.items()}

                     for i, q in enumerate(questions_data):
                         user_selected = answers_data.get(i)
                         correct_option = q['options'][q['correct_index']]
                         is_correct = user_selected == correct_option
                         
                         with st.expander(f"Q{i+1}: {q['question']} - {'✅' if is_correct else '❌'}", expanded=not is_correct):
                             st.write(f"**Category:** {q['category']}")
                             for opt in q['options']:
                                 prefix = "⚪ "
                                 if opt == correct_option: prefix = "✅ "
                                 elif opt == user_selected and not is_correct: prefix = "❌ "
                                 elif opt == user_selected and is_correct: prefix = "✅ "
                                     
                                 if opt == correct_option:
                                     st.markdown(f":green[**{prefix}{opt}**] (Correct Answer)")
                                 elif opt == user_selected:
                                     st.markdown(f":red[**{prefix}{opt}**] (Your Answer)")
                                 else:
                                     st.markdown(f"{prefix}{opt}")
                 else:
                     st.info("Detailed results not available for this session.")
             return

        # --- TIMER LOGIC ---
        test_duration = get_test_duration()
        
        if 'aptitude_questions' not in st.session_state:
            with st.container(border=True):
                st.subheader("Assessment Instructions")
                st.markdown(f"""
                * This exam consists of **20 Multiple Choice Questions**.
                * You have **{test_duration} minutes** to complete the test.
                * Once you start, the timer will not stop.
                * Answers will be automatically submitted when time runs out.
                """)
                
                if st.button("GENERATE & START EXAM", type="primary"):
                    with st.spinner(f"AI is generating a unique test for {user['role']} role..."):
                        st.session_state.aptitude_questions = generate_aptitude_questions(user['role'])
                        st.session_state.exam_start_time = datetime.now()
                        st.rerun()
        else:
            # Calculate Time Remaining
            elapsed = datetime.now() - st.session_state.exam_start_time
            remaining = timedelta(minutes=test_duration) - elapsed
            
            is_expired = remaining.total_seconds() <= 0
            
            # Show Timer
            if not is_expired:
                mins, secs = divmod(int(remaining.total_seconds()), 60)
                st.metric("Time Remaining", f"{mins:02}:{secs:02}")
            
            questions = st.session_state.aptitude_questions
            
            # --- AUTO SUBMIT OR MANUAL SUBMIT LOGIC ---
            if is_expired:
                st.error("⏰ Time is up! Submitting your answers automatically...")
                # Fall through to grading logic
            
            with st.form("exam_form"):
                # If expired, we don't render inputs, just processing
                if not is_expired:
                    for i, q in enumerate(questions):
                        st.markdown(f"**{i+1}. {q['question']}**")
                        st.caption(f"Category: {q['category']}")
                        
                        # Note: key=f"q_{i}" automatically stores selection in session_state
                        st.radio(
                            "Select Answer",
                            q['options'], 
                            key=f"q_{i}", 
                            label_visibility="collapsed"
                        )
                        st.divider()
                
                submit_clicked = st.form_submit_button("SUBMIT FINAL ANSWERS", type="primary")
            
            # Trigger submission if clicked OR if time expired
            if submit_clicked or is_expired:
                score = 0
                user_answers = {}
                
                # Retrieve answers from session state
                for i, q in enumerate(questions):
                    selected_option = st.session_state.get(f"q_{i}")
                    user_answers[i] = selected_option
                    
                    try:
                        if selected_option:
                            selected_index = q['options'].index(selected_option)
                            if selected_index == q['correct_index']:
                                score += 1
                    except:
                        pass
                
                final_percentage = int((score / len(questions)) * 100)
                
                details = {
                    "questions": questions,
                    "answers": user_answers 
                }
                
                # Update Candidate in DB FIRST so status is correct for resend function
                user['aptitude_score'] = final_percentage
                user['aptitude_details'] = details
                user['status'] = 'Aptitude Completed'
                database.save_candidate(user)
                
                # Resend Email (Passed/Failed) using helper
                email_sent, email_msg = resend_candidate_email(user)

                user['email_status'] = "Sent" if email_sent else "Failed"
                user['email_error'] = email_msg if not email_sent else None
                database.save_candidate(user)
                
                st.session_state.active_user = user
                
                if is_expired:
                     time.sleep(2) # Show the error message for a bit
                else:
                     st.balloons()
                
                st.rerun()

# --- MAIN APP ROUTING ---
nav_choice = sidebar_nav()

if nav_choice == "Candidate Portal":
    view_candidate_portal()
elif nav_choice == "HR Dashboard":
    view_hr_dashboard()
elif nav_choice == "Candidate Login":
    view_interview_room()
