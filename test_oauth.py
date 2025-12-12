"""Test Google Drive OAuth authentication"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'client_secret_318367230698-6uqtpl75r5j6t6vartbl1uib7ist5igu.apps.googleusercontent.com.json'
TOKEN_FILE = 'token.json'

def main():
    print("\n" + "="*60)
    print("GOOGLE DRIVE OAUTH AUTHENTICATION TEST")
    print("="*60)

    creds = None

    # Check for existing token
    if os.path.exists(TOKEN_FILE):
        print("\nFound existing token, loading...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            creds.refresh(Request())
        else:
            print("\nStarting OAuth flow...")
            print("A browser window will open for authentication.")
            print("Log in with: ahmedsabri85@gmail.com")
            print("-"*60)

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save token for future use
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"\nToken saved to {TOKEN_FILE}")

    # Test the connection
    print("\nConnecting to Google Drive...")
    service = build('drive', 'v3', credentials=creds)

    # Get user info
    about = service.about().get(fields="user, storageQuota").execute()
    user = about.get('user', {})
    quota = about.get('storageQuota', {})

    print("\n" + "="*60)
    print("CONNECTION SUCCESSFUL!")
    print("="*60)
    print(f"\nLogged in as: {user.get('displayName')} ({user.get('emailAddress')})")

    # Show storage info
    if quota:
        used = int(quota.get('usage', 0)) / (1024**3)
        limit = int(quota.get('limit', 0)) / (1024**3)
        print(f"Storage: {used:.2f} GB used of {limit:.2f} GB")

    # List some files
    print("\n" + "-"*60)
    print("First 5 files in your Drive:")
    print("-"*60)

    results = service.files().list(pageSize=5, fields="files(name, mimeType)").execute()
    files = results.get('files', [])

    for f in files:
        ftype = "FOLDER" if 'folder' in f['mimeType'] else "FILE"
        print(f"  [{ftype}] {f['name']}")

    print("\n" + "="*60)
    print("OAUTH TEST COMPLETE - Ready to use!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
