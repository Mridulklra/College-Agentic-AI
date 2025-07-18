"""
Test script for College Assistant Backend
Run this to test all API endpoints
"""

import requests
import json

# Base URL of your backend
BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health_check():
    """Test if server is running"""
    print_section("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the backend server is running!")
        return False

def test_document_status():
    """Check document upload status"""
    print_section("TEST 2: Document Status")
    try:
        response = requests.get(f"{BASE_URL}/documents/status")
        print(f"Status Code: {response.status_code}")
        print(f"Uploaded Documents: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_upload_document():
    """Test document upload"""
    print_section("TEST 3: Upload Sample Document")
    
    # Create a sample timetable file
    sample_content = """
COLLEGE TIMETABLE - Computer Science Department

MONDAY:
9:00 AM - 10:00 AM: Data Structures - Room 101 - Prof. Smith
10:15 AM - 11:15 AM: Operating Systems - Lab 2 - Prof. Johnson
11:30 AM - 12:30 PM: Database Management - Room 205 - Prof. Williams
2:00 PM - 3:00 PM: Web Development - Lab 1 - Prof. Brown

TUESDAY:
9:00 AM - 10:00 AM: Computer Networks - Room 303 - Prof. Davis
10:15 AM - 11:15 AM: Software Engineering - Room 101 - Prof. Miller
1:00 PM - 2:00 PM: AI and Machine Learning - Lab 3 - Prof. Wilson

WEDNESDAY:
9:00 AM - 10:00 AM: Data Structures Lab - Lab 2 - Prof. Smith
11:00 AM - 12:00 PM: Database Lab - Lab 1 - Prof. Williams
2:00 PM - 3:00 PM: Project Work - Room 401

THURSDAY:
9:00 AM - 10:00 AM: Computer Networks Lab - Lab 3 - Prof. Davis
10:15 AM - 11:15 AM: Operating Systems - Room 101 - Prof. Johnson
2:00 PM - 4:00 PM: Seminar - Auditorium 
FRIDAY:
9:00 AM - 10:00 AM: Web Development - Room 303 - Prof. Brown
10:15 AM - 11:15 AM: AI and Machine Learning - Room 205 - Prof. Wilson
11:30 AM - 12:30 PM: Software Engineering Lab - Lab 1 - Prof. Miller
"""
    
    # Save to a temporary fil
    with open("sample_timetable.txt", "w") as f:
        f.write(sample_content)
    
    try:
        # Upload the file
        with open("sample_timetable.txt", "rb") as f:
            files = {"file": ("timetable.txt", f, "text/plain")}
            response = requests.post(
                f"{BASE_URL}/upload/timetable",
                files=files
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Document uploaded successfully!")
            return True
        else:
            print("❌ Upload failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_query(question):
    """Test querying the agent"""
    print_section(f"TEST 4: Query - '{question}'")
    
    try:
        payload = {
            "message": question,
            "conversation_history": []
        }
        
        response = requests.post(
            f"{BASE_URL}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📝 AI Response:\n{data['response']}")
            if data.get('context_used'):
                print(f"\n📄 Context Used: Yes")
            print("\n✅ Query successful!")
            return True
        else:
            print(f"❌ Query failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_conversation():
    """Test conversation with history"""
    print_section("TEST 5: Conversation with History")
    
    try:
        # First message
        history = []
        
        message1 = "What classes do I have on Monday?"
        payload1 = {
            "message": message1,
            "conversation_history": history
        }
        
        print(f"User: {message1}")
        response1 = requests.post(f"{BASE_URL}/query", json=payload1)
        
        if response1.status_code == 200:
            ai_response1 = response1.json()['response']
            print(f"AI: {ai_response1[:200]}...")
            
            # Add to history
            history.append({"role": "user", "content": message1})
            history.append({"role": "assistant", "content": ai_response1})
            
            # Second message (follow-up)
            message2 = "What time is the Data Structures class?"
            payload2 = {
                "message": message2,
                "conversation_history": history
            }
            
            print(f"\nUser: {message2}")
            response2 = requests.post(f"{BASE_URL}/query", json=payload2)
            
            if response2.status_code == 200:
                ai_response2 = response2.json()['response']
                print(f"AI: {ai_response2}")
                print("\n✅ Conversation test successful!")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n🚀 Starting Backend Tests...")
    print("Make sure your backend is running on http://localhost:8000")
    print("Make sure Ollama is running with: ollama serve")
    
    tests_passed = 0
    total_tests = 5
    
    # Run tests
    if test_health_check():
        tests_passed += 1
    
    if test_document_status():
        tests_passed += 1
    
    if test_upload_document():
        tests_passed += 1
    
    # Test various queries
    queries = [
        "What's my schedule for Monday?",
        "When is my Operating Systems class?",
        "Tell me about my Wednesday classes"
    ]
    
    if test_query(queries[0]):
        tests_passed += 1
    
    if test_conversation():
        tests_passed += 1
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Your backend is working perfectly!")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    print("\n💡 Next Steps:")
    print("1. Try different queries")
    print("2. Upload your own timetable/syllabus PDF or TXT files")
    print("3. Build the frontend or use Postman for more testing")

if __name__ == "__main__":
    main()