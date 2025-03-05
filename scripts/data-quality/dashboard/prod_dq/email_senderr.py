import os
import base64
import sendgrid
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

def send_email(subject, body, to_email, attachment_path=None):
    """Sends an email using SendGrid API, with an optional CSV attachment."""
    
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    EMAIL_FROM = os.getenv("EMAIL_FROM")

    if not SENDGRID_API_KEY or not EMAIL_FROM:
        return "Error: SendGrid API key or sender email not configured."

    try:
        sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )

        # Attach CSV file if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                file_data = f.read()
                encoded_file = base64.b64encode(file_data).decode()  # Correct base64 encoding

            attachment = Attachment(
                FileContent(encoded_file),
                FileName(os.path.basename(attachment_path)),
                FileType("text/csv"),
                Disposition("attachment")
            )
            message.attachment = attachment

            print(f"📎 Attached file: {attachment_path}")  # Debugging Output
        else:
            print("⚠️ No attachment found.")  # Debugging Output

        response = sg.send(message)

        print(f"📨 SendGrid Response: {response.status_code}, {response.body}")

        if response.status_code in [200, 202]:
            return "Email sent successfully!"
        else:
            return f"Failed to send email. Status code: {response.status_code}, Error: {response.body}"
    except Exception as e:
        return f"❌ Failed to send email: {e}"



