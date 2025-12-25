"""
Google Calendar Setup - Run this ONCE to authenticate
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

def setup_calendar():
    print("\n" + "="*60)
    print("Google Calendar Authentication Setup")
    print("="*60)
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("\n❌ ERROR: credentials.json not found!")
        print("\nTo fix this:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a project (or select existing)")
        print("3. Enable Google Calendar API")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download as 'credentials.json'")
        print("6. Place it in the same folder as this script")
        return False
    
    print("\n✅ credentials.json found!")
    print("\nStarting authentication...")
    print("A browser window will open. Please:")
    print("1. Sign in with your Gmail account")
    print("2. Allow the requested permissions")
    print("3. Return here after successful authentication\n")
    
    try:
        # Delete old token if exists
        if os.path.exists('token.pickle'):
            os.remove('token.pickle')
            print("🗑️  Removed old token")
        
        # Start OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', 
            SCOPES
        )
        
        creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        
        print("\n" + "="*60)
        print("✅ SUCCESS! Calendar authenticated!")
        print("="*60)
        print("\nYou can now:")
        print("1. Start your backend: uvicorn main:app --reload")
        print("2. Calendar events will be created automatically")
        print("\ntoken.pickle has been created and will be used automatically.")
        return True
        
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\nTroubleshooting:")
        print("- Make sure you selected the correct Google account")
        print("- Check if Calendar API is enabled in your project")
        print("- Verify credentials.json is for a Desktop app")
        return False

if __name__ == "__main__":
    setup_calendar()