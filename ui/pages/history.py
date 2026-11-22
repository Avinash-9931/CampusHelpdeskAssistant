"""
Conversation History page module for Campus Helpdesk Assistant.
Enables students and administrators to review past inquiries, citations,
and manage their history.
"""

import json
import streamlit as st
from auth.service import get_user_chat_history, clear_user_chat_history
from ui.components import render_badge, render_empty_state, render_source_item


def render_history_page():
    """Renders the user-specific conversation history view."""
    curr_user = st.session_state.get("auth_user")
    if not curr_user:
        st.info("Please sign in to view your conversation history.")
        return

    user_id = curr_user["id"]

    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"<h2>My Conversation History</h2>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='color:var(--text-muted); font-size:13.5px; margin-top:-6px;'>"
            f"Logged in as <strong>{curr_user['name']}</strong> ({curr_user['role']}) · ID: <code>{user_id}</code>"
            f"</p>",
            unsafe_allow_html=True
        )
    with col_h2:
        with st.expander("🗑️ Clear My History"):
            st.warning("This will permanently delete all your conversation logs from the database.")
            if st.button("Confirm Delete All", type="primary", use_container_width=True, key="confirm_clear_history"):
                clear_user_chat_history(user_id)
                st.session_state.chat_history = []
                st.success("All your conversation history has been erased.")
                st.rerun()

    # Search / Filter
    search_q = st.text_input("🔍 Search past inquiries", placeholder="Filter by keyword (e.g. attendance, library, fee)...")

    # Fetch logs from SQLite
    history_items = get_user_chat_history(user_id, limit=100)

    # Also incorporate any in-memory turns that haven't refreshed
    if not history_items and not st.session_state.get("chat_history"):
        st.markdown(
            render_empty_state(
                title="No History Recorded Yet",
                message="Start an inquiry on the AI Chatbot page to build your verified question and citation log.",
                icon_name="message-square"
            ),
            unsafe_allow_html=True
        )
        return

    # Filter
    filtered = []
    for item in history_items:
        content = item.get("content", "")
        if not search_q or search_q.lower() in content.lower():
            filtered.append(item)

    if not filtered:
        st.info(f"No conversation history matching '{search_q}'.")
        return

    st.markdown(f"<div style='font-size:12px; font-weight:600; color:var(--text-muted); margin-bottom:12px;'>Showing {len(filtered)} recorded turn(s):</div>", unsafe_allow_html=True)

    for item in filtered:
        role = item.get("role", "assistant")
        content = item.get("content", "")
        created_at = item.get("created_at", "")
        meta = {}
        try:
            if item.get("metadata_json"):
                meta = json.loads(item["metadata_json"])
        except Exception:
            pass

        with st.container(border=True):
            r_col, t_col = st.columns([3, 1])
            with r_col:
                if role == "user":
                    st.markdown(f"**Student Question**", unsafe_allow_html=True)
                else:
                    mode_name = meta.get("mode", "assistant")
                    st.markdown(f"**Campus Assistant Response** ({mode_name})", unsafe_allow_html=True)
            with t_col:
                st.markdown(f"<div style='text-align:right; font-size:11px; color:#94A3B8;'>{created_at}</div>", unsafe_allow_html=True)

            st.markdown(content)

            citations = meta.get("citations", [])
            if citations:
                with st.expander(f"Citations ({len(citations)})", expanded=False):
                    for c in citations:
                        st.markdown(
                            render_source_item(
                                filename=c.get("filename", ""),
                                page=c.get("page", 1),
                                snippet=c.get("snippet", ""),
                                score=c.get("score")
                            ),
                            unsafe_allow_html=True
                        )
