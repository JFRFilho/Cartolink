"""
CartLink - Google OAuth2 Authentication
Manages the OAuth 2.0 flow for Google Drive access.

Flow:
  1. User clicks "Connect Google Drive"
  2. App redirects to Google consent screen (get_auth_url)
  3. Google redirects back with ?code=...
  4. App exchanges code for tokens (exchange_code_for_credentials)
  5. Tokens are saved locally in config/token.json
  6. Subsequent requests load credentials from token.json (load_credentials)
"""

import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# OAuth2 scopes required by CartLink
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',  # Create/manage files uploaded by this app
    'https://www.googleapis.com/auth/userinfo.email',  # Get user email (optional, for display)
    'openid'
]

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'config', 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'config', 'token.json')


def _get_redirect_uri():
    """Build the OAuth redirect URI from environment variables"""
    port = os.getenv('PORT', '5000')
    return os.getenv('OAUTH_REDIRECT_URI', f'http://localhost:{port}/auth/callback')


def get_auth_url() -> tuple:
    """
    Generate the Google OAuth2 authorization URL.

    Returns:
        Tuple of (authorization_url, state)

    Raises:
        FileNotFoundError: If credentials.json is not found
    """
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(
            f"credentials.json not found at {CREDENTIALS_PATH}. "
            "Please download it from Google Cloud Console and place it in the config/ folder."
        )

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=_get_redirect_uri()
    )

    auth_url, state = flow.authorization_url(
        access_type='offline',       # Get refresh token
        include_granted_scopes='true',
        prompt='consent'             # Always show consent to ensure refresh token
    )

    return auth_url, state


def exchange_code_for_credentials(code: str) -> Credentials:
    """
    Exchange the authorization code for OAuth2 credentials and save them.

    Args:
        code: Authorization code received from Google callback

    Returns:
        google.oauth2.credentials.Credentials object
    """
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=_get_redirect_uri()
    )

    # Exchange code for tokens
    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Save credentials to token.json for future use
    _save_credentials(credentials)

    return credentials


def load_credentials() -> Credentials | None:
    """
    Load saved credentials from token.json.
    Automatically refreshes expired tokens using the refresh token.

    Returns:
        Valid Credentials object, or None if not authenticated
    """
    if not os.path.exists(TOKEN_PATH):
        return None

    try:
        with open(TOKEN_PATH, 'r') as f:
            token_data = json.load(f)

        credentials = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes')
        )

        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            _save_credentials(credentials)

        return credentials

    except Exception as e:
        print(f"[CartLink] Error loading credentials: {e}")
        return None


def _save_credentials(credentials: Credentials) -> None:
    """
    Save credentials to token.json.

    Args:
        credentials: Credentials object to save
    """
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)

    token_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': list(credentials.scopes) if credentials.scopes else SCOPES
    }

    with open(TOKEN_PATH, 'w') as f:
        json.dump(token_data, f, indent=2)

    print(f"[CartLink] Credentials saved to {TOKEN_PATH}")
