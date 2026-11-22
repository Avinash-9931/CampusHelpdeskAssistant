"""
Login screen module for Campus Helpdesk Assistant.
Implements:
1. Google / Email One-Time Passcode (OTP) passwordless sign-in with auto student enrollment.
2. Institutional credentials authentication (Roll No / ID + Password) with rate-limit lockout.
3. Student self-service account registration with instant OTP email verification.
"""

import time
import streamlit as st
from config import settings
from auth.service import (
    authenticate_credentials,
    check_account_lockout,
    create_user,
    login_or_register_with_email,
    get_user_by_email
)
from auth.security import validate_password_policy
from auth.otp import create_otp
from auth.mailer import send_otp_email, mask_email
from ui.components import clean_html, render_icon
from ui.assets_svg import LOGO_FULL_SVG, LOGO_GLYPH_SVG, GOOGLE_ICON_SVG


def render_login_page():
    """Renders the FAANG-grade unified sign-in & registration portal."""
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    
    col_left, col_card, col_right = st.columns([1, 1.45, 1])

    with col_card:
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:20px;">
            <div style="display:inline-block; margin-bottom:10px;">{LOGO_GLYPH_SVG}</div>
            <h2 style="font-size:24px; font-weight:700; color:#0F172A; margin:0 0 6px 0; letter-spacing:-0.02em;">Campus Helpdesk Portal</h2>
            <p style="font-size:13.5px; color:#64748B; margin:0;">Sign in or create your student account to access AI assistance</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            tab_google, tab_id, tab_create = st.tabs([
                "🔑 Google / Email OTP",
                "🎓 Student / Staff ID",
                "✨ Create Account"
            ])

            # ==================================================================
            # TAB 1: GOOGLE / EMAIL OTP SIGN IN
            # ==================================================================
            with tab_google:
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:9px; margin:8px 0 14px 0; padding:10px 14px; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px;">
                    {GOOGLE_ICON_SVG}
                    <div style="font-size:13px; color:#334155; line-height:1.4;">
                        <strong>Fast Passwordless Access:</strong> Enter your Google (@gmail.com) or campus email to receive an instant 6-digit login code.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.form("google_email_otp_form", clear_on_submit=False):
                    email_input = st.text_input(
                        "Google / Campus Email Address",
                        placeholder="e.g. yourname@gmail.com",
                        key="login_google_email"
                    )

                    submit_google = st.form_submit_button(
                        "Send Verification Code to Email →",
                        type="primary",
                        use_container_width=True
                    )

                if submit_google:
                    cleaned_email = (email_input or "").strip().lower()
                    if not cleaned_email or "@" not in cleaned_email or "." not in cleaned_email:
                        st.error("Please enter a valid email address.")
                    else:
                        # Auto-enroll as student if first time, or fetch existing user
                        ok, msg, user = login_or_register_with_email(cleaned_email)
                        if not ok or not user:
                            st.error(msg or "Unable to process email login.")
                        else:
                            # Generate OTP
                            otp_ok, otp_code_or_err, retry_after = create_otp(user["id"])
                            if not otp_ok:
                                if retry_after > 0:
                                    st.warning(f"Please wait {retry_after} seconds before requesting a new code.")
                                else:
                                    st.error(otp_code_or_err)
                            else:
                                raw_otp = otp_code_or_err
                                user_name = user.get("name", "Student")
                                mail_success, mail_msg = send_otp_email(
                                    to_email=cleaned_email,
                                    otp_code=raw_otp,
                                    user_name=user_name
                                )

                                st.session_state.pending_auth = {
                                    "user": user,
                                    "email": cleaned_email,
                                    "masked_email": mask_email(cleaned_email),
                                    "raw_otp_dev": raw_otp if settings.DEV_MODE else None,
                                    "mail_sent": mail_success,
                                    "mail_note": mail_msg,
                                    "created_at": time.time()
                                }
                                st.session_state.auth_view = "otp"
                                st.rerun()

            # ==================================================================
            # TAB 2: INSTITUTIONAL ID + PASSWORD
            # ==================================================================
            with tab_id:
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

                    submit_id = st.form_submit_button(
                        "Continue with Password →",
                        type="primary",
                        use_container_width=True
                    )

                if submit_id:
                    cleaned_id = (user_id_input or "").strip()
                    cleaned_pwd = password_input or ""

                    if not cleaned_id or not cleaned_pwd:
                        st.error("Please enter both User ID and Password.")
                    else:
                        is_ok, reason, user = authenticate_credentials(
                            user_id=cleaned_id,
                            password=cleaned_pwd,
                            ip_address="127.0.0.1"
                        )

                        if not is_ok:
                            if reason == "LOCKED":
                                is_locked, remaining_mins = check_account_lockout(cleaned_id)
                                st.error(f"Account is temporarily locked. Please try again in {remaining_mins} minutes.")
                            else:
                                st.error("Invalid ID or password.")
                        else:
                            otp_ok, otp_code_or_err, retry_after = create_otp(cleaned_id)
                            if not otp_ok:
                                if retry_after > 0:
                                    st.warning(f"Please wait {retry_after} seconds before requesting a new code.")
                                else:
                                    st.error(otp_code_or_err)
                            else:
                                raw_otp = otp_code_or_err
                                user_email = user.get("email", "")
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

            # ==================================================================
            # TAB 3: CREATE NEW ACCOUNT (SELF-REGISTRATION)
            # ==================================================================
            with tab_create:
                st.markdown("""
                <div style="font-size:13px; color:#64748B; margin:8px 0 14px 0;">
                    Create a new Student account to start chatting with campus documents.
                </div>
                """, unsafe_allow_html=True)

                with st.form("create_account_form", clear_on_submit=False):
                    reg_name = st.text_input(
                        "Full Name",
                        placeholder="e.g. Avinash Singh",
                        key="reg_name_input"
                    )
                    reg_id = st.text_input(
                        "Student Roll No / Desired Username",
                        placeholder="e.g. S24CSEU0709 or avinash",
                        key="reg_id_input"
                    )
                    reg_email = st.text_input(
                        "Email Address (Gmail or University)",
                        placeholder="e.g. avinash@gmail.com",
                        key="reg_email_input"
                    )
                    reg_pwd = st.text_input(
                        "Password (min. 8 chars, letters & numbers)",
                        type="password",
                        placeholder="••••••••••••",
                        key="reg_pwd_input"
                    )
                    reg_pwd_confirm = st.text_input(
                        "Confirm Password",
                        type="password",
                        placeholder="••••••••••••",
                        key="reg_pwd_confirm_input"
                    )

                    submit_reg = st.form_submit_button(
                        "Create Account & Send Code →",
                        type="primary",
                        use_container_width=True
                    )

                if submit_reg:
                    cleaned_name = (reg_name or "").strip()
                    cleaned_id = (reg_id or "").strip()
                    cleaned_email = (reg_email or "").strip().lower()
                    cleaned_pwd = reg_pwd or ""
                    cleaned_confirm = reg_pwd_confirm or ""

                    if not cleaned_name or not cleaned_id or not cleaned_email or not cleaned_pwd:
                        st.error("All registration fields are required.")
                    elif "@" not in cleaned_email or "." not in cleaned_email:
                        st.error("Please enter a valid email address.")
                    elif cleaned_pwd != cleaned_confirm:
                        st.error("Passwords do not match. Please re-enter.")
                    else:
                        is_valid_pwd, pwd_err = validate_password_policy(cleaned_pwd)
                        if not is_valid_pwd:
                            st.error(pwd_err)
                        else:
                            # Create student user
                            ok, msg, _ = create_user(
                                user_id=cleaned_id,
                                name=cleaned_name,
                                email=cleaned_email,
                                role="Student",
                                password=cleaned_pwd,
                                force_password_change=False
                            )
                            if not ok:
                                st.error(msg)
                            else:
                                # Fetch newly created user and trigger OTP verification
                                new_user = get_user_by_email(cleaned_email)
                                if not new_user:
                                    st.error("Account created, but failed to fetch user. Please sign in.")
                                else:
                                    otp_ok, otp_code_or_err, retry_after = create_otp(new_user["id"])
                                    if not otp_ok:
                                        st.warning("Account created, but OTP generation failed. Please try signing in.")
                                    else:
                                        raw_otp = otp_code_or_err
                                        mail_success, mail_msg = send_otp_email(
                                            to_email=cleaned_email,
                                            otp_code=raw_otp,
                                            user_name=cleaned_name
                                        )

                                        st.session_state.pending_auth = {
                                            "user": new_user,
                                            "email": cleaned_email,
                                            "masked_email": mask_email(cleaned_email),
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
