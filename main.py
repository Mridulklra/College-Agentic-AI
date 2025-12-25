"""
College Assistant Agent - Enhanced Backend Server
Features: Image OCR, Email automation, Google Calendar integration
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import ollama
import PyPDF2
import os
from datetime import datetime, timedelta
import json
import base64
from PIL import Image
import pytesseract
import io
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

# Initialize FastAPI app
app = FastAPI(title="College Assistant API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gmail Configuration
GMAIL_USER = "mridulkalra700@gmail.com"
GMAIL_APP_PASSWORD = "frqd peuk jyef znta"  

# Google Calendar API Scopes
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
    student_emails: List[EmailStr]
    subject: str
    assignment_title: str
    description: str
    due_date: str  # Format: YYYY-MM-DD
    due_time: str = "23:59"  # Format: HH:MM

# ==================== HELPER FUNCTIONS ====================

class EmailManager:
    """Handles email sending and reminders"""
    
    def __init__(self, gmail_user: str, gmail_password: str):
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password
    
    def send_email(self, to_emails: List[str], subject: str, body: str, 
                   attachment_path: Optional[str] = None):
        """Send email with optional attachment"""
        try:
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
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
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
    
    def create_reminder_email_body(self, assignment_title: str, 
                                   days_left: int, due_date: str, 
                                   due_time: str) -> str:
        """Create HTML email body for reminder"""
        urgency = "🔴 URGENT" if days_left <= 1 else "⚠️ REMINDER"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #fff3e0; border-radius: 10px;">
                <h2 style="color: #d32f2f; border-bottom: 2px solid #d32f2f; padding-bottom: 10px;">
                    {urgency} Assignment Due Soon!
                </h2>
                
                <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; border: 2px solid #ff9800;">
                    <h3 style="color: #333; margin-top: 0;">{assignment_title}</h3>
                    
                    <div style="font-size: 24px; color: #d32f2f; text-align: center; padding: 20px; background-color: #ffebee; border-radius: 5px; margin: 15px 0;">
                        <strong>{days_left} {'day' if days_left == 1 else 'days'} left!</strong>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                        <p style="margin: 5px 0;"><strong>📅 Due Date:</strong> {due_date}</p>
                        <p style="margin: 5px 0;"><strong>⏰ Due Time:</strong> {due_time}</p>
                    </div>
                </div>
                
                <p style="color: #666; text-align: center; font-size: 16px; margin-top: 20px;">
                    <strong>Don't forget to submit your assignment!</strong>
                </p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Automated reminder from College Assistant AI<br>
                    Do not reply to this email
                </p>
            </div>
        </body>
        </html>
        """
        return body

class CalendarManager:
    """Handles Google Calendar integration"""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            # Token file stores user's access and refresh tokens
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)
            
            # If no valid credentials, let user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if os.path.exists('credentials.json'):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            'credentials.json', SCOPES)
                        self.creds = flow.run_local_server(port=0)
                    else:
                        print("credentials.json not found. Calendar features disabled.")
                        return
                
                # Save credentials for next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(self.creds, token)
            
            self.service = build('calendar', 'v3', credentials=self.creds)
        except Exception as e:
            print(f"Calendar authentication error: {e}")
    
    def create_event(self, summary: str, description: str, 
                    start_datetime: datetime, end_datetime: datetime,
                    attendees: List[str] = None) -> Optional[str]:
        """Create a calendar event"""
        if not self.service:
            return None
        
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
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 60},  # 1 hour before
                    ],
                },
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            event = self.service.events().insert(
                calendarId='primary', 
                body=event,
                sendUpdates='all'  # Send email invites to attendees
            ).execute()
            
            return event.get('id')
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None

class ImageOCR:
    """Extract text from images using OCR"""
    
    @staticmethod
    def extract_text_from_image(image_path: str) -> str:
        """Extract text from image using Tesseract OCR"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""

# ==================== DOCUMENT STORAGE ====================

class DocumentStore:
    """Stores and manages college documents"""
    
    def __init__(self):
        self.timetable = ""
        self.syllabus = ""
        self.college_info = ""
        self.uploads_dir = "uploads"
        self.assignments_dir = "assignments"
        
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.assignments_dir, exist_ok=True)
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return ""
    
    def extract_text_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR"""
        return ImageOCR.extract_text_from_image(file_path)
    
    def store_document(self, file_path: str, doc_type: str) -> bool:
        """Store document content based on type"""
        try:
            # Detect file type and extract text
            if file_path.lower().endswith('.pdf'):
                content = self.extract_text_from_pdf(file_path)
            elif file_path.lower().endswith('.txt'):
                content = self.extract_text_from_txt(file_path)
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                content = self.extract_text_from_image(file_path)
            else:
                return False
            
            # Store in appropriate category
            if doc_type == "timetable":
                self.timetable = content
            elif doc_type == "syllabus":
                self.syllabus = content
            elif doc_type == "info":
                self.college_info = content
            
            return True
        except Exception as e:
            print(f"Error storing document: {e}")
            return False
    
    def get_relevant_context(self, query: str) -> str:
        """Get relevant context based on query"""
        context = []
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['timetable', 'schedule', 'class', 'time']):
            if self.timetable:
                context.append(f"TIMETABLE:\n{self.timetable[:2000]}")
        
        if any(word in query_lower for word in ['syllabus', 'course', 'subject', 'curriculum']):
            if self.syllabus:
                context.append(f"SYLLABUS:\n{self.syllabus[:2000]}")
        
        if any(word in query_lower for word in ['college', 'campus', 'facility', 'about']):
            if self.college_info:
                context.append(f"COLLEGE INFO:\n{self.college_info[:2000]}")
        
        return "\n\n".join(context) if context else "No relevant documents uploaded yet."

