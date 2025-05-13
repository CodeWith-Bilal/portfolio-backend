from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create router
router = APIRouter()

# Pydantic model for contact form data
class ContactForm(BaseModel):
    name: str
    email: str
    subject: str
    message: str

@router.post("/send-email/")
async def send_email(contact: ContactForm):
    # Get SMTP credentials from environment variables
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    # Create email message
    msg = MIMEMultipart()
    msg["From"] = smtp_username
    msg["To"] = smtp_username  # Sending to yourself (portfolio owner)
    msg["Subject"] = f"Portfolio Contact: {contact.subject}"
    
    # Create email body
    body = f"""
    You have received a new message from your portfolio contact form:
    
    Name: {contact.name}
    Email: {contact.email}
    Subject: {contact.subject}
    
    Message:
    {contact.message}
    """
    
    msg.attach(MIMEText(body, "plain"))
    
    try:
        # Connect to SMTP server and send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return {"status": "success", "message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")