import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings


def get_firebase_app():
    if not firebase_admin._apps.get(settings.FIREBASE_APP_NAME):
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, name=settings.FIREBASE_APP_NAME)
    return firebase_admin.get_app(settings.FIREBASE_APP_NAME)


def verify_firebase_token(id_token):
    app = get_firebase_app()
    try:
        decoded = auth.verify_id_token(id_token, app=app)
        return decoded
    except Exception:
        return None
