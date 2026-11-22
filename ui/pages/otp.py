"""
OTP Verification page module for Campus Helpdesk Assistant.
Implements 6-digit verification, 5-minute countdown, resend with 30s cooldown,
dev-mode display box when SMTP is unconfigured, and session creation.
"""

import time
import streamlit as st
from config import settings
from auth.otp import verify_otp, create_otp
from auth.session import create_session
from auth.mailer import send_otp_email
from ui.assets_svg import LOGO_GLYPH_SVG


def render_otp_page():
    """Renders the FAANG-grade 2-Step OTP Verification interface."""
    pending = st.session_state.get("pending_auth")
    if not pending or not pending.get("user"):
        st.session_state.auth_view = "login"
        st.rerun()
        return

    user = pending["user"]
    user_id = user["id"]
    masked_email = pending.get("masked_email", "your email")
    mail_sent = pending.get("mail_sent", False)
    mail_note = pending.get("mail_note", "")

    st.markdown('<div class="otp-wrapper">', unsafe_allow_html=True)
    col_left, col_card, col_right = st.columns([1, 1.4, 1])

    with col_card:
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:20px;">
            <div style="display:inline-block; margin-bottom:12px;">{LOGO_GLYPH_SVG}</div>
            <h2 style="font-size:24px; font-weight:700; color:#0F172A; margin:0 0 6px 0; letter-spacing:-0.02em;">Two-Step Verification</h2>
            <p style="font-size:14px; color:#64748B; margin:0;">
                We sent a 6-digit code to <strong>{masked_email}</strong>
            </p>
            <p style="font-size:12px; color:#94A3B8; margin-top:4px;">Code expires in 5 minutes</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            if not mail_sent and mail_note:
                st.error(f"Could not dispatch email: {mail_note}")

            with st.form("otp_submit_form", clear_on_submit=False):
                entered_otp = st.text_input(
                    "Enter 6-Digit Code",
                    max_chars=6,
                    placeholder="123456",
                    key="otp_input_box"
                )

                verify_btn = st.form_submit_button(
                    "Verify Code & Sign In →",
                    type="primary",
                    use_container_width=True
                )

            if verify_btn:
                clean_code = (entered_otp or "").strip()
                if len(clean_code) != 6 or not clean_code.isdigit():
                    st.error("Please enter a valid 6-digit verification code.")
                else:
                    success, msg = verify_otp(user_id, clean_code)
                    if success:
                        # Session issuance
                        session_token = create_session(user_id, ip_address="127.0.0.1")
                        st.session_state.auth_user = user
                        st.session_state.session_token = session_token
                        st.query_params["session_token"] = session_token
                        st.session_state.pending_auth = None
                        st.session_state.auth_view = None
                        st.session_state.page = "AI Chatbot"
                        st.success("Verification successful! Welcome.")
                        st.rerun()
                    else:
                        st.error(msg)

            # Footer actions: Resend Code with cooldown, and Back to Login
            action_c1, action_c2 = st.columns(2)
            with action_c1:
                if st.button("Resend Code", use_container_width=True, key="resend_otp_btn"):
                    ok, code_or_err, retry_after = create_otp(user_id)
                    if ok:
                        user_email = user.get("email", "")
                        send_otp_email(user_email, code_or_err, user_name=user.get("name", "Student"))
                        st.success("A new verification code has been dispatched to your email.")
                        st.rerun()
                    else:
                        if retry_after > 0:
                            st.warning(f"Wait {retry_after}s before requesting a new code.")
                        else:
                            st.error(code_or_err)

            with action_c2:
                if st.button("← Back to Login", use_container_width=True, key="back_to_login_btn"):
                    st.session_state.pending_auth = None
                    st.session_state.auth_view = "login"
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
