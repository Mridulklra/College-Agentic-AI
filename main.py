"""
College Assistant Agent - Complete Working Backend
BAS YAHI EK FILE CHANGE KARO!
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional, List
import ollama
import PyPDF2
import os
from datetime import datetime, timedelta
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from PIL import Image
import pytesseract

# Initialize FastAPI
app = FastAPI(title="College Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gmail Config
GMAIL_USER = "mridulkalra700@gmail.com"
GMAIL_APP_PASSWORD = "frqd peuk jyef znta"

# Calendar Scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# ==================== DATA MODELS ====================

class ChatMessage(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []

class QueryResponse(BaseModel):
    response: str
    context_used: Optional[str] = None

class AssignmentEmail(BaseModel):
    student_emails: List[str]
    subject: str
    assignment_title: str
    description: str
    due_date: str
    due_time: str = "23:59"
    
    @field_validator('student_emails', mode='before')
    @classmethod
    def validate_emails(cls, v):
        if isinstance(v, str):
            v = [email.strip() for email in v.split(',')]
        elif isinstance(v, list):
            v = [email.strip() for email in v]
        
        v = [email for email in v if email]
        
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        validated_emails = []
        
        for email in v:
            if email_pattern.match(email):
                validated_emails.append(email.lower())
            else:
                raise ValueError(f"Invalid email: {email}")
        
        if not validated_emails:
            raise ValueError("At least one valid email required")
        
        return validated_emails

# ==================== EMAIL MANAGER ====================

class EmailManager:
    def __init__(self, gmail_user: str, gmail_password: str):
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password
    
    def send_email(self, to_emails: List[str], subject: str, body: str, 
                   attachment_path: Optional[str] = None):
        try:
            print(f"\n📧 Sending email to: {to_emails}")
            
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
                    msg.attach(part)
            
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                
                successful = []
                for recipient in to_emails:
                    try:
                        server.sendmail(self.gmail_user, [recipient], msg.as_string())
                        successful.append(recipient)
                        print(f"   ✅ Sent to: {recipient}")
                    except Exception as e:
                        print(f"   ❌ Failed: {recipient} - {e}")
                
                return len(successful) > 0
            
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    
    def create_assignment_email_body(self, assignment_title: str, description: str, 
                                     due_date: str, due_time: str, 
                                     calendar_link: str = None) -> str:
        
        calendar_btn = ""
        if calendar_link:
            calendar_btn = f"""
            <div style="margin: 20px 0; text-align: center;">
                <a href="{calendar_link}" 
                   style="display: inline-block; background-color: #4285f4; color: white; 
                          padding: 14px 28px; text-decoration: none; border-radius: 6px; 
                          font-weight: bold; font-size: 16px;">
                    📅 Add to Google Calendar
                </a>
            </div>
            """
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
                <div style="background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">📚 New Assignment</h1>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 30px;">
                        <h2 style="color: #ff6b35; margin-top: 0; font-size: 24px;">{assignment_title}</h2>
                        
                        <div style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #ff6b35; border-radius: 4px; margin: 20px 0;">
                            <p style="margin: 0 0 10px 0; color: #666; font-size: 14px; font-weight: bold;">SUBJECT</p>
                            <p style="margin: 0; color: #333; font-size: 16px;">{description.split('\\n')[0] if '\\n' in description else description[:100]}</p>
                        </div>
                        
                        <div style="background-color: #f0f8ff; padding: 20px; border-radius: 6px; margin: 20px 0;">
                            <p style="margin: 0 0 10px 0; color: #1976d2; font-weight: bold;">📝 DESCRIPTION</p>
                            <p style="margin: 0; color: #333; white-space: pre-wrap; line-height: 1.6;">{description}</p>
                        </div>
                        
                        <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); padding: 20px; border-radius: 6px; margin: 20px 0;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0;">
                                        <span style="font-size: 24px; margin-right: 10px;">📅</span>
                                        <strong style="color: #f57c00;">Due Date:</strong>
                                    </td>
                                    <td style="text-align: right; padding: 8px 0;">
                                        <span style="color: #333; font-size: 16px; font-weight: bold;">{due_date}</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0;">
                                        <span style="font-size: 24px; margin-right: 10px;">⏰</span>
                                        <strong style="color: #f57c00;">Due Time:</strong>
                                    </td>
                                    <td style="text-align: right; padding: 8px 0;">
                                        <span style="color: #333; font-size: 16px; font-weight: bold;">{due_time}</span>
                                    </td>
                                </tr>
                            </table>
                        </div>
                        
                        {calendar_btn}
                        
                        <div style="background-color: #e3f2fd; padding: 18px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #2196f3;">
                            <p style="margin: 0; font-size: 14px; color: #1565c0; line-height: 1.6;">
                                <strong>💡 Reminder:</strong> This assignment has been automatically added to your Google Calendar. 
                                You'll receive email reminders 1 day before, 1 hour before, and 30 minutes before the due time.
                            </p>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0;">
                        <p style="margin: 0 0 5px 0; color: #999; font-size: 12px;">
                            Sent by <strong>College Assistant AI</strong>
                        </p>
                        <p style="margin: 0; color: #999; font-size: 11px;">
                            Powered by Ollama | Do not reply to this email
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

# ==================== CALENDAR MANAGER ====================

class CalendarManager:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        try:
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)
            
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if os.path.exists('credentials.json'):
                        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                        self.creds = flow.run_local_server(port=0)
                    else:
                        print("⚠️ credentials.json not found - Calendar disabled")
                        return
                
                with open('token.pickle', 'wb') as token:
                    pickle.dump(self.creds, token)
            
            self.service = build('calendar', 'v3', credentials=self.creds)
            print("✅ Calendar authenticated!")
        except Exception as e:
            print(f"⚠️ Calendar auth failed: {e}")
    
    def create_event(self, summary: str, description: str, 
                    start_datetime: datetime, end_datetime: datetime,
                    attendees: List[str] = None):
        if not self.service:
            return None, None
        
        try:
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'email', 'minutes': 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            created = self.service.events().insert(
                calendarId='primary', 
                body=event,
                sendUpdates='all'
            ).execute()
            
            event_id = created.get('id')
            event_link = created.get('htmlLink')
            
            print(f"✅ Calendar event created: {event_link}")
            return event_id, event_link
            
        except Exception as e:
            print(f"❌ Calendar error: {e}")
            return None, None

# ==================== DOCUMENT STORE ====================

class DocumentStore:
    def __init__(self):
        self.timetable = ""
        self.syllabus = ""
        self.college_info = ""
        self.uploads_dir = "uploads"
        os.makedirs(self.uploads_dir, exist_ok=True)
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except:
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except:
            return ""
    
    def extract_text_from_image(self, file_path: str) -> str:
        try:
            image = Image.open(file_path)
            return pytesseract.image_to_string(image)
        except:
            return ""
    
    def store_document(self, file_path: str, doc_type: str) -> bool:
        try:
            if file_path.lower().endswith('.pdf'):
                content = self.extract_text_from_pdf(file_path)
            elif file_path.lower().endswith('.txt'):
                content = self.extract_text_from_txt(file_path)
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                content = self.extract_text_from_image(file_path)
            else:
                return False
            
            if doc_type == "timetable":
                self.timetable = content
            elif doc_type == "syllabus":
                self.syllabus = content
            elif doc_type == "info":
                self.college_info = content
            
            return True
        except:
            return False
    
    def get_relevant_context(self, query: str) -> str:
        context = []
        q = query.lower()
        
        if any(w in q for w in ['timetable', 'schedule', 'class', 'time']):
            if self.timetable:
                context.append(f"TIMETABLE:\n{self.timetable[:2000]}")
        
        if any(w in q for w in ['syllabus', 'course', 'subject']):
            if self.syllabus:
                context.append(f"SYLLABUS:\n{self.syllabus[:2000]}")
        
        if any(w in q for w in ['college', 'campus', 'facility']):
            if self.college_info:
                context.append(f"COLLEGE INFO:\n{self.college_info[:2000]}")
        
        return "\n\n".join(context) if context else "No documents uploaded."

# ==================== OLLAMA AGENT ====================

class CollegeAgent:
    def __init__(self, model_name: str = "llama3.2"):
        self.model = model_name
        self.system_prompt = "You are a helpful college assistant AI. Answer questions about timetables, syllabus, and college information concisely."
    
    def generate_response(self, query: str, context: str, 
                         conversation_history: List[ChatMessage] = None) -> str:
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if conversation_history:
                for msg in conversation_history[-5:]:
                    messages.append({"role": msg.role, "content": msg.content})
            
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"})
            
            response = ollama.chat(model=self.model, messages=messages)
            return response['message']['content']
        except:
            return "Error: Make sure Ollama is running (ollama serve)"

# Initialize everything
doc_store = DocumentStore()
email_manager = EmailManager(GMAIL_USER, GMAIL_APP_PASSWORD)
calendar_manager = CalendarManager()
agent = CollegeAgent()

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "College Assistant API",
        "calendar": "Enabled" if calendar_manager.service else "Disabled"
    }

@app.post("/upload/{doc_type}")
async def upload_document(doc_type: str, file: UploadFile = File(...)):
    if doc_type not in ["timetable", "syllabus", "info"]:
        raise HTTPException(400, "Invalid type")
    
    file_path = os.path.join(doc_store.uploads_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    if doc_store.store_document(file_path, doc_type):
        return {"status": "success", "message": f"{doc_type} uploaded", "filename": file.filename}
    raise HTTPException(500, "Processing failed")

@app.post("/send-assignment")
async def send_assignment(assignment: AssignmentEmail):
    try:
        print(f"\n{'='*60}")
        print(f"📧 Assignment: {assignment.assignment_title}")
        print(f"📩 To: {assignment.student_emails}")
        
        # Parse date/time
        due_date_obj = datetime.strptime(assignment.due_date, "%Y-%m-%d")
        due_time_parts = assignment.due_time.split(":")
        due_datetime = due_date_obj.replace(hour=int(due_time_parts[0]), minute=int(due_time_parts[1]))
        
        # Create calendar event FIRST
        event_id, event_link = None, None
        if calendar_manager.service:
            event_id, event_link = calendar_manager.create_event(
                summary=f"📚 {assignment.subject}: {assignment.assignment_title}",
                description=f"Subject: {assignment.subject}\n\n{assignment.description}\n\nDue: {assignment.due_date} at {assignment.due_time}",
                start_datetime=due_datetime - timedelta(hours=1),
                end_datetime=due_datetime,
                attendees=assignment.student_emails
            )
        
        # Create and send email
        email_body = email_manager.create_assignment_email_body(
            assignment.assignment_title,
            assignment.description,
            assignment.due_date,
            assignment.due_time,
            event_link
        )
        
        email_sent = email_manager.send_email(
            assignment.student_emails,
            f"📚 New Assignment: {assignment.subject} - {assignment.assignment_title}",
            email_body
        )
        
        print(f"{'='*60}\n")
        
        return {
            "status": "success",
            "email_sent": email_sent,
            "calendar_event_created": event_id is not None,
            "event_id": event_id,
            "event_link": event_link,
            "recipients": len(assignment.student_emails)
        }
    
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    try:
        context = doc_store.get_relevant_context(request.message)
        response = agent.generate_response(request.message, context, request.conversation_history)
        return QueryResponse(response=response, context_used=context if context != "No documents uploaded." else None)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/documents/status")
async def get_document_status():
    return {
        "timetable": bool(doc_store.timetable),
        "syllabus": bool(doc_store.syllabus),
        "info": bool(doc_store.college_info)
    }

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 College Assistant Backend")
    print(f"📧 Email: Enabled")
    print(f"📅 Calendar: {'Enabled' if calendar_manager.service else 'Disabled (Run setup_calendar.py)'}")
    print(f"🤖 Ollama: Make sure it's running!\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)