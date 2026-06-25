import json
import sqlite3
from database import get_db_connection

# --- User Model Functions ---

def create_user(fullname, email, password_hash):
    """Inserts a new user into the database. Returns user ID on success, or None on error (e.g. duplicate email)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)",
            (fullname, email, password_hash)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    """Retrieves a user row by email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Retrieves a user row by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_password(user_id, new_password_hash):
    """Updates a user's password hash."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_password_hash, user_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


# --- Report Model Functions ---

def create_report(user_id, report_name, file_path, extracted_text, summary, detailed_summary, deficiency_summary, key_findings, severity, alerts, suggestions=None):
    """
    Creates a new report record.
    key_findings: dict/list representing findings, will be JSON stringified.
    alerts: list representing warning alerts, will be JSON stringified.
    suggestions: list representing recommendations, will be JSON stringified.
    deficiency_summary: plain text summary of detected deficiencies.
    detailed_summary: longer text summary for deeper report context.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ensure they are saved as JSON strings
    key_findings_str = json.dumps(key_findings)
    alerts_str = json.dumps(alerts)
    suggestions_str = json.dumps(suggestions if suggestions is not None else [])
    deficiency_summary_value = deficiency_summary if deficiency_summary is not None else ''
    detailed_summary_value = detailed_summary if detailed_summary is not None else ''
    
    cursor.execute(
        """
        INSERT INTO reports (user_id, report_name, file_path, extracted_text, summary, detailed_summary, deficiency_summary, key_findings, severity, alerts, suggestions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, report_name, file_path, extracted_text, summary, detailed_summary_value, deficiency_summary_value, key_findings_str, severity, alerts_str, suggestions_str)
    )
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    return report_id

def update_report(report_id, user_id, report_name, summary, detailed_summary, deficiency_summary, key_findings, severity, alerts, suggestions=None):
    """
    Updates an existing report record.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    key_findings_str = json.dumps(key_findings)
    alerts_str = json.dumps(alerts)
    suggestions_str = json.dumps(suggestions if suggestions is not None else [])
    deficiency_summary_value = deficiency_summary if deficiency_summary is not None else ''
    detailed_summary_value = detailed_summary if detailed_summary is not None else ''
    
    cursor.execute(
        """
        UPDATE reports
        SET report_name = ?, summary = ?, detailed_summary = ?, deficiency_summary = ?, key_findings = ?, severity = ?, alerts = ?, suggestions = ?
        WHERE id = ? AND user_id = ?
        """,
        (report_name, summary, detailed_summary_value, deficiency_summary_value, key_findings_str, severity, alerts_str, suggestions_str, report_id, user_id)
    )
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_reports_by_user(user_id, search_query=None, severity_filter=None, sort_by='date_desc'):
    """
    Retrieves all reports for a specific user, with optional search, severity filtering, and sorting.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM reports WHERE user_id = ?"
    params = [user_id]
    
    if search_query:
        query += " AND (report_name LIKE ? OR extracted_text LIKE ?)"
        # Match report name or extracted text
        params.extend([f"%{search_query}%", f"%{search_query}%"])
        
    if severity_filter:
        query += " AND severity = ?"
        params.append(severity_filter)
        
    # Apply sorting
    if sort_by == 'date_asc':
        query += " ORDER BY upload_date ASC"
    elif sort_by == 'name_asc':
        query += " ORDER BY report_name ASC"
    elif sort_by == 'name_desc':
        query += " ORDER BY report_name DESC"
    else:  # default is date_desc
        query += " ORDER BY upload_date DESC"
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    reports = []
    for row in rows:
        report = dict(row)
        # Parse JSON fields
        try:
            report['key_findings'] = json.loads(report['key_findings'])
        except (TypeError, ValueError):
            report['key_findings'] = {}
            
        try:
            report['alerts'] = json.loads(report['alerts'])
        except (TypeError, ValueError):
            report['alerts'] = []
            
        try:
            report['suggestions'] = json.loads(report.get('suggestions', '[]'))
        except (TypeError, ValueError):
            report['suggestions'] = []
            
        report['deficiency_summary'] = report.get('deficiency_summary', '') or ''
        report['detailed_summary'] = report.get('detailed_summary', '') or ''
        reports.append(report)
        
    return reports

def get_report_by_id(report_id, user_id):
    """Retrieves a specific report for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ? AND user_id = ?", (report_id, user_id))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        report = dict(row)
        try:
            report['key_findings'] = json.loads(report['key_findings'])
        except (TypeError, ValueError):
            report['key_findings'] = {}
            
        try:
            report['alerts'] = json.loads(report['alerts'])
        except (TypeError, ValueError):
            report['alerts'] = []

        try:
            report['suggestions'] = json.loads(report.get('suggestions', '[]'))
        except (TypeError, ValueError):
            report['suggestions'] = []

        report['deficiency_summary'] = report.get('deficiency_summary', '') or ''
        report['detailed_summary'] = report.get('detailed_summary', '') or ''
        return report
    return None

def delete_report(report_id, user_id):
    """Deletes a specific report for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reports WHERE id = ? AND user_id = ?", (report_id, user_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_report_statistics(user_id):
    """
    Returns dashboard statistics for a user:
    - Total reports
    - Count of Normal reports
    - Count of Moderate reports
    - Count of Critical reports
    - Distribution by severity for charts
    - Common abnormal parameters count
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM reports WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM reports WHERE user_id = ? AND severity = 'Normal'", (user_id,))
    normal = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM reports WHERE user_id = ? AND severity = 'Moderate'", (user_id,))
    moderate = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM reports WHERE user_id = ? AND severity = 'Critical'", (user_id,))
    critical = cursor.fetchone()[0]
    
    # Let's count common abnormal parameters.
    # We retrieve the alerts lists for the user's reports.
    cursor.execute("SELECT alerts, key_findings FROM reports WHERE user_id = ?", (user_id,))
    alerts_rows = cursor.fetchall()
    conn.close()
    
    abnormal_counts = {}
    for row in alerts_rows:
        alerts_text = row[0]
        key_findings_text = row[1]
        if alerts_text:
            try:
                alerts_list = json.loads(alerts_text)
                for alert in alerts_list:
                    clean_alert = alert.replace("⚠ ", "").replace(" detected.", "").replace(".", "").strip()
                    abnormal_counts[clean_alert] = abnormal_counts.get(clean_alert, 0) + 1
                continue
            except (TypeError, ValueError):
                pass

        if key_findings_text:
            try:
                key_findings = json.loads(key_findings_text)
                for name, finding in key_findings.items():
                    if finding.get('status') and finding['status'] != 'Normal':
                        abnormal_counts[name] = abnormal_counts.get(name, 0) + 1
            except (TypeError, ValueError):
                pass
                
    return {
        'total': total,
        'normal': normal,
        'moderate': moderate,
        'critical': critical,
        'abnormal_parameters': abnormal_counts
    }
