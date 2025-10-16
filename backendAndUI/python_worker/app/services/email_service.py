"""
Email notification service for document upload confirmations.
Supports SendGrid, SMTP, and other providers.
"""

import os
import logging
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Email service with multiple provider support."""
    
    def __init__(self):
        self.provider = os.getenv("EMAIL_PROVIDER", "sendgrid").lower()
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.from_email = os.getenv("EMAIL_FROM", "noreply@knowledgesynthesis.app")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "Knowledge Synthesis")
        
        if self.enabled:
            logger.info(f"Email service enabled with provider: {self.provider}")
        else:
            logger.info("Email service disabled")
    
    async def send_upload_confirmation(
        self,
        user_email: str,
        user_name: str,
        document_title: str,
        document_id: str,
        triplet_count: int,
        uploaded_at: Optional[datetime] = None
    ) -> bool:
        """
        Send confirmation email after successful document upload.
        
        Args:
            user_email: Recipient email address
            user_name: User's full name
            document_title: Title of uploaded document
            document_id: Unique document identifier
            triplet_count: Number of relationships extracted
            uploaded_at: Upload timestamp
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Email service disabled, skipping notification")
            return False
        
        if not user_email:
            logger.warning("No user email provided, cannot send notification")
            return False
        
        try:
            subject = f"✅ Document Processed: {document_title}"
            
            html_content = self._build_upload_email_html(
                user_name=user_name,
                document_title=document_title,
                document_id=document_id,
                triplet_count=triplet_count,
                uploaded_at=uploaded_at or datetime.utcnow()
            )
            
            text_content = self._build_upload_email_text(
                user_name=user_name,
                document_title=document_title,
                triplet_count=triplet_count,
                uploaded_at=uploaded_at or datetime.utcnow()
            )
            
            if self.provider == "sendgrid":
                return await self._send_via_sendgrid(user_email, subject, html_content, text_content)
            elif self.provider == "smtp":
                return await self._send_via_smtp(user_email, subject, html_content, text_content)
            else:
                logger.error(f"Unsupported email provider: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send upload confirmation email: {e}")
            return False
    
    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """Send email using SendGrid API."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            api_key = os.getenv("SENDGRID_API_KEY")
            if not api_key:
                logger.error("SENDGRID_API_KEY not configured")
                return False
            
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content("text/plain", text_content),
                html_content=Content("text/html", html_content)
            )
            
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                return False
                
        except ImportError:
            logger.error("SendGrid library not installed. Run: pip install sendgrid")
            return False
        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return False
    
    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """Send email using SMTP."""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            
            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            
            if not smtp_user or not smtp_password:
                logger.error("SMTP credentials not configured")
                return False
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(message)
            
            logger.info(f"Email sent successfully via SMTP to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return False
    
    def _build_upload_email_html(
        self,
        user_name: str,
        document_title: str,
        document_id: str,
        triplet_count: int,
        uploaded_at: datetime
    ) -> str:
        """Build HTML email content."""
        app_url = os.getenv("APP_URL", "http://localhost:8000")
        viewer_url = f"{app_url}/app?tab=viewing&doc={document_id}"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Processed</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">✅ Document Processed</h1>
    </div>
    
    <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <p style="font-size: 16px; margin-bottom: 20px;">Hi {user_name},</p>
        
        <p style="font-size: 16px; margin-bottom: 20px;">
            Your document has been successfully processed and added to your knowledge graph!
        </p>
        
        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
            <h2 style="margin-top: 0; color: #667eea; font-size: 20px;">📄 {document_title}</h2>
            <ul style="list-style: none; padding: 0; margin: 15px 0;">
                <li style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">
                    <strong>Relationships Extracted:</strong> {triplet_count}
                </li>
                <li style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">
                    <strong>Processed At:</strong> {uploaded_at.strftime('%B %d, %Y at %I:%M %p UTC')}
                </li>
                <li style="padding: 8px 0;">
                    <strong>Document ID:</strong> <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-size: 12px;">{document_id[:12]}...</code>
                </li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{viewer_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                View in Graph Viewer →
            </a>
        </div>
        
        <div style="background: #fef3c7; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #f59e0b;">
            <p style="margin: 0; font-size: 14px; color: #92400e;">
                <strong>💡 Next Steps:</strong><br>
                • Review the extracted relationships in the viewer<br>
                • Verify accuracy using the Review Queue<br>
                • Upload more documents to expand your knowledge graph
            </p>
        </div>
        
        <p style="font-size: 14px; color: #6b7280; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
            Thank you for using Knowledge Synthesis!<br>
            <strong>The Knowledge Synthesis Team</strong>
        </p>
    </div>
    
    <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #9ca3af;">
        <p>
            If you did not upload this document, please contact support.<br>
            <a href="{app_url}" style="color: #667eea; text-decoration: none;">Knowledge Synthesis Platform</a>
        </p>
    </div>
</body>
</html>
"""
    
    def _build_upload_email_text(
        self,
        user_name: str,
        document_title: str,
        triplet_count: int,
        uploaded_at: datetime
    ) -> str:
        """Build plain text email content."""
        app_url = os.getenv("APP_URL", "http://localhost:8000")
        
        return f"""
Hi {user_name},

Your document has been successfully processed and added to your knowledge graph!

DOCUMENT DETAILS
================
Title: {document_title}
Relationships Extracted: {triplet_count}
Processed At: {uploaded_at.strftime('%B %d, %Y at %I:%M %p UTC')}

NEXT STEPS
==========
• Review the extracted relationships in the graph viewer
• Verify accuracy using the Review Queue  
• Upload more documents to expand your knowledge graph

View your graph: {app_url}/app

Thank you for using Knowledge Synthesis!

---
The Knowledge Synthesis Team
{app_url}
"""


# Global email service instance
email_service = EmailService()


async def send_upload_notification(
    user_email: str,
    user_name: str,
    document_title: str,
    document_id: str,
    triplet_count: int
) -> bool:
    """
    Convenience function to send upload confirmation.
    
    Usage:
        await send_upload_notification(
            user_email="user@example.com",
            user_name="John Doe",
            document_title="Research Paper.pdf",
            document_id="abc123",
            triplet_count=42
        )
    """
    return await email_service.send_upload_confirmation(
        user_email=user_email,
        user_name=user_name,
        document_title=document_title,
        document_id=document_id,
        triplet_count=triplet_count,
        uploaded_at=datetime.utcnow()
    )




