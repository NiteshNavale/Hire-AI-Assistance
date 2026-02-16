
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import time
from datetime import datetime
import random
import string
from google import genai
from google.genai import types

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
        
        /* Global Background & Font */
        .stApp {
            background-color: #f8fafc;
            font-family: 'Inter', sans-serif;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
        }
        
        /* Card Styling */
        .hireai-card {
            background: white;
            padding: 24px;
            border-radius: 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
        
        .hireai-label {
            font-size: 10px;
            font-weight: 900;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        /* Buttons */
        .stButton>button {
            width: 100%;
            border-radius: 12px;
            font-weight: 700;
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 12px;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #1d4ed8;
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
        }

        /* Metrics */
        [data-testid="stMetricValue"] {
            font-weight: 900;
            color: #1e293b;
        }
        
        /* Headers */
        h1, h2, h3 {
            font-weight: 900 !important;
            letter-spacing: -1px !important;
            color: #0f172a !important;
        }

        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

apply_custom_styles()

# --- INITIALIZATION ---
if 'candidates' not in st.session_state:
    st.session_state.candidates = []
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

def generate_key():
    return f"{''.join(random.choices(string.ascii_uppercase, k=4))}-{''.join(random.choices(string.digits, k=4))}"

# --- VIEWS ---
def sidebar_nav():
    with st.sidebar:
        st.markdown("""
            <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 30px;'>
                <div style='background: #2563eb; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 900;'>H</div>
                <h2 style='margin: 0; font-size: 24px;'>HireAI</h2>
            </div>
        """, unsafe_allow_html=True)
        
        choice = st.radio("MAIN NAVIGATION", 
                         ["Candidate Portal", "Interview Room", "HR Dashboard"],
                         label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown("<p class='hireai-label'>System Status</p>", unsafe_allow_html=True)
        st.success("AI Core: Connected")
        st.info("Proctoring: Active")
        
        if st.session_state.active_user:
            if st.button("Logout Candidate"):
                st.session_state.active_user = None
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
                    resume_text = resume.read().decode("utf-8", errors="ignore")
                    analysis = screen_resume_ai(resume_text, role)
                    access_key = generate_key()
                    
                    new_candidate = {
                        "name": name,
                        "email": email,
                        "role": role,
                        "score": analysis['overallScore'],
                        "technical": analysis['technicalMatch'],
                        "summary": analysis['summary'],
                        "access_key": access_key,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }
                    st.session_state.candidates.append(new_candidate)
                    st.balloons()
                    st.success("Profile Screened!")
            else:
                st.warning("Please fill all fields.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        if st.session_state.candidates and st.session_state.candidates[-1]['name'] == name:
            c = st.session_state.candidates[-1]
            st.markdown(f"""
                <div style='background: #eff6ff; border: 2px dashed #3b82f6; padding: 30px; border-radius: 24px; text-align: center;'>
                    <p class='hireai-label' style='color: #3b82f6;'>Your Interview Key</p>
                    <h1 style='font-size: 48px; color: #1d4ed8; margin: 10px 0;'>{c['access_key']}</h1>
                    <p style='font-size: 14px; color: #1e40af;'>Save this key! You will need it to enter the secure proctored round.</p>
                </div>
            """, unsafe_allow_html=True)

def view_hr_dashboard():
    st.markdown("<h1>Recruiter Command Center</h1>", unsafe_allow_html=True)
    
    if not st.session_state.candidates:
        st.info("The pipeline is currently empty.")
        return

    df = pd.DataFrame(st.session_state.candidates)
    
    # Hero Metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("<div class='hireai-card'>", unsafe_allow_html=True)
        st.metric("Total Candidates", len(df))
        st.markdown("</div>", unsafe_allow_html=True)
    with m2:
        st.markdown("<div class='hireai-card'>", unsafe_allow_html=True)
        st.metric("Avg Score", f"{int(df['score'].mean())}%")
        st.markdown("</div>", unsafe_allow_html=True)
    with m3:
        st.markdown("<div class='hireai-card'>", unsafe_allow_html=True)
        st.metric("Shortlisted", len(df[df['score'] > 70]))
        st.markdown("</div>", unsafe_allow_html=True)

    # Data & Visuals
    st.markdown("### Talent Pipeline")
    st.dataframe(df[['name', 'role', 'score', 'access_key', 'date']], use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(df, x='name', y='score', color='score', color_continuous_scale="Viridis", title="Candidate Rankings")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = px.pie(df, names='role', title="Department Split", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)

def view_interview_room():
    if not st.session_state.active_user:
        st.markdown("<h1>Secure Proctoring Portal</h1>", unsafe_allow_html=True)
        st.markdown("<div class='hireai-card' style='max-width: 500px; margin: 0 auto;'>", unsafe_allow_html=True)
        key_input = st.text_input("Enter your 8-digit Access Key", placeholder="XXXX-0000")
        if st.button("VERIFY IDENTITY"):
            match = next((c for c in st.session_state.candidates if c['access_key'] == key_input), None)
            if match:
                st.session_state.active_user = match
                st.rerun()
            else:
                st.error("Invalid key. Access Denied.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        user = st.session_state.active_user
        st.markdown(f"<h1>Proctored Round: {user['name']}</h1>", unsafe_allow_html=True)
        
        chat_col, feed_col = st.columns([2, 1])
        
        with feed_col:
            st.markdown("<div class='hireai-card' style='background: #0f172a;'>", unsafe_allow_html=True)
            st.camera_input("Identity Verification", key="proctor_cam")
            st.markdown("""
                <div style='color: #94a3b8; font-size: 11px; margin-top: 15px;'>
                    <b>PROCTOR LOG:</b><br>
                    • Biometric sync: OK<br>
                    • Audio baseline: Detected<br>
                    • Browser state: LOCKED
                </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with chat_col:
            if 'messages' not in st.session_state:
                st.session_state.messages = [{"role": "assistant", "content": f"Hello {user['name']}. I am your HireAI interviewer. Let's begin the technical round."}]
            
            for m in st.session_state.messages:
                with st.chat_message(m['role']):
                    st.write(m['content'])
            
            if prompt := st.chat_input("Explain your experience with microservices..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("AI Evaluator is listening..."):
                    time.sleep(1.5)
                    st.session_state.messages.append({"role": "assistant", "content": "Interesting point. How would you handle state management in that scenario?"})
                    st.rerun()

# --- MAIN APP ROUTING ---
nav_choice = sidebar_nav()

if nav_choice == "Candidate Portal":
    view_candidate_portal()
elif nav_choice == "HR Dashboard":
    view_hr_dashboard()
elif nav_choice == "Interview Room":
    view_interview_room()
