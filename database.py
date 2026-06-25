import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'medical.db')

def get_db_connection():
    """Establishes a connection to the SQLite database with row factory and foreign keys enabled."""
    db_dir = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database, creating required tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Reports Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_name TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL,
            extracted_text TEXT,
            summary TEXT,
            detailed_summary TEXT,
            deficiency_summary TEXT,
            key_findings TEXT, -- JSON string
            severity TEXT,
            alerts TEXT, -- JSON string
            suggestions TEXT, -- JSON string
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Database migration: add new columns if they do not exist
    cursor.execute("PRAGMA table_info(reports)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'suggestions' not in columns:
        cursor.execute("ALTER TABLE reports ADD COLUMN suggestions TEXT DEFAULT '[]'")
        print("Migrated database: added suggestions column to reports table")
    if 'deficiency_summary' not in columns:
        cursor.execute("ALTER TABLE reports ADD COLUMN deficiency_summary TEXT DEFAULT ''")
        print("Migrated database: added deficiency_summary column to reports table")
    if 'detailed_summary' not in columns:
        cursor.execute("ALTER TABLE reports ADD COLUMN detailed_summary TEXT DEFAULT ''")
        print("Migrated database: added detailed_summary column to reports table")
        
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
