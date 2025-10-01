"""
OTP Delivery Service for HaliCred
Handles SMS (via Africa's Talking) and Email (via SMTP) delivery for OTP codes.
Supports three modes:
- Terminal mode (OTP_MODE=off): Prints OTP to console
- Development mode (OTP_MODE=on, ENVIRONMENT_MODE=development): Uses Africa's Talking sandbox
- Production mode (OTP_MODE=on, ENVIRONMENT_MODE=production): Uses Africa's Talking production
"""

import logging
import asyncio
from typing import Tuple, Optional
from datetime import datetime
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import africastalking

from app.config import settings

logger = logging.getLogger(__name__)


class OTPDeliveryService:
    """Service for delivering OTP codes via SMS and email"""

    def __init__(self):
        """Initialize Africa's Talking client based on environment mode"""
        self.africas_talking_sms = None
        self.africas_talking_username = None
        self.africas_talking_sender_id = None

        # Initialize Africa's Talking based on ENVIRONMENT_MODE
        if settings.ENVIRONMENT_MODE.lower() == "production":
            # Production credentials
            username = settings.AFRICAS_TALKING_USERNAME_PRODUCTION
            api_key = settings.AFRICAS_TALKING_API_KEY_PRODUCTION
            self.africas_talking_sender_id = settings.AFRICAS_TALKING_SENDER_ID_PRODUCTION
            env_label = "PRODUCTION"
        else:
            # Development/Sandbox credentials
            username = settings.AFRICAS_TALKING_USERNAME_DEVELOPMENT
            api_key = settings.AFRICAS_TALKING_API_KEY_DEVELOPMENT
            self.africas_talking_sender_id = settings.AFRICAS_TALKING_SENDER_ID_DEVELOPMENT
            env_label = "DEVELOPMENT/SANDBOX"

        if username and api_key:
            try:
                africastalking.initialize(username, api_key)
                self.africas_talking_sms = africastalking.SMS
                self.africas_talking_username = username
                logger.info(f"✅ Africa's Talking SMS client initialized successfully ({env_label} mode)")
                logger.info(f"   Username: {username}, Sender ID: {self.africas_talking_sender_id}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Africa's Talking client: {e}")
        else:
            logger.warning(f"⚠️ Africa's Talking credentials not configured for {env_label} mode")

    async def send_otp(
        self,
        identifier: str,
        contact_type: str,
        code: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Send OTP code via SMS or email based on contact type and OTP_MODE.

        Args:
            identifier: Phone number or email address
            contact_type: "phone" or "email"
            code: 6-digit OTP code

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        otp_mode = settings.OTP_MODE.lower()

        # Mode 1: Terminal Only (OTP_MODE=off)
        if otp_mode == "off":
            return self._print_to_terminal(identifier, contact_type, code)

        # Mode 2 & 3: SMS/Email Delivery (OTP_MODE=on)
        elif otp_mode == "on":
            if contact_type == "phone":
                return await self._send_sms_africas_talking(identifier, code)
            elif contact_type == "email":
                return await self._send_email_smtp(identifier, code)
            else:
                error = f"Invalid contact type: {contact_type}"
                logger.error(error)
                return False, error
        else:
            error = f"Invalid OTP_MODE: {otp_mode}. Must be 'on' or 'off'"
            logger.error(error)
            return False, error

    def _print_to_terminal(
        self,
        identifier: str,
        contact_type: str,
        code: str
    ) -> Tuple[bool, None]:
        """Print OTP to console when OTP_MODE=off"""
        border = "═" * 60
        env_mode = settings.ENVIRONMENT_MODE.upper()

        logger.info("")
        logger.info(f"╔{border}╗")
        logger.info(f"║{'TERMINAL MODE - OTP DELIVERY'.center(60)}║")
        logger.info(f"║{f'(OTP_MODE=off)'.center(60)}║")
        logger.info(f"╠{border}╣")
        logger.info(f"║  Environment: {env_mode:<47}║")
        logger.info(f"║  Contact Type: {contact_type.upper():<44}║")
        logger.info(f"║  Recipient: {identifier:<47}║")
        logger.info(f"║  {''.ljust(58)}║")
        logger.info(f"║  🔐 OTP CODE: {code.center(43)}║")
        logger.info(f"║  {''.ljust(58)}║")
        logger.info(f"║  Expires: 5 minutes{' '.ljust(39)}║")
        logger.info(f"║  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<41}║")
        logger.info(f"║  {''.ljust(58)}║")
        logger.info(f"║  ℹ️  Set OTP_MODE=on to enable SMS/Email delivery{' '.ljust(6)}║")
        logger.info(f"╚{border}╝")
        logger.info("")
        return True, None

    async def _send_sms_africas_talking(
        self,
        phone: str,
        code: str
    ) -> Tuple[bool, Optional[str]]:
        """Send SMS via Africa's Talking API"""
        if not self.africas_talking_sms:
            error = "Africa's Talking SMS client not initialized - check credentials"
            logger.error(f"❌ {error}")
            return False, error

        try:
            # Format the SMS message
            message = self._format_sms_text(code)

            # Prepare recipient list (Africa's Talking expects a list)
            recipients = [phone]

            # Send SMS with Africa's Talking SDK
            # Use sender ID if available (production), otherwise defaults to AFRICASTKNG
            sender_id = self.africas_talking_sender_id if self.africas_talking_sender_id != "not available" else None

            logger.info(f"📤 Sending SMS to {phone} via Africa's Talking...")
            logger.info(f"   Environment: {settings.ENVIRONMENT_MODE.upper()}")
            logger.info(f"   Username: {self.africas_talking_username}")
            logger.info(f"   Sender ID: {sender_id or 'Default (AFRICASTKNG)'}")

            # Send SMS - run in thread pool as africastalking is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.africas_talking_sms.send(message, recipients, sender_id)
            )

            # Parse response
            sms_data = response.get("SMSMessageData", {})
            recipients_data = sms_data.get("Recipients", [])

            if recipients_data:
                recipient = recipients_data[0]
                status_code = recipient.get("statusCode")
                status = recipient.get("status")
                cost = recipient.get("cost", "N/A")
                message_id = recipient.get("messageId", "N/A")

                # Status codes: 100=Processed, 101=Sent, 102=Queued
                if status_code in [100, 101, 102]:
                    logger.info(f"✅ SMS sent successfully to {phone}")
                    logger.info(f"   Status: {status} (Code: {status_code})")
                    logger.info(f"   Cost: {cost}")
                    logger.info(f"   Message ID: {message_id}")
                    return True, None
                else:
                    error = f"SMS delivery failed - Status: {status} (Code: {status_code})"
                    logger.error(f"❌ {error}")
                    return False, error
            else:
                error = "No recipient data in Africa's Talking response"
                logger.error(f"❌ {error}")
                logger.error(f"   Full response: {response}")
                return False, error

        except Exception as e:
            error = f"Africa's Talking SMS error: {str(e)}"
            logger.error(f"❌ SMS delivery failed to {phone}")
            logger.error(f"   Error: {error}")
            return False, error

    def _format_sms_text(self, code: str) -> str:
        """Format SMS message text for OTP delivery"""
        return f"""Your HaliCred verification code is:

{code}

Valid for 5 minutes. Do not share this code.

- HaliCred Team"""

    async def _send_email_smtp(
        self,
        email: str,
        code: str
    ) -> Tuple[bool, Optional[str]]:
        """Send OTP via email using SMTP"""
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME:
            error = "SMTP not configured - check SMTP_HOST and SMTP_USERNAME in .env"
            logger.error(f"❌ {error}")
            return False, error

        if settings.SMTP_PASSWORD == "not_configured_yet":
            error = "SMTP_PASSWORD not configured in .env file"
            logger.error(f"❌ {error}")
            return False, error

        try:
            logger.info(f"📧 Sending OTP email to {email}...")

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Your HaliCred Verification Code: {code}"
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            message["To"] = email

            # Plain text version
            text_content = self._format_email_text(code)
            text_part = MIMEText(text_content, "plain")

            # HTML version
            html_content = self._format_email_html(code)
            html_part = MIMEText(html_content, "html")

            message.attach(text_part)
            message.attach(html_part)

            # Send email via SMTP
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                use_tls=True
            )

            logger.info(f"✅ Email sent successfully to {email}")
            return True, None

        except Exception as e:
            error = f"SMTP error: {str(e)}"
            logger.error(f"❌ Email delivery failed to {email}")
            logger.error(f"   Error: {error}")
            return False, error

    def _format_email_text(self, code: str) -> str:
        """Format plain text email content"""
        return f"""Hello,

Your HaliCred verification code is:

{code}

This code will expire in 5 minutes.

For your security:
- Do not share this code with anyone
- HaliCred will never ask you for this code via phone call

If you did not request this code, please ignore this email.

Best regards,
The HaliCred Team

---
This is an automated message. Please do not reply to this email.
HaliCred - Green Credit Scoring Platform
"""

    def _format_email_html(self, code: str) -> str:
        """Format HTML email content with professional styling"""
        year = datetime.now().year
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your HaliCred Verification Code</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f7fa;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f4f7fa;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">
                                HaliCred
                            </h1>
                            <p style="margin: 8px 0 0 0; color: #e0e7ff; font-size: 16px; font-weight: 500;">
                                Green Credit Scoring Platform
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px 0; color: #2d3748; font-size: 16px; line-height: 1.6;">
                                Hello,
                            </p>
                            <p style="margin: 0 0 30px 0; color: #2d3748; font-size: 16px; line-height: 1.6;">
                                Your verification code is:
                            </p>

                            <!-- OTP Code Box -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                                <tr>
                                    <td align="center" style="padding: 0;">
                                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 30px; display: inline-block;">
                                            <div style="background-color: #ffffff; border-radius: 8px; padding: 20px 40px; display: inline-block;">
                                                <span style="font-size: 40px; font-weight: 800; letter-spacing: 12px; color: #667eea; font-family: 'Courier New', monospace; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                                    {code}
                                                </span>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 0 0 30px 0; color: #718096; font-size: 14px; line-height: 1.6; text-align: center;">
                                This code will expire in <strong style="color: #667eea;">5 minutes</strong>
                            </p>

                            <!-- Security Notice -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-top: 30px;">
                                <tr>
                                    <td style="padding: 20px; background-color: #fff5f5; border-left: 4px solid #f56565; border-radius: 8px;">
                                        <p style="margin: 0 0 12px 0; color: #742a2a; font-size: 14px; font-weight: 700;">
                                            🔒 Security Reminder
                                        </p>
                                        <ul style="margin: 0; padding-left: 20px; color: #742a2a; font-size: 13px; line-height: 1.8;">
                                            <li>Never share this code with anyone</li>
                                            <li>HaliCred will never ask for this code via phone</li>
                                            <li>If you didn't request this, please ignore this email</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>

                            <!-- Help Text -->
                            <p style="margin: 30px 0 0 0; color: #718096; font-size: 13px; line-height: 1.6; text-align: center;">
                                Need help? Contact us at <a href="mailto:support@halicred.com" style="color: #667eea; text-decoration: none;">support@halicred.com</a>
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f7fafc; border-top: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
                            <p style="margin: 0 0 8px 0; color: #718096; font-size: 12px; line-height: 1.5; text-align: center;">
                                This is an automated message. Please do not reply to this email.
                            </p>
                            <p style="margin: 0; color: #a0aec0; font-size: 11px; text-align: center;">
                                © {year} HaliCred. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>

                <!-- Disclaimer -->
                <p style="margin: 20px 0 0 0; color: #a0aec0; font-size: 11px; line-height: 1.5; text-align: center; max-width: 600px;">
                    You are receiving this email because you requested a verification code for HaliCred.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>"""


# Global service instance
otp_delivery_service = OTPDeliveryService()
