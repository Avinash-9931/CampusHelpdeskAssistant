"""
Reusable UI component builders for AI-Powered Campus Helpdesk Assistant.
Provides SVG icon generation, badges, status strips, source citation drawers,
custom chat bubbles, skeletons, and empty state cards. No emoji icons used.
"""

import html
from typing import List, Dict, Any, Optional
from datetime import datetime


def sanitize_text(text: str) -> str:
    """Escapes HTML entities from user input or untrusted document content."""
    return html.escape(str(text or ""))


def clean_html(html_str: str) -> str:
    """
    Strips all leading and trailing whitespace from each line of an HTML string.
    Guarantees no line starts with 4+ spaces, preventing Markdown from mistaking HTML for a code block.
    """
    return "".join(line.strip() for line in str(html_str or "").splitlines() if line.strip())


# ==============================================================================
# 1. LUCIDE-STYLE INLINE SVG ICON GENERATOR
# ==============================================================================
_ICON_PATHS: Dict[str, str] = {
    "graduation-cap": (
        '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/>'
        '<path d="M22 10v6"/>'
        '<path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>'
    ),
    "message-square": (
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
    ),
    "file-text": (
        '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
        '<path d="M14 2v4a2 2 0 0 0 2 2h4"/>'
        '<path d="M10 9H8"/>'
        '<path d="M16 13H8"/>'
        '<path d="M16 17H8"/>'
    ),
    "database": (
        '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
        '<path d="M3 5V19A9 3 0 0 0 21 19V5"/>'
        '<path d="M3 12A9 3 0 0 0 21 12"/>'
    ),
    "shield-check": (
        '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
        '<path d="m9 12 2 2 4-4"/>'
    ),
    "external-link": (
        '<path d="M15 3h6v6"/>'
        '<path d="M10 14 21 3"/>'
        '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    ),
    "alert-triangle": (
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
    ),
    "check-circle": (
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<polyline points="22 4 12 14.01 9 11.01"/>'
    ),
    "x-circle": (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="15" y1="9" x2="9" y2="15"/>'
        '<line x1="9" y1="9" x2="15" y2="15"/>'
    ),
    "search": (
        '<circle cx="11" cy="11" r="8"/>'
        '<line x1="21" y1="21" x2="16.65" y2="16.65"/>'
    ),
    "trash-2": (
        '<path d="M3 6h18"/>'
        '<path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>'
        '<path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>'
        '<line x1="10" y1="11" x2="10" y2="17"/>'
        '<line x1="14" y1="11" x2="14" y2="17"/>'
    ),
    "refresh-cw": (
        '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>'
        '<path d="M21 3v5h-5"/>'
        '<path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>'
        '<path d="M8 16H3v5"/>'
    ),
    "upload-cloud": (
        '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>'
        '<path d="M12 12v9"/>'
        '<path d="m16 16-4-4-4 4"/>'
    ),
    "book-open": (
        '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>'
        '<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>'
    ),
    "info": (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="12" y1="16" x2="12" y2="12"/>'
        '<line x1="12" y1="8" x2="12.01" y2="8"/>'
    ),
    "help-circle": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
    ),
    "user": (
        '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>'
    ),
    "lock": (
        '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>'
        '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
    ),
    "key": (
        '<circle cx="7.5" cy="15.5" r="5.5"/>'
        '<path d="m21 2-9.6 9.6"/>'
        '<path d="m15.5 7.5 3 3L22 7l-3-3"/>'
    ),
    "log-out": (
        '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
        '<polyline points="16 17 21 12 16 7"/>'
        '<line x1="21" y1="12" x2="9" y2="12"/>'
    ),
    "sparkles": (
        '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>'
        '<path d="M5 3v4"/>'
        '<path d="M19 17v4"/>'
        '<path d="M3 5h4"/>'
        '<path d="M17 19h4"/>'
    ),
    "cpu": (
        '<rect x="4" y="4" width="16" height="16" rx="2"/>'
        '<rect x="9" y="9" width="6" height="6"/>'
        '<path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/>'
        '<path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>'
    ),
    "terminal": (
        '<polyline points="4 17 10 11 4 5"/>'
        '<line x1="12" y1="19" x2="20" y2="19"/>'
    ),
    "clock": (
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="12 6 12 12 16 14"/>'
    ),
    "map-pin": (
        '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>'
        '<circle cx="12" cy="10" r="3"/>'
    ),
    "dollar-sign": (
        '<line x1="12" y1="2" x2="12" y2="22"/>'
        '<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>'
    ),
    "arrow-right": (
        '<line x1="5" y1="12" x2="19" y2="12"/>'
        '<polyline points="12 5 19 12 12 19"/>'
    ),
    "building": (
        '<rect width="16" height="20" x="4" y="2" rx="2" ry="2"/>'
        '<path d="M9 22v-4h6v4"/>'
        '<path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/>'
        '<path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/>'
        '<path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/>'
    ),
    "layers": (
        '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/>'
        '<path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/>'
        '<path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>'
    ),
    "check": (
        '<polyline points="20 6 9 17 4 12"/>'
    ),
    "play": (
        '<polygon points="6 3 20 12 6 21 6 3"/>'
    )
}


