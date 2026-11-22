"""
Home page module for Campus Helpdesk Assistant.
Faithfully recreates the visual language and structure of the reference Dribbble SaaS landing page:
- Floating pill navigation header
- Dashed headline box with corner handles and animated cursor glyph
- Shimmering floating skeleton AI card (left) and metric badge (right)
- Three-column feature strip with dashed borders, robot mascot, and flowing connector arrows
- Live index status telemetry strip and grounded RAG architecture overview
"""

import streamlit as st
from config import settings
from ui.components import (
    render_icon,
    render_badge,
    render_status_strip,
    render_demo_banner,
    clean_html
)
from ui.assets_svg import (
    CURSOR_GLYPH_SVG,
    ICON_AI_HELPER_SVG,
    ICON_GRAPH_SVG,
    ROBOT_MASCOT_SVG,
    CHAT_CARD_ILLUSTRATION_SVG,
    CONNECTOR_ARROW_LEFT_SVG,
    CONNECTOR_ARROW_RIGHT_SVG
)


def render_home_page():
    """Renders the Dribbble SaaS style Home page view."""
    # Persistent Demo Warning Banner if active
    if st.session_state.get("demo_active", False):
        st.markdown(render_demo_banner(), unsafe_allow_html=True)

    # =========================================================================
    # 1. HERO SECTION WITH FLOATING CARDS & DASHED SELECTION HEADLINE
    # =========================================================================
    h_col_left, h_col_center, h_col_right = st.columns([0.85, 2.5, 0.85], gap="small")

    with h_col_left:
        # Floating left skeleton card ("AI Helper" with shimmer)
        st.markdown(f"""
        <div class="floating-card-left" style="margin-top:48px;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
                {ICON_AI_HELPER_SVG}
                <span style="font-weight:700; font-size:13px; color:#0F172A;">AI Helper</span>
            </div>
            <div style="height:9px; width:112px; background:#E2E8F0; border-radius:4px; margin-bottom:8px;" class="skeleton-shimmer"></div>
            <div style="height:9px; width:78px; background:#E2E8F0; border-radius:4px;" class="skeleton-shimmer"></div>
        </div>
        """, unsafe_allow_html=True)

    with h_col_center:
        # Centered Hero Title & Action Buttons
        st.markdown(f"""
        <div style="text-align:center;">
            <div class="hero-eyebrow">
                <span>•</span> Grounded in official documents <span>•</span>
            </div>
            <div class="hero-headline-wrapper">
                <span class="corner-handle tl"></span>
                <span class="corner-handle tr"></span>
                <span class="corner-handle bl"></span>
                <span class="corner-handle br"></span>
                <h1 class="hero-headline">
                    Stop searching PDFs<br>
                    Start getting answers{CURSOR_GLYPH_SVG}
                </h1>
            </div>
            <p style="font-size:15.5px; color:#64748B; max-width:640px; margin:0 auto 12px auto; line-height:1.6;">
                Find verified university answers in seconds, grounded in official policy.<br>
                Search university regulations, examination procedures, fee structures, and campus guidelines with verified page-level citations and zero speculative hallucination.
            </p>
            <p style="font-size:11.5px; color:#94A3B8; margin:0 auto 20px auto; letter-spacing:0.02em;">
                SCSE4041 Prompt Engineering · Grounded Institutional RAG Architecture
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Primary & Secondary Action Pill Buttons
        b_spacer1, b_act1, b_act2, b_spacer2 = st.columns([0.4, 1.2, 1.2, 0.4], gap="small")
        with b_act1:
            if st.button("💬 Ask the assistant", type="primary", use_container_width=True, key="hero_cta_chat"):
                st.session_state.page = "AI Chatbot"
                st.rerun()
        with b_act2:
            curr_user = st.session_state.get("auth_user", {})
            u_role = curr_user.get("role", "Student")
            if u_role == "Admin":
                if st.button("📁 Upload documents", use_container_width=True, key="hero_cta_kb"):
                    st.session_state.page = "Knowledge Base"
                    st.rerun()
            else:
                if st.button("💬 My Chat History", use_container_width=True, key="hero_cta_history"):
                    st.session_state.page = "My History"
                    st.rerun()

    with h_col_right:
        # Floating right card (Square Metric Card with caption)
        st.markdown(f"""
        <div class="floating-card-right" style="margin-top:48px; text-align:center;">
            <div style="display:inline-flex; align-items:center; justify-content:center; width:44px; height:44px; border-radius:12px; background:#0F172A; margin-bottom:10px;">
                {ICON_GRAPH_SVG}
            </div>
            <div style="font-size:11.5px; font-weight:700; color:#475569;">• Cites page numbers</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 36px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 2. THREE-COLUMN FEATURE STRIP WITH CONNECTOR ARROWS
    # =========================================================================
    c_left, c_arrow1, c_mid, c_arrow2, c_right = st.columns([1.1, 0.3, 1.6, 0.3, 1.1], gap="small")

    with c_left:
        # Left Dashed Card: Instant answers with page citations
        st.markdown("""
        <div class="feature-strip-card">
            <div style="font-size:16px; font-weight:800; color:#0F172A; margin-bottom:6px; line-height:1.25;">
                Instant answers with page citations
            </div>
            <div style="font-size:12.5px; color:#64748B; margin-bottom:16px; line-height:1.5;">
                Verbatim excerpts retrieved from official institutional policy files.
            </div>
            <div style="border:1px dashed #CBD5E1; border-radius:14px; padding:12px; background:rgba(255,255,255,0.7);">
                <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                    <span style="font-size:14px;">📄</span>
                    <span style="font-weight:700; font-size:12px; color:#1E293B;">university_policy.pdf</span>
                </div>
                <div style="font-size:11.5px; color:#64748B; line-height:1.45;">
                    "Undergraduate students must maintain minimum 75% attendance..."
                </div>
                <div style="margin-top:8px; display:inline-block; background:#EFF6FF; color:#2563EB; font-weight:700; font-size:10.5px; padding:2px 8px; border-radius:4px;">
                    Page 1 · Section 2.1
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_arrow1:
        # Left Flowing Connector Arrow
        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:center; height:100%; min-height:160px;">
            {CONNECTOR_ARROW_LEFT_SVG}
        </div>
        """, unsafe_allow_html=True)

    with c_mid:
        # Center Container: Faint dot grid, Robot Mascot, Chat Preview, CTA button
        st.markdown(f"""
        <div class="center-grid-container" style="text-align:center;">
            <div style="display:flex; justify-content:center; align-items:center; gap:16px; margin-bottom:14px; flex-wrap:wrap;">
                {ROBOT_MASCOT_SVG}
                {CHAT_CARD_ILLUSTRATION_SVG}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open chatbot ↗", type="primary", use_container_width=True, key="mid_open_chatbot_btn"):
            st.session_state.page = "AI Chatbot"
            st.rerun()

    with c_arrow2:
        # Right Flowing Connector Arrow
        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:center; height:100%; min-height:160px;">
            {CONNECTOR_ARROW_RIGHT_SVG}
        </div>
        """, unsafe_allow_html=True)

    with c_right:
        # Right Dashed Card: Chat with your documents
        max_mb = settings.MAX_UPLOAD_SIZE_MB
        st.markdown(f"""
        <div class="feature-strip-card">
            <div style="font-size:16px; font-weight:800; color:#0F172A; margin-bottom:6px; line-height:1.25;">
                Chat with your documents
            </div>
            <div style="font-size:12.5px; color:#64748B; margin-bottom:16px; line-height:1.5;">
                Ask complex questions and receive immediate answers with zero hallucinations.
            </div>
            <div style="border:1px dashed #CBD5E1; border-radius:14px; padding:16px 12px; background:rgba(255,255,255,0.7); text-align:center;">
                <div style="font-size:24px; margin-bottom:4px;">📥</div>
                <div style="font-weight:700; font-size:12px; color:#1E293B; margin-bottom:4px;">
                    Knowledge Ingestion
                </div>
                <div style="font-size:11.5px; color:#64748B; line-height:1.4;">
                    Please ensure your document contains text and is under {max_mb} MB
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 3. LIVE SYSTEM TELEMETRY STRIP (REAL SYSTEM VALUES)
    # =========================================================================
    retriever = st.session_state.get("retriever")
    if retriever:
        stats = retriever.get_stats()
        ai_engine = st.session_state.get("ai_engine")
        is_ai_ready = ai_engine.is_available() if ai_engine else False
        ai_mode = f"Gemini ({settings.GEMINI_MODEL})" if is_ai_ready else "Fallback Mode (Direct Evidence)"
        status_html = render_status_strip(
            doc_count=stats["document_count"],
            chunk_count=stats["chunk_count"],
            ai_mode=ai_mode,
            retrieval_method=retriever.active_method()
        )
        st.markdown(status_html, unsafe_allow_html=True)

    # =========================================================================
    # 4. RAG ARCHITECTURE PILLARS
    # =========================================================================
    st.markdown("<h3 style='margin-top:28px; margin-bottom:16px;'>How the Grounded Architecture Operates</h3>", unsafe_allow_html=True)
    p1, p2, p3, p4 = st.columns(4, gap="medium")
    
    with p1:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:16px; height:100%; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
            <div style="font-size:11px; font-weight:700; color:#2F5BEA; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px;">
                01 · Ingestion
            </div>
            <div style="font-weight:700; font-size:14.5px; color:#0F172A; margin-bottom:6px;">High-Fidelity PDF Parse</div>
            <div style="font-size:12.5px; color:#64748B; line-height:1.5;">
                PyMuPDF extracts clean text pages, chunked into 350-word bounded segments with exact page metadata.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with p2:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:16px; height:100%; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
            <div style="font-size:11px; font-weight:700; color:#2F5BEA; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px;">
                02 · Dual-Tier Search
            </div>
            <div style="font-weight:700; font-size:14.5px; color:#0F172A; margin-bottom:6px;">Semantic + Lexical</div>
            <div style="font-size:12.5px; color:#64748B; line-height:1.5;">
                Combines dense vector similarity with offline BM25-grade TF-IDF lexical retrieval with relevance thresholding.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with p3:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:16px; height:100%; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
            <div style="font-size:11px; font-weight:700; color:#2F5BEA; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px;">
                03 · Grounded Synthesis
            </div>
            <div style="font-weight:700; font-size:14.5px; color:#0F172A; margin-bottom:6px;">Zero Hallucination</div>
            <div style="font-size:12.5px; color:#64748B; line-height:1.5;">
                Gemini answers are synthesized strictly from retrieved passages with verbatim page-level source citations.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with p4:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:16px; height:100%; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
            <div style="font-size:11px; font-weight:700; color:#2F5BEA; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px;">
                04 · Verbatim Guard
            </div>
            <div style="font-weight:700; font-size:14.5px; color:#0F172A; margin-bottom:6px;">Refusal & Referrals</div>
            <div style="font-size:12.5px; color:#64748B; line-height:1.5;">
                Queries lacking verified document facts trigger polite refusals and guide students to official department desks.
            </div>
        </div>
        """, unsafe_allow_html=True)
