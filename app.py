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
from google import genai
from google.genai import types
from dotenv import load_dotenv  # Import dotenv
import database  # Import the shared database module

# --- LOAD ENVIRONMENT VARIABLES ---
# This ensures it works on local machines, VPS, and hosting panels using .env files
load_dotenv()

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
        
        /* Hide default Streamlit chrome */
        #MainMenu {visibility: hidden;} 
        footer {visibility: hidden;} 
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- INITIALIZATION ---
database.init_db()
# Load candidates from DB. 
# We fetch this at the start of the script run. 
# Streamlit re-runs the whole script on interaction, so this stays up to date.
candidates = database.get_candidates()

if 'active_user' not in st.session_state:
    st.session_state.active_user = None

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
    return f"https://meet.google.com/{''.join(random.choices(string.ascii_lowercase, k=3))}-{''.join(random.choices(string.ascii_lowercase, k=4))}-{''.join(random.choices(string.ascii_lowercase, k=3))}"

# --- AI LOGIC ---
def screen_resume_ai(text, role):
    prompt = f"Analyze this resume for a {role} role. Provide a match score and summary. Resume: {text}"
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema={
                'type': 'OBJECT',
                'properties': {
                    'overallScore': {'type': 'INTEGER'},
                    'summary': {'type': 'STRING'},
                    'technicalMatch': {'type': 'INTEGER'}
                },
                'required': ['overallScore', 'summary']
            }
        )
    )
    return json.loads(response.text)

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

# --- VIEWS ---
def sidebar_nav():
    with st.sidebar:
        col_logo, col_title = st.columns([1, 4])
        with col_logo:
             st.markdown("### 🎯")
        with col_title:
             st.markdown("### HireAI")
        
        # Using a key ensures better state stability
        choice = st.radio("Navigation", 
                         ["Candidate Portal", "Candidate Login", "HR Dashboard"],
                         key="nav_radio")
        
        st.divider()
        st.caption("SYSTEM STATUS")
        
        # Notifications
        if choice == "HR Dashboard":
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
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader("Application Form")
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email Address", placeholder="john@example.com")
            role = st.selectbox("Apply for Role", ["Software Engineer", "Frontend Developer", "Product Manager", "Data Analyst"])
            resume = st.file_uploader("Upload Resume (TXT/PDF)", type=['txt', 'pdf'])
            
            if st.button("Submit Application", type="primary"):
                if name and email and resume:
                    with st.spinner("AI is analyzing your profile..."):
                        try:
                            resume_text = resume.read().decode("utf-8", errors="ignore")
                            analysis = screen_resume_ai(resume_text, role)
                            access_key = generate_key()
                            c_id = str(uuid.uuid4())
                            
                            new_candidate = {
                                "id": c_id,
                                "name": name,
                                "email": email,
                                "role": role,
                                "status": "Screening",
                                "score": analysis['overallScore'],
                                "technical": analysis['technicalMatch'],
                                "summary": analysis['summary'],
                                "access_key": access_key,
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "aptitude_score": None,
                                "aptitudeDate": None,
                                "aptitudeTime": None,
                                "round2Date": None,
                                "round2Time": None,
                                "round2Link": None
                            }
                            database.save_candidate(new_candidate)
                            st.balloons()
                            st.success("Profile Screened Successfully!")
                            st.session_state.last_submitted = new_candidate
                        except Exception as e:
                            st.error(f"Error processing application: {e}")
                else:
                    st.warning("Please fill all fields.")

    with col2:
        if 'last_submitted' in st.session_state:
            c = st.session_state.last_submitted
            with st.container(border=True):
                st.info("Please save your credentials")
                st.markdown(f"## {c['access_key']}")
                st.caption("Use this Access Key to login to the interview portal.")
                st.markdown(f"**Role:** {c['role']}")
                st.markdown(f"**AI Score:** {c['score']}/100")

