"""
Login screen module for Campus Helpdesk Assistant.
Implements credentials authentication (ID + Password), rate-limit lockout,
and transitions to email OTP verification.
"""

import time
import streamlit as st
from config import settings
from auth.service import authenticate_credentials, check_account_lockout
from auth.otp import create_otp
from auth.mailer import send_otp_email, mask_email
from ui.components import clean_html, render_icon
from ui.assets_svg import LOGO_FULL_SVG, LOGO_GLYPH_SVG


def render_login_page():
    """Renders the FAANG-grade sign-in interface."""
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    
    col_left, col_card, col_right = st.columns([1, 1.4, 1])

    with col_card:
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:24px;">
            <div style="display:inline-block; margin-bottom:12px;">{LOGO_GLYPH_SVG}</div>
            <h2 style="font-size:24px; font-weight:700; color:#0F172A; margin:0 0 6px 0; letter-spacing:-0.02em;">Sign in to Campus Helpdesk</h2>
            <p style="font-size:14px; color:#64748B; margin:0;">Enter your Student Roll Number or Staff ID to continue</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            # Quick credentials hint for testers/evaluators
            st.markdown("""
            <div style="background:#F1F5F9; border:1px solid #E2E8F0; border-radius:8px; padding:10px 14px; margin-bottom:18px; font-size:12px; color:#475569;">
                <div style="font-weight:600; margin-bottom:3px; color:#1E293B;">Demo Evaluation Credentials:</div>
                <div style="display:flex; justify-content:space-between;">
                    <span><strong>Admin:</strong> <code>admin</code> / <code>admin123</code></span>
                    <span><strong>Student:</strong> <code>student</code> / <code>student123</code></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.form("login_credentials_form", clear_on_submit=False):
                user_id_input = st.text_input(
                    "User ID / Student Roll Number",
                    placeholder="e.g. S24CSEU0709 or admin",
                    key="login_user_id"
                )
                password_input = st.text_input(
                    "Password",
                    type="password",
                    placeholder="••••••••••••",
                    key="login_password"
                )

                submit_btn = st.form_submit_button(
                    "Continue with Password →",
                    type="primary",
                    use_container_width=True
                )

            if submit_btn:
                cleaned_id = (user_id_input or "").strip()
                cleaned_pwd = password_input or ""

                if not cleaned_id or not cleaned_pwd:
                    st.error("Please enter both User ID and Password.")
                else:
                    # Authenticate credentials with lockout protection
                    is_ok, reason, user = authenticate_credentials(
                        user_id=cleaned_id,
                        password=cleaned_pwd,
                        ip_address="127.0.0.1"
                    )

                    if not is_ok:
                        if reason == "LOCKED":
                            is_locked, remaining_mins = check_account_lockout(cleaned_id)
                            st.error(f"Account is temporarily locked due to repeated failed attempts. Please try again in {remaining_mins} minutes.")
                        else:
                            st.error("Invalid ID or password.")
                    else:
                        # Credentials verified: generate OTP challenge
                        otp_ok, otp_code_or_err, retry_after = create_otp(cleaned_id)
                        if not otp_ok:
                            if retry_after > 0:
                                st.warning(f"Please wait {retry_after} seconds before requesting a new verification code.")
                            else:
                                st.error(otp_code_or_err)
                        else:
                            raw_otp = otp_code_or_err
                            user_email = user.get("email", "")
                            
                            # Dispatch OTP email
                            mail_success, mail_msg = send_otp_email(
                                to_email=user_email,
                                otp_code=raw_otp,
                                user_name=user.get("name", "Student")
                            )

                            st.session_state.pending_auth = {
                                "user": user,
                                "email": user_email,
                                "masked_email": mask_email(user_email),
                                "raw_otp_dev": raw_otp if settings.DEV_MODE else None,
                                "mail_sent": mail_success,
                                "mail_note": mail_msg,
                                "created_at": time.time()
                            }
                            st.session_state.auth_view = "otp"
                            st.rerun()

        st.markdown("""
        <div style="text-align:center; margin-top:20px; font-size:12px; color:#94A3B8;">
            Protected by Argon2id password hashing and 2-Step Email Verification.
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
