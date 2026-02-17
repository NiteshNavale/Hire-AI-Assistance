
import sqlite3
import json
import os
import uuid

# Use absolute path for DB to avoid Current Working Directory issues on some hosting panels
DB_FOLDER = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DB_FOLDER, "hireai.db")

def init_db():
    """Initialize the SQLite database with users and candidates tables."""
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
    
    # Candidates Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            data JSON NOT NULL
        )
    ''')
    
    # Create default admin if not exists
    c.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', 'admin123'))
        
    conn.commit()
    conn.close()

def create_user(username, password):
    """Create a new user. Returns True if successful, False if username exists."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

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
    
    # Normalize access key if present (React uses accessKey, Python uses access_key)
    # We keep the JSON as is, just ensuring we have a stable ID.
    
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

# Init DB when imported to ensure file exists immediately
init_db()
