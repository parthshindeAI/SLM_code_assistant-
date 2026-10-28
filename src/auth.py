"""Optional Google sign-in plus an offline demo sign-in."""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = PROJECT_DIR / "credentials.json"
TOKEN_FILE = PROJECT_DIR / "token.json"

SCOPES = ["openid", "email", "profile"]
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def credentials_ready():
    """True if the Google OAuth client file is in the right place."""
    return CREDENTIALS_FILE.exists()


def demo_login(name):
    """Offline sign-in. Returns (email, error)."""
    name = (name or "").strip()
    if not name:
        return None, "Please type a name (for example: student@example.com)."
    if "@" in name:
        return name, None
    # allow plain names like "Aarav"
    return name + "@demo.local", None


def login():
    """Sign in with Google and return (email, error_message).

    error_message is None when the sign-in worked.
    """
    if not credentials_ready():
        return None, (
            "credentials.json was not found.\n\n"
            "Put your Google OAuth client file here:  " + str(CREDENTIALS_FILE) +
            "\n\nOr skip Google sign-in and use Demo mode below - "
            "the app works exactly the same without an account."
        )

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import AuthorizedSession, Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        return None, (
            "The Google OAuth libraries are not installed. Run:  "
            "pip install google-auth-oauthlib"
        )

    try:
        credentials = None
        if TOKEN_FILE.exists():
            credentials = Credentials.from_authorized_user_file(
                str(TOKEN_FILE), SCOPES
            )
            if credentials.scopes and not set(SCOPES).issubset(credentials.scopes):
                credentials = None

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            credentials = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
        response = AuthorizedSession(credentials).get(USERINFO_URL, timeout=15)
        response.raise_for_status()
        profile = response.json()
        email = profile.get("email")
        if not email or not profile.get("email_verified"):
            return None, "Google sign-in did not return a verified email address."
        return email, None
    except Exception as error:
        return None, "Google sign-in failed: " + str(error)


def logout():
    """Delete the saved token. Return an error message if it cannot be removed."""
    if not TOKEN_FILE.exists():
        return None
    try:
        TOKEN_FILE.unlink()
    except OSError as error:
        return "Could not remove the saved Google sign-in token: " + str(error)
    return None
