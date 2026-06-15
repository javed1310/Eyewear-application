"""
OptiFlow — Notification Service
Handles sending Email (via Resend) and WhatsApp (via Twilio) alerts for SLA breaches and high-risk orders.
"""

import httpx
from typing import Optional
from app.models.order import Order
from app.models.customer import Customer
from app.core.config import settings

class NotificationService:
    def __init__(self):
        self.resend_api_key = getattr(settings, "RESEND_API_KEY", None)
        self.twilio_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
        self.twilio_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
        self.twilio_from = getattr(settings, "TWILIO_WHATSAPP_FROM", None)
        self.ops_email = getattr(settings, "OPS_ALERT_EMAIL", "ops@optiflow.demo")

    async def send_email(self, to_email: str, subject: str, body: str):
        """Sends an email alert using Resend API."""
        print(f"[EMAIL] To: {to_email} | Subject: {subject}")
        print(f"[EMAIL] Body: {body}")
        
        if not self.resend_api_key:
            print("[EMAIL] Skipped: RESEND_API_KEY not configured.")
            return

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {self.resend_api_key}"},
                    json={
                        "from": "OptiFlow Alerts <alerts@optiflow.demo>", # Must be verified domain in prod
                        "to": [to_email],
                        "subject": subject,
                        "text": body
                    }
                )
                response.raise_for_status()
                print(f"[EMAIL] Sent successfully via Resend. ID: {response.json().get('id')}")
            except Exception as e:
                print(f"[EMAIL] Failed to send via Resend: {e}")

    async def send_whatsapp(self, to_phone: str, message: str):
        """Sends a WhatsApp alert using Twilio API."""
        print(f"[WHATSAPP] To: {to_phone} | Message: {message}")
        
        if not self.twilio_sid or not self.twilio_token or not self.twilio_from:
            print("[WHATSAPP] Skipped: Twilio credentials not configured.")
            return

        # Ensure phone numbers have the 'whatsapp:' prefix
        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"
            
        from_phone = self.twilio_from
        if not from_phone.startswith("whatsapp:"):
            from_phone = f"whatsapp:{from_phone}"

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    auth=(self.twilio_sid, self.twilio_token),
                    data={
                        "From": from_phone,
                        "To": to_phone,
                        "Body": message
                    }
                )
                response.raise_for_status()
                print(f"[WHATSAPP] Sent successfully via Twilio. SID: {response.json().get('sid')}")
            except Exception as e:
                print(f"[WHATSAPP] Failed to send via Twilio: {e}")

    async def alert_breach(self, order: Order, customer: Optional[Customer] = None):
        """Alerts the manager and/or customer about an SLA breach."""
        subject = f"URGENT: Order {order.order_number} has BREACHED SLA"
        body = f"Order {order.order_number} is currently in {order.status.replace('_', ' ')} and has breached its SLA target of {order.sla_target_at}."
        
        # Alert internal ops team
        await self.send_email(self.ops_email, subject, body)
        
        # If customer provided, we might send an apology or update
        if customer and customer.email:
            customer_subject = f"Update regarding your Eyewear Order ({order.order_number})"
            customer_body = f"Dear {customer.name}, we are experiencing a slight delay with your order. We are expediting it."
            await self.send_email(customer.email, customer_subject, customer_body)
            
            if customer.phone:
                await self.send_whatsapp(customer.phone, customer_body)

    async def alert_at_risk(self, order: Order):
        """Alerts the lab team about an at-risk order."""
        subject = f"WARNING: Order {order.order_number} is AT RISK"
        body = f"Order {order.order_number} has a high probability of missing its SLA. Please expedite."
        await self.send_email(self.ops_email, subject, body)

notification_service = NotificationService()
