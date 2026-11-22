"""
Visual styles and design tokens for Campus Helpdesk Assistant.
Faithfully recreates the visual language of the reference Dribbble SaaS landing page:
- Soft neutral background canvas (#E9E7E6)
- Main application sheet (28px radius, 1px white border, soft drop shadow) with smooth multi-stop gradient:
  warm peach and cream at left/center, fading to periwinkle blue at top right, and white at bottom.
- Floating pill navigation bar with blur backdrop
- Dashed selection boxes with corner handles and animated cursor glyph
- Floating skeleton and metric cards with subtle bobbing motion
- Original inline SVG robot mascot and chat card preview
- Three-column feature strip with dashed borders and flowing connector arrows
- High-contrast, crystal-clear chat input bar with dark text on white
- Full RBAC and dark/light mode token integration
"""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* =============================================================================
   1. DESIGN TOKENS & SYSTEM VARIABLES
   ============================================================================= */
:root {
    --bg-canvas: #E9E7E6;
    --sheet-bg: radial-gradient(circle at 18% 28%, #FDE4D4 0%, rgba(253, 228, 212, 0) 50%),
                radial-gradient(circle at 88% 16%, #C3D5FB 0%, rgba(195, 213, 251, 0) 48%),
                linear-gradient(180deg, #F8F5F2 0%, #FFFFFF 100%);
    --surface: #FFFFFF;
    --surface-secondary: #F1F5F9;
    --surface-hover: #F8FAFC;
    
    --border: #E2E8F0;
    --border-dashed: rgba(148, 163, 184, 0.45);
    --border-focus: #2F5BEA;
    
    --text-main: #0F172A;
    --text-muted: #64748B;
    --text-light: #94A3B8;
    
    --accent: #2F5BEA;
    --accent-hover: #1E40AF;
    --accent-soft: rgba(47, 91, 234, 0.08);
    --accent-border: rgba(47, 91, 234, 0.2);
    
    --success: #10B981;
    --success-bg: #ECFDF5;
    --success-border: #A7F3D0;
    --success-text: #065F46;
    
    --warning: #F59E0B;
    --warning-bg: #FFFBEB;
    --warning-border: #FDE68A;
    --warning-text: #92400E;
    
    --danger: #EF4444;
    --danger-bg: #FEF2F2;
    --danger-border: #FECACA;
    --danger-text: #991B1B;
    
    --radius-xl: 28px;
    --radius-lg: 20px;
    --radius-md: 12px;
    --radius-sm: 8px;
    --radius-pill: 9999px;
    
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
    --shadow-lg: 0 14px 34px -4px rgba(15, 23, 42, 0.08);
    --shadow-sheet: 0 24px 64px rgba(15, 23, 42, 0.08);
    
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
    border: 1px solid rgba(255, 255, 255, 0.95) !important;
    border-radius: var(--radius-xl) !important;
    box-shadow: var(--shadow-sheet) !important;
    padding: 24px 32px 48px 32px !important;
    max-width: 1240px !important;
    margin: 16px auto 32px auto !important;
    position: relative;
}

/* =============================================================================
   3. FLOATING PILL NAVIGATION BAR
   ============================================================================= */
.nav-pill-wrapper {
    position: sticky;
    top: 12px;
    z-index: 999;
    margin-bottom: 24px;
}

.nav-pill-container {
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.95);
    border-radius: var(--radius-pill);
    padding: 8px 18px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04);
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

h1 { font-size: 32px !important; line-height: 1.2 !important; }
h2 { font-size: 24px !important; line-height: 1.25 !important; }
h3 { font-size: 18px !important; line-height: 1.35 !important; }
h4 { font-size: 15px !important; line-height: 1.4 !important; }

p, span, div {
    font-family: var(--font-sans);
    color: var(--text-main);
}

code {
    font-family: var(--font-mono) !important;
    background-color: var(--surface-secondary) !important;
    color: var(--accent) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 0.88em !important;
    border: 1px solid var(--border) !important;
}

/* =============================================================================
   5. BUTTONS & PILL CONTROLS
   ============================================================================= */
/* All Streamlit Buttons default to smooth rounded pills */
div.stButton > button {
    font-family: var(--font-sans) !important;
    font-weight: 600 !important;
    font-size: 12.5px !important;
    border-radius: var(--radius-pill) !important;
    padding: 7px 12px !important;
    white-space: nowrap !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1px solid var(--border) !important;
    background-color: var(--surface) !important;
    color: var(--text-main) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
}

div.stButton > button:hover {
    border-color: #CBD5E1 !important;
    background-color: #F8FAFC !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06) !important;
}

div.stButton > button:active {
    transform: scale(0.98) !important;
}

/* Primary Button: Solid Vibrant Blue Pill with Soft Glow Shadow */
div.stButton > button[type="primary"] {
    background-color: var(--accent) !important;
    color: #FFFFFF !important;
    border-color: var(--accent) !important;
    box-shadow: 0 4px 14px rgba(47, 91, 234, 0.3) !important;
}

div.stButton > button[type="primary"]:hover {
    background-color: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(47, 91, 234, 0.42) !important;
}

/* =============================================================================
   6. HERO SECTION: DASHED SELECTION BOX & FLOATING CARDS
   ============================================================================= */
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #2F5BEA;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-bottom: 14px;
}

.hero-headline-wrapper {
    display: inline-block;
    position: relative;
    padding: 16px 28px;
    margin: 6px auto 16px auto;
    border: 1.5px dashed rgba(15, 23, 42, 0.22);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.45);
}

