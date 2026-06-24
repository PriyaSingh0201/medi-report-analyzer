import os
import re
import datetime
import jwt
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, send_file, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

import models
import utils

# Define blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
reports_bp = Blueprint('reports', __name__)

# --- Helper Security Decorator ---

def token_required(f):
    """Decorator to protect routes and ensure a valid JWT token is present in cookies."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')
        
        # Also check Authorization header as fallback
        if not token and 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
        if not token:
            # If the request is for an API, return JSON; otherwise, redirect to login page
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication token is missing!'}), 401
            return redirect(url_for('auth.login_page'))
            
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = models.get_user_by_id(data['user_id'])
            if not current_user:
                raise Exception("User not found in database")
        except jwt.ExpiredSignatureError:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Token has expired!'}), 401
            return redirect(url_for('auth.login_page'))
        except Exception as e:
            if request.path.startswith('/api/'):
                return jsonify({'error': f'Invalid token: {str(e)}'}), 401
            return redirect(url_for('auth.login_page'))
            
        # Inject user row into route function
        return f(current_user, *args, **kwargs)
        
    return decorated


# --- Page Routing ---

@main_bp.route('/')
def home():
    """Home redirect route."""
    token = request.cookies.get('access_token')
    if token:
        try:
            jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            return redirect(url_for('main.dashboard_page'))
        except Exception:
            pass
    return redirect(url_for('auth.login_page'))

@main_bp.route('/dashboard')
@token_required
def dashboard_page(current_user):
    """Renders dashboard template."""
    return render_template('dashboard.html', user=current_user)

@main_bp.route('/history')
@token_required
def history_page(current_user):
    """Renders history analysis template."""
    return render_template('history.html', user=current_user)

@main_bp.route('/profile')
@token_required
def profile_page(current_user):
    """Renders profile and password update template."""
    return render_template('profile.html', user=current_user)


# --- Authentication Page Routes ---

@auth_bp.route('/register')
def register_page():
    """Renders registration view."""
    return render_template('register.html')

@auth_bp.route('/login')
def login_page():
    """Renders login view."""
    return render_template('login.html')


# --- Authentication API Routes ---

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    """API endpoint to register a new user with input validations."""
    data = request.get_json() or {}
    fullname = data.get('fullname', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    
    # Validation checks
    if not fullname or not email or not password or not confirm_password:
        return jsonify({'error': 'All fields are required!'}), 400
        
    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return jsonify({'error': 'Invalid email address format!'}), 400
        
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long!'}), 400
        
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match!'}), 400
        
    # Check if user already exists
    existing = models.get_user_by_email(email)
    if existing:
        return jsonify({'error': 'Email is already registered!'}), 400
        
    # Password hashing using Werkzeug
    hashed_pwd = generate_password_hash(password)
    user_id = models.create_user(fullname, email, hashed_pwd)
    
    if user_id:
        return jsonify({'message': 'Registration successful! Redirecting to login...'}), 201
    else:
        return jsonify({'error': 'Failed to create user. Please try again.'}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """API endpoint to login a user, set JWT Cookie, and return user info."""
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and Password are required!'}), 400
        
    user = models.get_user_by_email(email)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid email or password credentials!'}), 401
        
    # Generate JWT access token (valid for 24 hours)
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")
    
    # Store token in cookie
    response = jsonify({
        'message': 'Login successful!',
        'user': {
            'fullname': user['fullname'],
            'email': user['email']
        }
    })
    
    # Configure secure cookie (HTTPOnly, SameSite)
    response.set_cookie(
        'access_token',
        token,
        httponly=True,
        max_age=24 * 3600,
        samesite='Lax'
    )
    return response

@auth_bp.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """API endpoint to log out a user and clear cookie."""
    response = jsonify({'message': 'Logged out successfully!'})
    response.delete_cookie('access_token')
    return response

@auth_bp.route('/api/auth/change-password', methods=['POST'])
@token_required
def api_change_password(current_user):
    """API endpoint to change user password."""
    data = request.get_json() or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_new_password = data.get('confirm_new_password', '')
    
    if not current_password or not new_password or not confirm_new_password:
        return jsonify({'error': 'All fields are required!'}), 400
        
    if not check_password_hash(current_user['password'], current_password):
        return jsonify({'error': 'Incorrect current password!'}), 400
        
    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters long!'}), 400
        
    if new_password != confirm_new_password:
        return jsonify({'error': 'New passwords do not match!'}), 400
        
    new_hash = generate_password_hash(new_password)
    updated = models.update_user_password(current_user['id'], new_hash)
    
    if updated:
        return jsonify({'message': 'Password updated successfully!'}), 200
    return jsonify({'error': 'Failed to update password.'}), 500


# --- Reports & AI Operations API ---

def allowed_file(filename):
    """Validates that files are in standard allowed categories."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'png', 'jpg', 'jpeg', 'txt'}

