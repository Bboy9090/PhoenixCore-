from fastapi import APIRouter, HTTPException, Request, Depends, Header
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os
import logging
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"]
)

# --- Models ---

class AdminRole(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"

class AdminUser(BaseModel):
    user_id: str
    username: str
    email: str
    role: AdminRole
    created_at: str
    last_login: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# --- Auth Constants ---
SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'dev-secret-key-change-in-production')
serializer = URLSafeTimedSerializer(SECRET_KEY)

# --- Dependencies ---

async def get_current_admin(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        # Max age: 24 hours
        payload = serializer.loads(token, max_age=86400)
        return payload
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="Token expired")
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- Endpoints ---

@router.post("/auth/login")
async def login(req: LoginRequest):
    # Mock authentication
    if req.username == "admin" and req.password == "admin":
        payload = {
            "user_id": "admin_001",
            "username": "admin",
            "email": "admin@phoenixdrive.local",
            "role": AdminRole.ADMIN.value
        }
        token = serializer.dumps(payload)
        return {
            "status": "ok",
            "token": token,
            "user": payload,
            "expires_in": 86400
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/health")
async def admin_health(admin_user: Dict[str, Any] = Depends(get_current_admin)):
    return {
        "status": "ok",
        "admin_user": admin_user,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/metrics/installations")
async def get_installation_metrics(admin_user: Dict[str, Any] = Depends(get_current_admin)):
    return {
        "status": "ok",
        "metrics": {
            "total_installations": 1247,
            "successful": 1189,
            "failed": 58,
            "in_progress": 3,
            "success_rate": 95.3
        }
    }

@router.get("/installations")
async def list_installations(limit: int = 50, offset: int = 0, admin_user: Dict[str, Any] = Depends(get_current_admin)):
    return {
        "status": "ok",
        "installations": [
            {
                "installation_id": "inst_00001",
                "mac_model": "MacBook Pro 15\" (2018)",
                "status": "completed",
                "progress": 100
            }
        ],
        "total": 1247
    }
