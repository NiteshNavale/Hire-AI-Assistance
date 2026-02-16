
import os
import json
import uuid
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

app = FastAPI()

# Enable CORS for easier local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "candidates_db.json"
USERS_FILE = "users_db.json"

# Mock Auth Token storage
active_tokens = set()

def load_json(filename, default=[]):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                content = f.read()
                return json.loads(content) if content else default
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return default
    return default

def save_json(filename, data):
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

# Initialize default admin
def init_users():
    users = load_json(USERS_FILE, [])
    if not any(u['username'] == 'admin' for u in users):
        print("Initializing default user: admin / admin123")
        users.append({"username": "admin", "password": "admin123"})
        save_json(USERS_FILE, users)
    else:
        print("User database loaded successfully.")

@app.post("/api/login")
async def login(request: Request):
    print("--- Login Request Received ---")
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        print(f"Attempting login for user: {username}")
        
        users = load_json(USERS_FILE, [])
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        
        if user:
            token = str(uuid.uuid4())
            active_tokens.add(token)
            print(f"Login successful for {username}. Token generated.")
            return {"status": "success", "token": token, "username": username}
        else:
            print(f"Login failed for {username}: Invalid credentials.")
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        print(f"Critical error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/candidates")
async def get_candidates(authorization: Optional[str] = Header(None)):
    token = (authorization or "").replace("Bearer ", "")
    if not token or token not in active_tokens:
         print(f"Unauthorized access attempt to /api/candidates. Token: {token}")
         raise HTTPException(status_code=403, detail="Not authorized")
    return load_json(DB_FILE, [])

@app.post("/api/candidates")
async def update_candidates(request: Request, authorization: Optional[str] = Header(None)):
    # We allow the candidate portal to post without a token for new apps
    # but in a production environment, we'd separate 'apply' from 'bulk update'
    try:
        data = await request.json()
        save_json(DB_FILE, data)
        return {"status": "success"}
    except Exception as e:
        print(f"Error updating candidates: {e}")
        raise HTTPException(status_code=500, detail="Failed to save data")

@app.get("/")
async def read_index():
    return FileResponse("index.html")

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    init_users()
    if not os.path.exists(DB_FILE):
        save_json(DB_FILE, [])
    print("\n------------------------------------------------")
    print("HireAI Assistant starting on http://localhost:8000")
    print("Default Login: admin / admin123")
    print("------------------------------------------------\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
