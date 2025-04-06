import smtplib
from email.message import EmailMessage
from .config import EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT

def send_interview_email(recipient_email, candidate_name, job_title):
    """Sends a personalized interview request email."""
    if not recipient_email:
        print(f"Error sending email: No recipient email provided for {candidate_name}.")
        return False
    if not EMAIL_ADDRESS or EMAIL_ADDRESS == "default_email@example.com" or not EMAIL_PASSWORD or EMAIL_PASSWORD == "default_password":
         print("Error sending email: Email credentials not configured in config.py or .env file.")
         return False


    subject = f"Interview Invitation: {job_title} Position"
    body = f"""
    Dear {candidate_name if candidate_name else 'Candidate'},

    Thank you for your interest in the {job_title} position at Our Company.

    We were impressed with your qualifications and would like to invite you for an initial interview to discuss your experience and the role further.

    We have the following potential time slots available:
    * [Date 1] at [Time 1] [Timezone]
    * [Date 2] at [Time 2] [Timezone]
    * [Date 3] at [Time 3] [Timezone]

    Please let us know which of these times works best for you, or suggest an alternative if none are suitable. The interview will be conducted via [Video Call Platform, e.g., Google Meet/Zoom] and is expected to last approximately 30-45 minutes.

    We look forward to hearing from you soon.

    Best regards,

    [Your Name/Hiring Team]
    Our Company
    """

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient_email
    msg.set_content(body)

    try:
        print(f"Attempting to send email to {recipient_email} via {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Successfully sent interview invitation to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        print(f"SMTP Authentication Error: Failed to login with {EMAIL_ADDRESS}. Check credentials/App Password.")
        return False
    except smtplib.SMTPConnectError:
         print(f"SMTP Connection Error: Failed to connect to server {SMTP_SERVER}:{SMTP_PORT}.")
         return False
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {e}")
        return False