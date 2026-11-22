"""
Role-Based Access Control (RBAC) guards for Campus Helpdesk.
Enforces permissions in code for all sensitive backend actions and pages.
"""

from typing import Optional, Dict, Any
import streamlit as st


def require_role(arg1: Any = "Student", arg2: Any = None) -> bool:
    """
    Evaluates whether the specified user meets the required role permission level.
    Supports either require_role('Admin', user) or require_role(user, 'Admin').
    
    Roles:
    - 'Student': Accessible by both Student and Admin.
    - 'Admin': Strictly accessible by Admin only.
    
    Returns:
        bool: True if authorized, False if forbidden.
    """
    if isinstance(arg1, str) and (isinstance(arg2, dict) or arg2 is None):
        required_role = arg1
        current_user = arg2 if arg2 is not None else st.session_state.get("auth_user")
    elif isinstance(arg1, dict) and isinstance(arg2, str):
        current_user = arg1
        required_role = arg2
    elif isinstance(arg1, dict) and arg2 is None:
        current_user = arg1
        required_role = "Student"
    else:
        required_role = str(arg1)
        current_user = st.session_state.get("auth_user")

    if not current_user or not isinstance(current_user, dict):
        return False

    user_role = current_user.get("role", "")
    if user_role == "Admin":
        return True

    if required_role == "Student" and user_role == "Student":
        return True

    return False


def enforce_backend_role(required_role: str, current_user: Optional[Dict[str, Any]] = None) -> None:
    """
    Raises a PermissionError if the current user lacks the required role.
    Use at the top of backend mutation functions (upload, delete, reprocess, user admin).
    """
    if not require_role(required_role, current_user):
        raise PermissionError(f"Access Denied: Action requires '{required_role}' authorization.")


def render_access_denied_view(section_name: str = "this section") -> None:
    """Renders a calm, institutional FAANG-grade access denied screen."""
    st.markdown(f"""
    <div style="max-width:560px; margin:48px auto; background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:36px; text-align:center; box-shadow:0 4px 16px rgba(15,23,42,0.04);">
        <div style="width:48px; height:48px; border-radius:12px; background:#FEF2F2; border:1px solid #FECACA; display:flex; align-items:center; justify-content:center; margin:0 auto 16px auto; color:#DC2626; font-size:20px;">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
        </div>
        <h3 style="font-size:18px; font-weight:700; color:#0F172A; margin:0 0 8px 0;">
            Access Restricted
        </h3>
        <p style="font-size:14px; line-height:1.55; color:#64748B; margin:0 0 24px 0;">
            You do not have administrative permission to access <strong>{section_name}</strong>. 
            Student accounts have full access to <strong>Chat</strong>, personal <strong>History</strong>, and <strong>Help</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        if st.button("Return to Chat", type="primary", use_container_width=True, key="access_denied_home_btn"):
            st.session_state.page = "Chat"
            st.rerun()
