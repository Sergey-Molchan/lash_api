import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, Request

sessions = {}

def create_session() -> str:
    token = secrets.token_hex(32)
    sessions[token] = datetime.now() + timedelta(hours=24)
    return token

def verify_session(token: str) -> bool:
    if token not in sessions:
        return False
    if sessions[token] < datetime.now():
        del sessions[token]
        return False
    return True

def logout(token: str):
    if token in sessions:
        del sessions[token]

def check_admin_auth(request: Request):
    token = request.cookies.get("admin_token")
    if not token or not verify_session(token):
        raise HTTPException(status_code=401, detail="Не авторизован")
    return True