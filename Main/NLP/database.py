# database.py
import sqlite3
from datetime import datetime
import json
from pathlib import Path

# Database file location
DB_PATH = Path(__file__).parent / "tos_research.db"

def init_database():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT UNIQUE NOT NULL,
            tos_id TEXT NOT NULL,
            tos_title TEXT NOT NULL,
            condition_group TEXT NOT NULL,
            tos_length INTEGER NOT NULL,
            time_started TIMESTAMP NOT NULL,
            time_ended TIMESTAMP,
            total_reading_time INTEGER,
            time_to_bottom INTEGER,
            time_before_summary INTEGER,
            did_read_complete BOOLEAN,
            max_scroll_depth REAL,
            scroll_behavior TEXT,
            summary_generated BOOLEAN,
            summary_generated_at TIMESTAMP,
            risk_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Scroll events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scroll_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            scroll_depth REAL NOT NULL,
            scroll_position INTEGER NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    ''')
    
    # Clause clicks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clause_clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            category TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            position_start INTEGER NOT NULL,
            position_end INTEGER NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    ''')
    
    # Detected categories table (for each session)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detected_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            category TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def create_user(name: str) -> int:
    """Create a new user and return their ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user_by_name(name: str):
    """Get user by name or create if doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    else:
        # Create new user
        user_id = create_user(name)
        return {"id": user_id, "name": name}

def save_session_data(user_id: int, metrics: dict):
    """Save session metrics to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert session
    cursor.execute('''
        INSERT INTO sessions (
            user_id, session_id, tos_id, tos_title, condition_group, tos_length,
            time_started, time_ended, total_reading_time, time_to_bottom, 
            time_before_summary, did_read_complete, max_scroll_depth, 
            scroll_behavior, summary_generated, summary_generated_at, risk_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        metrics.get('sessionId'),
        metrics.get('tosId'),
        metrics.get('tosTitle'),
        metrics.get('conditionGroup'),
        metrics.get('tosLength'),
        metrics.get('timeStarted'),
        metrics.get('timeEnded'),
        metrics.get('totalReadingTime'),
        metrics.get('timeToBottom'),
        metrics.get('timeBeforeSummary'),
        metrics.get('didReadComplete'),
        metrics.get('maxScrollDepth'),
        metrics.get('scrollBehavior'),
        metrics.get('summaryGenerated'),
        metrics.get('summaryGeneratedAt'),
        metrics.get('riskScore')
    ))
    
    session_id = metrics.get('sessionId')
    
    # Insert scroll events
    for event in metrics.get('scrollEvents', []):
        cursor.execute('''
            INSERT INTO scroll_events (session_id, timestamp, scroll_depth, scroll_position)
            VALUES (?, ?, ?, ?)
        ''', (session_id, event['timestamp'], event['scrollDepth'], event['scrollPosition']))
    
    # Insert clause clicks
    for click in metrics.get('clausesClicked', []):
        cursor.execute('''
            INSERT INTO clause_clicks (session_id, category, timestamp, position_start, position_end)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session_id,
            click['category'],
            click['timestamp'],
            click['position']['start'],
            click['position']['end']
        ))
    
    # Insert detected categories
    for category in metrics.get('detectedCategories', []):
        cursor.execute('''
            INSERT INTO detected_categories (session_id, category)
            VALUES (?, ?)
        ''', (session_id, category))
    
    conn.commit()
    conn.close()

def get_user_sessions(user_id: int):
    """Get all sessions for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions

def export_all_data_csv():
    """Export all data to CSV format (for analysis)"""
    import csv
    from io import StringIO
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all sessions with user names
    cursor.execute('''
        SELECT 
            u.name as user_name,
            s.*
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.created_at
    ''')
    
    sessions = cursor.fetchall()
    conn.close()
    
    if not sessions:
        return None
    
    # Convert to CSV
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=sessions[0].keys())
    writer.writeheader()
    for session in sessions:
        writer.writerow(dict(session))
    
    return output.getvalue()

# Initialize database when module is imported
init_database()