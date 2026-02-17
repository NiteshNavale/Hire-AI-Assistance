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

# --- LOAD ENVIRONMENT VARIABLES ---
# This ensures it works on local machines, VPS, and hosting panels using .env files
load_dotenv()

# Force reload of database module to pick up schema changes/new functions
# This fixes the "AttributeError: module 'database' has no attribute 'get_jobs'"
importlib.reload(database)

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
candidates = database.get_candidates()
# Load jobs from DB
jobs = database.get_jobs()

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
def screen_resume_ai(text, role_title, job_description, skills_required, min_experience):
    """
    Screens resume with temperature=0.0 and a fixed seed for deterministic results.
    Uses the specific Job Description provided by HR.
    """
    
    # Generate a deterministic integer seed from the content
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
    1. Check if the candidate matches the Minimum Experience. If they have less than {min_experience} years, the Score MUST be below 40.
    2. Check if the candidate has the Mandatory Skills ({skills_required}). If they miss key skills, deduct points significantly.
    3. Score from 0-100 based on strict evidence in the text.
    4. Provide a summary explaining the score, specifically mentioning if they met the experience and skill requirements.
    """
    
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0, # CRITICAL: Zero temperature ensures consistent/deterministic results
            seed=seed,       # CRITICAL: Fixed seed ensures reproducibility
            response_mime_type='application/json',
            response_schema={
                'type': 'OBJECT',
                'properties': {
                    'overallScore': {'type': 'INTEGER'},
                    'summary': {'type': 'STRING'},
                    'technicalMatch': {'type': 'INTEGER'}
                },
                'required': ['overallScore', 'summary', 'technicalMatch']
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
    
    # Reload jobs to ensure we have latest
    current_jobs = database.get_jobs()
    
    if not current_jobs:
        st.warning("No positions are currently open. Please check back later.")
        return

    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader("Application Form")
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email Address", placeholder="john@example.com")
            
            # Dynamic Dropdown based on DB jobs
            job_options = {j['title']: j for j in current_jobs}
            selected_role_title = st.selectbox("Apply for Role", list(job_options.keys()))
            
            # Show the description of selected job
            selected_job = job_options[selected_role_title]
            
            with st.expander("View Job Requirements"):
                st.markdown(f"**Required Experience:** {selected_job.get('min_experience', 0)}+ Years")
                if selected_job.get('skills'):
                    st.markdown(f"**Must-Have Skills:**")
                    for s in selected_job['skills'].split(','):
                        st.markdown(f"- {s}")
                st.markdown("---")
                st.write(selected_job['description'])

            resume = st.file_uploader("Upload Resume (TXT/PDF)", type=['txt', 'pdf'])
            
            if st.button("Submit Application", type="primary"):
                if name and email and resume:
                    with st.spinner("AI is rigorously analyzing your profile against specific job requirements..."):
                        try:
                            resume_text = resume.read().decode("utf-8", errors="ignore")
                            
                            # Pass specific JD, Skills and Exp to AI
                            analysis = screen_resume_ai(
                                resume_text, 
                                selected_role_title, 
                                selected_job['description'],
                                selected_job.get('skills', ''),
                                selected_job.get('min_experience', 0)
                            )
                            
                            access_key = generate_key()
                            c_id = str(uuid.uuid4())
                            
                            new_candidate = {
                                "id": c_id,
                                "name": name,
                                "email": email,
                                "role": selected_role_title, # Store the title
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
                                "round2Link": None,
                                "archived": False
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
                st.markdown("**Note:** This score is based strictly on the skills and experience required.")

def view_hr_dashboard():
    st.title("Recruiter Command Center")
    
    # Reload data
    active_candidates = [c for c in candidates if not c.get('archived')]
    archived_candidates = [c for c in candidates if c.get('archived')]
    
    tab_pipeline, tab_jobs, tab_archived = st.tabs([
        f"Active Pipeline ({len(active_candidates)})", 
        "Manage Jobs / JDs",
        f"Archived ({len(archived_candidates)})"
    ])
    
    # --- ACTIVE PIPELINE TAB ---
    with tab_pipeline:
        if not candidates:
            st.info("The pipeline is currently empty. Candidates will appear here once they apply.")
        else:
            # Metrics
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
                st.info("No active candidates.")
            else:
                # Table Header
                with st.container(border=True):
                    col_c, col_s, col_sc, col_a = st.columns([2.5, 1.5, 1, 2])
                    col_c.markdown("**Candidate**")
                    col_s.markdown("**Stage**")
                    col_sc.markdown("**Scores**")
                    col_a.markdown("**Action**")

                # Table Rows
                for c in active_candidates:
                    with st.container(border=True):
                        col_c, col_s, col_sc, col_a = st.columns([2.5, 1.5, 1, 2])
                        
                        # 1. Candidate Details
                        with col_c:
                            st.markdown(f"**{c['name']}**")
                            st.caption(f"{c['role']}")
                            st.caption(f"📧 {c['email']}")
                            st.caption("Access Key:")
                            st.code(c.get('access_key'), language="text")
                        
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
                            with st.popover("Why this score?"):
                                st.markdown(f"### Assessment for {c['name']}")
                                st.info(c.get('summary', 'No summary available.'))
                                if c.get('technical'):
                                    st.markdown(f"**Technical Match:** {c.get('technical')}/100")
                            
                            if c.get('aptitude_score') is not None:
                                st.markdown(f"Aptitude: **{c['aptitude_score']}**")
                            else:
                                st.markdown("Aptitude: --")

                        # 4. Actions
                        with col_a:
                            col_act_main, col_act_del = st.columns([4, 1])
                            with col_act_main:
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
                                elif c['status'] == 'Aptitude Scheduled':
                                    st.info("Waiting for exam...")
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
                                        st.error("Low Score")
                                elif c['status'] == 'Interview Scheduled':
                                    st.link_button("Join Meeting", c['round2Link'])
                            with col_act_del:
                                if st.button("🗑", key=f"archive_{c['id']}", help="Archive Candidate"):
                                    c['archived'] = True
                                    database.save_candidate(c)
                                    st.toast(f"Archived {c['name']}")
                                    st.rerun()

    # --- JOB MANAGEMENT TAB ---
    with tab_jobs:
        st.subheader("Manage Job Descriptions")
        st.markdown("Add roles with specific skills and experience requirements. The AI will strictly use these for screening.")
        
        with st.form("add_job_form"):
            col_j1, col_j2 = st.columns([1, 1])
            with col_j1:
                new_title = st.text_input("Job Title", placeholder="e.g. Senior Backend Engineer")
            with col_j2:
                new_exp = st.number_input("Minimum Experience (Years)", min_value=0, max_value=20, step=1, value=2)

            # Predefined common skills list + dynamic addition
            common_skills = [
                "Python", "Java", ".NET", ".NET Core", "C#", "JavaScript", "TypeScript", "React", "Angular", "Vue.js",
                "Node.js", "Django", "Flask", "FastAPI", "Spring Boot", "SQL", "PostgreSQL", "MongoDB", "AWS", "Azure",
                "GCP", "Docker", "Kubernetes", "CI/CD", "Git", "Machine Learning", "Data Analysis"
            ]
            new_skills = st.multiselect("Required Skills (Select all that apply)", options=common_skills)
            
            new_desc = st.text_area("Detailed Job Description", height=200, placeholder="Paste the full job description here. Include culture, soft skills, and day-to-day responsibilities.")
            
            if st.form_submit_button("Create Job Posting", type="primary"):
                if new_title and new_desc and new_skills:
                    database.save_job(new_title, new_desc, new_skills, new_exp)
                    st.success(f"Job '{new_title}' created successfully!")
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
                        # Show badges for requirements
                        st.markdown(f"**Experience:** {job.get('min_experience', 0)}+ Years")
                        if job.get('skills'):
                            skills_list = job['skills'].split(',')
                            # Display skills as tags
                            tags_html = " ".join([f"<span style='background-color:#e0f2fe; color:#0284c7; padding:2px 8px; border-radius:12px; font-size:12px; font-weight:600; margin-right:4px;'>{s}</span>" for s in skills_list])
                            st.markdown(tags_html, unsafe_allow_html=True)
                        
                        with st.expander("Show Detailed Description"):
                            st.write(job['description'])
                    with col_j2:
                        if st.button("Delete", key=f"del_job_{job['id']}"):
                            database.delete_job(job['id'])
                            st.rerun()

    # --- ARCHIVED TAB ---
    with tab_archived:
        if not archived_candidates:
            st.info("No archived candidates.")
        else:
            for c in archived_candidates:
                with st.container(border=True):
                    col_ac, col_as, col_arest = st.columns([3, 2, 1])
                    with col_ac:
                        st.markdown(f"**{c['name']}** (Archived)")
                        st.caption(f"{c['role']}")
                    with col_as:
                        st.caption(f"Last Status: {c['status']}")
                        st.caption(f"Score: {c.get('score', 0)}")
                    with col_arest:
                        if st.button("Restore", key=f"restore_{c['id']}"):
                            c['archived'] = False
                            database.save_candidate(c)
                            st.toast(f"Restored {c['name']}")
                            st.rerun()

def view_interview_room():
    if not st.session_state.active_user:
        st.title("Candidate Login")
        col_c, _ = st.columns([1, 1])
        with col_c:
            with st.container(border=True):
                key_input = st.text_input("Enter your 8-digit Access Key", placeholder="XXXX-0000")
                if st.button("Login to Portal", type="primary"):
                    # Only check non-archived candidates for login
                    match = next((c for c in candidates if c.get('access_key') == key_input and not c.get('archived')), None)
                    if match:
                        st.session_state.active_user = match
                        st.rerun()
                    else:
                        st.error("Invalid key or account archived.")
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
