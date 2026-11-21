"""
Global CSS design system for AI-Powered Campus Helpdesk Assistant.
Enforces custom editorial SaaS aesthetic with deep navy palette, Plus Jakarta Sans typography,
chrome removal, layered shadows, responsive layouts, and motion guidelines.
"""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* =============================================================================
   1. DESIGN TOKENS (CSS VARIABLES)
   ============================================================================= */
:root {
    --navy: #0B1F3A;
    --navy-2: #13294B;
    --navy-light: #1E3A8A;
    --accent: #2563EB;
    --accent-hover: #1D4ED8;
    --accent-soft: #E8F0FE;
    --bg: #F6F8FB;
    --surface: #FFFFFF;
    --border: #E2E8F0;
    --border-hover: #CBD5E1;
    --text: #0F172A;
    --text-muted: #64748B;
    --text-light: #94A3B8;

    /* Status Colors */
    --success: #16A34A;
    --success-bg: #F0FDF4;
    --success-border: #BBF7D0;
    --warning: #D97706;
    --warning-bg: #FFFBEB;
    --warning-border: #FDE68A;
    --danger: #DC2626;
    --danger-bg: #FEF2F2;
    --danger-border: #FECACA;

    /* Spacing & Sizing */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-full: 9999px;
    --shadow-soft: 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.06);
    --shadow-hover: 0 4px 6px rgba(15, 23, 42, 0.05), 0 12px 32px rgba(15, 23, 42, 0.1);
    --shadow-card: 0 2px 4px rgba(11, 31, 58, 0.03), 0 1px 2px rgba(11, 31, 58, 0.02);
}

/* =============================================================================
   2. GLOBAL RESET & BASE TYPOGRAPHY
   ============================================================================= */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: var(--text);
    background-color: var(--bg);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: -0.02em !important;
    font-weight: 700 !important;
    color: var(--navy);
    margin-top: 0;
}

h1 { font-size: 44px !important; line-height: 1.15 !important; }
h2 { font-size: 28px !important; line-height: 1.25 !important; }
h3 { font-size: 20px !important; line-height: 1.35 !important; }
h4 { font-size: 16px !important; line-height: 1.4 !important; }

p, span, div, label {
    font-size: 14px;
    line-height: 1.55;
}

small, .text-sm {
    font-size: 12px;
    line-height: 1.4;
}

code, pre, .font-mono {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}

/* =============================================================================
   3. CHROME REMOVAL & LAYOUT STRUCTURE
   ============================================================================= */
/* Hide Streamlit Default Chrome */
header[data-testid="stHeader"],
footer,
#MainMenu,
div[data-testid="stDecoration"],
button[title="View app in Streamlit Community Cloud"],
.stDeployButton {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}

/* Max Container Width & 8px Grid Alignment */
.block-container {
    max-width: 1180px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    margin: 0 auto !important;
}

/* =============================================================================
   4. NAVIGATION BAR (TOP CUSTOM NAV)
   ============================================================================= */
.top-navbar-container {
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 10px 18px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: var(--shadow-soft);
    position: sticky;
    top: 12px;
    z-index: 999;
}

.brand-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
    text-decoration: none;
    color: var(--navy);
}

.brand-icon-box {
    width: 36px;
    height: 36px;
    background: var(--navy);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--surface);
}

.brand-title {
    font-weight: 800;
    font-size: 15px;
    letter-spacing: -0.01em;
    color: var(--navy);
    line-height: 1.2;
}

.brand-subtitle {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-muted);
}

/* Nav Item styling inside custom container */
.nav-links-row {
    display: flex;
    align-items: center;
    gap: 6px;
}

.nav-link-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-radius: var(--radius-sm);
    font-size: 13px;
    font-weight: 600;
    color: var(--text-muted);
    text-decoration: none;
    transition: all 0.15s ease;
    border: 1px solid transparent;
    cursor: pointer;
}

.nav-link-btn:hover {
    color: var(--navy);
    background-color: var(--bg);
}

.nav-link-btn.active {
    color: var(--accent);
    background-color: var(--accent-soft);
    border-color: rgba(37, 99, 235, 0.2);
}

/* Restyle Streamlit Radio when used for Nav */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex;
    flex-direction: row;
    gap: 8px;
    justify-content: center;
    background: var(--surface);
    padding: 6px 10px;
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-card);
}

