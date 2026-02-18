# 🎯 HireAI: Intelligent Recruitment Portal

HireAI is a high-performance, AI-driven recruitment platform that automates resume screening, aptitude testing, and interview scheduling using Google Gemini 2.5/3 models.

---

## 🚀 Quick Start Installation

Follow these steps to get HireAI up and running on your local machine or VPS.

### 1. Prerequisites
Ensure you have the following installed:
* **Python 3.10 or higher**
* **pip** (Python package manager)
* A terminal or command prompt

### 2. Clone the Repository
```bash
# Download the project files
git clone <your-repository-url>
cd hireai
```

### 3. Set Up Virtual Environment (Recommended)
```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 API Configuration

HireAI requires two external services to function at full capacity: **Google Gemini** (for AI Analysis) and **SendGrid** (for Automated Emails).

### Step 1: Google Gemini API Key
1. Go to the [Google AI Studio](https://aistudio.google.com/).
2. Create a new API Key.
3. Copy this key.

### Step 2: SendGrid API Key (Optional for Emails)
1. Sign up at [SendGrid](https://sendgrid.com/).
2. Create an **API Key** with "Full Access".
3. Verify a **Single Sender Identity** (the email address the system will "send from").

### Step 3: Configure Environment Variables
Create a file named `.env` in the root directory (or copy `.env.example`):

```ini
# Core AI Config
API_KEY=your_gemini_api_key_here

# Email Config (Optional)
SENDGRID_API_KEY=your_sendgrid_key_here
FROM_EMAIL=your_verified_sender_email@company.com

# Test Config
APTITUDE_TEST_DURATION_MINUTES=20
```

*Note: For Streamlit Cloud deployment, add these same keys to the "Secrets" section in the Streamlit dashboard.*

---

## 🏃 Running the Application

You can start the main portal using Streamlit:

```bash
streamlit run app.py
```

The application will typically be available at `http://localhost:8501`.

---

## 🛡️ Default Credentials

Once the app is running, navigate to the **HR Dashboard** in the sidebar.

| Username | Password | Role |
| :--- | :--- | :--- |
| `admin` | `admin123` | Super Admin |

> **Security Tip**: Change the admin password or create new recruiter accounts immediately under the **Manage Team** tab in the HR Dashboard.

---

## 🛠️ Troubleshooting

*   **Database Locked**: If you see SQLite locking errors, ensure only one instance of the app is writing to `hireai.db` at a time.
*   **AI Quota Exceeded**: If the screening fails, it may be due to Gemini API rate limits. The app includes an automatic retry logic, but you may need to wait 60 seconds.
*   **Emails not sending**: Ensure your `FROM_EMAIL` matches the verified sender in your SendGrid account exactly.

---

## 📦 Project Structure
* `app.py`: The main Streamlit interface.
* `database.py`: Handles local SQLite storage for jobs and candidates.
* `email_service.py`: Integration with SendGrid for automated notifications.
* `services/geminiService.ts`: (Used by the React fallback components).
