"""
Home page module for AI-Powered Campus Helpdesk Assistant.
Renders asymmetric hero banner, interactive preview card, live status strip,
four-step pipeline cards, welcome message, and disclaimer notice.
"""

import streamlit as st
from config import settings
from ui.components import (
    render_icon,
    render_badge,
    render_status_strip,
    render_demo_banner
)


def render_home_page():
    """Renders the Home page view."""
    # Persistent Demo Warning Banner if active
    if st.session_state.get("demo_active", False):
        st.markdown(render_demo_banner(), unsafe_allow_html=True)

    # 1. Live Status Strip (real system values)
    retriever = st.session_state.retriever
    ai_engine = st.session_state.ai_engine
    stats = retriever.get_stats()

    ai_mode_label = (
        f"Gemini Active ({settings.GEMINI_MODEL})"
        if ai_engine.is_available()
        else "Fallback Mode (Direct Evidence)"
    )
    retrieval_method_label = retriever.active_method()

    st.markdown(
        render_status_strip(
            doc_count=stats["document_count"],
            chunk_count=stats["chunk_count"],
            ai_mode=ai_mode_label,
            retrieval_method=retrieval_method_label
        ),
        unsafe_allow_html=True
    )

    # 2. Asymmetric Two-Column Hero
    hero_col_left, hero_col_right = st.columns([1.2, 0.8], gap="large")

    with hero_col_left:
        st.markdown(f"""
        <div class="hero-container fade-up">
            <div class="hero-eyebrow">
                {render_icon("shield-check", size=13, color="#BFDBFE")}
                SCSE4041 Prompt Engineering · Milestone 2 · Team Invictus
            </div>
            <div class="hero-title">
                Find verified university answers in seconds, grounded in official policy.
            </div>
            <div class="hero-subtitle">
                Zero hallucination, automatic departmental referrals, and page-level source citations. 
                Answers strictly derived from uploaded institutional PDF documents.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Primary and Secondary CTA Buttons
        btn_c1, btn_c2 = st.columns([1, 1], gap="small")
        with btn_c1:
            if st.button("💬 Ask the Assistant", type="primary", use_container_width=True, key="hero_ask_btn"):
                st.session_state.page = "AI Chatbot"
                st.rerun()
        with btn_c2:
            if st.button("📁 Upload Documents", use_container_width=True, key="hero_upload_btn"):
                st.session_state.page = "Knowledge Base"
                st.rerun()

    with hero_col_right:
        # Stylized Product Preview Card (HTML/CSS)
        st.markdown(f"""
        <div class="preview-card fade-up">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <span class="preview-badge">{render_icon("terminal", size=12, color="#64748B")} Live Interface Preview</span>
                <span class="badge badge-accent">Grounding Active</span>
            </div>
            <div class="preview-bubble-user">
                What is the minimum attendance requirement?
            </div>
            <div class="preview-bubble-ai">
                <div style="font-weight:700; color:#0B1F3A; font-size:12px; margin-bottom:4px; display:flex; align-items:center; gap:6px;">
                    {render_icon("graduation-cap", size=14, color="#2563EB")} Campus Helpdesk
                </div>
                Enrolled undergraduate students must maintain a minimum attendance of <strong>75%</strong> in each registered course to be eligible for End-Semester examinations.
                <div style="margin-top:10px; padding-top:8px; border-top:1px dashed #CBD5E1;">
                    <span class="citation-chip">
                        {render_icon("file-text", size=10, color="#2563EB")} university_policy_demo.pdf (p. 1)
                    </span>
                </div>
            </div>
            <div style="font-size:11px; color:#94A3B8; text-align:center; font-style:italic; margin-top:8px;">
                Illustrative preview of the grounded answer & citation interface
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Welcome Message Box
    st.markdown(f"""
    <div class="custom-card fade-up" style="margin-top:24px; border-left:4px solid var(--accent); padding:18px 24px;">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
            {render_icon("message-square", size=20, color="#2563EB")}
            <h4 style="margin:0; color:#0B1F3A;">Welcome to your Campus Helpdesk</h4>
        </div>
        <p style="color:#334155; margin:0; font-size:14px; line-height:1.6;">
            Hello! Welcome to your AI Campus Helpdesk Assistant. Ask me anything about university academics, examinations, 
            attendance, fees, hostel facilities and campus procedures. I'll help you find answers using the available university documents.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 4. "How It Works" in Four Staggered Steps
    st.markdown("<h3 style='margin-top:36px; margin-bottom:16px;'>How the Grounded Pipeline Operates</h3>", unsafe_allow_html=True)
    step_cols = st.columns(4, gap="medium")

    steps = [
        ("upload-cloud", "1. Ingest & Validate", "PDFs are verified for magic-byte integrity (%PDF), encrypted/corrupt detection, and page extraction."),
        ("database", "2. Chunk & Index", "Page-level text streams are segmented into overlapping semantic chunks with strict metadata attribution."),
        ("search", "3. Dual-Tier Retrieval", "Queries undergo TF-IDF lexical matching or Gemini semantic search with mandatory score threshold gating."),
        ("shield-check", "4. Answer with Sources", "Grounded generation or direct evidence mode is delivered with clickable, page-level citations.")
    ]

    for idx, (col, (icon, title, desc)) in enumerate(zip(step_cols, steps)):
        with col:
            st.markdown(f"""
            <div class="custom-card fade-up" style="height:100%; animation-delay: {idx * 0.05}s;">
                <div style="width:36px; height:36px; background:var(--accent-soft); border-radius:8px; display:flex; align-items:center; justify-content:center; margin-bottom:12px; color:var(--accent);">
                    {render_icon(icon, size=18, color="#2563EB")}
                </div>
                <div style="font-weight:700; font-size:15px; color:var(--navy); margin-bottom:6px;">{title}</div>
                <div style="font-size:12.5px; line-height:1.55; color:var(--text-muted);">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # 5. University Disclaimer Card
    st.markdown(f"""
    <div class="disclaimer-card fade-up">
        {render_icon("info", size=20, color="#64748B")}
        <div>
            <strong style="color:var(--navy);">Important Institutional Disclaimer:</strong>
            This system operates strictly on Retrieval-Augmented Generation (RAG) bounded to uploaded documents. 
            It never invents or hallucinates fees, deadlines, or regulations. When specific facts are absent or ambiguous in the uploaded files, 
            students must consult official departmental offices.
        </div>
    </div>
    """, unsafe_allow_html=True)
