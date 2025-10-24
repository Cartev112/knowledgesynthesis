"""Authentication dependencies and utilities."""
from fastapi import HTTPException, Request, status
from typing import Optional

from ..models.user import User


# Simple session storage (imported from auth routes)
# In production, use Redis or database
from ..routes.auth import sessions


def get_current_user(request: Request) -> User:
    """
    Dependency to get current authenticated user from session.
    
    Usage:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user}
    """
    # Check for user info in headers (from Node.js proxy)
    user_id = request.headers.get("X-User-ID")
    user_email = request.headers.get("X-User-Email")
    
    if user_id and user_email:
        # User authenticated via Node.js, create User object
        return User(
            user_id=user_id,
            email=user_email,
            first_name=request.headers.get("X-User-First-Name", ""),
            last_name=request.headers.get("X-User-Last-Name", ""),
            username=request.headers.get("X-User-Username"),
            roles=request.headers.get("X-User-Roles", "user").split(",")
        )
    
    # Fallback to session cookie
    session_id = request.cookies.get("session_id")
    
    if not session_id or session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    session_data = sessions[session_id]
    
    # Convert session data to User model
    user = User(
        user_id=session_data.get("user_id", session_data.get("email")),
        email=session_data.get("email"),
        first_name=session_data.get("first_name", ""),
        last_name=session_data.get("last_name", ""),
        username=session_data.get("username"),
        roles=session_data.get("roles", ["user"]),
    )
    
    return user


def get_current_user_optional(request: Request) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.
    
    Usage:
        @router.get("/public")
        def public_route(current_user: Optional[User] = Depends(get_current_user_optional)):
            if current_user:
                return {"message": f"Hello {current_user.full_name}"}
            return {"message": "Hello guest"}
    """
    try:
        return get_current_user(request)
    except HTTPException:
        return None


def require_role(required_role: str):
    """
    Dependency factory to require specific role.
    
    Usage:
        @router.delete("/admin/users/{user_id}")
        def delete_user(
            user_id: str,
            current_user: User = Depends(require_role("admin"))
        ):
            # Only admins can access this
            pass
    """
    def role_checker(request: Request) -> User:
        user = get_current_user(request)
        if required_role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )
        return user
    
    return role_checker