@reports_bp.route('/api/reports/upload', methods=['POST'])
@token_required
def api_upload_report(current_user):
    """API endpoint to upload, run OCR extraction, execute AI rules, store report database record."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded!'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected!'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Allowed formats are PDF, PNG, JPG, JPEG!'}), 400
        
    # Read filename safely
    filename = secure_filename(file.filename)
    
    # Append timestamp to filename to prevent collisions
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename_parts = filename.rsplit('.', 1)
    unique_filename = f"{filename_parts[0]}_{timestamp}.{filename_parts[1]}"
    
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(upload_path)
    
    # Check File Size limit (10MB)
    file_size = os.path.getsize(upload_path)
    if file_size > 10 * 1024 * 1024:
        os.remove(upload_path)
        return jsonify({'error': 'File exceeds maximum size of 10MB!'}), 400
        
    # Text Extraction
    ext = unique_filename.rsplit('.', 1)[1].lower()
    extracted_text = ""
    
    if ext == 'pdf':
        extracted_text = utils.extract_text_from_pdf(upload_path)
    elif ext == 'txt':
        with open(upload_path, 'r', encoding='utf-8', errors='ignore') as f:
            extracted_text = f.read()
    else:
        extracted_text = utils.extract_text_from_image(upload_path)
        
    # AI Medical Report Analysis
    analysis = utils.analyze_medical_text(extracted_text)
    
    # Save Report record inside Database
    report_id = models.create_report(
        user_id=current_user['id'],
        report_name=file.filename, # Keep original filename for presentation
        file_path=os.path.join('uploads', unique_filename),
        extracted_text=extracted_text,
        summary=analysis['summary'],
        key_findings=analysis['key_findings'],
        severity=analysis['severity'],
        alerts=analysis['alerts'],
        suggestions=analysis.get('suggestions', [])
    )
    
    if not report_id:
        os.remove(upload_path)
        return jsonify({'error': 'Failed to save report details inside DB!'}), 500
        
    # Send email notification if severity is CRITICAL (Bonus Feature)
    if analysis['severity'] == 'Critical' and analysis['alerts']:
        utils.send_critical_email(
            user_email=current_user['email'],
            user_fullname=current_user['fullname'],
            report_name=file.filename,
            alerts=analysis['alerts']
        )
        
    return jsonify({
        'message': 'Report processed successfully!',
        'report_id': report_id,
        'analysis': analysis
    }), 201

@reports_bp.route('/api/reports', methods=['GET'])
@token_required
def api_get_reports(current_user):
    """API endpoint to get all user's reports with search, filter, and sorting options."""
    search = request.args.get('search', '').strip()
    severity = request.args.get('severity', '').strip()
    sort_by = request.args.get('sort_by', 'date_desc')
    
    # Map empty strings to None
    search_val = search if search else None
    severity_val = severity if severity else None
    
    reports = models.get_reports_by_user(current_user['id'], search_val, severity_val, sort_by)
    return jsonify({'reports': reports})

