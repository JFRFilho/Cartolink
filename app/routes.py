"""
CartLink - Routes
Defines all HTTP endpoints for the application
"""

import os
import uuid
import json
import time
import threading
from flask import (
    Blueprint, render_template, request, jsonify,
    session, redirect, url_for, current_app
)
from werkzeug.utils import secure_filename

from app.drive_service import DriveService
from app.auth import get_auth_url, exchange_code_for_credentials, load_credentials

# Blueprints
main_bp = Blueprint('main', __name__)
drive_bp = Blueprint('drive', __name__)

# In-memory upload status tracker (use Redis in production)
upload_status = {}


def _has_admin_access():
    """Validate access to admin-only setup routes."""
    expected_key = os.getenv('ADMIN_SETUP_KEY')
    provided_key = request.args.get('key') or request.headers.get('X-Admin-Setup-Key')

    if not expected_key:
        return False

    return provided_key == expected_key


def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', set())
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


# ─── MAIN ROUTES ─────────────────────────────────────────────────────────────

@main_bp.route('/')
def index():
    """Main page"""
    creds = load_credentials()
    drive_ready = creds is not None and creds.valid
    return render_template('index.html', drive_ready=drive_ready)


@main_bp.route('/auth/google')
def google_auth():
    """Redirect user to Google OAuth consent screen"""
    if not _has_admin_access():
        return jsonify({'error': 'Admin access required'}), 403

    auth_url, state = get_auth_url()
    session['oauth_state'] = state
    return redirect(auth_url)


@main_bp.route('/auth/callback')
def google_callback():
    """Handle OAuth callback from Google"""
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return render_template('index.html', auth_error=error, drive_ready=False)

    if not code:
        return render_template('index.html', auth_error='No authorization code received', drive_ready=False)

    try:
        exchange_code_for_credentials(code)
        return redirect(url_for('main.index'))
    except Exception as e:
        return render_template('index.html', auth_error=str(e), drive_ready=False)


@main_bp.route('/auth/status')
def auth_status():
    """Check authentication status"""
    if not _has_admin_access():
        return jsonify({'error': 'Admin access required'}), 403

    creds = load_credentials()
    if creds and creds.valid:
        return jsonify({'authenticated': True})
    elif creds and creds.expired and creds.refresh_token:
        try:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            return jsonify({'authenticated': True})
        except Exception:
            return jsonify({'authenticated': False})
    return jsonify({'authenticated': False})


@main_bp.route('/auth/logout')
def logout():
    """Remove stored credentials"""
    if not _has_admin_access():
        return jsonify({'error': 'Admin access required'}), 403

    if os.getenv('GOOGLE_OAUTH_TOKEN') or os.getenv('GOOGLE_OAUTH_REFRESH_TOKEN'):
        return jsonify({
            'error': 'As credenciais estao configuradas via .env. Remova GOOGLE_OAUTH_TOKEN e GOOGLE_OAUTH_REFRESH_TOKEN manualmente para desconectar.'
        }), 400

    token_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config', 'token.json'
    )
    if os.path.exists(token_path):
        os.remove(token_path)
    return redirect(url_for('main.index'))


# ─── API ROUTES ───────────────────────────────────────────────────────────────

@drive_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and send to Google Drive"""
    # Validate server-side Google Drive credentials
    creds = load_credentials()
    if not creds or not creds.valid:
        return jsonify({
            'error': (
                'Servico temporariamente indisponivel. '
                'A conta principal do Google Drive nao esta configurada no servidor.'
            )
        }), 503

    # Validate file presence
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed.'}), 400

    # Create a unique upload ID for status tracking
    upload_id = str(uuid.uuid4())
    upload_status[upload_id] = {
        'status': 'saving',
        'message': 'Saving file temporarily...',
        'progress': 10,
        'link': None,
        'error': None
    }

    # Save file temporarily
    filename = secure_filename(file.filename)
    temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{upload_id}_{filename}")
    file.save(temp_path)

    # Process upload in background thread
    app = current_app._get_current_object()
    thread = threading.Thread(
        target=process_upload,
        args=(upload_id, temp_path, filename, creds, app)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'upload_id': upload_id})


def process_upload(upload_id, temp_path, filename, creds, app):
    """Background process: upload to Drive and set permissions"""
    with app.app_context():
        try:
            drive = DriveService(creds)

            # Step 1: Uploading
            upload_status[upload_id].update({
                'status': 'uploading',
                'message': 'Uploading file to Google Drive...',
                'progress': 35
            })
            time.sleep(0.5)  # Brief pause for UX

            # Step 2: Actual upload
            folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', None)
            file_id, file_name = drive.upload_file(temp_path, filename, folder_id)

            upload_status[upload_id].update({
                'status': 'processing',
                'message': 'File uploaded. Processing...',
                'progress': 65
            })
            time.sleep(0.3)

            # Step 3: Set permissions
            upload_status[upload_id].update({
                'status': 'permissions',
                'message': 'Applying public sharing permissions...',
                'progress': 80
            })

            drive.set_public_permission(file_id)
            link = drive.get_shareable_link(file_id)

            # Step 4: Done
            upload_status[upload_id].update({
                'status': 'done',
                'message': 'Link gerado com sucesso!',
                'progress': 100,
                'link': link,
                'file_name': file_name
            })

        except Exception as e:
            upload_status[upload_id].update({
                'status': 'error',
                'message': f'Error: {str(e)}',
                'progress': 0,
                'error': str(e)
            })
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)


@drive_bp.route('/status/<upload_id>')
def get_upload_status(upload_id):
    """Poll upload status"""
    status = upload_status.get(upload_id)
    if not status:
        return jsonify({'error': 'Upload ID not found'}), 404
    return jsonify(status)
