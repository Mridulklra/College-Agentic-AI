"""
Debug Email Issues - Run this to diagnose the problem
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

GMAIL_USER = "mridulkalra700@gmail.com"
GMAIL_APP_PASSWORD = "frqd peuk jyef znta"

def validate_email_format(email):
    """Check if email format is valid"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def test_email_sending(test_email):
    """Test sending to a specific email"""
    print(f"\n{'='*60}")
    print(f"Testing Email: {test_email}")
    print(f"{'='*60}")
    
    # Step 1: Validate format
    print(f"\n1. Validating email format...")
    if not validate_email_format(test_email):
        print(f"   ❌ INVALID EMAIL FORMAT: {test_email}")
        return False
    print(f"   ✅ Email format is valid")
    
    # Step 2: Clean email
    print(f"\n2. Cleaning email...")
    cleaned_email = test_email.strip().lower()
    print(f"   Original: '{test_email}'")
    print(f"   Cleaned:  '{cleaned_email}'")
    
    # Step 3: Create message
    print(f"\n3. Creating email message...")
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = cleaned_email
    msg['Subject'] = 'Test Email - College Assistant Debug'
    
    body = f"""
    <html>
    <body>
        <h2>Email Delivery Test</h2>
        <p>This is a test email to verify delivery.</p>
        <p><strong>Recipient:</strong> {cleaned_email}</p>
        <p><strong>Sent from:</strong> College Assistant AI</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))
    print(f"   ✅ Message created")
    
    # Step 4: Connect to SMTP
    print(f"\n4. Connecting to Gmail SMTP...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
        print(f"   ✅ Connected to smtp.gmail.com:587")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    try:
        # Step 5: Start TLS
        print(f"\n5. Starting TLS encryption...")
        server.starttls()
        print(f"   ✅ TLS started")
        
        # Step 6: Login
        print(f"\n6. Logging in as {GMAIL_USER}...")
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        print(f"   ✅ Login successful")
        
        # Step 7: Send email
        print(f"\n7. Sending email to {cleaned_email}...")
        
        # Get detailed error info
        refused = server.sendmail(GMAIL_USER, [cleaned_email], msg.as_string())
        
        if refused:
            print(f"   ❌ Server refused recipient: {refused}")
            for email, (code, error_msg) in refused.items():
                print(f"      Email: {email}")
                print(f"      Error Code: {code}")
                print(f"      Error Message: {error_msg.decode() if isinstance(error_msg, bytes) else error_msg}")
            return False
        else:
            print(f"   ✅ Email sent successfully!")
            return True
            
    except smtplib.SMTPRecipientsRefused as e:
        print(f"   ❌ RECIPIENTS REFUSED: {e}")
        print(f"   This means the email address was rejected by Gmail's server")
        print(f"   Possible reasons:")
        print(f"   - Email doesn't exist")
        print(f"   - Email domain has issues")
        print(f"   - Recipient server is blocking emails")
        return False
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ AUTHENTICATION ERROR: {e}")
        print(f"   Check your App Password!")
        return False
        
    except Exception as e:
        print(f"   ❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return False
        
    finally:
        print(f"\n8. Closing connection...")
        server.quit()
        print(f"   ✅ Connection closed")

def main():
    print("="*60)
    print("EMAIL DEBUGGING TOOL")
    print("="*60)
    
    # Test emails
    test_cases = [
        "mridulkalra700@gmail.com",  # Your primary email
        "mridulkalra86@gmail.com",   # Your secondary email
        "test@example.com",           # Invalid (will fail)
    ]
    
    print("\nGmail Account:", GMAIL_USER)
    print("App Password:", "frqd peuk jyef znta")
    print("\n")
    
    results = []
    
    for test_email in test_cases:
        result = test_email_sending(test_email)
        results.append((test_email, result))
        print("\n" + "="*60 + "\n")
        
        # Pause between tests
        if test_email != test_cases[-1]:
            input("Press Enter to test next email...")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for email, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{status}: {email}")
    
    successful = sum(1 for _, result in results if result)
    print(f"\nTotal: {successful}/{len(results)} emails sent successfully")
    
    if successful == 0:
        print("\n⚠️ NO EMAILS SENT!")
        print("\nTroubleshooting steps:")
        print("1. Verify Gmail App Password is correct")
        print("2. Ensure 2-Step Verification is enabled on Gmail")
        print("3. Check if 'Less secure app access' is needed (shouldn't be with App Password)")
        print("4. Try generating a new App Password")
        print("5. Check Gmail account isn't blocked or suspended")
    elif successful < len(results):
        print("\n⚠️ SOME EMAILS FAILED!")
        print("\nThe failed emails might:")
        print("- Not exist")
        print("- Have typos")
        print("- Have domain issues")
    else:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYour email sending is working correctly.")
        print("The issue is likely in how emails are formatted from the frontend.")

if __name__ == "__main__":
    main()