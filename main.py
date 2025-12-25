"""
Enhanced Email Manager with Better Validation
Add this to your main.py to replace the existing send_assignment endpoint
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import List
import re

class AssignmentEmail(BaseModel):
    student_emails: List[str]  # Changed from EmailStr to str for custom validation
    subject: str
    assignment_title: str
    description: str
    due_date: str
    due_time: str = "23:59"
    
    @field_validator('student_emails', mode='before')
    @classmethod
    def validate_emails(cls, v):
        """Clean and validate email addresses"""
        if isinstance(v, str):
            # If it's a single string, split by comma
            v = [email.strip() for email in v.split(',')]
        elif isinstance(v, list):
            # If it's already a list, clean each email
            v = [email.strip() for email in v]
        
        # Remove empty strings
        v = [email for email in v if email]
        
        # Validate each email format
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        validated_emails = []
        
        for email in v:
            if email_pattern.match(email):
                validated_emails.append(email.lower())  # Normalize to lowercase
            else:
                raise ValueError(f"Invalid email format: {email}")
        
        if not validated_emails:
            raise ValueError("At least one valid email address is required")
        
        return validated_emails

# Update the send_assignment endpoint
@app.post("/send-assignment")
async def send_assignment(assignment: AssignmentEmail):
    """Send assignment email with improved error handling"""
    try:
        print(f"\n{'='*60}")
        print("Processing Assignment Email Request")
        print(f"{'='*60}")
        print(f"Recipients: {assignment.student_emails}")
        print(f"Subject: {assignment.subject}")
        print(f"Title: {assignment.assignment_title}")
        print(f"Due Date: {assignment.due_date} {assignment.due_time}")
        
        # Validate emails are not empty
        if not assignment.student_emails:
            raise HTTPException(status_code=400, detail="No valid email addresses provided")
        
        # Parse due date and time
        due_date_obj = datetime.strptime(assignment.due_date, "%Y-%m-%d")
        due_time_parts = assignment.due_time.split(":")
        due_datetime = due_date_obj.replace(
            hour=int(due_time_parts[0]), 
            minute=int(due_time_parts[1])
        )
        
        # Create email body
        email_body = email_manager.create_assignment_email_body(
            assignment.assignment_title,
            assignment.description,
            assignment.due_date,
            assignment.due_time
        )
        
        print(f"\nAttempting to send email to: {assignment.student_emails}")
        
        # Send email with better error handling
        try:
            email_sent = email_manager.send_email(
                assignment.student_emails,
                f"📚 New Assignment: {assignment.subject}",
                email_body
            )
            print(f"Email send result: {email_sent}")
        except Exception as email_error:
            print(f"Email sending error: {email_error}")
            email_sent = False
        
        # Create calendar event
        event_id = None
        calendar_created = False
        
        if calendar_manager.service:
            try:
                event_id = calendar_manager.create_event(
                    summary=f"Assignment Due: {assignment.assignment_title}",
                    description=f"{assignment.subject}\n\n{assignment.description}",
                    start_datetime=due_datetime - timedelta(hours=1),
                    end_datetime=due_datetime,
                    attendees=assignment.student_emails
                )
                calendar_created = event_id is not None
                print(f"Calendar event created: {calendar_created}")
            except Exception as cal_error:
                print(f"Calendar creation error: {cal_error}")
        
        response_data = {
            "status": "success" if email_sent else "partial_success",
            "message": "Assignment processed",
            "email_sent": email_sent,
            "calendar_event_created": calendar_created,
            "event_id": event_id,
            "recipients": len(assignment.student_emails),
            "recipient_emails": assignment.student_emails
        }
        
        if not email_sent:
            response_data["warning"] = "Email sending failed. Check Gmail credentials and App Password."
        
        print(f"\nResponse: {response_data}")
        print(f"{'='*60}\n")
        
        return response_data
    
    except ValueError as ve:
        print(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    
    except Exception as e:
        print(f"Error processing assignment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error sending assignment: {str(e)}")


# Enhanced EmailManager.send_email method
class EmailManager:
    """Handles email sending with better error reporting"""
    
    def __init__(self, gmail_user: str, gmail_password: str):
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password
    
    def send_email(self, to_emails: List[str], subject: str, body: str, 
                   attachment_path: Optional[str] = None):
        """Send email with detailed error logging"""
        try:
            print(f"\n--- Email Send Attempt ---")
            print(f"From: {self.gmail_user}")
            print(f"To: {to_emails}")
            print(f"Subject: {subject}")
            
            # Validate email addresses before sending
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            for email in to_emails:
                if not email_pattern.match(email):
                    print(f"❌ Invalid email format: {email}")
                    raise ValueError(f"Invalid email address: {email}")
            
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(attachment_path)
                    part.add_header('Content-Disposition', f'attachment; filename={filename}')
                    msg.attach(part)
            
            print(f"Connecting to SMTP server...")
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
                print(f"Connected. Starting TLS...")
                server.starttls()
                
                print(f"Logging in...")
                server.login(self.gmail_user, self.gmail_password)
                
                print(f"Sending message...")
                # Send to each recipient individually to catch failures
                failed_recipients = []
                successful_recipients = []
                
                for recipient in to_emails:
                    try:
                        msg['To'] = recipient
                        server.send_message(msg)
                        successful_recipients.append(recipient)
                        print(f"✅ Sent to: {recipient}")
                    except Exception as recipient_error:
                        failed_recipients.append(recipient)
                        print(f"❌ Failed to send to {recipient}: {recipient_error}")
                
                if failed_recipients:
                    print(f"\n⚠️ Failed recipients: {failed_recipients}")
                    print(f"✅ Successful recipients: {successful_recipients}")
                    
                    if not successful_recipients:
                        return False
                
                print(f"✅ Email sent successfully to {len(successful_recipients)} recipient(s)")
            
            return True
            
        except smtplib.SMTPAuthenticationError as auth_error:
            print(f"❌ SMTP Authentication Error: {auth_error}")
            print("Check your Gmail App Password!")
            return False
            
        except smtplib.SMTPRecipientsRefused as recip_error:
            print(f"❌ Recipients Refused: {recip_error}")
            print("One or more email addresses were rejected by the server")
            return False
            
        except smtplib.SMTPException as smtp_error:
            print(f"❌ SMTP Error: {smtp_error}")
            return False
            
        except Exception as e:
            print(f"❌ Unexpected error sending email: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_assignment_email_body(self, assignment_title: str, 
                                     description: str, due_date: str, 
                                     due_time: str) -> str:
        """Create HTML email body for assignment"""
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; border-radius: 10px;">
                <h2 style="color: #ff6b35; border-bottom: 2px solid #ff6b35; padding-bottom: 10px;">
                    📚 New Assignment Posted
                </h2>
                
                <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">{assignment_title}</h3>
                    
                    <p><strong>Description:</strong></p>
                    <p style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #ff6b35; border-radius: 3px;">
                        {description}
                    </p>
                    
                    <div style="margin-top: 20px; padding: 15px; background-color: #fff3e0; border-radius: 5px;">
                        <p style="margin: 5px 0;"><strong>📅 Due Date:</strong> {due_date}</p>
                        <p style="margin: 5px 0;"><strong>⏰ Due Time:</strong> {due_time}</p>
                    </div>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 20px;">
                    <em>This assignment has been added to your Google Calendar. 
                    You will receive reminder emails as the due date approaches.</em>
                </p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Sent by College Assistant AI<br>
                    Do not reply to this email
                </p>
            </div>
        </body>
        </html>
        """
        return body