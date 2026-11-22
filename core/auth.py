"""
Authentication and role-based access module for AI-Powered Campus Helpdesk Assistant.
Supports Student and Administrator credentials with sample quick-login profiles.
"""

from typing import Optional, Dict, Any

USERS_DB = {
    "student": {
        "password": "student123",
        "role": "Student",
        "name": "Avinash Kumar",
        "id": "S24CSEU0709",
        "department": "B.Tech Computer Science & Engineering",
        "avatar": "🎓"
    },
    "s24cseu0709": {
        "password": "student123",
        "role": "Student",
        "name": "Avinash Kumar",
        "id": "S24CSEU0709",
        "department": "B.Tech Computer Science & Engineering",
        "avatar": "🎓"
    },
    "admin": {
        "password": "admin123",
        "role": "Admin",
        "name": "System Administrator",
        "id": "ADM-001",
        "department": "Office of Academic Affairs & Policy Helpdesk",
        "avatar": "🛡️"
    },
    "faculty": {
        "password": "faculty123",
        "role": "Admin",
        "name": "Course Faculty / Evaluator",
        "id": "faculty",
        "department": "Department of Computer Science & Engineering",
        "avatar": "🎓"
    },
    "guest": {
        "password": "guest123",
        "role": "Admin",
        "name": "Guest Examiner",
        "id": "guest",
        "department": "Academic Evaluation Committee",
        "avatar": "⚖️"
    }
}


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticates a user against the institutional user registry.
    Returns user metadata dictionary if valid, else None.
    """
    uname = (username or "").strip().lower()
    pwd = (password or "").strip()

    user = USERS_DB.get(uname)
    if user and user["password"] == pwd:
        return {
            "username": uname,
            "role": user["role"],
            "name": user["name"],
            "id": user["id"],
            "department": user["department"],
            "avatar": user["avatar"]
        }
    return None
