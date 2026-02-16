
import os
import uuid
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Any, Dict
from pydantic import BaseModel
import uvicorn
import database

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Explicit DB Initialization on Startup
@app.on_event("startup")
def startup_event():
    database.init_db()

# Models for Request Bodies
class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreateRequest(BaseModel):
    username: str
    password: str

# Mock Auth Token storage
active_tokens = set()

# NOTE: We use 'def' instead of 'async def' for routes that call the synchronous database module.
# This ensures FastAPI runs them in a thread pool, preventing the event loop from blocking.

@app.post("/api/login")
def login(data: LoginRequest):
    print(f"--- Login Request Received for {data.username} ---")
    
    # HARDCODED AUTHENTICATION (Bypassing Database)
    # This prevents DB locking issues from affecting access to the portal.
    if data.username == "admin" and data.password == "admin123":
        token = str(uuid.uuid4())
        active_tokens.add(token)
        print(f"Login successful for {data.username}.")
        return {"status": "success", "token": token, "username": data.username}
    
    print(f"Login failed for {data.username}.")
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/users")
def create_user(data: UserCreateRequest, authorization: Optional[str] = Header(None)):
    # User management is disabled when using hardcoded auth
    raise HTTPException(status_code=501, detail="User management is disabled in this mode.")

@app.get("/api/candidates")
def get_candidates(authorization: Optional[str] = Header(None)):
    token = (authorization or "").replace("Bearer ", "")
    return database.get_candidates()

@app.post("/api/candidates")
def update_candidates(request: Request, candidate_data: Any = None):
    pass

@app.post("/api/candidates")
async def update_candidates_async(request: Request, authorization: Optional[str] = Header(None)):
    try:
        data = await request.json()
        if isinstance(data, list):
            database.bulk_save_candidates(data)
        else:
            database.save_candidate(data)
        return {"status": "success"}
    except Exception as e:
        print(f"Error updating candidates: {e}")
        raise HTTPException(status_code=500, detail="Failed to save data")

@app.get("/")
async def read_index():
    return FileResponse("index.html")

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    # If run directly (not via uvicorn command line), we also init db
    database.init_db()
    print("HireAI Server running...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
