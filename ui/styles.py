"""
Visual styles and design tokens for Campus Helpdesk Assistant.
Faithfully recreates the visual language of the reference Calley Dark AI Agent SaaS Dashboard:
- Deep obsidian dark background canvas (#0B0E14)
- Main application sheet (#0E121B, 20px radius, 1px #1E2433 border, soft shadow)
- Calley top breadcrumb navigation (Dashboard > AI Agent)
- Royal blue announcement banner (#1D4ED8 to #2563EB gradient)
- Dark conversational feed with user and agent cards, avatars, and timestamps
- Sleek horizontal quick inquiry chips dock
- High-contrast dark chat input dock (#141824, 1.5px border, blue send button)
- Faculty 1-click evaluator login cards
- Full RBAC integration and responsive layout
"""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* =============================================================================
   1. DESIGN TOKENS & SYSTEM VARIABLES (CALLEY DARK SAAS AESTHETIC)
   ============================================================================= */
:root {
    --bg-canvas: #0B0E14;
    --sheet-bg: #0E121B;
    --surface: #131722;
    --surface-card: #151922;
    --surface-secondary: #181E2C;
    --surface-hover: #1E2536;
    
    --border: #1E2433;
    --border-subtle: #232B3E;
    --border-dashed: rgba(148, 163, 184, 0.22);
    --border-focus: #2563EB;
    
    --text-main: #F8FAFC;
    --text-muted: #94A3B8;
    --text-light: #64748B;
    
    --accent: #2563EB;
    --accent-hover: #1D4ED8;
    --accent-soft: rgba(37, 99, 235, 0.16);
    --accent-border: rgba(37, 99, 235, 0.38);
    
    --success: #10B981;
    --success-bg: rgba(16, 185, 129, 0.14);
    --success-border: rgba(16, 185, 129, 0.3);
    --success-text: #34D399;
    
    --warning: #F59E0B;
    --warning-bg: rgba(245, 158, 11, 0.14);
    --warning-border: rgba(245, 158, 11, 0.3);
    --warning-text: #FBBF24;
    
    --danger: #EF4444;
    --danger-bg: rgba(239, 68, 68, 0.14);
    --danger-border: rgba(239, 68, 68, 0.3);
    --danger-text: #F87171;
    
    --radius-xl: 22px;
    --radius-lg: 16px;
    --radius-md: 10px;
    --radius-sm: 6px;
    --radius-pill: 9999px;
    
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
    --shadow-lg: 0 14px 34px rgba(0, 0, 0, 0.55);
    --shadow-sheet: 0 20px 60px rgba(0, 0, 0, 0.65);
    
    --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

/* =============================================================================
   2. PAGE CANVAS & MAIN SHEET CONTAINER
   ============================================================================= */
html, body, [data-testid="stAppViewContainer"] {
    font-family: var(--font-sans);
    color: var(--text-main);
    background-color: var(--bg-canvas) !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Streamlit Header chrome removal */
#MainMenu, header, footer, div[data-testid="stDecoration"] {
    visibility: hidden;
    height: 0;
}

header[data-testid="stHeader"] {
    background: transparent !important;
    z-index: 10;
}

/* Main App Sheet */
.main .block-container {
    background: var(--sheet-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-xl) !important;
    box-shadow: var(--shadow-sheet) !important;
    padding: 20px 28px 40px 28px !important;
    max-width: 1240px !important;
    margin: 12px auto 28px auto !important;
    position: relative;
}

/* =============================================================================
   3. FLOATING PILL NAVIGATION BAR
   ============================================================================= */
.nav-pill-wrapper {
    position: sticky;
    top: 10px;
    z-index: 999;
    margin-bottom: 20px;
}

.nav-pill-container {
    background: rgba(14, 18, 27, 0.94);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border);
    border-radius: var(--radius-pill);
    padding: 7px 18px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

/* =============================================================================
   4. TYPOGRAPHY & HEADINGS
   ============================================================================= */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-sans) !important;
    font-weight: 700 !important;
    color: var(--text-main) !important;
    letter-spacing: -0.02em !important;
}

h1 { font-size: 30px !important; line-height: 1.2 !important; }
h2 { font-size: 22px !important; line-height: 1.25 !important; }
h3 { font-size: 17px !important; line-height: 1.35 !important; }
h4 { font-size: 14.5px !important; line-height: 1.4 !important; }

p, span, div {
    font-family: var(--font-sans);
    color: var(--text-main);
}

code {
    font-family: var(--font-mono) !important;
    background-color: var(--surface-secondary) !important;
    color: #60A5FA !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 0.88em !important;
    border: 1px solid var(--border) !important;
}

/* =============================================================================
   5. BUTTONS & PILL CONTROLS (CALLEY SAAS THEME)
   ============================================================================= */
