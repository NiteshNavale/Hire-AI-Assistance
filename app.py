
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
import database  # Import the shared database module

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
        
        /* Sidebar Styling - Ensure visibility in both Light and Dark modes */
        [data-testid="stSidebar"] { 
            background-color: #ffffff; 
            border-right: 1px solid #e2e8f0; 
        }
        
        /* Force dark text color for sidebar elements to prevent white-on-white in Dark Mode */
        [data-testid="stSidebar"] * {
            color: #0f172a !important;
        }

        /* Card Styling */
        .hireai-card {
            background: white; padding: 24px; border-radius: 20px;
            border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
        .hireai-label {
            font-size: 10px; font-weight: 900; color: #64748b;
            text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
        }
        
        /* Button Styling */
        .stButton>button {
            width: 100%; border-radius: 12px; font-weight: 700;
            background-color: #2563eb; color: white; border: none; padding: 12px;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #1d4ed8; transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
        }
        
        /* Metrics & Headings */
        [data-testid="stMetricValue"] { font-weight: 900; color: #1e293b; }
        h1, h2, h3 { font-weight: 900 !important; letter-spacing: -1px !important; color: #0f172a !important; }
        
        /* Hide default Streamlit chrome */
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- INITIALIZATION ---
database.init_db()
# Load candidates from DB instead of session state list
candidates = database.get_candidates()

if 'active_user' not in st.session_state:
    st.session_state.active_user = None

# --- API CLIENT ---
def get_client():
    api_key = st.secrets["API_KEY"] if "API_KEY" in st.secrets else os.environ.get("API_KEY")
    if not api_key:
        st.error("Missing API_KEY. Please add it to Secrets.")
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
        st.markdown("""
            <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 30px;'>
                <div style='background: #2563eb; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 900;'>H</div>
                <h2 style='margin: 0; font-size: 24px;'>HireAI</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # Using a key ensures better state stability, though not strictly required if UI flow is linear.
        choice = st.radio("MAIN NAVIGATION", 
                         ["Candidate Portal", "Candidate Login", "HR Dashboard"],
                         label_visibility="collapsed",
                         key="nav_radio")
        
        st.markdown("---")
        st.markdown("<p class='hireai-label'>System Status</p>", unsafe_allow_html=True)
        
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
                 st.markdown(f"""
                    <div style='background: #fef2f2; border: 1px solid #fee2e2; padding: 12px; border-radius: 12px; margin-bottom: 20px; animation: pulse 2s infinite;'>
                        <p style='color: #dc2626; font-weight: bold; font-size: 12px; margin: 0;'>🔔 Meeting Starting Soon</p>
                        <p style='color: #7f1d1d; font-size: 11px; margin-top: 4px;'>Round 2 with {", ".join(upcoming_meetings)} starts in < 5 mins!</p>
                    </div>
                """, unsafe_allow_html=True)

        if st.session_state.active_user:
            if st.button("Logout Candidate"):
                st.session_state.active_user = None
                if 'aptitude_questions' in st.session_state:
                    del st.session_state.aptitude_questions
                st.rerun()
                
    return choice

def view_candidate_portal():
    st.markdown("<h1>Join HireAI Pipeline</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Submit your profile for instant AI screening.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<div class='hireai-card'>", unsafe_allow_html=True)
        name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email Address", placeholder="john@example.com")
        role = st.selectbox("Apply for Role", ["Software Engineer", "Frontend Developer", "Product Manager", "Data Analyst"])
        resume = st.file_uploader("Upload Resume (TXT/PDF)", type=['txt', 'pdf'])
        
        if st.button("SUBMIT APPLICATION"):
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
                        st.success("Profile Screened!")
                        st.session_state.last_submitted = new_candidate
                    except Exception as e:
                        st.error(f"Error processing application: {e}")
            else:
                st.warning("Please fill all fields.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        if 'last_submitted' in st.session_state:
            c = st.session_state.last_submitted
            st.markdown(f"""
                <div style='background: #eff6ff; border: 2px dashed #3b82f6; padding: 30px; border-radius: 24px; text-align: center;'>
                    <p class='hireai-label' style='color: #3b82f6;'>Your Interview Key</p>
                    <h1 style='font-size: 48px; color: #1d4ed8; margin: 10px 0;'>{c['access_key']}</h1>
                    <p style='font-size: 14px; color: #1e40af;'>Save this key! You will need it to login later.</p>
                </div>
            """, unsafe_allow_html=True)

def view_hr_dashboard():
    st.markdown("<h1>Recruiter Command Center</h1>", unsafe_allow_html=True)
    
    if not candidates:
        st.info("The pipeline is currently empty.")
        return

    df = pd.DataFrame(candidates)
    
    # 1. Pipeline Metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("<div class='hireai-card'>", unsafe_allow_html=True)
        st.metric("Total Candidates", len(df))
        st.markdown("</div>", unsafe_allow_html=True)
    with m2:
        st.markdown("<div class='hireai-card'>", unsafe_allow_html=True)
        # Handle nullable scores in dataframe
        aptitude_takers = df[df['aptitude_score'].notnull()] if 'aptitude_score' in df.columns else pd.DataFrame()
        avg_apt = int(aptitude_takers['aptitude_score'].mean()) if not aptitude_takers.empty else 0
        st.metric("Avg Aptitude Score", f"{avg_apt}%")
        st.markdown("</div>", unsafe_allow_html=True)
    with m3:
        st.markdown("<div class='hireai-card'>", unsafe_allow_html=True)
        upcoming = "None"
        for c in candidates:
             if c.get('round2Date'): 
                 upcoming = f"{c['round2Date']} {c['round2Time']}"
        st.metric("Next Interview", upcoming)
        st.markdown("</div>", unsafe_allow_html=True)

    # 2. Actionable Pipeline
    st.markdown("### 🚦 Candidate Stages")
    
    tabs = st.tabs(["1. Screening & Schedule", "2. Aptitude Results", "3. Round 2 Interviews"])
    
    # Tab 1: Schedule Aptitude
    with tabs[0]:
        for c in candidates:
            if c.get('status') == 'Screening':
                with st.container():
                    st.markdown(f"""
                    <div class='hireai-card' style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h3 style='margin:0;'>{c['name']}</h3>
                            <p style='color: #64748b; margin:0;'>{c['role']} • Resume Score: {c.get('score', 0)}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        d = st.date_input("Exam Date", key=f"d_{c['id']}")
                    with c2:
                        t = st.time_input("Exam Start Time", key=f"t_{c['id']}")
                    with c3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Schedule Exam", key=f"btn_{c['id']}"):
                            c['aptitudeDate'] = d.strftime("%Y-%m-%d")
                            c['aptitudeTime'] = t.strftime("%H:%M")
                            c['status'] = 'Aptitude Scheduled'
                            database.save_candidate(c)
                            st.toast(f"Exam scheduled! Email sent to {c['email']}.", icon="📧")
                            st.rerun()

    # Tab 2: View Results & Schedule Round 2
    with tabs[1]:
        completed = [c for c in candidates if c.get('aptitude_score') is not None]
        if not completed:
            st.info("No aptitude tests completed yet.")
        
        for c in completed:
            if c.get('status') != 'Interview Scheduled':
                is_passed = c['aptitude_score'] >= 50
                color = "#16a34a" if is_passed else "#dc2626"
                result_text = "PASSED" if is_passed else "FAILED"
                
                with st.container():
                    st.markdown(f"""
                    <div class='hireai-card'>
                        <div style='display: flex; justify-content: space-between;'>
                            <h3>{c['name']}</h3>
                            <div style='text-align: right;'>
                                <span style='font-size: 24px; font-weight: 900; color: {color}'>{c['aptitude_score']}%</span>
                                <span style='font-size: 12px; font-bold; color: {color}; background: {color}20; padding: 2px 6px; border-radius: 4px; vertical-align: middle; margin-left: 8px;'>{result_text}</span>
                                <p style='font-size: 10px; text-transform: uppercase;'>Score</p>
                            </div>
                        </div>
                        <p><strong>Role:</strong> {c['role']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if is_passed:
                        st.markdown("#### Schedule Round 2 Interview")
                        cc1, cc2, cc3 = st.columns([2, 2, 1])
                        with cc1:
                            r2d = st.date_input("Interview Date", key=f"r2d_{c['id']}")
                        with cc2:
                            r2t = st.time_input("Start Time", key=f"r2t_{c['id']}")
                        with cc3:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("Schedule Round 2", key=f"r2btn_{c['id']}"):
                                c['round2Date'] = r2d.strftime("%Y-%m-%d")
                                c['round2Time'] = r2t.strftime("%H:%M")
                                c['round2Link'] = generate_meeting_link()
                                c['status'] = 'Interview Scheduled'
                                database.save_candidate(c)
                                st.toast(f"Interview set! Invite sent to {c['email']}", icon="📅")
                                st.rerun()
                    else:
                        st.error("Candidate failed aptitude cutoff (< 50%). Cannot schedule Round 2.")

    # Tab 3: Upcoming Interviews
    with tabs[2]:
        interviews = [c for c in candidates if c.get('status') == 'Interview Scheduled']
        if not interviews:
            st.info("No upcoming interviews.")
        
        for c in interviews:
            st.markdown(f"""
            <div class='hireai-card' style='border-left: 5px solid #2563eb;'>
                <h3>{c['name']}</h3>
                <p>📅 {c['round2Date']} at {c['round2Time']}</p>
                <p>🔗 <a href='{c['round2Link']}' target='_blank'>{c['round2Link']}</a></p>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"Join Meeting with {c['name']}", c['round2Link'])

def view_interview_room():
    if not st.session_state.active_user:
        st.markdown("<h1>Candidate Login</h1>", unsafe_allow_html=True)
        st.markdown("<div class='hireai-card' style='max-width: 500px; margin: 0 auto;'>", unsafe_allow_html=True)
        key_input = st.text_input("Enter your 8-digit Access Key", placeholder="XXXX-0000")
        if st.button("LOGIN"):
            match = next((c for c in candidates if c.get('access_key') == key_input), None)
            if match:
                st.session_state.active_user = match
                st.rerun()
            else:
                st.error("Invalid key. Access Denied.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        user = st.session_state.active_user
        
        # --- VIEW 1: ROUND 2 INTERVIEW ---
        if user.get('status') == 'Interview Scheduled':
            st.markdown(f"<h1>Final Interview: {user['name']}</h1>", unsafe_allow_html=True)
            st.markdown(f"""
                <div class='hireai-card' style='text-align: center; padding: 40px;'>
                    <div style='font-size: 50px;'>🤝</div>
                    <h2>Congratulations! You passed the Aptitude Round.</h2>
                    <p>Your technical interview is scheduled for:</p>
                    <h3 style='color: #2563eb; font-size: 24px;'>{user['round2Date']} at {user['round2Time']}</h3>
                    <div style='margin-top: 30px;'>
                        <a href='{user['round2Link']}' target='_blank' style='background: #2563eb; color: white; padding: 15px 30px; border-radius: 12px; text-decoration: none; font-weight: bold;'>JOIN VIDEO MEETING NOW</a>
                    </div>
                    <p style='margin-top: 20px; font-size: 12px; color: #64748b;'>HR has been notified of your readiness.</p>
                </div>
            """, unsafe_allow_html=True)
            return

        # --- VIEW 2: APTITUDE EXAM GATING ---
        st.markdown(f"<h1>Aptitude Portal: {user['name']}</h1>", unsafe_allow_html=True)
        
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
            
            st.markdown(f"""
                <div class='hireai-card' style='text-align: center; border-left: 5px solid #f59e0b;'>
                    <h3>⏳ Exam Locked</h3>
                    <p>Your exam is scheduled for <strong>{scheduled_datetime_str}</strong>.</p>
                    <p style='font-size: 20px; font-weight: bold; color: #f59e0b;'>
                        Starts in: {diff.days}d {hours}h {mins}m
                    </p>
                    <p style='font-size: 12px; color: #94a3b8;'>Please refresh the page at the scheduled time.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Refresh Timer"):
                st.rerun()
            return

        # --- VIEW 3: COMPLETED STATE ---
        if user.get('aptitude_score') is not None:
             st.markdown(f"""
                <div class='hireai-card' style='text-align: center; padding: 50px;'>
                    <div style='font-size: 60px;'>🏆</div>
                    <h2 style='color: #2563eb;'>Exam Submitted</h2>
                    <p style='font-size: 18px; color: #64748b;'>Thank you. HR is reviewing your results.</p>
                    <div style='font-size: 40px; font-weight: 900; color: #0f172a; margin-top: 20px;'>{user['aptitude_score']}%</div>
                    <p class='hireai-label'>Final Score</p>
                    <p style='margin-top: 20px; font-size: 12px;'>You will receive an email if you are shortlisted for Round 2.</p>
                </div>
             """, unsafe_allow_html=True)
             return

        # --- VIEW 4: EXAM INTERFACE ---
        if 'aptitude_questions' not in st.session_state:
            st.markdown("""
                <div class='hireai-card'>
                    <h3>Assessment Instructions</h3>
                    <ul style='color: #475569; line-height: 1.8;'>
                        <li>This exam consists of <strong>20 Multiple Choice Questions</strong>.</li>
                        <li>Once you start, please complete all questions before submitting.</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("GENERATE & START EXAM"):
                with st.spinner(f"AI is generating a unique test for {user['role']} role..."):
                    st.session_state.aptitude_questions = generate_aptitude_questions(user['role'])
                    st.rerun()
        else:
            questions = st.session_state.aptitude_questions
            with st.form("exam_form"):
                user_answers = {}
                for i, q in enumerate(questions):
                    st.markdown(f"<div style='background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;'>", unsafe_allow_html=True)
                    st.markdown(f"<span class='hireai-label'>{q['category']}</span>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-weight: 700; font-size: 16px; margin: 8px 0;'>{i+1}. {q['question']}</p>", unsafe_allow_html=True)
                    
                    user_answers[i] = st.radio(
                        f"Select answer for question {i+1}", 
                        q['options'], 
                        key=f"q_{i}", 
                        label_visibility="collapsed"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                
                if st.form_submit_button("SUBMIT FINAL ANSWERS"):
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
