import json
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, exceptions, messaging

from app.core.config import get_settings
from app.core.observability.logging import logger

settings = get_settings()
_firebase_app: firebase_admin.App | None = None


def init_firebase() -> None:
    global _firebase_app
    cred_path = settings.firebase_credentials_path

    if not cred_path:
        logger.warning(
            "FIREBASE_CREDENTIALS_PATH is not set. Push notifications have been switched to mock mode."
        )
        return

    path = Path(cred_path)
    if not path.is_file():
        logger.error(f"Firebase key file not found at path: {cred_path}")
        return

    try:
        cred = credentials.Certificate(str(path))
        _firebase_app = firebase_admin.initialize_app(cred)

        logger.info("Firebase Admin SDK launched successfully.")

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Invalid Firebase credentials file format ({cred_path}): {e}")
        _firebase_app = None

    except exceptions.FirebaseError as e:
        logger.error(f"Firebase SDK initialization error: {e}")
        _firebase_app = None


def get_messaging():
    if _firebase_app is None:
        return None
    return messaging