div.stButton > button {
    font-family: var(--font-sans) !important;
    font-weight: 600 !important;
    font-size: 12.5px !important;
    border-radius: var(--radius-pill) !important;
    padding: 7px 14px !important;
    white-space: nowrap !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1px solid var(--border-subtle) !important;
    background-color: var(--surface-card) !important;
    color: var(--text-main) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
}

div.stButton > button:hover {
    border-color: #3B82F6 !important;
    background-color: var(--surface-hover) !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
}

div.stButton > button:active {
    transform: scale(0.98) !important;
}

/* Primary Button: Vibrant Royal Blue Pill */
div.stButton > button[type="primary"] {
    background-color: var(--accent) !important;
    color: #FFFFFF !important;
    border-color: var(--accent) !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
}

div.stButton > button[type="primary"]:hover {
    background-color: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.45) !important;
}

/* =============================================================================
   6. CALLEY DASHBOARD HEADER, BREADCRUMB & ANNOUNCEMENT BANNER
   ============================================================================= */
.calley-breadcrumb-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 12px;
    margin-bottom: 12px;
    border-bottom: 1px solid var(--border);
}

.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #60A5FA;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-bottom: 12px;
}

.hero-headline-wrapper {
    display: inline-block;
    position: relative;
    padding: 16px 28px;
    margin: 6px auto 14px auto;
    border: 1.5px dashed rgba(96, 165, 250, 0.4);
    border-radius: 20px;
    background: rgba(19, 23, 34, 0.85);
}

.hero-headline {
    font-size: clamp(32px, 5vw, 50px) !important;
    font-weight: 800 !important;
    color: #FFFFFF !important;
    letter-spacing: -0.035em !important;
    line-height: 1.15 !important;
    margin: 0 !important;
}

.corner-handle {
    position: absolute;
    width: 7px;
    height: 7px;
    background: #2563EB;
    border: 1.5px solid #FFFFFF;
    border-radius: 2px;
}
.corner-handle.tl { top: -4px; left: -4px; }
.corner-handle.tr { top: -4px; right: -4px; }
.corner-handle.bl { bottom: -4px; left: -4px; }
.corner-handle.br { bottom: -4px; right: -4px; }

.floating-card-left {
    background: #141824;
    border: 1px solid #1E2433;
    border-radius: 16px;
    padding: 14px 18px;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.4);
}

.floating-card-right {
    background: #141824;
    border: 1px solid #1E2433;
    border-radius: 16px;
    padding: 14px 18px;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.4);
}

.feature-strip-card {
    border: 1.5px dashed var(--border-dashed);
    border-radius: 24px;
    background: rgba(20, 24, 36, 0.75);
    backdrop-filter: blur(10px);
    padding: 24px 20px;
    height: 100%;
}

.center-grid-container {
    border: 1.5px dashed var(--border-dashed);
    border-radius: 24px;
    background: rgba(20, 24, 36, 0.85);
    background-image: radial-gradient(rgba(148, 163, 184, 0.15) 1.2px, transparent 1.2px);
    background-size: 16px 16px;
    padding: 24px 20px;
    height: 100%;
}

.calley-breadcrumb {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-light);
}

.calley-breadcrumb .sep {
    color: #475569;
    font-size: 11px;
}

.calley-breadcrumb .active-item {
    color: #FFFFFF;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 6px;
}

.calley-announcement-banner {
    background: linear-gradient(90deg, #1D4ED8 0%, #2563EB 100%);
    border-radius: 12px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #FFFFFF;
    margin-bottom: 18px;
    box-shadow: 0 4px 18px rgba(37, 99, 235, 0.3);
}

.calley-announcement-banner * {
    color: #FFFFFF !important;
}

.calley-chat-time-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 16px 0 20px 0;
    position: relative;
    text-align: center;
}

.calley-chat-time-divider::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    height: 1px;
    background: var(--border);
    z-index: 1;
}

.calley-chat-time-divider span {
    background: var(--sheet-bg);
    padding: 0 14px;
    font-size: 11.5px;
    font-weight: 600;
    color: var(--text-light);
    position: relative;
    z-index: 2;
    letter-spacing: 0.03em;
}

/* =============================================================================
   7. CHAT MESSAGE CARDS (CALLEY DARK SAAS AESTHETIC)
   ============================================================================= */
.calley-msg-user-container {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 16px;
}

.calley-msg-assistant-container {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 16px;
}

.calley-avatar-circle {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
    flex-shrink: 0;
}

.calley-avatar-user {
    background: #1E293B;
    color: #93C5FD;
    border: 1px solid #334155;
}

.calley-avatar-bot {
    background: #1E3A8A;
    color: #60A5FA;
    border: 1px solid #2563EB;
}

