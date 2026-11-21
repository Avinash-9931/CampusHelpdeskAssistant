"""
AI-Powered Campus Helpdesk Assistant
Streamlit Web Application Entry Point
Milestone 2 | Course: SCSE4041 Prompt Engineering | Team Invictus (PE-B01-15)
Primary Developers: Avinash Kumar (Backend), Divyanshu Raj (Frontend)
"""

import streamlit as st
from config import settings
from core.retriever import KnowledgeBase
from core.ai_engine import AIEngine
from core.prompt_manager import PromptManager
from core.chatbot import ChatbotController

from ui.styles import GLOBAL_CSS
from ui.components import render_icon, render_badge
from ui.pages.home import render_home_page
from ui.pages.chatbot import render_chatbot_page
from ui.pages.knowledge_base import render_knowledge_base_page
from ui.pages.evaluation import render_evaluation_page
from ui.pages.about import render_about_page


# ==============================================================================
# 1. PAGE CONFIGURATION & METADATA
# ==============================================================================
st.set_page_config(
    page_title="Campus Helpdesk Assistant | Invictus",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ==============================================================================
# 2. SESSION STATE INITIALIZATION & RESOURCE CACHING
# ==============================================================================
def init_session_state():
    """Initializes persistent components and session state variables."""
    if "retriever" not in st.session_state:
        st.session_state.retriever = KnowledgeBase()

    if "ai_engine" not in st.session_state:
        st.session_state.ai_engine = AIEngine()

    if "prompt_manager" not in st.session_state:
        st.session_state.prompt_manager = PromptManager()

    if "chatbot" not in st.session_state:
        st.session_state.chatbot = ChatbotController(
            retriever=st.session_state.retriever,
            ai_engine=st.session_state.ai_engine,
            prompt_manager=st.session_state.prompt_manager
        )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "demo_active" not in st.session_state:
        # Check if demo document is currently in the knowledge base
        st.session_state.demo_active = "university_policy_demo.pdf" in st.session_state.retriever.documents

    if "page" not in st.session_state:
        st.session_state.page = "Home"

    if "prefer_semantic" not in st.session_state:
        st.session_state.prefer_semantic = False

    if "active_prompt_version" not in st.session_state:
        st.session_state.active_prompt_version = "final"


init_session_state()

# Inject Global CSS Tokens & Styles
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ==============================================================================
# 3. TOP NAVIGATION BAR
# ==============================================================================
PAGES = [
    "Home",
    "AI Chatbot",
    "Knowledge Base",
    "Test / Evaluation",
    "About Project"
]

PAGE_ICONS = {
    "Home": "building",
    "AI Chatbot": "message-square",
    "Knowledge Base": "database",
    "Test / Evaluation": "terminal",
    "About Project": "info"
}

# Top Nav Header Container
nav_brand_col, nav_links_col = st.columns([1.1, 2.9], gap="medium")

with nav_brand_col:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; padding:6px 0;">
        <div style="width:38px; height:38px; background:var(--navy); border-radius:8px; display:flex; align-items:center; justify-content:center; color:#FFFFFF;">
            {render_icon("graduation-cap", size=20)}
        </div>
        <div>
            <div style="font-weight:800; font-size:15px; color:var(--navy); line-height:1.2; letter-spacing:-0.01em;">
                Campus Helpdesk Assistant
            </div>
            <div style="font-size:11px; font-weight:600; color:var(--text-muted);">
                Team Invictus · SCSE4041 · Milestone 2
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with nav_links_col:
    # Top nav buttons row with visual active indication
    btn_cols = st.columns(5, gap="small")
    for idx, page_name in enumerate(PAGES):
        is_active = (st.session_state.page == page_name)
        with btn_cols[idx]:
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{page_name}", key=f"nav_top_{page_name}", type=btn_type, use_container_width=True):
                st.session_state.page = page_name
                st.rerun()

st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin:12px 0 20px 0;'>", unsafe_allow_html=True)


# ==============================================================================
# 4. SIDEBAR SETTINGS (COLLAPSIBLE / OPTIONAL)
# ==============================================================================
with st.sidebar:
    st.markdown(f"### {render_icon('terminal', size=16)} System Controls", unsafe_allow_html=True)

    # API Key Configuration
    current_key = st.session_state.ai_engine.api_key
    user_api_key = st.text_input(
        "Gemini API Key (Optional)",
        value=current_key,
        type="password",
        help="Optional Google AI Studio key. If left blank, system operates in verified offline lexical fallback mode."
    )
    if user_api_key != current_key:
        st.session_state.ai_engine.update_key(user_api_key)
        st.rerun()

    # Retrieval Tier Selector
    if st.session_state.ai_engine.is_available():
        retrieval_pref = st.selectbox(
            "Retrieval Method",
            options=["Semantic (Gemini Embeddings)", "Lexical (TF-IDF N-Grams)"],
            index=0 if st.session_state.prefer_semantic else 1
        )
        st.session_state.prefer_semantic = (retrieval_pref == "Semantic (Gemini Embeddings)")
    else:
        st.markdown("""
        <div style="font-size:12px; color:var(--text-muted); background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:10px;">
            <strong>Active Tier:</strong> Lexical (TF-IDF)<br>
            <span style="font-size:11px;">Running in zero-key offline evidence mode.</span>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.prefer_semantic = False

    # Prompt Template Selection
    st.session_state.active_prompt_version = st.selectbox(
        "Prompt Template",
        options=["final", "v3", "v2", "v1"],
        format_func=lambda x: f"Prompt: {x.upper()} {'(Optimized)' if x=='final' else ''}",
        index=0
    )

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:11.5px; color:var(--text-muted); line-height:1.5;">
        <strong>Campus Helpdesk Assistant</strong><br>
        SCSE4041 Milestone 2 · C1<br>
        Team Invictus (PE-B01-15)
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# 5. PAGE ROUTER
# ==============================================================================
current_page = st.session_state.page

if current_page == "Home":
    render_home_page()
elif current_page == "AI Chatbot":
    render_chatbot_page()
elif current_page == "Knowledge Base":
    render_knowledge_base_page()
elif current_page == "Test / Evaluation":
    render_evaluation_page()
elif current_page == "About Project":
    render_about_page()
else:
    st.session_state.page = "Home"
    render_home_page()