div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    background: transparent;
    padding: 8px 16px;
    border-radius: var(--radius-sm);
    border: 1px solid transparent;
    font-weight: 600;
    font-size: 13px;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.15s ease;
}

div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
    background: var(--bg);
    color: var(--navy);
}

div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] {
    background: var(--accent-soft);
    color: var(--accent) !important;
    border-color: rgba(37, 99, 235, 0.25);
}

/* =============================================================================
   5. BANNERS & NOTICES
   ============================================================================= */
.demo-alert-banner {
    background-color: var(--warning-bg);
    border: 1px solid var(--warning-border);
    border-left: 4px solid var(--warning);
    border-radius: var(--radius-md);
    padding: 12px 18px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #92400E;
    font-size: 13px;
    font-weight: 500;
    box-shadow: 0 1px 2px rgba(217, 119, 6, 0.05);
}

.disclaimer-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 16px 20px;
    margin-top: 24px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    color: var(--text-muted);
    font-size: 13px;
    line-height: 1.5;
}

/* =============================================================================
   6. CARDS & HERO SECTIONS
   ============================================================================= */
/* Subtle aurora background with fine mesh */
.hero-container {
    background: linear-gradient(135deg, #0B1F3A 0%, #13294B 50%, #1E3A8A 100%);
    border-radius: var(--radius-lg);
    padding: 44px 40px;
    color: #FFFFFF;
    position: relative;
    overflow: hidden;
    margin-bottom: 28px;
    box-shadow: var(--shadow-soft);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-container::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -20%;
    width: 140%;
    height: 180%;
    background: radial-gradient(circle at 70% 30%, rgba(37, 99, 235, 0.25) 0%, transparent 60%),
                radial-gradient(circle at 20% 80%, rgba(19, 41, 75, 0.4) 0%, transparent 50%);
    pointer-events: none;
    animation: auroraMesh 16s ease-in-out infinite alternate;
}

@keyframes auroraMesh {
    0% { transform: translateY(0px) rotate(0deg); }
    100% { transform: translateY(-20px) rotate(2deg); }
}

.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(37, 99, 235, 0.25);
    border: 1px solid rgba(96, 165, 250, 0.35);
    color: #BFDBFE;
    padding: 4px 12px;
    border-radius: var(--radius-full);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 16px;
}

.hero-title {
    font-size: 38px;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.025em;
    margin-bottom: 14px;
    color: #FFFFFF;
}

.hero-subtitle {
    font-size: 16px;
    line-height: 1.55;
    color: #CBD5E1;
    max-width: 580px;
    margin-bottom: 26px;
}

/* Illustrative Product Preview Card */
.preview-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--radius-md);
    padding: 20px;
    color: var(--text);
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.2);
}

.preview-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-bottom: 12px;
}

.preview-bubble-user {
    background: var(--navy);
    color: #FFFFFF;
    padding: 10px 14px;
    border-radius: 12px 12px 2px 12px;
    font-size: 13px;
    font-weight: 500;
    margin-left: 20%;
    margin-bottom: 12px;
    text-align: right;
}

.preview-bubble-ai {
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--navy);
    padding: 12px 14px;
    border-radius: 12px 12px 12px 2px;
    font-size: 13px;
    line-height: 1.5;
    margin-right: 15%;
    margin-bottom: 10px;
}

/* Generic Custom Card */
.custom-card {
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 24px;
    box-shadow: var(--shadow-soft);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.custom-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
    border-color: var(--border-hover);
}

/* Live Status Strip */
.status-strip-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 28px;
}

.status-metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 16px 18px;
    box-shadow: var(--shadow-card);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.status-metric-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.status-metric-value {
    font-size: 18px;
    font-weight: 800;
    color: var(--navy);
    letter-spacing: -0.01em;
}

/* =============================================================================
   7. BADGES & PILLS
   ============================================================================= */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 9px;
    border-radius: var(--radius-full);
    font-size: 11px;
    font-weight: 600;
    line-height: 1.3;
}

.badge-navy {
    background-color: var(--navy);
    color: #FFFFFF;
}

.badge-accent {
    background-color: var(--accent-soft);
    color: var(--accent);
    border: 1px solid rgba(37, 99, 235, 0.2);
}

.badge-success {
    background-color: var(--success-bg);
    color: var(--success);
    border: 1px solid var(--success-border);
}

.badge-warning {
    background-color: var(--warning-bg);
    color: var(--warning);
    border: 1px solid var(--warning-border);
}