.calley-msg-bubble-user {
    background: #151922;
    border: 1px solid #232B3A;
    border-radius: 14px;
    padding: 12px 18px;
    max-width: 82%;
    color: #F1F5F9;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.calley-msg-bubble-bot {
    background: #182030;
    border: 1px solid #25334D;
    border-radius: 14px;
    padding: 14px 20px;
    max-width: 88%;
    color: #F1F5F9;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}

/* Assistant Card Container in Streamlit */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: var(--surface-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35) !important;
    padding: 16px !important;
    margin-bottom: 14px !important;
}

/* High-Contrast, Crystal-Clear Dark Chat Input Box */
[data-testid="stChatInput"] {
    background-color: #141824 !important;
    border-radius: var(--radius-lg) !important;
    border: 1.5px solid #232B3E !important;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.45) !important;
    padding: 4px 10px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25), 0 8px 30px rgba(0, 0, 0, 0.6) !important;
}

[data-testid="stChatInput"] textarea {
    font-family: var(--font-sans) !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #F8FAFC !important;
    background: transparent !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #64748B !important;
    font-size: 13.5px !important;
    opacity: 1 !important;
}

[data-testid="stChatInput"] button {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border-radius: 50% !important;
    transition: transform 0.15s ease !important;
}

[data-testid="stChatInput"] button:hover {
    transform: scale(1.05) !important;
    background-color: #1D4ED8 !important;
}

/* =============================================================================
   8. STREAMLIT FORM CONTROLS & INPUTS (DARK MODE STYLING)
   ============================================================================= */
div[data-baseweb="input"] {
    background-color: #141824 !important;
    border: 1px solid #232B3E !important;
    border-radius: var(--radius-md) !important;
}

div[data-baseweb="input"]:focus-within {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
}

div[data-baseweb="input"] input {
    color: #F8FAFC !important;
    font-family: var(--font-sans) !important;
}

div[data-baseweb="select"] > div {
    background-color: #141824 !important;
    border: 1px solid #232B3E !important;
    border-radius: var(--radius-md) !important;
    color: #F8FAFC !important;
}

/* Tabs */
div[data-baseweb="tab-list"] {
    border-bottom: 1px solid var(--border) !important;
    gap: 8px !important;
}

button[data-baseweb="tab"] {
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border-bottom-width: 2px !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #60A5FA !important;
    border-bottom-color: #2563EB !important;
}

/* Expander */
div[data-testid="stExpander"] {
    background-color: #131722 !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
}

div[data-testid="stExpander"] summary {
    color: #CBD5E1 !important;
    font-weight: 600 !important;
}

/* Alerts / Info Boxes */
div[data-testid="stAlert"] {
    background-color: #151922 !important;
    border: 1px solid #232B3E !important;
    border-radius: var(--radius-md) !important;
    color: #F1F5F9 !important;
}

/* =============================================================================
   9. BADGES & STATUS STRIPS
   ============================================================================= */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11.5px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: var(--radius-pill);
    letter-spacing: 0.02em;
    line-height: 1.3;
}

.badge-accent {
    background: var(--accent-soft);
    color: #60A5FA;
    border: 1px solid var(--accent-border);
}

.badge-success {
    background: var(--success-bg);
    color: var(--success-text);
    border: 1px solid var(--success-border);
}

.badge-warning {
    background: var(--warning-bg);
    color: var(--warning-text);
    border: 1px solid var(--warning-border);
}

.badge-danger {
    background: var(--danger-bg);
    color: var(--danger-text);
    border: 1px solid var(--danger-border);
}

.badge-muted {
    background: var(--surface-secondary);
    color: var(--text-muted);
    border: 1px solid var(--border);
}

/* Status Pill Strip */
.status-pill-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 14px;
    margin-bottom: 16px;
}

.status-pill-item {
    background: #141824;
    border: 1px solid var(--border);
    border-radius: var(--radius-pill);
    padding: 6px 14px;
    font-size: 12px;
    color: var(--text-muted);
    display: inline-flex;
    align-items: center;
    gap: 7px;
    box-shadow: var(--shadow-sm);
}

.status-pill-item strong {
    color: #F1F5F9;
}

/* Shimmer Loading */
.skeleton-shimmer {
    background: linear-gradient(90deg, #182030 25%, #232B3E 50%, #182030 75%);
    background-size: 200% 100%;
    animation: skeletonShimmer 1.5s infinite;
    border-radius: 6px;
}

@keyframes skeletonShimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* =============================================================================
   10. SIDEBAR STYLING (CALLEY DARK SAAS AESTHETIC)
   ============================================================================= */
[data-testid="stSidebar"] {
    background-color: #0B0E14 !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] .block-container {
    background: #0B0E14 !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    padding: 20px 16px !important;
}

/* Support Online Indicator */
.online-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11.5px;
    font-weight: 600;
    color: #10B981;
}

.online-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #10B981;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
}

/* Accessibility: Respect Reduced Motion */
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
</style>
"""
