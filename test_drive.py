"""Test Google Drive API connection using Service Account"""
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Service account credentials file
SERVICE_ACCOUNT_FILE = 'work-pc-storage-5e227b7e424e.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    """Test Google Drive API connection with Service Account."""
    print("\n" + "="*60)
    print("TESTING GOOGLE DRIVE CONNECTION (Service Account)")
    print("="*60)

    # Load service account credentials
    print("\nLoading service account credentials...")
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    print(f"Service Account: {credentials.service_account_email}")

    # Build the Drive API service
    print("Connecting to Google Drive API...")
    service = build('drive', 'v3', credentials=credentials)

    # List all files/folders shared with this service account
    print("\n" + "-"*60)
    print("FILES/FOLDERS SHARED WITH SERVICE ACCOUNT:")
    print("-"*60)

    results = service.files().list(
        pageSize=20,
        fields="files(id, name, mimeType, owners)"
    ).execute()

    files = results.get('files', [])

    if not files:
        print('\nNo files found!')
        print('Make sure you shared a folder with:')
        print('  file-transfer@work-pc-storage.iam.gserviceaccount.com')
    else:
        print(f"\nFound {len(files)} item(s):\n")
        for f in files:
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                icon = "[FOLDER]"
            else:
                icon = "[FILE]  "
            print(f"  {icon} {f['name']}")
            print(f"           ID: {f['id']}")

    print("\n" + "="*60)
    print("CONNECTION TEST COMPLETE!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
