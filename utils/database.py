import sqlite3
import os
from .config import DB_PATH

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return conn

def setup_database():
    """Creates the necessary tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Job Descriptions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            original_text TEXT,
            summary TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Candidates Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE, -- Email should be unique
            phone TEXT,
            cv_filename TEXT NOT NULL,
            cv_text TEXT,
            extracted_skills TEXT,
            extracted_experience TEXT,
            extracted_education TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Matches Table (Linking JDs and Candidates)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jd_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            match_score INTEGER,
            is_shortlisted BOOLEAN DEFAULT FALSE,
            interview_email_sent BOOLEAN DEFAULT FALSE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (jd_id) REFERENCES job_descriptions (id),
            FOREIGN KEY (candidate_id) REFERENCES candidates (id),
            UNIQUE(jd_id, candidate_id) -- Ensure only one match per JD/candidate pair
        )
    ''')

    conn.commit()
    conn.close()
    print("Database setup complete.")

def add_job_description(title, original_text, summary):
    """Adds a new job description and its summary to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO job_descriptions (title, original_text, summary)
            VALUES (?, ?, ?)
        ''', (title, original_text, summary))
        jd_id = cursor.lastrowid
        conn.commit()
        return jd_id
    except sqlite3.Error as e:
        print(f"Database error adding JD: {e}")
        return None
    finally:
        conn.close()

def add_candidate(name, email, phone, cv_filename, cv_text, skills, experience, education):
    """Adds a candidate, ensuring email uniqueness."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO candidates (name, email, phone, cv_filename, cv_text, extracted_skills, extracted_experience, extracted_education)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                name=excluded.name,
                phone=excluded.phone,
                cv_filename=excluded.cv_filename,
                cv_text=excluded.cv_text,
                extracted_skills=excluded.extracted_skills,
                extracted_experience=excluded.extracted_experience,
                extracted_education=excluded.extracted_education,
                timestamp=CURRENT_TIMESTAMP
        ''', (name, email, phone, cv_filename, cv_text, skills, experience, education))
        conn.commit()
        # Get the ID of the inserted or updated candidate
        cursor.execute("SELECT id FROM candidates WHERE email = ?", (email,))
        result = cursor.fetchone()
        return result['id'] if result else None
    except sqlite3.Error as e:
        print(f"Database error adding candidate: {e}")
        return None
    finally:
        conn.close()


def add_or_update_match(jd_id, candidate_id, score, is_shortlisted):
    """Adds or updates a match record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO matches (jd_id, candidate_id, match_score, is_shortlisted)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(jd_id, candidate_id) DO UPDATE SET
                match_score=excluded.match_score,
                is_shortlisted=excluded.is_shortlisted,
                timestamp=CURRENT_TIMESTAMP
        ''', (jd_id, candidate_id, score, is_shortlisted))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error adding/updating match: {e}")
        return False
    finally:
        conn.close()

def update_email_sent_status(match_id):
    """Updates the email sent status for a specific match."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE matches
            SET interview_email_sent = TRUE
            WHERE id = ?
        ''', (match_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error updating email status: {e}")
        return False
    finally:
        conn.close()

def get_all_jds():
    """Retrieves all job descriptions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, summary, timestamp FROM job_descriptions ORDER BY timestamp DESC")
    jds = cursor.fetchall()
    conn.close()
    return jds

def get_jd_summary(jd_id):
    """Retrieves the summary for a specific job description."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT summary FROM job_descriptions WHERE id = ?", (jd_id,))
    result = cursor.fetchone()
    conn.close()
    return result['summary'] if result else None

def get_candidates_for_jd(jd_id):
    """Retrieves candidates matched with a specific JD, including match details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            c.id as candidate_id, c.name, c.email, c.phone, c.cv_filename,
            m.id as match_id, m.match_score, m.is_shortlisted, m.interview_email_sent
        FROM candidates c
        JOIN matches m ON c.id = m.candidate_id
        WHERE m.jd_id = ?
        ORDER BY m.match_score DESC
    ''', (jd_id,))
    candidates = cursor.fetchall()
    conn.close()
    return candidates

def get_candidate_details(candidate_id):
    """Retrieves full details for a specific candidate."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, email, phone, cv_filename, cv_text, extracted_skills, extracted_experience, extracted_education
        FROM candidates
        WHERE id = ?
    ''', (candidate_id,))
    candidate = cursor.fetchone()
    conn.close()
    return candidate

def get_shortlisted_candidates_for_emailing(jd_id):
    """Retrieves shortlisted candidates for a JD who haven't been emailed yet."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            c.name, c.email,
            m.id as match_id
        FROM candidates c
        JOIN matches m ON c.id = m.candidate_id
        WHERE m.jd_id = ? AND m.is_shortlisted = TRUE AND m.interview_email_sent = FALSE
    ''', (jd_id,))
    candidates = cursor.fetchall()
    conn.close()
    return candidates

# Setup the database when this module is imported
setup_database()