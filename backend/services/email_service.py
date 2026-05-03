"""
Email Service — sends reports to participants.
Uses Resend (resend.com) for transactional email.
"""
import os
import base64
import resend


def send_report_email(
    to_email: str,
    participant_name: str,
    docx_bytes: bytes,
    filename: str = "SAAQReport.docx",
):
    """Send a SAAQ report to a participant via email."""
    resend.api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "mark@skillfullyaware.com")

    if not resend.api_key:
        print("  RESEND_API_KEY not set, skipping email")
        return None

    try:
        result = resend.Emails.send({
            "from": f"SkillfullyAware <{from_email}>",
            "to": [to_email],
            "subject": f"Your SAAQ Awareness Report is Ready, {participant_name}",
            "html": f"""
            <div style="font-family: Calibri, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <h2 style="color: #1F3864;">Your SAAQ Report is Ready</h2>
                <p>Hi {participant_name},</p>
                <p>Thank you for completing the SkillfullyAware Awareness Quotient assessment. Your personalized diagnostic report is attached to this email.</p>
                <p>This report provides a comprehensive developmental snapshot including:</p>
                <ul>
                    <li>Your developmental stage estimate</li>
                    <li>Power center analysis across 8 dimensions</li>
                    <li>Core aptitude assessment</li>
                    <li>Shadow indicators and growth areas</li>
                    <li>A personalized 90-day practice plan</li>
                </ul>
                <p>Please take your time reviewing it. The insights are meant to be practical, strengths-forward, and action-oriented.</p>
                <p>If you have any questions about your report, don't hesitate to reach out.</p>
                <p style="margin-top: 30px;">Warmly,<br>
                <strong>Mark Pirtle</strong><br>
                SkillfullyAware</p>
            </div>
            """,
            "attachments": [{
                "filename": filename,
                "content": base64.b64encode(docx_bytes).decode("utf-8"),
                "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            }],
        })
        print(f"  Email sent to {to_email}: {result}")
        return result
    except Exception as e:
        print(f"  Email failed: {e}")
        return None
