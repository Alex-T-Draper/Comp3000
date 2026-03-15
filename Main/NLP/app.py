# app.py - Updated with user tracking and database
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from nlp_service import analyse_text
import database as db

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
    summaryGenerated: bool
    summaryGeneratedAt: Optional[str] = None
    riskScore: Optional[int] = None
    scrollEvents: List[Dict[str, Any]] = []
    clausesClicked: List[Dict[str, Any]] = []
    detectedCategories: List[str] = []

# ===== NLP Endpoints =====

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
    Create a new user or get existing user by name
    """
    user_data = db.get_user_by_name(user.name)
    return {
        "userId": user_data["id"],
        "name": user_data["name"],
        "message": "User found" if user_data else "User created"
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