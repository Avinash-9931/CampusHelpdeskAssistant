"""
AI Chatbot page module for AI-Powered Campus Helpdesk Assistant.
Provides interactive conversational interface with quick question chips,
streaming generator output for AI mode, instant delivery for fallback evidence/refusals,
collapsible source citation drawers, mode badges, and empty states.
"""

import time
import html
import textwrap
from datetime import datetime
import streamlit as st
from config import settings
from core.chatbot import ChatResult
from ui.components import (
    render_icon,
    render_badge,
    render_source_item,
    render_skeleton,
    render_empty_state,
    render_fallback_notice_banner,
    render_demo_banner
)


def _simulate_stream(text: str):
    """Generator for streaming typewriter effect on Gemini generated answers."""
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(0.015)


def render_chatbot_page():
    """Renders the AI Chatbot page view."""
    # Persistent Demo Warning Banner if active
    if st.session_state.get("demo_active", False):
        st.markdown(render_demo_banner(), unsafe_allow_html=True)

    # Header with title and clear button
    head_col, clear_col = st.columns([4, 1])
    with head_col:
        st.markdown("<h2>Campus Helpdesk Assistant</h2>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:var(--text-muted); margin-top:-6px; font-size:13.5px;'>"
            "Answers strictly grounded in official university documents with page-level citations."
            "</p>",
            unsafe_allow_html=True
        )
    with clear_col:
        if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat_top_btn"):
            st.session_state.chat_history = []
            st.rerun()

    # 1. Quick-Question Chips
    st.markdown(
        "<div style='font-size:12px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:8px;'>"
        "Quick Inquiries:"
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
            # Shorten label for button display
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

    st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin:18px 0;'>", unsafe_allow_html=True)

    # 2. Chat Conversation History Display
    chat_history = st.session_state.get("chat_history", [])

    if not chat_history:
        # Clean Empty State
        st.markdown(
            render_empty_state(
                title="No Inquiries Yet",
                message="Select one of the quick inquiry chips above or type a question below to search university policies.",
                icon_name="message-square"
            ),
            unsafe_allow_html=True
        )
    else:
        for msg_idx, msg in enumerate(chat_history):
            role = msg["role"]
            content = msg["content"]
            timestamp = msg.get("timestamp", datetime.now().strftime("%I:%M %p"))

            if role == "user":
                # User Message Bubble (HTML escaped for XSS safety)
                safe_user_content = html.escape(content)
                user_html = textwrap.dedent(f"""
                <div class="chat-message-row user">
                    <div class="chat-bubble-user">
                        <div style="font-size:11px; font-weight:700; color:#93C5FD; margin-bottom:4px; display:flex; justify-content:space-between;">
                            <span>Student Inquiry</span>
                            <span>{timestamp}</span>
                        </div>
                        <div style="font-size:14px; line-height:1.5;">{safe_user_content}</div>
                    </div>
                </div>
                """).strip()
                st.markdown(user_html, unsafe_allow_html=True)
            else:
                # Assistant Message Bubble
                mode = msg.get("mode", "gemini")
                method = msg.get("retrieval_method", "TF-IDF lexical")
                citations = msg.get("citations", [])
                error_info = msg.get("error")

                # Mode badge determination
                if mode == "gemini":
                    mode_badge = render_badge("Gemini 2.5 Flash", kind="success", icon_name="sparkles")
                elif mode == "fallback":
                    if error_info:
                        mode_badge = render_badge("Rate-Limit Fallback", kind="warning", icon_name="shield-check")
                    else:
                        mode_badge = render_badge("Evidence only (no API key)", kind="warning", icon_name="shield-check")
                elif mode == "no_context":
                    mode_badge = render_badge("No relevant context", kind="danger", icon_name="alert-triangle")
                else:
                    mode_badge = render_badge("Error Notice", kind="danger", icon_name="x-circle")

                method_badge = render_badge(method, kind="accent")

                # Fallback notice banner if mode is fallback
                fallback_banner = render_fallback_notice_banner(error_msg=error_info) if mode == "fallback" else ""

                header_html = textwrap.dedent(f"""
                <div class="chat-message-row assistant">
                    <div class="chat-bubble-assistant">
                        <div class="chat-bubble-meta">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <div style="width:24px; height:24px; background:var(--navy); border-radius:6px; display:flex; align-items:center; justify-content:center; color:#FFFFFF;">
                                    {render_icon("graduation-cap", size=13)}
                                </div>
                                <span style="font-weight:700; color:var(--navy); font-size:13px;">Campus Helpdesk Assistant</span>
                                {mode_badge}
                            </div>
                            <div style="display:flex; align-items:center; gap:8px;">
                                {method_badge}
                                <span>{timestamp}</span>
                            </div>
                        </div>
                        {fallback_banner}
                    </div>
                </div>
                """).strip()
                st.markdown(header_html, unsafe_allow_html=True)
                # Render content with native markdown formatting
                st.markdown(content)

                # Collapsible Source Cards under Answer
                if citations:
                    with st.expander(f"📌 Verified Citations & Source Evidence ({len(citations)})", expanded=False):
                        for cite in citations:
                            fname = cite.get("filename", "")
                            page = cite.get("page", 1)
                            snippet = cite.get("snippet", "")
                            score = cite.get("score")
                            st.markdown(
                                render_source_item(filename=fname, page=page, snippet=snippet, score=score),
                                unsafe_allow_html=True
                            )

    # 3. Chat Input Box (Sticky Bottom)
    chat_input_val = st.chat_input("Type your question here (e.g. 'What is the attendance rule?')")
    active_query = pending_query or chat_input_val

    if active_query:
        # Rapid repeated submission / double-click debounce guard
        now_ts = time.time()
        last_sent = st.session_state.get("_last_query_time", 0.0)
        last_query_text = st.session_state.get("_last_query_text", "")
        if active_query == last_query_text and (now_ts - last_sent) < 1.0:
            # Suppress duplicate rapid trigger
            st.stop()

        st.session_state["_last_query_time"] = now_ts
        st.session_state["_last_query_text"] = active_query

        # Check if Knowledge Base is completely empty
        retriever = st.session_state.retriever
        stats = retriever.get_stats()

        # Append student message to history
        now_time = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_history.append({
            "role": "user",
            "content": active_query,
            "timestamp": now_time
        })

        if stats["chunk_count"] == 0:
            # Friendly Guidance to Knowledge Base
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
                "retrieval_method": retriever.active_method(),
                "citations": [],
                "timestamp": datetime.now().strftime("%I:%M %p")
            })
            st.rerun()

        # Show shimmering skeleton while searching
        skeleton_placeholder = st.empty()
        skeleton_placeholder.markdown(render_skeleton(), unsafe_allow_html=True)

        # Call real ChatbotController logic
        chatbot = st.session_state.chatbot
        result: ChatResult = chatbot.ask(
            question=active_query,
            history=st.session_state.chat_history[:-1],
            prefer_semantic=st.session_state.get("prefer_semantic", False),
            prompt_version=st.session_state.get("active_prompt_version", "final")
        )

        skeleton_placeholder.empty()

        # Format answer text
        formatted_answer = result.answer

        # Append assistant response to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": formatted_answer,
            "mode": result.mode,
            "retrieval_method": result.retrieval_method,
            "citations": [s.to_dict() for s in result.sources],
            "timestamp": datetime.now().strftime("%I:%M %p")
        })

        st.rerun()
