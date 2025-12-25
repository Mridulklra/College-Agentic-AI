"""
Test Email Sending for Assignment System
Run this to debug email issues
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Your Gmail credentials
GMAIL_USER = "mridulkalra700@gmail.com"
GMAIL_APP_PASSWORD = "frqd peuk jyef znta"

def test_basic_email():
    """Test 1: Basic email sending"""
    print("\n" + "="*60)
    print("TEST 1: Basic Email Test")
    print("="*60)
    
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = 'mridulkalra86@gmail.com'  # Send to your other email
        msg['Subject'] = 'Test Email from College Assistant'
        
        body = "This is a test email. If you receive this, email sending works!"
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"Connecting to Gmail SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        print("✅ Connected to SMTP server")
        
        print("Starting TLS...")
        server.starttls()
        print("✅ TLS started")
        
        print(f"Logging in as {GMAIL_USER}...")
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        print("✅ Login successful")
        
        print("Sending email...")
        server.send_message(msg)
        print("✅ Email sent successfully!")
        
        server.quit()
        print("✅ Connection closed")
        
        print("\n✅ TEST 1 PASSED!")
        print("Check mridulkalra700@gmail.com inbox for test email")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\nPossible fixes:")
        print("1. Check App Password is correct")
        print("2. Enable 2-Step Verification on Gmail")
        print("3. Generate new App Password")
        return False
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

def test_html_email():
    """Test 2: HTML email (like assignment emails)"""
    print("\n" + "="*60)
    print("TEST 2: HTML Assignment Email")
    print("="*60)
    
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = 'mridulkalra700@gmail.com'
        msg['Subject'] = '📚 Test Assignment: Data Structures'
        
        html_body = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
                <h2 style="color: #ff6b35;">📚 New Assignment Posted</h2>
                
                <div style="background-color: white; padding: 20px; margin: 20px 0;">
                    <h3>Linked List Implementation</h3>
                    <p><strong>Description:</strong></p>
                    <p style="background-color: #f5f5f5; padding: 15px;">
                        Implement insert, delete, and search operations for linked list
                    </p>
                    
                    <div style="margin-top: 20px; padding: 15px; background-color: #fff3e0;">
                        <p><strong>📅 Due Date:</strong> 2024-12-30</p>
                        <p><strong>⏰ Due Time:</strong> 23:59</p>
                    </div>
                </div>
                
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Sent by College Assistant AI - Test Email
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        print(f"Sending HTML email to mridulkalra700@gmail.com...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print("✅ HTML email sent successfully!")
        print("\n✅ TEST 2 PASSED!")
        print("Check inbox for formatted assignment email")
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

def test_multiple_recipients():
    """Test 3: Multiple recipients"""
    print("\n" + "="*60)
    print("TEST 3: Multiple Recipients")
    print("="*60)
    
    try:
        recipients = ['mridulkalra700@gmail.com', 'mridulkalra2226@gmail.com']
        
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = 'Test: Multiple Recipients'
        
        body = "This email was sent to multiple recipients for testing."
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"Sending to: {recipients}")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print("✅ Email sent to multiple recipients!")
        print("\n✅ TEST 3 PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

def test_backend_endpoint():
    """Test 4: Test actual backend endpoint"""
    print("\n" + "="*60)
    print("TEST 4: Backend API Endpoint")
    print("="*60)
    
    try:
        import requests
        
        payload = {
            "student_emails": ["mridulkalra700@gmail.com"],
            "subject": "Data Structures",
            "assignment_title": "Linked List Assignment",
            "description": "Implement insert, delete, and search operations",
            "due_date": "2024-12-30",
            "due_time": "23:59"
        }
        
        print("Sending request to backend...")
        print(f"Payload: {payload}")
        
        response = requests.post(
            "http://localhost:8000/send-assignment",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Backend Response:")
            print(f"   - Email Sent: {data.get('email_sent')}")
            print(f"   - Calendar Created: {data.get('calendar_event_created')}")
            print(f"   - Recipients: {data.get('recipients')}")
            
            if data.get('email_sent'):
                print("\n✅ TEST 4 PASSED!")
                return True
            else:
                print("\n❌ Backend returned email_sent=False")
                return False
        else:
            print(f"\n❌ Backend error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend!")
        print("Make sure backend is running: uvicorn main:app --reload")
        return False
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

def main():
    """Run all email tests"""
    print("\n🚀 College Assistant - Email Testing Suite")
    print("="*60)
    print("This will test email sending functionality step by step")
    print("="*60)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Basic Email
    if test_basic_email():
        tests_passed += 1
        input("\nPress Enter to continue to Test 2...")
    else:
        print("\n⚠️ Fix Test 1 before continuing!")
        return
    
    # Test 2: HTML Email
    if test_html_email():
        tests_passed += 1
        input("\nPress Enter to continue to Test 3...")
    
    # Test 3: Multiple Recipients
    if test_multiple_recipients():
        tests_passed += 1
        input("\nPress Enter to continue to Test 4...")
    
    # Test 4: Backend Endpoint
    print("\n⚠️ Make sure your backend is running!")
    print("Terminal: uvicorn main:app --reload")
    input("Press Enter when backend is ready...")
    
    if test_backend_endpoint():
        tests_passed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Email system is working!")
    else:
        print(f"⚠️ {total_tests - tests_passed} test(s) failed")
        
    print("\n💡 Next Steps:")
    if tests_passed == 4:
        print("✅ Email system working - test from frontend!")
    elif tests_passed >= 1 and tests_passed < 4:
        print("⚠️ Basic email works but backend has issues")
        print("   Check main.py EmailManager class")
    else:
        print("❌ Email authentication failed")
        print("   1. Check Gmail App Password")
        print("   2. Enable 2-Step Verification")
        print("   3. Generate new App Password")

if __name__ == "__main__":
    main()