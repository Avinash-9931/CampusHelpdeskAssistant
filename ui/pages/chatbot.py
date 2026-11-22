"""
AI Chatbot page module for AI-Powered Campus Helpdesk Assistant.
Faithfully recreates the visual language of the reference Calley Dark AI Agent SaaS Dashboard:
- Breadcrumb header (Dashboard > AI Agent)
- Royal blue announcement banner (#1D4ED8 to #2563EB gradient)
- Started — Today divider line
- User & AI Agent dark bubble cards with circular avatars and timestamps
- Sleek quick question chips
- Collapsible verified citations
- Crystal-clear dark chat dock with prompt input
"""

import time
import html
import json
import re
import textwrap
from datetime import datetime
import streamlit as st
from config import settings
from core.chatbot import ChatResult
from auth.service import save_chat_turn
from ui.components import (
    render_icon,
    render_badge,
    render_source_item,
    render_skeleton,
    render_empty_state,
    clean_html
)
from ui.assets_svg import LOGO_GLYPH_SVG


def _simulate_stream(text: str):
    """Generator for streaming typewriter effect on answers."""
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(0.015)


def render_chatbot_page():
    """Renders the Calley Dark AI Agent Dashboard chat interface."""
    # 1. Calley Top Breadcrumb & Status Bar
    st.markdown(clean_html(f"""
    <div class="calley-breadcrumb-bar">
        <div class="calley-breadcrumb">
            <span>Dashboard</span>
            <span class="sep">></span>
            <span class="active-item">✨ AI Agent</span>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
            <div class="online-indicator"><span class="online-dot"></span> Online</div>
        </div>
    </div>
    <div class="calley-announcement-banner">
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:18px;">🏛️</span>
            <div>
                <strong style="font-size:13.5px;">Verified Academic Policy Assistant</strong>
                <span style="font-size:12.5px; opacity:0.9;"> • 100% Grounded in Official Documents with Page Citations</span>
            </div>
        </div>
        <div style="font-size:11px; font-weight:700; background:rgba(255,255,255,0.2); padding:3px 10px; border-radius:9999px;">
            Zero Hallucination
        </div>
    </div>
    """), unsafe_allow_html=True)

    # 2. Header with title and clear button
    head_col, clear_col = st.columns([4.2, 0.9])
    with head_col:
        st.markdown("<h2>Campus Helpdesk Assistant</h2>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:var(--text-muted); margin-top:-6px; font-size:13px;'>"
            "Answers strictly grounded in official university documents with page-level citations."
            "</p>",
            unsafe_allow_html=True
        )
    with clear_col:
        if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat_top_btn"):
            st.session_state.chat_history = []
            st.rerun()

    # 3. Quick-Question Chips
    st.markdown(
        "<div style='font-size:11.5px; font-weight:700; color:var(--text-light); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;'>"
        "<span>⚡ Quick Inquiries (Click to ask instantly):</span>"
        "<span style='font-size:11px; font-weight:500; text-transform:none; color:#60A5FA;'>Or type manually in the input bar below ↓</span>"
        "</div>",
        unsafe_allow_html=True
    )

    chip_queries = [
        "What is the minimum attendance requirement?",
        "How do I apply for examination admit card?",
        "What are the central library timings and borrowing rules?",
        "What is the fee payment and late registration procedure?",
        "What are the residential hostel curfew rules?",
        "When does academic course registration commence?"
    ]

    chip_cols = st.columns(3, gap="small")
    chip_cols_2 = st.columns(3, gap="small")
    all_chip_cols = chip_cols + chip_cols_2

    pending_query = None
    for idx, (col, q_text) in enumerate(zip(all_chip_cols, chip_queries)):
        with col:
            btn_label = q_text
            if "attendance" in q_text.lower():
                btn_label = "Attendance Requirement"
            elif "examination" in q_text.lower():
                btn_label = "Examination Admit Card"
            elif "library" in q_text.lower():
                btn_label = "Library Borrowing & Timings"
            elif "fee" in q_text.lower():
                btn_label = "Fee Payment & Penalties"
            elif "hostel" in q_text.lower():
                btn_label = "Hostel Curfew Regulations"
            elif "registration" in q_text.lower():
                btn_label = "Course Registration Schedule"

            if st.button(f"📌 {btn_label}", key=f"chip_btn_{idx}", use_container_width=True):
                pending_query = q_text

    st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin:14px 0 10px 0;'>", unsafe_allow_html=True)

    # 4. Chat Conversation History Display
    chat_history = st.session_state.get("chat_history", [])

    if not chat_history:
        st.markdown(
            render_empty_state(
                title="No Inquiries Yet",
                message="Select one of the quick inquiry chips above or type a question below to search university policies.",
                icon_name="message-square"
            ),
            unsafe_allow_html=True
        )
    else:
        # Calley "Started - Today" divider line
        st.markdown(
            '<div class="calley-chat-time-divider"><span>Started — Today</span></div>',
            unsafe_allow_html=True
        )

        curr_user = st.session_state.get("auth_user", {})
        u_initial = (curr_user.get("name", "Student")[:1] or "S").upper()

        for msg_idx, msg in enumerate(chat_history):
            role = msg["role"]
            content = msg["content"]
            timestamp = msg.get("timestamp", datetime.now().strftime("%I:%M %p"))

            if role == "user":
                safe_user_content = html.escape(content)
                user_card_html = clean_html(f"""
                <div class="calley-msg-user-container">
                    <div class="calley-avatar-circle calley-avatar-user">
                        {u_initial}
                    </div>
                    <div class="calley-msg-bubble-user">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; font-size:11.5px; color:#94A3B8;">
                            <span style="font-weight:700; color:#E2E8F0;">Student</span>
                            <span style="font-size:11px; color:#64748B;">{timestamp}</span>
                        </div>
                        <div style="font-size:14px; line-height:1.55; color:#F1F5F9;">{safe_user_content}</div>
                    </div>
                </div>
                """)
                st.markdown(user_card_html, unsafe_allow_html=True)
            else:
                citations = msg.get("citations", [])
                error_info = msg.get("error")
                mode = msg.get("mode", "gemini")

                clean_content = content
                if "<div" in clean_content or "<svg" in clean_content:
                    clean_content = re.sub(r'<[^>]+>', '', clean_content).strip()

                asst_card_html = clean_html(f"""
                <div class="calley-msg-assistant-container">
                    <div class="calley-avatar-circle calley-avatar-bot">
                        {LOGO_GLYPH_SVG}
                    </div>
                    <div class="calley-msg-bubble-bot">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; font-size:11.5px; color:#94A3B8;">
                            <div style="display:flex; align-items:center; gap:6px;">
                                <span style="font-weight:700; color:#60A5FA;">Campus AI Agent</span>
                                <span style="font-size:10px; color:#10B981;">● Verified</span>
                            </div>
                            <span style="font-size:11px; color:#64748B;">{timestamp}</span>
                        </div>
                    </div>
                </div>
                """)
                st.markdown(asst_card_html, unsafe_allow_html=True)

                with st.container(border=True):
                    if mode == "fallback":
                        fallback_desc = f" ({error_info})" if error_info else ""
                        st.info(
                            f"ℹ️ **Direct Evidence Mode Active:** Generative AI is operating in fallback mode{fallback_desc}. "
                            f"Showing verified verbatim excerpts retrieved directly from official policy files."
                        )

                    st.markdown(clean_content)

                    # Collapsible verified source citations
                    if citations:
                        with st.expander(f"📚 Verified Sources & Page Citations ({len(citations)})", expanded=False):
                            for c in citations:
                                st.markdown(render_source_item(
                                    filename=c.get("filename", "Official Policy"),
                                    page=c.get("page", 1),
                                    snippet=c.get("snippet", ""),
                                    score=c.get("score")
                                ), unsafe_allow_html=True)

    # 5. Chat Input Dock (Streamlit Chat Input)
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:11px; color:var(--text-light); margin-bottom:6px; display:flex; align-items:center; gap:5px;'>"
        "<span>💡 <em>Hint:</em> Ask about attendance criteria, hostel timings, grading, or fee deadlines...</span>"
        "</div>",
        unsafe_allow_html=True
    )

    user_query = st.chat_input("Type your message here...", key="chatbot_user_query_input")

    active_query = pending_query or user_query

    if active_query:
        retriever = st.session_state.retriever
        stats = retriever.get_stats()

        now_time = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_history.append({
            "role": "user",
            "content": active_query,
            "timestamp": now_time
        })

        if stats["chunk_count"] == 0:
            office = st.session_state.chatbot.get_department_referral(active_query)
            no_doc_msg = (
                "ℹ️ **No official university documents are currently indexed in the knowledge base.**\n\n"
                "I cannot answer questions without verified official documents. "
                "Please navigate to the **Knowledge Base** tab to upload documents or load the demo handbook, "
                f"or reach out directly to the:\n\n🏛️ **{office}**"
            )
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": no_doc_msg,
                "mode": "no_context",
                "citations": [],
                "timestamp": datetime.now().strftime("%I:%M %p")
            })
            st.rerun()

        # Show shimmering skeleton during retrieval
        skeleton_placeholder = st.empty()
        skeleton_placeholder.markdown(render_skeleton(), unsafe_allow_html=True)

        chatbot = st.session_state.chatbot
        result: ChatResult = chatbot.ask(
            question=active_query,
            history=st.session_state.chat_history[:-1],
            prefer_semantic=st.session_state.get("prefer_semantic", False),
            prompt_version=st.session_state.get("active_prompt_version", "final")
        )

        skeleton_placeholder.empty()

        formatted_answer = result.answer

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": formatted_answer,
            "mode": result.mode,
            "citations": [s.to_dict() for s in result.sources],
            "error": result.error,
            "timestamp": datetime.now().strftime("%I:%M %p")
        })

        # Persist conversation turn into SQLite
        curr_user = st.session_state.get("auth_user")
        if curr_user and curr_user.get("id"):
            u_id = curr_user["id"]
            save_chat_turn(
                user_id=u_id,
                conversation_id="default_conv",
                role="user",
                content=active_query
            )
            save_chat_turn(
                user_id=u_id,
                conversation_id="default_conv",
                role="assistant",
                content=formatted_answer,
                metadata_json=json.dumps({
                    "mode": result.mode,
                    "citations": [s.to_dict() for s in result.sources]
                })
            )

        st.rerun()
