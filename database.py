
import sqlite3
import json
import os
import uuid

# Use absolute path for DB to avoid Current Working Directory issues on some hosting panels
DB_FOLDER = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DB_FOLDER, "hireai.db")

def init_db():
    """Initialize the SQLite database with users, candidates, and jobs tables."""
    # Timeout added to prevent locking
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    
    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    
    # Check if 'email' column exists in users, if not, add it (Migration)
    try:
        c.execute("SELECT email FROM users LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE users ADD COLUMN email TEXT")

    # Candidates Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            data JSON NOT NULL
        )
    ''')

    # Jobs Table - Initialize
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            skills TEXT,
            min_experience INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- MIGRATION LOGIC FOR EXISTING DATABASES ---
    # Check if 'skills' column exists, if not, add it
    try:
        c.execute("SELECT skills FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE jobs ADD COLUMN skills TEXT")
        
    # Check if 'min_experience' column exists, if not, add it
    try:
        c.execute("SELECT min_experience FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE jobs ADD COLUMN min_experience INTEGER")
    
    # Create default admin if not exists
    c.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', ('admin', 'admin123', 'admin@hireai.com'))
        
    conn.commit()
    conn.close()

def create_user(username, password, email=""):
    """Create a new user. Returns True if successful, False if username exists."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, password, email))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def get_users():
    """Retrieve all users."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_user(username, email, password):
    """Update user email and password."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    c.execute("UPDATE users SET email = ?, password = ? WHERE username = ?", (email, password, username))
    conn.commit()
    conn.close()

def delete_user(username):
    """Delete a user."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def get_candidates():
    """Retrieve all candidates as a list of dictionaries."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT data FROM candidates")
    rows = c.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        try:
            results.append(json.loads(row['data']))
        except:
            continue
    return results

def save_candidate(candidate):
    """Insert or Update a candidate."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    
    # Ensure ID exists
    if 'id' not in candidate:
        candidate['id'] = str(uuid.uuid4())
    
    c.execute(
        "INSERT OR REPLACE INTO candidates (id, data) VALUES (?, ?)", 
        (candidate['id'], json.dumps(candidate))
    )
    conn.commit()
    conn.close()
    return candidate

def bulk_save_candidates(candidates):
    """Save a list of candidates (e.g. from React sync)."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    for cand in candidates:
        if 'id' not in cand:
            cand['id'] = str(uuid.uuid4())
        c.execute(
            "INSERT OR REPLACE INTO candidates (id, data) VALUES (?, ?)", 
            (cand['id'], json.dumps(cand))
        )
    conn.commit()
    conn.close()

def login_user(username, password):
    """Authenticate user."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

# --- JOB MANAGEMENT FUNCTIONS ---
def get_jobs():
    """Retrieve all job descriptions."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_job(title, description, skills=None, min_experience=0):
    """Create a new job posting with skills and experience."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    job_id = str(uuid.uuid4())
    
    # Convert list of skills to comma-separated string if needed
    skills_str = skills if isinstance(skills, str) else ",".join(skills) if skills else ""
    
    c.execute(
        "INSERT INTO jobs (id, title, description, skills, min_experience) VALUES (?, ?, ?, ?, ?)", 
        (job_id, title, description, skills_str, min_experience)
    )
    conn.commit()
    conn.close()
    return job_id

def delete_job(job_id):
    """Delete a job posting."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    c.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()

def bulk_delete_candidates(candidate_ids):
    """Delete multiple candidates by ID."""
    if not candidate_ids:
        return
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    # Create placeholders for the list
    placeholders = ','.join('?' * len(candidate_ids))
    sql = f"DELETE FROM candidates WHERE id IN ({placeholders})"
    c.execute(sql, candidate_ids)
    conn.commit()
    conn.close()

# Init DB when imported to ensure file exists immediately
init_db()
