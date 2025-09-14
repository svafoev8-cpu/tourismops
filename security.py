from functools import wraps
from flask import abort
from flask_login import current_user

ROLE = {
    "CASHIER": "cashier",
    "ACCOUNTANT": "accountant",
    "FINANCIER": "financier",
    "MANAGER_INT": "manager_internal",
    "MANAGER_EXT": "manager_external",
    "CURATOR": "curator",      # только чтение
    "EXEC": "executive",       # руководство (просмотр всего)
    "ADMIN": "admin",          # полный доступ
}

def roles_required(*allowed):
    """Разрешить доступ только перечисленным ролям (или админу)."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in allowed and current_user.role != ROLE["ADMIN"]:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return deco

def read_only_for(*roles):
    """Запретить изменения (POST/PUT/PATCH/DELETE) для указанных ролей."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask import request
            if request.method in ("POST", "PUT", "PATCH", "DELETE") and current_user.role in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return deco
