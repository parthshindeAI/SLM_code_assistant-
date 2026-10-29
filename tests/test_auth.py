import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src import auth


class AuthTests(unittest.TestCase):
    def test_google_sign_in_uses_canonical_openid_scopes(self):
        self.assertEqual(
            auth.SCOPES,
            [
                "openid",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email",
            ],
        )

    def test_demo_login_requires_name(self):
        self.assertEqual(
            auth.demo_login("  "), (None, "Please type a name (for example: student@example.com).")
        )
        self.assertEqual(auth.demo_login(" student@example.com "), ("student@example.com", None))
        self.assertEqual(auth.demo_login("Aarav"), ("Aarav@demo.local", None))

    def test_login_reports_missing_credentials_file(self):
        with patch.object(auth, "CREDENTIALS_FILE", Path("missing-credentials.json")):
            email, error = auth.login()

        self.assertIsNone(email)
        self.assertIn("credentials.json was not found", error)

    def test_login_uses_saved_credentials(self):
        credentials = Mock(
            valid=True,
            expired=False,
            refresh_token="refresh-token",
            scopes=auth.SCOPES,
        )
        credentials.to_json.return_value = '{"token": "cached"}'
        response = Mock()
        response.json.return_value = {
            "email": "person@example.com",
            "email_verified": True,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            credentials_file = Path(temp_dir) / "credentials.json"
            token_file = Path(temp_dir) / "token.json"
            credentials_file.touch()
            token_file.write_text("cached token", encoding="utf-8")
            with (
                patch.object(auth, "CREDENTIALS_FILE", credentials_file),
                patch.object(auth, "TOKEN_FILE", token_file),
                patch(
                    "google.oauth2.credentials.Credentials.from_authorized_user_file",
                    return_value=credentials,
                ) as load_credentials,
                patch("google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file") as flow,
                patch("google.auth.transport.requests.AuthorizedSession") as session,
            ):
                session.return_value.get.return_value = response
                email, error = auth.login()
                saved_token = token_file.read_text(encoding="utf-8")

        self.assertEqual(email, "person@example.com")
        self.assertIsNone(error)
        load_credentials.assert_called_once()
        flow.assert_not_called()
        self.assertEqual(saved_token, '{"token": "cached"}')

    def test_login_reauthorizes_legacy_token_with_different_scopes(self):
        old_credentials = Mock(
            valid=True,
            expired=False,
            refresh_token="old-refresh-token",
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        )
        new_credentials = Mock(
            valid=True,
            expired=False,
            refresh_token="refresh-token",
            scopes=auth.SCOPES,
        )
        new_credentials.to_json.return_value = '{"token": "new"}'
        response = Mock()
        response.json.return_value = {
            "email": "person@example.com",
            "email_verified": True,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            credentials_file = Path(temp_dir) / "credentials.json"
            token_file = Path(temp_dir) / "token.json"
            credentials_file.touch()
            token_file.write_text("old token", encoding="utf-8")
            with (
                patch.object(auth, "CREDENTIALS_FILE", credentials_file),
                patch.object(auth, "TOKEN_FILE", token_file),
                patch(
                    "google.oauth2.credentials.Credentials.from_authorized_user_file",
                    return_value=old_credentials,
                ),
                patch(
                    "google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file"
                ) as create_flow,
                patch("google.auth.transport.requests.AuthorizedSession") as session,
            ):
                create_flow.return_value.run_local_server.return_value = new_credentials
                session.return_value.get.return_value = response
                email, error = auth.login()
                saved_token = token_file.read_text(encoding="utf-8")

        self.assertEqual(email, "person@example.com")
        self.assertIsNone(error)
        create_flow.assert_called_once()
        create_flow.return_value.run_local_server.assert_called_once_with(port=0)
        self.assertEqual(saved_token, '{"token": "new"}')

    def test_logout_removes_saved_token(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            token_file = Path(temp_dir) / "token.json"
            token_file.touch()
            with patch.object(auth, "TOKEN_FILE", token_file):
                error = auth.logout()

        self.assertIsNone(error)
        self.assertFalse(token_file.exists())


if __name__ == "__main__":
    unittest.main()
