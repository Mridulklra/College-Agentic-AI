"""
College Assistant Agent - Backend Server
This application uses Ollama for AI responses and processes college documents
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
import PyPDF2
import os
from typing import Optional, List
import json

# Initialize FastAPI app
app = FastAPI(title="College Assistant API")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATA MODELS ====================

class ChatMessage(BaseModel):
    """Model for chat messages"""
    role: str
    content: str

class QueryRequest(BaseModel):
    """Model for user queries"""
    message: str
    conversation_history: List[ChatMessage] = []

class QueryResponse(BaseModel):
    """Model for agent responses"""
    response: str
    context_used: Optional[str] = None

# ==================== DOCUMENT STORAGE ====================

class DocumentStore:
    """
    Stores and manages college documents (timetable, syllabus, etc.)
    In production, use a proper database or vector store
    """
    def __init__(self):
        self.timetable = ""
        self.syllabus = ""
        self.college_info = ""
        self.uploads_dir = "uploads"
        
        # Create uploads directory if it doesn't exist
        os.makedirs(self.uploads_dir, exist_ok=True)
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file"""
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
        """Extract text content from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return ""
    
    def store_document(self, file_path: str, doc_type: str) -> bool:
        """Store document content based on type"""
        try:
            # Extract text based on file extension
            if file_path.endswith('.pdf'):
                content = self.extract_text_from_pdf(file_path)
            elif file_path.endswith('.txt'):
                content = self.extract_text_from_txt(file_path)
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
        """
        Get relevant context based on query
        In production, use RAG (Retrieval Augmented Generation) with embeddings
        """
        context = []
        query_lower = query.lower()
        
        # Simple keyword matching (improve with embeddings in production)
        if any(word in query_lower for word in ['timetable', 'schedule', 'class', 'time']):
            if self.timetable:
                context.append(f"TIMETABLE:\n{self.timetable[:1000]}")  # Limit context size
        
        if any(word in query_lower for word in ['syllabus', 'course', 'subject', 'curriculum']):
            if self.syllabus:
                context.append(f"SYLLABUS:\n{self.syllabus[:1000]}")
        
        if any(word in query_lower for word in ['college', 'campus', 'facility', 'about']):
            if self.college_info:
                context.append(f"COLLEGE INFO:\n{self.college_info[:1000]}")
        
        return "\n\n".join(context) if context else "No relevant documents uploaded yet."

# Initialize document store
doc_store = DocumentStore()

# ==================== OLLAMA AGENT ====================

class CollegeAgent:
    """
    AI Agent using Ollama for answering college-related queries
    """
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
        """
        Generate response using Ollama with context
        """
        try:
            # Build messages for Ollama
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                }
            ]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-5:]:  # Keep last 5 messages
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Add current query with context
            user_message = f"Context from college documents:\n{context}\n\nUser Query: {query}"
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call Ollama API
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            
            return response['message']['content']
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I encountered an error. Please ensure Ollama is running and the model is available."

# Initialize agent
agent = CollegeAgent()

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "running", "message": "College Assistant API is active"}

@app.post("/upload/{doc_type}")
async def upload_document(doc_type: str, file: UploadFile = File(...)):
    """
    Upload college documents (timetable, syllabus, or college info)
    """
    if doc_type not in ["timetable", "syllabus", "info"]:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    # Save uploaded file
    file_path = os.path.join(doc_store.uploads_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Process and store document
    success = doc_store.store_document(file_path, doc_type)
    
    if success:
        return {
            "status": "success",
            "message": f"{doc_type.capitalize()} uploaded and processed successfully",
            "filename": file.filename
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to process document")

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Send query to the college assistant agent
    """
    try:
        # Get relevant context from documents
        context = doc_store.get_relevant_context(request.message)
        
        # Generate response using Ollama
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
    """
    Check which documents have been uploaded
    """
    return {
        "timetable": bool(doc_store.timetable),
        "syllabus": bool(doc_store.syllabus),
        "college_info": bool(doc_store.college_info)
    }

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    print("Starting College Assistant Backend...")
    print("Make sure Ollama is running: ollama serve")
    print("Pull required model: ollama pull llama3.2")
    uvicorn.run(app, host="0.0.0.0", port=8000)