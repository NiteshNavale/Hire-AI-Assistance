# 🎯 PROJECT DOCUMENTATION: HireAI Recruitment Assistant

## 1. Executive Summary
**HireAI** is a state-of-the-art recruitment automation platform. It leverages the **Google Gemini 3** Large Language Model (LLM) to perform objective resume screening, generate role-specific aptitude tests, and manage multi-stage interview pipelines. The system is designed to reduce bias, decrease "time-to-hire," and provide candidates with instant feedback through a gamified interface.

---

## 2. Technical Stack
| Component | Technology |
| :--- | :--- |
| **Backend Framework** | Streamlit (Python 3.10+) |
| **AI Engine** | Google Gemini API (@google/genai) |
| **Database** | SQLite3 (Relational) |
| **Email Service** | SendGrid API |
| **Styling** | Tailwind CSS / Streamlit Custom CSS |
| **Visualization** | Plotly & Pandas |

---

## 3. System Prerequisites
Before beginning the installation, ensure the following environment is prepared:
1. **Python 3.10 or 3.11** installed.
2. **Pip** (Python Package Manager).
3. **Google Cloud Account** (for Gemini API).
4. **SendGrid Account** (for automated email notifications).

---

## 4. Step-by-Step Installation Guide

### Step 1: Environment Setup
Open your terminal and execute the following commands to isolate the project environment:
```bash
# Create a virtual environment
python -m venv venv

# Activate the environment (Windows)
venv\Scripts\activate

# Activate the environment (Mac/Linux)
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### Step 2: API Key Acquisition
#### A. Google Gemini API (Core Brain)
1. Visit the [Google AI Studio](https://aistudio.google.com/).
2. Navigate to "Get API Key".
3. Create a key in a new or existing project.
4. Copy the key for use in the `.env` file.

#### B. SendGrid API (Email Automation)
1. Sign up at [SendGrid.com](https://sendgrid.com/).
2. Go to **Settings > API Keys** and generate a key with "Full Access".
3. **Critical**: Go to **Settings > Sender Authentication** and verify a "Single Sender". The email you verify here MUST match the `FROM_EMAIL` in your settings.

---

## 5. Configuration & Security
Create a `.env` file in the project root directory. This file stores your private credentials securely.

| Key | Description | Example Value |
| :--- | :--- | :--- |
| `API_KEY` | Google Gemini API Key | `AIzaSyB...` |
| `SENDGRID_API_KEY` | SendGrid Integration Key | `SG.xyz...` |
| `FROM_EMAIL` | Verified Sender Email | `hr@company.com` |
| `TEST_DURATION` | Minutes for Aptitude Exam | `20` |

---

## 6. Application Launch
To start the application, run the following command:
```bash
streamlit run app.py
```
The server will initialize the SQLite database (`hireai.db`) automatically and host the portal at `http://localhost:8501`.

---

## 7. User Workflows

### 7.1 Recruiter (HR) Portal
*   **Initial Login**: Use `admin` / `admin123`.
*   **Job Management**: Define roles, required skills, and minimum experience.
*   **Pipeline Management**: 
    *   Review AI-screened candidates.
    *   Schedule Aptitude Exams.
    *   Review exam scores and schedule Video Interviews.
    *   Issue Selection/Joining letters.

### 7.2 Candidate Portal
*   **Application**: Upload resume and fill basic details.
*   **Access Key**: Every candidate receives a unique 8-digit key (e.g., `ABCD-1234`).
*   **Assessment**: Candidates use their key to log in and take a timed, AI-generated aptitude test based on their specific role.

---

## 8. Troubleshooting & Maintenance
*   **Database Locking**: SQLite may lock if multiple write operations happen simultaneously. The app includes a 30-second timeout retry logic to handle this.
*   **Email Simulation**: If SendGrid is not configured, the system defaults to "Simulation Mode," printing the email content to the terminal console instead of sending a live message.
*   **AI Rate Limits**: If receiving `429: Resource Exhausted` errors, the app will automatically attempt an exponential backoff (20s, 40s, 60s).