.badge-danger {
    background-color: var(--danger-bg);
    color: var(--danger);
    border: 1px solid var(--danger-border);
}

.badge-muted {
    background-color: #F1F5F9;
    color: var(--text-muted);
    border: 1px solid var(--border);
}

.citation-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #F8FAFC;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 3px 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    color: var(--navy);
    margin-right: 6px;
    margin-bottom: 6px;
}

/* =============================================================================
   8. CHAT INTERFACE & BUBBLES
   ============================================================================= */
.chat-stream-container {
    display: flex;
    flex-direction: column;
    gap: 18px;
    margin-bottom: 30px;
}

.chat-message-row {
    display: flex;
    width: 100%;
}

.chat-message-row.user {
    justify-content: flex-end;
}

.chat-message-row.assistant {
    justify-content: flex-start;
}

.chat-bubble-user {
    max-width: 78%;
    background-color: var(--navy);
    color: #FFFFFF;
    border-radius: 16px 16px 4px 16px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(11, 31, 58, 0.08);
}

.chat-bubble-assistant {
    max-width: 86%;
    background-color: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 16px 16px 16px 4px;
    padding: 20px 22px;
    box-shadow: var(--shadow-soft);
}

.chat-bubble-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    font-size: 12px;
    color: var(--text-muted);
}

.chat-bubble-content {
    font-size: 14.5px;
    line-height: 1.65;
    color: var(--text);
}

.chat-bubble-content p {
    margin-bottom: 10px;
}

.chat-bubble-content p:last-child {
    margin-bottom: 0;
}

/* Source Card Container */
.sources-card-wrapper {
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px dashed var(--border);
}

.source-item-card {
    background-color: #F8FAFC;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 12px;
}

/* Shimmer Skeleton Loader */
.skeleton-box {
    background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: var(--radius-sm);
}

@keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* Empty State Box */
.empty-state-box {
    text-align: center;
    padding: 48px 24px;
    background: var(--surface);
    border: 1px dashed var(--border);
    border-radius: var(--radius-lg);
    color: var(--text-muted);
}

.empty-state-icon {
    width: 48px;
    height: 48px;
    margin: 0 auto 12px auto;
    color: var(--text-light);
}

/* =============================================================================
   9. STREAMLIT WIDGET OVERRIDES
   ============================================================================= */
/* Custom Button */
div.stButton > button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    border-radius: var(--radius-sm) !important;
    padding: 8px 18px !important;
    transition: all 0.15s ease !important;
    border: 1px solid var(--border) !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}

div.stButton > button:hover {
    border-color: var(--border-hover) !important;
    transform: translateY(-1px) !important;
}

div.stButton > button:active {
    transform: scale(0.98) !important;
}

div.stButton > button[kind="primary"] {
    background-color: var(--navy) !important;
    color: #FFFFFF !important;
    border-color: var(--navy) !important;
}

div.stButton > button[kind="primary"]:hover {
    background-color: var(--navy-2) !important;
    border-color: var(--navy-2) !important;
}

/* Text Input & Chat Input */
div[data-testid="stTextInput"] input,
div[data-testid="stChatInput"] textarea {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    background-color: var(--surface) !important;
    font-size: 14px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}

/* File Uploader */
div[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1px dashed var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 16px !important;
    transition: border-color 0.2s ease !important;
}

div[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}

/* Dataframe wrapper */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    background: var(--surface);
    overflow: hidden;
}

/* Expander */
div[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background-color: var(--surface) !important;
    box-shadow: none !important;
}

/* =============================================================================
   10. ANIMATIONS & ACCESSIBILITY
   ============================================================================= */
.fade-up {
    animation: fadeUp 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Reduced Motion Override */
@media (prefers-reduced-motion: reduce) {
    *, ::before, ::after {
        animation-delay: -1ms !important;
        animation-duration: 1ms !important;
        animation-iteration-count: 1 !important;
        background-attachment: initial !important;
        scroll-behavior: auto !important;
        transition-delay: 0s !important;
        transition-duration: 0s !important;
    }
}

/* Mobile & Tablet Responsiveness */
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .hero-container {
        padding: 28px 20px !important;
    }

    .hero-title {
        font-size: 26px !important;
    }

    .status-strip-grid {
        grid-template-columns: 1fr 1fr !important;
    }

    .top-navbar-container {
        flex-direction: column;
        gap: 12px;
        align-items: flex-start;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] {
        flex-wrap: wrap;
    }
}
</style>
"""