def render_icon(name: str, size: int = 16, color: str = "currentColor", stroke_width: float = 1.75) -> str:
    """Renders a Lucide-style inline line SVG icon without emojis."""
    path_data = _ICON_PATHS.get(name, _ICON_PATHS["info"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:inline-block; vertical-align:middle; flex-shrink:0;">'
        f'{path_data}'
        f'</svg>'
    )


# ==============================================================================
# 2. STATUS STRIP & BADGES
# ==============================================================================
def render_badge(label: str, kind: str = "navy", icon_name: Optional[str] = None) -> str:
    """Renders a styled badge (navy, accent, success, warning, danger, muted)."""
    icon_html = f"{render_icon(icon_name, size=12)} " if icon_name else ""
    return f'<span class="badge badge-{kind}">{icon_html}{label}</span>'


def render_demo_banner() -> str:
    """Renders a persistent amber banner when synthetic demo data is loaded, styled as a pill bar."""
    warning_icon = render_icon("alert-triangle", size=16, color="#D97706")
    return clean_html(f"""
    <div class="demo-pill-banner">
        <div style="display:flex; align-items:center; gap:8px;">
            {warning_icon}
            <div>
                <strong>DEMO DATA ACTIVE:</strong> Currently using synthetic <em>Apex Metropolitan University Policy Handbook</em>. 
                Values and fees are for testing & evaluation purposes only.
            </div>
        </div>
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; color:#B45309; white-space:nowrap;">
            Verification Mode
        </div>
    </div>
    """)


def render_status_strip(doc_count: int, chunk_count: int, ai_mode: str, retrieval_method: str) -> str:
    """Renders the live status strip as small white pills under the feature strip."""
    file_icon = render_icon("file-text", size=13, color="#2F5BEA")
    layers_icon = render_icon("layers", size=13, color="#2F5BEA")
    cpu_icon = render_icon("cpu", size=13, color="#2F5BEA")
    db_icon = render_icon("database", size=13, color="#2F5BEA")

    ai_badge = (
        render_badge(ai_mode, kind="success", icon_name="sparkles")
        if "Gemini" in ai_mode
        else render_badge("Fallback Mode", kind="warning", icon_name="shield-check")
    )

    retrieval_badge = render_badge(retrieval_method, kind="accent", icon_name="database")

    return clean_html(f"""
    <div class="status-pill-strip">
        <div class="status-pill-item">
            {file_icon}
            <span>Indexed Documents: <strong>{doc_count} files</strong></span>
        </div>
        <div class="status-pill-item">
            {layers_icon}
            <span>Knowledge Chunks: <strong>{chunk_count} chunks</strong></span>
        </div>
        <div class="status-pill-item">
            {cpu_icon}
            <span>AI Generation Mode: {ai_badge}</span>
        </div>
        <div class="status-pill-item">
            {db_icon}
            <span>Active Retrieval Tier: {retrieval_badge}</span>
        </div>
    </div>
    """)


# ==============================================================================
# 3. SOURCE CARDS & CITATIONS
# ==============================================================================
def render_citation_chip(filename: str, page: int, score: Optional[float] = None) -> str:
    """Renders a compact citation chip with metadata."""
    safe_fn = sanitize_text(filename)
    score_str = f" · {score:.3f}" if score is not None else ""
    return clean_html(
        f'<span class="citation-chip" style="display:inline-flex; align-items:center; gap:5px; background:#EEF2FF; border:1px solid #C7D2FE; border-radius:6px; padding:3px 8px; font-family:\'JetBrains Mono\', monospace; font-size:11px; color:#2F5BEA;">'
        f'{render_icon("file-text", size=11, color="#2F5BEA")} {safe_fn} (p. {page}{score_str})'
        f'</span>'
    )


def render_source_item(filename: str, page: int, snippet: str, score: Optional[float] = None) -> str:
    """Renders an individual collapsible source citation block with dashed border."""
    safe_fn = sanitize_text(filename)
    safe_snippet = sanitize_text(snippet)
    score_badge = render_badge(f"Relevance: {score:.3f}", kind="accent") if score is not None else ""
    return clean_html(f"""
    <div class="source-item-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-weight:700; color:#2F5BEA; font-family:'JetBrains Mono', monospace; font-size:12px;">
                    {render_icon("file-text", size=13, color="#2F5BEA")} {safe_fn}
                </span>
                <span class="badge badge-muted">Page {page}</span>
            </div>
            <div>{score_badge}</div>
        </div>
        <div style="font-size:12.5px; line-height:1.5; color:#475569; font-style:italic; border-left:2px solid #C7D2FE; padding-left:10px; margin-top:4px;">
            "{safe_snippet}"
        </div>
    </div>
    """)


# ==============================================================================
# 4. SKELETON LOADER & EMPTY STATES
# ==============================================================================
def render_skeleton() -> str:
    """Renders a smooth shimmer skeleton placeholder during retrieval & generation."""
    search_icon = render_icon("search", size=15, color="#2F5BEA")
    return clean_html(f"""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,0.04); margin-bottom:16px;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:14px; color:#2F5BEA; font-weight:700; font-size:13px;">
            {search_icon} <span>Searching official university policy documents...</span>
        </div>
        <div class="skeleton-box" style="height:14px; width:92%; margin-bottom:10px;"></div>
        <div class="skeleton-box" style="height:14px; width:78%; margin-bottom:10px;"></div>
        <div class="skeleton-box" style="height:14px; width:64%;"></div>
    </div>
    """)


def render_empty_state(title: str, message: str, icon_name: str = "help-circle") -> str:
    """Renders a clean empty state card."""
    icon_svg = render_icon(icon_name, size=36, color="#94A3B8")
    return clean_html(f"""
    <div style="text-align:center; padding:40px 24px; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
        <div style="width:48px; height:48px; margin:0 auto 12px auto; color:#94A3B8;">{icon_svg}</div>
        <h4 style="color:#0F172A; font-size:16px; margin-bottom:6px; font-weight:700;">{title}</h4>
        <p style="color:#64748B; font-size:13.5px; max-width:440px; margin:0 auto; line-height:1.5;">{message}</p>
    </div>
    """)


# ==============================================================================
# 5. CHAT MESSAGE BUILDERS
# ==============================================================================
def render_fallback_notice_banner(error_msg: Optional[str] = None) -> str:
    """Banner displayed above fallback mode answers to clearly demarcate evidence from AI generation."""
    info_icon = render_icon("info", size=16, color="#D97706")
    if error_msg:
        notice_text = f"<strong>AI Generation Temporarily Unavailable:</strong> {sanitize_text(error_msg)}. Showing direct evidence from official documents."
    else:
        notice_text = "<strong>Direct Evidence Mode:</strong> Offline lexical retrieval mode active. Showing verified verbatim excerpts retrieved from official policy files."
    return clean_html(f'<div style="background-color:#FEF3C7; border:1px solid #FDE68A; border-radius:10px; padding:10px 14px; margin-bottom:12px; display:flex; align-items:center; gap:10px; font-size:12.5px; color:#92400E;">{info_icon}<div>{notice_text}</div></div>')