# Initialize components
doc_store = DocumentStore()
email_manager = EmailManager(GMAIL_USER, GMAIL_APP_PASSWORD)
calendar_manager = CalendarManager()

# ==================== OLLAMA AGENT ====================

class CollegeAgent:
    """AI Agent using Ollama"""
    
    def __init__(self, model_name: str = "llama3.2"):
        self.model = model_name
        self.system_prompt = """You are a helpful college assistant AI. Your role is to:
1. Answer questions about timetables, schedules, and class timings
2. Provide information about syllabus and course content
3. Share college information and facilities
4. Help with general college-related queries

Always be concise, friendly, and accurate. If you don't have enough information 
in the provided context, politely ask the user to upload relevant documents.

Format your responses clearly with proper structure when needed."""
    
    def generate_response(self, query: str, context: str, 
                         conversation_history: List[ChatMessage] = None) -> str:
        """Generate response using Ollama"""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if conversation_history:
                for msg in conversation_history[-5:]:
                    messages.append({"role": msg.role, "content": msg.content})
            
            user_message = f"Context from college documents:\n{context}\n\nUser Query: {query}"
            messages.append({"role": "user", "content": user_message})
            
            response = ollama.chat(model=self.model, messages=messages)
            return response['message']['content']
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I encountered an error. Please ensure Ollama is running."

agent = CollegeAgent()

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running", 
        "message": "College Assistant API with Email & Calendar Integration"
    }

@app.post("/upload/{doc_type}")
async def upload_document(doc_type: str, file: UploadFile = File(...)):
    """Upload documents (supports PDF, TXT, and Images)"""
    if doc_type not in ["timetable", "syllabus", "info"]:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    # Save file
    file_path = os.path.join(doc_store.uploads_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Process document
    success = doc_store.store_document(file_path, doc_type)
    
    if success:
        return {
            "status": "success",
            "message": f"{doc_type.capitalize()} uploaded and processed successfully",
            "filename": file.filename
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to process document")

@app.post("/upload/assignment")
async def upload_assignment(file: UploadFile = File(...)):
    """Upload assignment file"""
    try:
        file_path = os.path.join(doc_store.assignments_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "status": "success",
            "message": "Assignment file uploaded successfully",
            "filename": file.filename,
            "file_path": file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload assignment: {str(e)}")

@app.post("/send-assignment")
async def send_assignment(assignment: AssignmentEmail):
    """Send assignment email and create calendar events"""
    try:
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
        
        # Send email
        email_sent = email_manager.send_email(
            assignment.student_emails,
            f"📚 New Assignment: {assignment.subject}",
            email_body
        )
        
        # Create calendar event
        event_id = None
        if calendar_manager.service:
            event_id = calendar_manager.create_event(
                summary=f"Assignment Due: {assignment.assignment_title}",
                description=f"{assignment.subject}\n\n{assignment.description}",
                start_datetime=due_datetime - timedelta(hours=1),
                end_datetime=due_datetime,
                attendees=assignment.student_emails
            )
        
        # Schedule reminders (in real app, use task queue like Celery)
        # For now, just return success
        
        return {
            "status": "success",
            "message": "Assignment sent successfully",
            "email_sent": email_sent,
            "calendar_event_created": event_id is not None,
            "event_id": event_id,
            "recipients": len(assignment.student_emails)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending assignment: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """Query the AI agent"""
    try:
        context = doc_store.get_relevant_context(request.message)
        response = agent.generate_response(
            query=request.message,
            context=context,
            conversation_history=request.conversation_history
        )
        
        return QueryResponse(
            response=response,
            context_used=context if context != "No relevant documents uploaded yet." else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/documents/status")
async def get_document_status():
    """Check document upload status"""
    return {
        "timetable": bool(doc_store.timetable),
        "syllabus": bool(doc_store.syllabus),
        "college_info": bool(doc_store.college_info)
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Enhanced College Assistant Backend...")
    print("Features: Image OCR, Email Automation, Google Calendar Integration")
    print("Make sure Ollama is running: ollama serve")
    uvicorn.run(app, host="0.0.0.0", port=8000)