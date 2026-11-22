"""
About Project page module for AI-Powered Campus Helpdesk Assistant.
Displays course metadata, Team Invictus roster with developer attributions,
tech stack specifications, architecture topology, and honest limitations analysis.
"""

import sys
import streamlit as st
import pypdf
import sklearn
import numpy as np

from config import settings
from ui.components import (
    render_icon,
    render_badge,
    render_demo_banner
)


def render_about_page():
    """Renders the About Project view."""
    # Persistent Demo Warning Banner if active
    if st.session_state.get("demo_active", False):
        st.markdown(render_demo_banner(), unsafe_allow_html=True)

    st.markdown("<h2>About the Project</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:var(--text-muted); margin-top:-6px; font-size:13.5px;'>"
        "Mission specifications, team attribution, technical topology, and operational boundaries."
        "</p>",
        unsafe_allow_html=True
    )

    meta = settings.PROJECT_METADATA

    # 1. Project Metadata Card
    st.markdown(f"""
    <div class="custom-card fade-up" style="border-left:4px solid var(--navy); margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <h3 style="margin:0 0 6px 0; color:var(--navy);">{meta['title']}</h3>
                <div style="font-size:13px; color:var(--text-muted);">
                    <strong>Problem Statement:</strong> {meta['problem_statement']}
                </div>
            </div>
            <div>
                <span class="badge badge-navy">Team ID: {meta['team_id']}</span>
            </div>
        </div>
        <div style="margin-top:14px; padding-top:12px; border-top:1px solid var(--border); display:flex; gap:16px; font-size:12.5px; color:var(--text-muted);">
            <div><strong>Cohort:</strong> Invictus</div>
            <div><strong>Architecture:</strong> Grounded RAG with Zero-Hallucination Refusal Gate</div>
            <div><strong>Execution Mode:</strong> Dual-Tier (Offline Lexical / Gemini Semantic)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Team Members Roster
    st.markdown("### Team Invictus Roster & Roles")
    member_cols = st.columns(3, gap="medium")

    for idx, member in enumerate(meta["members"]):
        col = member_cols[idx % 3]
        role_label = member.get("role", "Core Contributor")
        role_kind = "accent" if "Primary" in role_label else "muted"

        with col:
            st.markdown(f"""
            <div class="custom-card fade-up" style="margin-bottom:14px; padding:16px 18px;">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                    <div style="width:32px; height:32px; background:var(--accent-soft); border-radius:8px; display:flex; align-items:center; justify-content:center; color:var(--accent);">
                        {render_icon("graduation-cap", size=16, color="#2F5BEA")}
                    </div>
                    <div>
                        <div style="font-weight:700; color:var(--navy); font-size:14px; line-height:1.2;">
                            {member['name']}
                        </div>
                        <div style="font-size:11px; font-family:'JetBrains Mono', monospace; color:var(--text-muted);">
                            {member['id']}
                        </div>
                    </div>
                </div>
                <div>{render_badge(role_label, kind=role_kind)}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin:24px 0;'>", unsafe_allow_html=True)

    # 3. Technical Specifications & Stack
    st.markdown("### Technical Specifications & Architecture")
    tech_c1, tech_c2 = st.columns(2, gap="large")

    with tech_c1:
        st.markdown(f"""
        <div class="custom-card fade-up" style="height:100%;">
            <div style="font-weight:700; color:var(--navy); font-size:15px; margin-bottom:10px; display:flex; align-items:center; gap:8px;">
                {render_icon("cpu", size=16, color="#2F5BEA")} System Infrastructure
            </div>
            <ul style="font-size:13px; line-height:1.7; color:#334155; padding-left:18px; margin:0;">
                <li><strong>Runtime Environment:</strong> Python 3.10+ (Verified on Python 3.12)</li>
                <li><strong>Presentation Layer:</strong> Streamlit with custom CSS tokens, Plus Jakarta Sans typography, and Lucide line icons</li>
                <li><strong>Generative LLM SDK:</strong> Official Google GenAI SDK (<code>google-genai</code>) with exponential backoff and error classification</li>
                <li><strong>PDF Stream Parser:</strong> <code>pypdf</code> with per-page text cleaning and layout extraction</li>
                <li><strong>Local Persistence:</strong> JSON knowledge base storage (<code>knowledge_base.json</code>) and NumPy embedding cache (<code>embeddings_cache.npy</code>)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with tech_c2:
        st.markdown(f"""
        <div class="custom-card fade-up" style="height:100%;">
            <div style="font-weight:700; color:var(--navy); font-size:15px; margin-bottom:10px; display:flex; align-items:center; gap:8px;">
                {render_icon("shield-check", size=16, color="#2F5BEA")} Groundedness & Security Controls
            </div>
            <ul style="font-size:13px; line-height:1.7; color:#334155; padding-left:18px; margin:0;">
                <li><strong>Relevance Gating:</strong> Lexical similarity threshold (min score 0.13) terminates out-of-domain queries without invoking LLM</li>
                <li><strong>Departmental Routing:</strong> Automatic routing to Accounts, Examinations, Library, and Academic Affairs</li>
                <li><strong>Injection Isolation:</strong> XML data wrappers (<code>&lt;context&gt;</code>, <code>&lt;user_query&gt;</code>) prevent instruction hijacking</li>
                <li><strong>Deterministic Citations:</strong> Citations constructed strictly from chunk metadata, never parsed from model output</li>
                <li><strong>Offline Fallback Mode:</strong> Full functionality with direct verbatim evidence display when no API key is supplied</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin:24px 0;'>", unsafe_allow_html=True)

    # 4. System Health & Runtime Diagnostics (4.2 Health Summary)
    st.markdown("### System Health & Runtime Diagnostics")
    retriever = st.session_state.get("retriever")
    stats = retriever.get_stats() if retriever else {}
    doc_count = stats.get("document_count", 0)
    chunk_count = stats.get("chunk_count", 0)
    has_key = "Yes" if settings.has_api_key() else "No"
    active_method = retriever.active_method() if retriever else "TF-IDF lexical"
    py_ver = sys.version.split()[0]
    st_ver = getattr(st, "__version__", "1.x")
    pypdf_ver = getattr(pypdf, "__version__", "5.x")
    sklearn_ver = getattr(sklearn, "__version__", "1.x")

    st.markdown(f"""
    <div class="custom-card fade-up" style="margin-bottom:20px;">
        <div style="font-weight:700; color:var(--navy); font-size:14px; margin-bottom:12px; display:flex; align-items:center; gap:8px;">
            {render_icon("terminal", size=15, color="#2F5BEA")} Live Diagnostic Health Overview
        </div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:14px;">
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:12px;">
                <div style="font-size:11.5px; color:#64748B; font-weight:600; text-transform:uppercase;">Python Runtime</div>
                <div style="font-size:14px; font-weight:700; color:#0B1F3A; font-family:'JetBrains Mono', monospace; margin-top:2px;">Python {py_ver}</div>
            </div>
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:12px;">
                <div style="font-size:11.5px; color:#64748B; font-weight:600; text-transform:uppercase;">Core Packages</div>
                <div style="font-size:12px; color:#0B1F3A; font-family:'JetBrains Mono', monospace; margin-top:2px;">
                    streamlit {st_ver} · pypdf {pypdf_ver} · sklearn {sklearn_ver}
                </div>
            </div>
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:12px;">
                <div style="font-size:11.5px; color:#64748B; font-weight:600; text-transform:uppercase;">Gemini Key Configured</div>
                <div style="font-size:14px; font-weight:700; color:{'#16A34A' if has_key == 'Yes' else '#D97706'}; margin-top:2px;">
                    {has_key} ({'AI Generation Ready' if has_key == 'Yes' else 'Offline Fallback Active'})
                </div>
            </div>
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:12px;">
                <div style="font-size:11.5px; color:#64748B; font-weight:600; text-transform:uppercase;">Active Retrieval Tier</div>
                <div style="font-size:13px; font-weight:700; color:#2F5BEA; margin-top:2px;">
                    {active_method}
                </div>
            </div>
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:12px;">
                <div style="font-size:11.5px; color:#64748B; font-weight:600; text-transform:uppercase;">Indexed Knowledge</div>
                <div style="font-size:14px; font-weight:700; color:#0B1F3A; margin-top:2px;">
                    {doc_count} documents ({chunk_count} chunks)
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin:24px 0;'>", unsafe_allow_html=True)

    # 5. System Limitations Analysis
    st.markdown("### Operational Boundaries & Limitations Analysis")
    st.markdown(
        "<p style='color:var(--text-muted); font-size:13px;'>"
        "In accordance with transparent engineering principles, the system adheres to the following operational constraints:"
        "</p>",
        unsafe_allow_html=True
    )

    lim_c1, lim_c2, lim_c3 = st.columns(3, gap="medium")

    with lim_c1:
        st.markdown(f"""
        <div class="custom-card fade-up" style="height:100%;">
            <div style="font-weight:700; color:var(--navy); font-size:14px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                {render_icon("file-text", size=15, color="#D97706")} Scanned PDFs & OCR
            </div>
            <div style="font-size:12.5px; color:var(--text-muted); line-height:1.5;">
                The core pipeline parses native digital PDF text streams. Scanned image-only PDFs lacking a text layer 
                raise an informative <code>ScannedPDFError</code> indicating OCR is not enabled, preventing silent ingestion failures.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with lim_c2:
        st.markdown(f"""
        <div class="custom-card fade-up" style="height:100%;">
            <div style="font-weight:700; color:var(--navy); font-size:14px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                {render_icon("database", size=15, color="#2F5BEA")} Lexical Synonymity
            </div>
            <div style="font-size:12.5px; color:var(--text-muted); line-height:1.5;">
                In default Fallback Mode, TF-IDF retrieval depends on keyword matching and morphological normalization. 
                Queries using distant synonyms not found in the source text may receive lower scores unless semantic embeddings are active.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with lim_c3:
        st.markdown(f"""
        <div class="custom-card fade-up" style="height:100%;">
            <div style="font-weight:700; color:var(--navy); font-size:14px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                {render_icon("layers", size=15, color="#16A34A")} Complex Table Extraction
            </div>
            <div style="font-size:12.5px; color:var(--text-muted); line-height:1.5;">
                Multi-column financial fee schedules and grade distribution matrices extracted via linear stream reading 
                can experience cell concatenation. Students should verify complex tabular fee schedules directly with the Bursar.
            </div>
        </div>
        """, unsafe_allow_html=True)
