# Google Drive API Setup Guide for Streamlit Apps

This guide documents how to set up a Streamlit app that can read/write files to your Google Drive. This approach can be used as a free alternative to Supabase or other cloud storage for personal projects.

## What This Enables

- Upload/download files via a web app
- Programmatically read/write Excel, CSV, JSON files
- Use Google Drive as a database backend (up to 15GB free, or your full quota)
- Access from any device (work PC, mobile, personal laptop)

---

## Step 1: Create a Google Cloud Project

1. Go to: https://console.cloud.google.com
2. Click **"Select a project"** → **"New Project"**
3. Name it (e.g., "My App Storage")
4. Click **Create**

---

## Step 2: Enable Google Drive API

1. In Google Cloud Console, go to: **APIs & Services** → **Library**
2. Search for **"Google Drive API"**
3. Click on it → Click **"Enable"**

---

## Step 3: Create OAuth 2.0 Credentials

### 3a. Configure OAuth Consent Screen

1. Go to: **APIs & Services** → **OAuth consent screen**
   - Or try: https://console.cloud.google.com/apis/credentials/consent
2. Choose **"External"** (unless you have Google Workspace)
3. Fill in:
   - App name: anything (e.g., "File Transfer")
   - User support email: your email
   - Developer contact email: your email
4. Click **Save and Continue** through the rest

### 3b. Add Yourself as a Test User (IMPORTANT!)

1. Go to: **Google Auth Platform** → **Audience**
   - Or: **OAuth consent screen** → **Test users**
   - Direct link: https://console.cloud.google.com/auth/audience
2. Click **"+ ADD USERS"**
3. Add your Gmail address (e.g., `yourname@gmail.com`)
4. Click **Save**

> **Why?** Unverified apps can only be used by test users. Without this step, you'll get "Access blocked" error.

### 3c. Create OAuth Client ID

1. Go to: **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: anything (e.g., "Streamlit App")
5. Click **Create**
6. **Download the JSON file** (click the download button)
7. Save it in your project folder

---

## Step 4: Authenticate and Get Token (One-Time)

Create a test script to authenticate and save your token:

```python
# test_oauth.py
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'your_client_secret_file.json'  # The file you downloaded
TOKEN_FILE = 'token.json'

def main():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            print(f"Token saved to {TOKEN_FILE}")

    # Test connection
    service = build('drive', 'v3', credentials=creds)
    about = service.about().get(fields="user").execute()
    print(f"Connected as: {about['user']['emailAddress']}")

if __name__ == '__main__':
    main()
```

Run it:
```bash
python test_oauth.py
```

A browser will open. Log in with your Google account and allow access. This creates `token.json`.

---

## Step 5: Use in Your Streamlit App

```python
import streamlit as st
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_credentials():
    """Get Google credentials from secrets (cloud) or local file."""
    creds = None

    # For Streamlit Cloud deployment
    try:
        if 'google_token' in st.secrets:
            token_info = {
                'token': st.secrets['google_token']['token'],
                'refresh_token': st.secrets['google_token']['refresh_token'],
                'token_uri': st.secrets['google_token']['token_uri'],
                'client_id': st.secrets['google_token']['client_id'],
                'client_secret': st.secrets['google_token']['client_secret'],
                'scopes': list(st.secrets['google_token']['scopes']),
            }
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    except:
        pass

    # For local development
    if creds is None and os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Refresh if expired
    if creds and not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds

def get_drive_service():
    creds = get_credentials()
    return build('drive', 'v3', credentials=creds, cache_discovery=False)
```

---

## Step 6: Deploy to Streamlit Cloud

### 6a. Push to GitHub

Make sure your `.gitignore` includes:
```
token.json
*client_secret*.json
```

Push your app (without credentials) to GitHub.

### 6b. Configure Secrets in Streamlit Cloud

1. Go to: https://share.streamlit.io
2. Deploy your app
3. Go to **Settings** → **Secrets**
4. Add your token in TOML format:

```toml
[google_token]
token = "ya29.xxxxx..."
refresh_token = "1//xxxxx..."
token_uri = "https://oauth2.googleapis.com/token"
client_id = "xxxxx.apps.googleusercontent.com"
client_secret = "GOCSPX-xxxxx"
scopes = ["https://www.googleapis.com/auth/drive"]
```

Get these values from your `token.json` file.

---

## Common Operations

### List Files in a Folder
```python
def list_files(service, folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])
```

### Upload a File
```python
from googleapiclient.http import MediaIoBaseUpload
import io

def upload_file(service, folder_id, filename, content, mime_type):
    metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type)
    file = service.files().create(body=metadata, media_body=media, fields='id').execute()
    return file['id']
```

### Download a File
```python
from googleapiclient.http import MediaIoBaseDownload
import io

def download_file(service, file_id):
    request = service.files().get_media(fileId=file_id)
    content = io.BytesIO()
    downloader = MediaIoBaseDownload(content, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    content.seek(0)
    return content.read()
```

### Read Excel/CSV File
```python
import pandas as pd

def read_excel_from_drive(service, file_id):
    content = download_file(service, file_id)
    return pd.read_excel(io.BytesIO(content))

def read_csv_from_drive(service, file_id):
    content = download_file(service, file_id)
    return pd.read_csv(io.BytesIO(content))
```

### Write DataFrame to Drive
```python
def save_excel_to_drive(service, folder_id, filename, df):
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return upload_file(service, folder_id, filename, buffer.read(),
                       'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
```

---

## What We Tried (And Why It Failed)

### Service Account Approach ❌
- Created a service account
- Shared a folder with the service account email
- **Failed because:** Service accounts don't have storage quota. They can only access files shared with them, not create new files.

### OAuth Without Test User ❌
- Created OAuth credentials
- Tried to authenticate
- **Failed because:** Unverified apps require test users to be explicitly added in Google Cloud Console.

### OAuth With Test User ✅
- Added ourselves as a test user
- Authenticated successfully
- Token saved and works for deployment

---

## Key Takeaways

1. **Use OAuth, not Service Account** for personal apps that need to create files
2. **Always add yourself as a test user** before authenticating
3. **Save the token.json** - it contains refresh_token for long-term access
4. **Use Streamlit secrets** for cloud deployment (never commit tokens)
5. **Google Drive = Free 15GB database** that you can manipulate programmatically

---

## Useful Links

- Google Cloud Console: https://console.cloud.google.com
- Google Drive API Docs: https://developers.google.com/drive/api/v3/reference
- Streamlit Secrets Docs: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
