"""
Email delivery module for Campus Helpdesk Two-Factor OTP.
Integrates with Gmail SMTP using App Passwords over STARTTLS.
Supports Dev Mode fallback when SMTP credentials are not configured.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Optional
from config import settings
from core.logger import logger


def mask_email(email: str) -> str:
    """
    Masks an email address for safe UI presentation (e.g. avinash@gmail.com -> a*****@gmail.com).
    """
    if not email or "@" not in email:
        return "******"
    user_part, domain = email.strip().split("@", 1)
    if len(user_part) <= 2:
        masked_user = user_part[0] + "***"
    else:
        masked_user = user_part[0] + "*" * (len(user_part) - 1)
    return f"{masked_user}@{domain}"


def send_otp_email(
    to_email: str,
    otp_code: str,
    user_name: str = "Student",
    purpose: str = "login",
    ttl_minutes: int = 5,
    recipient_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Dispatches a branded 6-digit OTP email using Gmail SMTP with STARTTLS.
    
    Returns:
        (success: bool, status_message: str)
    """
    if recipient_name:
        user_name = recipient_name
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER or "avinashsingh5493@gmail.com"
    smtp_pass = settings.SMTP_APP_PASSWORD
    from_name = settings.MAIL_FROM_NAME

    # Dynamic fallback: check Streamlit session or use to_email if it's a Gmail address
    if not smtp_user:
        try:
            import streamlit as st
            custom_sender = st.session_state.get("custom_smtp_user")
            if custom_sender:
                smtp_user = custom_sender.strip()
        except Exception:
            pass

    if not smtp_user and to_email and to_email.strip().lower().endswith("@gmail.com"):
        smtp_user = to_email.strip()

    has_smtp = bool(smtp_user and smtp_pass and smtp_host)

    # 1. Dev Mode Check
    if settings.DEV_MODE and not has_smtp:
        logger.info(f"[DEV MODE OTP] Generated OTP code for {mask_email(to_email)} (Purpose: {purpose})")
        print(f"\n[DEV MODE OTP] >>> One-Time Passcode for {to_email} is: {otp_code} (Valid {ttl_minutes} min) <<<\n")
        return True, "DEV_MODE"

    if not has_smtp:
        return False, "Email service is not configured. Please contact the campus administrator."

    subject = f"{otp_code} is your Campus Helpdesk verification code"
    purpose_desc = "account sign-in" if purpose == "login" else "password reset"

    # Clean HTML Template (FAANG-grade styling, neutral colors, prominent blue OTP box)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Campus Helpdesk Verification</title>
    </head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background-color:#F8FAFC; margin:0; padding:32px 16px; color:#0F172A;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:520px; background-color:#FFFFFF; border-radius:16px; border:1px solid #E2E8F0; box-shadow:0 4px 12px rgba(15,23,42,0.04); overflow:hidden;">
        <tr>
          <td style="padding:28px 32px 20px 32px; border-bottom:1px solid #F1F5F9;">
            <div style="font-size:18px; font-weight:800; color:#0F172A; letter-spacing:-0.02em;">
              campus<span style="color:#2F5BEA;">helpdesk</span>
            </div>
            <div style="font-size:12px; font-weight:500; color:#64748B; margin-top:2px;">
              Official Academic & Policy Helpdesk
            </div>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <h2 style="font-size:20px; font-weight:700; color:#0F172A; margin:0 0 12px 0;">
              Verify your identity
            </h2>
            <p style="font-size:14px; line-height:1.6; color:#475569; margin:0 0 24px 0;">
              Hello {user_name},<br>
              A request was received for <strong>{purpose_desc}</strong> on the Campus Helpdesk Assistant. Use the verification code below to proceed:
            </p>
            <div style="background-color:#F0F4FF; border:1px solid #C7D2FE; border-radius:12px; padding:20px; text-align:center; margin:0 0 24px 0;">
              <span style="font-family:'Courier New',Courier,monospace; font-size:34px; font-weight:800; letter-spacing:8px; color:#2F5BEA;">
                {otp_code}
              </span>
            </div>
            <p style="font-size:13px; color:#64748B; line-height:1.5; margin:0 0 16px 0;">
              ⏱️ This passcode is single-use and will expire in <strong>{ttl_minutes} minutes</strong>.
            </p>
            <p style="font-size:12px; color:#94A3B8; line-height:1.5; margin:0;">
              If you did not request this verification code, please ignore this email or notify your campus IT security desk immediately.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px; background-color:#F8FAFC; border-top:1px solid #F1F5F9; font-size:11.5px; color:#94A3B8; text-align:center;">
            Campus Helpdesk Assistant · Official University Policy & Academic Support
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    plain_content = f"""Campus Helpdesk Verification
    
Hello {user_name},

Your one-time passcode for {purpose_desc} is: {otp_code}

This passcode will expire in {ttl_minutes} minutes.
If you did not request this code, please ignore this email.

Campus Helpdesk Security
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_email
    msg.attach(MIMEText(plain_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=12.0) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        logger.info(f"Successfully sent OTP email to {mask_email(to_email)}")
        return True, "SUCCESS"
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail SMTP authentication failed. Please verify the App Password.")
        return False, "Failed to authenticate with the email server. Please check your App Password configuration."
    except Exception as e:
        logger.error(f"Failed to send email to {mask_email(to_email)}: {type(e).__name__}")
        return False, "Unable to send verification email. Please check your internet connection and SMTP configuration."
