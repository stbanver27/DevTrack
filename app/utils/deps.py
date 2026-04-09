from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import decode_token
from app.models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Dependency: returns User or redirects to login."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    return user


class RequireAuth:
    """Use as dependency on page routes that require authentication."""
    def __call__(self, request: Request, db: Session = Depends(get_db)):
        user = get_current_user(request, db)
        if not user or not user.is_active:
            return RedirectResponse(url="/login", status_code=302)
        return user