def view_hr_dashboard():
    st.title("Recruiter Command Center")
    
    if not candidates:
        st.info("The pipeline is currently empty. Candidates will appear here once they apply.")
        return

    df = pd.DataFrame(candidates)
    
    # 1. Pipeline Metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        with st.container(border=True):
            st.metric("Total Candidates", len(df))
    with m2:
        with st.container(border=True):
            # Handle nullable scores in dataframe
            aptitude_takers = df[df['aptitude_score'].notnull()] if 'aptitude_score' in df.columns else pd.DataFrame()
            avg_apt = int(aptitude_takers['aptitude_score'].mean()) if not aptitude_takers.empty else 0
            st.metric("Avg Aptitude Score", f"{avg_apt}%")
    with m3:
        with st.container(border=True):
            upcoming = "None"
            for c in candidates:
                 if c.get('round2Date'): 
                     upcoming = f"{c['round2Date']} {c['round2Time']}"
            st.metric("Next Interview", upcoming)

    # 2. Master Pipeline List (Shows ALL candidates)
    st.subheader("Candidate Pipeline")
    st.markdown("View and manage all candidates in the system.")
    
    # Table Header
    with st.container(border=True):
        col_c, col_s, col_sc, col_a = st.columns([2.5, 1.5, 1, 2])
        col_c.markdown("**Candidate**")
        col_s.markdown("**Stage**")
        col_sc.markdown("**Scores**")
        col_a.markdown("**Action**")

    # Table Rows
    for c in candidates:
        with st.container(border=True):
            col_c, col_s, col_sc, col_a = st.columns([2.5, 1.5, 1, 2])
            
            # 1. Candidate Details
            with col_c:
                st.markdown(f"**{c['name']}**")
                st.caption(f"{c['role']}")
                st.caption(f"📧 {c['email']}")
            
            # 2. Stage/Status
            with col_s:
                status_color = "gray"
                if c['status'] == 'Screening': status_color = "blue"
                elif c['status'] == 'Aptitude Scheduled': status_color = "orange"
                elif c['status'] == 'Aptitude Completed': status_color = "green" if (c.get('aptitude_score') or 0) >= 50 else "red"
                elif c['status'] == 'Interview Scheduled': status_color = "violet"
                
                st.markdown(f":{status_color}[{c['status']}]")
                if c.get('aptitudeDate'):
                    st.caption(f"Exam: {c['aptitudeDate']} {c['aptitudeTime']}")

            # 3. Scores
            with col_sc:
                st.markdown(f"Resume: **{c.get('score', 0)}**")
                if c.get('aptitude_score') is not None:
                    st.markdown(f"Aptitude: **{c['aptitude_score']}**")
                else:
                    st.markdown("Aptitude: --")

            # 4. Actions
            with col_a:
                # Screening -> Schedule Aptitude
                if c['status'] == 'Screening':
                    with st.popover("Schedule Exam"):
                        d = st.date_input("Date", key=f"d_{c['id']}")
                        t = st.time_input("Time", key=f"t_{c['id']}")
                        if st.button("Confirm Schedule", key=f"btn_{c['id']}", type="primary"):
                            c['aptitudeDate'] = d.strftime("%Y-%m-%d")
                            c['aptitudeTime'] = t.strftime("%H:%M")
                            c['status'] = 'Aptitude Scheduled'
                            database.save_candidate(c)
                            st.toast(f"Exam scheduled for {c['name']}", icon="📧")
                            st.rerun()
                
                # Aptitude Scheduled -> Waiting
                elif c['status'] == 'Aptitude Scheduled':
                    st.info("Waiting for candidate to take exam.")

                # Aptitude Completed -> Schedule Round 2 (if passed)
                elif c['status'] == 'Aptitude Completed':
                    if (c.get('aptitude_score') or 0) >= 50:
                        with st.popover("Schedule Round 2"):
                            r2d = st.date_input("Interview Date", key=f"r2d_{c['id']}")
                            r2t = st.time_input("Start Time", key=f"r2t_{c['id']}")
                            if st.button("Confirm Interview", key=f"r2btn_{c['id']}", type="primary"):
                                c['round2Date'] = r2d.strftime("%Y-%m-%d")
                                c['round2Time'] = r2t.strftime("%H:%M")
                                c['round2Link'] = generate_meeting_link()
                                c['status'] = 'Interview Scheduled'
                                database.save_candidate(c)
                                st.toast(f"Interview set for {c['name']}", icon="📅")
                                st.rerun()
                    else:
                        st.error("Low Score. No Action.")

                # Interview Scheduled -> Link
                elif c['status'] == 'Interview Scheduled':
                    st.link_button("Join Meeting", c['round2Link'])

