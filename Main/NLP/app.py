# app.py - Updated with user tracking and database
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, PlainTextResponse
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from nlp_service import analyse_text
import database as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",  # Angular dev server
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Request/Response Models =====

class SummRequest(BaseModel):
    text: str
    num_sentences: int = 6
    abstractive: bool = False

    @validator('text')
    def validate_text(cls, v):
        if len(v) > 500_000:
            raise ValueError('Text exceeds maximum length of 500,000 characters')
        if len(v.strip()) < 50:
            raise ValueError('Text too short for meaningful analysis')
        return v

    @validator('num_sentences')
    def validate_num_sentences(cls, v):
        if v < 1 or v > 30:
            raise ValueError('num_sentences must be between 1 and 30')
        return v

class UserCreate(BaseModel):
    name: str

class MetricsSave(BaseModel):
    userId: str  # User's name
    sessionId: str
    tosId: str
    tosTitle: str
    conditionGroup: str
    tosLength: int
    timeStarted: str
    timeEnded: Optional[str] = None
    totalReadingTime: Optional[int] = None
    timeToBottom: Optional[int] = None
    timeBeforeSummary: Optional[int] = None
    didReadComplete: bool
    maxScrollDepth: float
    scrollBehavior: str
    scrollUpCount: int = 0
    reReadSections: int = 0
    totalPauseTime: int = 0
    summaryGenerated: bool
    summaryGeneratedAt: Optional[str] = None
    summaryViewDuration: Optional[int] = None
    riskScore: Optional[int] = None
    scrollEvents: List[Dict[str, Any]] = []
    pauseEvents: List[Dict[str, Any]] = []
    clausesClicked: List[Dict[str, Any]] = []
    hoverEvents: List[Dict[str, Any]] = []
    detectedCategories: List[str] = []

# ===== NLP Endpoints =====

# Whitelist of allowed ToS filenames (without extension)
ALLOWED_TOS_FILES = {
    'ecommerce_tos', 'cloudstorage_tos', 'socialmedia_tos',
    'education_tos', 'fitness_tos', 'musicstreaming_tos',
}

@app.get("/api/tos/{filename}", response_class=PlainTextResponse)
def get_tos_file(filename: str):
    """Serve a ToS text file by name (without .txt extension)."""
    if filename not in ALLOWED_TOS_FILES:
        raise HTTPException(status_code=404, detail="ToS file not found")
    
    filepath = os.path.join(os.path.dirname(__file__), "tos_documents", f"{filename}.txt")
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="ToS file not found")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/summarize")
def summarize(req: SummRequest):
    """
    Analyze Terms of Service text and return:
    - Extractive summary (key bullets)
    - Grouped clauses by category
    - Risk score
    - Detected clauses with context
    - Keywords
    """
    return analyse_text(
        req.text, 
        num_sentences=req.num_sentences, 
        do_abstractive=req.abstractive
    )

# ===== User Management Endpoints =====

@app.post("/api/users")
def create_or_get_user(user: UserCreate):
    """
    Create a new user - returns error if name already exists
    """
    # Check if name already exists
    if db.is_user_name_taken(user.name):
        raise HTTPException(
            status_code=400, 
            detail="Name already exists. Please choose a different name."
        )
    
    # Create new user
    user_id = db.create_user(user.name)
    return {
        "userId": user_id,
        "name": user.name,
        "message": "User created"
    }

@app.get("/api/users/{user_name}")
def get_user(user_name: str):
    """
    Get user information by name
    """
    user_data = db.get_user_by_name(user_name)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return user_data

# ===== Metrics Endpoints =====

@app.post("/api/metrics")
def save_metrics(metrics: MetricsSave):
    """
    Save user session metrics to database
    """
    try:
        # Get user by name
        user_data = db.get_user_by_name(metrics.userId)
        user_id = user_data["id"]
        
        # Convert to dict for database
        metrics_dict = metrics.dict()
        
        # Save to database
        db.save_session_data(user_id, metrics_dict)
        
        return {
            "success": True,
            "message": "Metrics saved successfully",
            "userId": user_id,
            "sessionId": metrics.sessionId
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving metrics: {str(e)}")

@app.get("/api/metrics/user/{user_name}")
def get_user_metrics(user_name: str):
    """
    Get all session metrics for a specific user
    """
    user_data = db.get_user_by_name(user_name)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    sessions = db.get_user_sessions(user_data["id"])
    return {
        "user": user_data,
        "sessions": sessions,
        "total_sessions": len(sessions)
    }

@app.get("/api/export/csv")
def export_csv():
    """
    Export all metrics data as CSV for analysis
    """
    csv_data = db.export_all_data_csv()
    if not csv_data:
        raise HTTPException(status_code=404, detail="No data to export")
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tos_research_data.csv"}
    )

# ===== Utility Endpoints =====

@app.get("/")
def root():
    return {
        "message": "ToS NLP API with User Tracking",
        "docs": "/docs",
        "version": "2.0.0",
        "database": str(db.DB_PATH)
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }

@app.get("/api/stats")
def get_stats():
    """
    Get overall statistics
    """
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    # Count users
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()["count"]
    
    # Count sessions
    cursor.execute("SELECT COUNT(*) as count FROM sessions")
    session_count = cursor.fetchone()["count"]
    
    # Count scroll events
    cursor.execute("SELECT COUNT(*) as count FROM scroll_events")
    scroll_count = cursor.fetchone()["count"]
    
    # Count clause clicks
    cursor.execute("SELECT COUNT(*) as count FROM clause_clicks")
    click_count = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "total_users": user_count,
        "total_sessions": session_count,
        "total_scroll_events": scroll_count,
        "total_clause_clicks": click_count
    }