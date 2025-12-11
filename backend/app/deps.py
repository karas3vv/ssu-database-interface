from fastapi import Request, HTTPException


def get_current_user(request: Request):
    user = request.session.get("user")
    return user


def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется вход в систему.")
    return user


def require_admin(request: Request):
    user = require_login(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав.")
    return user