def view_interview_room():
    if not st.session_state.active_user:
        st.title("Candidate Login")
        col_c, _ = st.columns([1, 1])
        with col_c:
            with st.container(border=True):
                key_input = st.text_input("Enter your 8-digit Access Key", placeholder="XXXX-0000")
                if st.button("Login to Portal", type="primary"):
                    match = next((c for c in candidates if c.get('access_key') == key_input), None)
                    if match:
                        st.session_state.active_user = match
                        st.rerun()
                    else:
                        st.error("Invalid key. Access Denied.")
    else:
        user = st.session_state.active_user
        
        # --- VIEW 1: ROUND 2 INTERVIEW ---
        if user.get('status') == 'Interview Scheduled':
            st.title(f"Final Interview: {user['name']}")
            with st.container(border=True):
                st.success("Congratulations! You passed the Aptitude Round.")
                st.markdown(f"### Interview Time: {user['round2Date']} at {user['round2Time']}")
                st.link_button("JOIN VIDEO MEETING NOW", user['round2Link'])
                st.caption("HR has been notified of your readiness.")
            return

        # --- VIEW 2: APTITUDE EXAM GATING ---
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

        # --- VIEW 3: COMPLETED STATE ---
        if user.get('aptitude_score') is not None:
             with st.container(border=True):
                 st.header("Exam Submitted")
                 st.metric("Final Score", f"{user['aptitude_score']}%")
                 st.info("Thank you. HR is reviewing your results.")
             return

        # --- VIEW 4: EXAM INTERFACE ---
        if 'aptitude_questions' not in st.session_state:
            with st.container(border=True):
                st.subheader("Assessment Instructions")
                st.markdown("""
                * This exam consists of **20 Multiple Choice Questions**.
                * Once you start, please complete all questions before submitting.
                """)
                
                if st.button("GENERATE & START EXAM", type="primary"):
                    with st.spinner(f"AI is generating a unique test for {user['role']} role..."):
                        st.session_state.aptitude_questions = generate_aptitude_questions(user['role'])
                        st.rerun()
        else:
            questions = st.session_state.aptitude_questions
            with st.form("exam_form"):
                user_answers = {}
                for i, q in enumerate(questions):
                    st.markdown(f"**{i+1}. {q['question']}**")
                    st.caption(f"Category: {q['category']}")
                    
                    user_answers[i] = st.radio(
                        "Select Answer",
                        q['options'], 
                        key=f"q_{i}", 
                        label_visibility="collapsed"
                    )
                    st.divider()
                
                if st.form_submit_button("SUBMIT FINAL ANSWERS", type="primary"):
                    score = 0
                    for i, q in enumerate(questions):
                        selected_option = user_answers.get(i)
                        try:
                            selected_index = q['options'].index(selected_option)
                            if selected_index == q['correct_index']:
                                score += 1
                        except:
                            pass
                    
                    final_percentage = int((score / len(questions)) * 100)
                    
                    # Update Candidate in DB
                    user['aptitude_score'] = final_percentage
                    user['status'] = 'Aptitude Completed'
                    database.save_candidate(user)
                    st.session_state.active_user = user
                    
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
