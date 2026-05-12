"""
CartLink - Google OAuth2 Authentication
Manages the OAuth 2.0 flow for Google Drive access.

Flow:
  1. User clicks "Connect Google Drive"
  2. App redirects to Google consent screen (get_auth_url)
  3. Google redirects back with ?code=...
  4. App exchanges code for tokens (exchange_code_for_credentials)
  5. Tokens are saved locally in config/token.json
  6. Subsequent requests load credentials from .env or token.json
"""

import os
import json
from datetime import datetime, timezone
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
ENV_PATH = os.path.join(BASE_DIR, '.env')


def _get_redirect_uri():
    """Build the OAuth redirect URI from environment variables"""
    port = os.getenv('PORT', '5000')
    return os.getenv('OAUTH_REDIRECT_URI', f'http://localhost:{port}/auth/callback')


def _get_env_client_config() -> dict | None:
    """Build Google OAuth client config from environment variables."""
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

    if not client_id or not client_secret:
        return None

    return {
        'web': {
            'client_id': client_id,
            'project_id': os.getenv('GOOGLE_PROJECT_ID', ''),
            'auth_uri': os.getenv('GOOGLE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
            'token_uri': os.getenv('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            'auth_provider_x509_cert_url': os.getenv(
                'GOOGLE_AUTH_PROVIDER_X509_CERT_URL',
                'https://www.googleapis.com/oauth2/v1/certs'
            ),
            'client_secret': client_secret,
            'redirect_uris': [_get_redirect_uri()]
        }
    }


def _build_flow() -> Flow:
    """Create an OAuth flow using env vars when available, otherwise credentials.json."""
    env_client_config = _get_env_client_config()
    if env_client_config:
        return Flow.from_client_config(
            env_client_config,
            scopes=SCOPES,
            redirect_uri=_get_redirect_uri()
        )

    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(
            f"Google OAuth credentials not found. Set GOOGLE_CLIENT_ID and "
            f"GOOGLE_CLIENT_SECRET in .env or place credentials.json at {CREDENTIALS_PATH}."
        )

    return Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=_get_redirect_uri()
    )


def _load_token_data_from_env() -> dict | None:
    """Load saved OAuth token data from environment variables."""
    token = os.getenv('GOOGLE_OAUTH_TOKEN')
    refresh_token = os.getenv('GOOGLE_OAUTH_REFRESH_TOKEN')
    expiry = os.getenv('GOOGLE_OAUTH_EXPIRY')

    if not token and not refresh_token:
        return None

    scopes = os.getenv('GOOGLE_OAUTH_SCOPES')
    return {
        'token': token,
        'refresh_token': refresh_token,
        'token_uri': os.getenv('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'scopes': [scope.strip() for scope in scopes.split(',')] if scopes else SCOPES,
        'expiry': expiry
    }


def _load_token_data_from_file() -> dict | None:
    """Load saved OAuth token data from token.json."""
    if not os.path.exists(TOKEN_PATH):
        return None

    with open(TOKEN_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _parse_expiry(value: str | None) -> datetime | None:
    """Parse a saved OAuth expiry timestamp."""
    if not value:
        return None

    try:
        expiry = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if expiry.tzinfo:
            expiry = expiry.astimezone(timezone.utc).replace(tzinfo=None)
        return expiry
    except ValueError:
        return None


def _save_env_value(lines: list[str], key: str, value: str) -> list[str]:
    """Replace or append a key=value pair in the local .env file."""
    updated = False
    new_line = f'{key}={value}'

    for index, line in enumerate(lines):
        if line.startswith(f'{key}='):
            lines[index] = new_line
            updated = True
            break

    if not updated:
        lines.append(new_line)

    return lines


def _save_credentials_to_env(credentials: Credentials) -> None:
    """Persist OAuth credentials to .env for future app restarts."""
    if not os.path.exists(ENV_PATH):
        return

    with open(ENV_PATH, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    env_updates = {
        'GOOGLE_CLIENT_ID': credentials.client_id or os.getenv('GOOGLE_CLIENT_ID', ''),
        'GOOGLE_CLIENT_SECRET': credentials.client_secret or os.getenv('GOOGLE_CLIENT_SECRET', ''),
        'GOOGLE_TOKEN_URI': credentials.token_uri or os.getenv('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
        'GOOGLE_OAUTH_TOKEN': credentials.token or '',
        'GOOGLE_OAUTH_REFRESH_TOKEN': credentials.refresh_token or os.getenv('GOOGLE_OAUTH_REFRESH_TOKEN', ''),
        'GOOGLE_OAUTH_SCOPES': ','.join(credentials.scopes) if credentials.scopes else ','.join(SCOPES),
        'GOOGLE_OAUTH_EXPIRY': credentials.expiry.isoformat() if credentials.expiry else ''
    }

    for key, value in env_updates.items():
        lines = _save_env_value(lines, key, value)
        os.environ[key] = value

    with open(ENV_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def get_auth_url() -> tuple:
    """
    Generate the Google OAuth2 authorization URL.

    Returns:
        Tuple of (authorization_url, state)

    Raises:
        FileNotFoundError: If .env and credentials.json are both missing Google OAuth config
    """
    flow = _build_flow()

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
    flow = _build_flow()

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
    token_sources = (
        ('token.json', _load_token_data_from_file),
        ('.env', _load_token_data_from_env),
    )

    for source_name, load_token_data in token_sources:
        try:
            token_data = load_token_data()
            if not token_data:
                continue

            credentials = Credentials(
                token=token_data.get('token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=token_data.get('scopes'),
                expiry=_parse_expiry(token_data.get('expiry'))
            )

            # Older saved tokens did not include expiry, so verify them with Google
            # instead of treating a stale access token as valid forever.
            has_expiry = bool(token_data.get('expiry'))
            if (credentials.expired or not credentials.valid or not has_expiry) and credentials.refresh_token:
                credentials.refresh(Request())
                _save_credentials(credentials)
            elif not has_expiry:
                continue

            if credentials.valid:
                return credentials

        except Exception as e:
            print(f"[CartLink] Error loading credentials from {source_name}: {e}", flush=True)

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
        'scopes': list(credentials.scopes) if credentials.scopes else SCOPES,
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
    }

    with open(TOKEN_PATH, 'w') as f:
        json.dump(token_data, f, indent=2)

    _save_credentials_to_env(credentials)
    print(f"[CartLink] Credentials saved to {TOKEN_PATH}")
