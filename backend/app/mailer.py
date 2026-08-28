import html

import httpx

from .config import settings


def _send_email(to: str, subject: str, title: str, body: str, action_label: str, action_url: str) -> bool:
    if not settings.resend_api_key:
        return False
    safe_body = html.escape(body)
    safe_title = html.escape(title)
    safe_label = html.escape(action_label)
    safe_url = html.escape(action_url, quote=True)
    markup = f"""
    <div style='font-family:Arial,sans-serif;max-width:620px;margin:auto;color:#152235'>
      <h2>{safe_title}</h2>
      <p>{safe_body}</p>
      <p><a href='{safe_url}' style='display:inline-block;background:#1565c0;color:white;text-decoration:none;padding:12px 18px;border-radius:8px;font-weight:700'>{safe_label}</a></p>
      <p style='font-size:12px;color:#718096'>If you did not request this action, you can ignore this email.</p>
    </div>
    """
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
            json={"from": settings.email_from, "to": [to], "subject": subject, "html": markup},
            timeout=10.0,
        )
        response.raise_for_status()
        return True
    except Exception:
        return False


def send_password_reset(to: str, raw_token: str) -> bool:
    url = f"{settings.frontend_url.rstrip('/')}/reset-password?token={raw_token}"
    return _send_email(to, "Reset your QualiCore password", "Reset your password", "A password reset was requested for your QualiCore account. This link expires in 30 minutes and can only be used once.", "Reset Password", url)


def send_email_verification(to: str, raw_token: str) -> bool:
    url = f"{settings.frontend_url.rstrip('/')}/verify-email?token={raw_token}"
    return _send_email(to, "Verify your QualiCore email", "Verify your work email", "Confirm ownership of this email address to strengthen your QualiCore account security.", "Verify Email", url)


def send_invitation(to: str, raw_token: str, organization_name: str) -> bool:
    url = f"{settings.frontend_url.rstrip('/')}/join?token={raw_token}"
    return _send_email(to, f"Invitation to join {organization_name} on QualiCore", "You are invited to QualiCore AI", f"{organization_name} invited you to join its Project Assurance workspace. This invitation expires in 7 days.", "Accept Invitation", url)
