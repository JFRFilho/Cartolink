"""
CartLink - Google Drive File Sharing Tool
Main Flask application entry point
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.routes import main_bp, drive_bp


def create_app():
    """Application factory pattern"""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'cartlink-dev-secret-2024')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_FILE_SIZE_MB', 100)) * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_uploads')
    app.config['ALLOWED_EXTENSIONS'] = set(
        os.getenv('ALLOWED_EXTENSIONS', 'pdf,doc,docx,xls,xlsx,ppt,pptx,txt,csv,jpg,jpeg,png,gif,zip,rar,mp4,mp3').split(',')
    )

    # Create temp upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Enable CORS
    CORS(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(drive_bp, url_prefix='/api')

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    print(f"\n{'='*50}")
    print(f"  CartLink is running at http://localhost:{port}")
    print(f"{'='*50}\n")
    app.run(host='0.0.0.0', port=port, debug=debug)