@reports_bp.route('/api/reports/<int:report_id>', methods=['GET'])
@token_required
def api_get_report_detail(current_user, report_id):
    """API endpoint to get details of a specific report."""
    report = models.get_report_by_id(report_id, current_user['id'])
    if not report:
        return jsonify({'error': 'Report not found!'}), 404
    return jsonify({'report': report})

@reports_bp.route('/api/reports/<int:report_id>', methods=['DELETE'])
@token_required
def api_delete_report(current_user, report_id):
    """API endpoint to delete a report and its stored file."""
    report = models.get_report_by_id(report_id, current_user['id'])
    if not report:
        return jsonify({'error': 'Report not found!'}), 404
        
    # Delete file from disk
    file_path = os.path.join(os.path.dirname(__file__), report['file_path'])
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error removing file: {e}")
            
    deleted = models.delete_report(report_id, current_user['id'])
    if deleted:
        return jsonify({'message': 'Report deleted successfully!'})
    return jsonify({'error': 'Failed to delete report.'}), 500

@reports_bp.route('/api/reports/<int:report_id>/update', methods=['PUT'])
@token_required
def api_update_report(current_user, report_id):
    """API endpoint to update a report's details and saved metrics."""
    report = models.get_report_by_id(report_id, current_user['id'])
    if not report:
        return jsonify({'error': 'Report not found!'}), 404
        
    data = request.get_json() or {}
    report_name = data.get('report_name', '').strip()
    summary = data.get('summary', '').strip()
    key_findings = data.get('key_findings', {})
    severity = data.get('severity', 'Normal').strip()
    alerts = data.get('alerts', [])
    suggestions = data.get('suggestions', [])
    
    if not report_name:
        return jsonify({'error': 'Report name is required!'}), 400
        
    updated = models.update_report(
        report_id=report_id,
        user_id=current_user['id'],
        report_name=report_name,
        summary=summary,
        key_findings=key_findings,
        severity=severity,
        alerts=alerts,
        suggestions=suggestions
    )
    
    if updated:
        return jsonify({
            'message': 'Report analysis updated successfully!',
            'report': {
                'id': report_id,
                'report_name': report_name,
                'summary': summary,
                'key_findings': key_findings,
                'severity': severity,
                'alerts': alerts,
                'suggestions': suggestions
            }
        }), 200
        
    return jsonify({'error': 'Failed to update report details.'}), 500

@reports_bp.route('/api/reports/<int:report_id>/download', methods=['GET'])
@token_required
def api_download_pdf(current_user, report_id):
    """API endpoint to generate and download the medical report PDF analysis."""
    report = models.get_report_by_id(report_id, current_user['id'])
    if not report:
        return jsonify({'error': 'Report not found!'}), 404
        
    # Temporary PDF file location
    temp_dir = os.path.join(os.path.dirname(__file__), 'database', 'temp_pdfs')
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = f"analysis_report_{report_id}.pdf"
    pdf_path = os.path.join(temp_dir, temp_filename)
    
    # Generate the PDF
    success = utils.generate_pdf_report(report, current_user['fullname'], pdf_path)
    
    if not success:
        return jsonify({'error': 'Failed to generate PDF analysis report!'}), 500
        
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"Dooper_Analysis_{report['report_name'].rsplit('.', 1)[0]}.pdf",
        mimetype='application/pdf'
    )

@reports_bp.route('/api/profile', methods=['GET'])
@token_required
def api_profile_stats(current_user):
    """API endpoint to retrieve profile stats and count details."""
    stats = models.get_report_statistics(current_user['id'])
    return jsonify({
        'user': {
            'id': current_user['id'],
            'fullname': current_user['fullname'],
            'email': current_user['email'],
            'created_at': current_user['created_at']
        },
        'stats': stats
    })