.hero-headline {
    font-size: clamp(34px, 5vw, 54px) !important;
    font-weight: 800 !important;
    color: #0D0F14 !important;
    letter-spacing: -0.035em !important;
    line-height: 1.15 !important;
    margin: 0 !important;
}

.corner-handle {
    position: absolute;
    width: 7px;
    height: 7px;
    background: #FFFFFF;
    border: 1.5px solid #0F172A;
    border-radius: 2px;
}
.corner-handle.tl { top: -4px; left: -4px; }
.corner-handle.tr { top: -4px; right: -4px; }
.corner-handle.bl { bottom: -4px; left: -4px; }
.corner-handle.br { bottom: -4px; right: -4px; }

/* Floating Cards bobbing animation */
@keyframes bobSlow {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

@keyframes bobSlowReverse {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(7px); }
}

.floating-card-left {
    background: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    padding: 14px 18px;
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
    animation: bobSlow 6s ease-in-out infinite;
}

.floating-card-right {
    background: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    padding: 14px 18px;
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
    animation: bobSlowReverse 5.5s ease-in-out infinite;
}

/* Animated Hand Cursor Ripple */
@keyframes ripplePulse {
    0% { r: 6; opacity: 0.8; }
    100% { r: 16; opacity: 0; }
}
.cursor-ripple {
    animation: ripplePulse 1.8s ease-out infinite;
}

/* =============================================================================
   7. THREE-COLUMN FEATURE STRIP & FLOWING CONNECTOR ARROWS
   ============================================================================= */
.feature-strip-card {
    border: 1.5px dashed var(--border-dashed);
    border-radius: 24px;
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: blur(10px);
    padding: 24px 20px;
    height: 100%;
    position: relative;
    transition: all 0.2s ease;
}

.feature-strip-card:hover {
    border-color: #2F5BEA;
    background: rgba(255, 255, 255, 0.9);
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
}

.center-grid-container {
    border: 1.5px dashed var(--border-dashed);
    border-radius: 24px;
    background: rgba(255, 255, 255, 0.88);
    background-image: radial-gradient(rgba(148, 163, 184, 0.28) 1.2px, transparent 1.2px);
    background-size: 16px 16px;
    padding: 24px 20px;
    height: 100%;
    position: relative;
    transition: all 0.2s ease;
}

.center-grid-container:hover {
    border-color: #2F5BEA;
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
}

/* Flowing connector arrows stroke dash */
@keyframes strokeDashFlow {
    to {
        stroke-dashoffset: -16;
    }
}
.arrow-dash-flow {
    animation: strokeDashFlow 1.2s linear infinite;
}

/* =============================================================================
   8. CHAT INTERFACE & INPUT BAR (HIGH-CONTRAST & NO RAW CODEBLOCKS)
   ============================================================================= */
.chat-message-row {
    margin-bottom: 18px;
}

.chat-bubble-user {
    background: #2F5BEA;
    color: #FFFFFF;
    border-radius: 18px 18px 4px 18px;
    padding: 14px 18px;
    max-width: 80%;
    box-shadow: 0 4px 16px rgba(47, 91, 234, 0.25);
    font-size: 14.5px;
    line-height: 1.55;
}

.chat-bubble-user * {
    color: #FFFFFF !important;
}

/* Assistant Card Container */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04) !important;
    padding: 18px !important;
    margin-bottom: 16px !important;
}

/* High-Contrast, Crystal-Clear Chat Input Box */
[data-testid="stChatInput"] {
    background-color: #FFFFFF !important;
    border-radius: var(--radius-pill) !important;
    border: 1.5px solid #CBD5E1 !important;
    box-shadow: 0 6px 24px rgba(15, 23, 42, 0.08) !important;
    padding: 4px 8px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: #2F5BEA !important;
    box-shadow: 0 0 0 3px rgba(47, 91, 234, 0.22), 0 8px 30px rgba(15, 23, 42, 0.12) !important;
}

[data-testid="stChatInput"] textarea {
    font-family: var(--font-sans) !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
    color: #0F172A !important;
    background: transparent !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #64748B !important;
    font-size: 13.5px !important;
    opacity: 1 !important;
}

[data-testid="stChatInput"] button {
    background-color: #2F5BEA !important;
    color: #FFFFFF !important;
    border-radius: 50% !important;
    transition: transform 0.15s ease !important;
}

[data-testid="stChatInput"] button:hover {
    transform: scale(1.05) !important;
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
    color: var(--accent);
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
    margin-bottom: 18px;
}

.status-pill-item {
    background: rgba(255, 255, 255, 0.9);
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
    color: var(--text-main);
}

/* Shimmer Loading */
.skeleton-shimmer {
    background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
    background-size: 200% 100%;
    animation: skeletonShimmer 1.5s infinite;
    border-radius: 6px;
}

@keyframes skeletonShimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] .block-container {
    background: var(--surface) !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    padding: 24px 18px !important;
}

/* Responsive Hide for Connector Arrows below 900px */
@media (max-width: 900px) {
    .connector-arrow {
        display: none !important;
    }
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
