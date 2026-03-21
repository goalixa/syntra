import requests
from config import settings


def check_permission(user_id: str, action: str):

    url = f"{settings.AUTH_SERVICE_URL}/permissions/check"

    payload = {
        "user_id": user_id,
        "action": action
    }

    try:
        res = requests.post(url, json=payload)
        return res.json()
    except:
        return {"allowed": False}
