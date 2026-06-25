import os
from flask import Flask
from dotenv import load_dotenv

from database import init_db
from routes import main_bp, auth_bp, reports_bp

# Load environment variables from .env file if available
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Core Configurations
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production_123!')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    # Limit max upload size to 10MB
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 
    
    # Ensure uploads directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize the Database
    init_db()
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(reports_bp)
    
    # Global error handlers
    @app.errorhandler(413)
    def file_too_large(e):
        return {"error": "Uploaded file is too large! Maximum limit is 10MB."}, 413
        
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
