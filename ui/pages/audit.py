"""
Audit Log Inspection page module for Campus Helpdesk Assistant.
Enforces RBAC (Admin only) and displays immutable security event records.
"""

import streamlit as st
from auth.guards import require_role, render_access_denied_view
from auth.service import get_audit_logs
from ui.components import render_badge


def render_audit_page():
    """Renders the Administrator Audit & Compliance Trail."""
    curr_user = st.session_state.get("auth_user")
    if not require_role(curr_user, "Admin"):
        render_access_denied_view("Security & Administrative Audit Log")
        return

    st.markdown("<h2>Security & Administrative Audit Log</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:var(--text-muted); font-size:13.5px; margin-top:-6px;'>"
        "Tamper-evident trail of logins, OTP requests, document uploads, and credential changes."
        "</p>",
        unsafe_allow_html=True
    )

    f_col1, f_col2 = st.columns([2, 1])
    with f_col1:
        action_options = [
            "All Actions",
            "login_success",
            "login_failure",
            "otp_create",
            "otp_verify_success",
            "otp_verify_failed",
            "user_create",
            "user_status_toggle",
            "user_role_change",
            "password_reset",
            "document_upload",
            "document_delete"
        ]
        selected_action = st.selectbox("Filter by action type", action_options)
    with f_col2:
        limit = st.slider("Max entries to show", min_value=25, max_value=200, value=100, step=25)

    filter_param = None if selected_action == "All Actions" else selected_action
    logs = get_audit_logs(limit=limit, action_filter=filter_param)

    if not logs:
        st.info("No audit records matching the specified criteria.")
        return

    st.markdown(f"<div style='font-size:12px; color:var(--text-muted); margin-bottom:12px;'>Showing {len(logs)} audit record(s):</div>", unsafe_allow_html=True)

    # Render as formatted table
    for entry in logs:
        action_name = entry.get("action", "")
        # Badge coloring
        if "success" in action_name or "create" in action_name:
            badge_kind = "success"
        elif "fail" in action_name or "lockout" in action_name:
            badge_kind = "danger"
        elif "delete" in action_name or "toggle" in action_name:
            badge_kind = "warning"
        else:
            badge_kind = "accent"

        with st.container(border=True):
            col_a, col_b, col_c = st.columns([1.5, 3.5, 1.5])
            with col_a:
                st.markdown(render_badge(action_name, kind=badge_kind), unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:11px; color:#94A3B8; margin-top:4px;'>Actor: <code>{entry.get('user_id') or 'ANONYMOUS'}</code></div>", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"<div style='font-size:13px; color:#1E293B;'>{entry.get('details', '')}</div>", unsafe_allow_html=True)
            with col_c:
                st.markdown(f"<div style='font-size:11px; color:#64748B; text-align:right;'>{entry.get('timestamp')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:10px; color:#94A3B8; text-align:right;'>IP: {entry.get('ip_address', '127.0.0.1')}</div>", unsafe_allow_html=True)
