from typing import Annotated, TypedDict

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class CurrentUser(TypedDict):
    username: str
    role: str

security = HTTPBearer(auto_error=False)

def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]) -> CurrentUser:
    
    print("Credentials object:", credentials)

    expected_token = "secret-token"
    if credentials is None:
        print("No credentials provided")
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    print("Scheme received:", repr(credentials.scheme))
    print("Token received:", repr(credentials.credentials))

    if credentials.credentials == "secret-token":
        return {
            "username": "rio",
            "role": "user"
        }
    
    if credentials.credentials == "second-user-token":
        return {
            "username": "alex",
            "role": "user"
        }
    
    if credentials.credentials == "admin-token":
        return {
            "username": "admin",
            "role": "admin"
        }
        

    raise HTTPException(status_code=401, detail="Unauthorized")

def require_admin(
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> CurrentUser:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user