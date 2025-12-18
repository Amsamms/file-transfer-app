#!/usr/bin/env python3
"""
Automatic cleanup script for Google Drive WorkPC_Transfer folder.
Deletes files older than 7 days.
Designed to run via GitHub Actions.
"""
import os
import logging
from datetime import datetime, timedelta, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_NAME = 'WorkPC_Transfer'
MAX_AGE_DAYS = 7

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_credentials():
    """Get Google credentials from environment variables."""
    token_info = {
        'token': os.environ.get('GOOGLE_TOKEN'),
        'refresh_token': os.environ.get('GOOGLE_REFRESH_TOKEN'),
        'token_uri': os.environ.get('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'scopes': SCOPES,
    }

    # Validate required fields
    required = ['token', 'refresh_token', 'client_id', 'client_secret']
    missing = [k for k in required if not token_info.get(k)]
    if missing:
        raise ValueError(f"Missing required credentials: {missing}")

    creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    # Refresh if expired
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            logger.info("Token expired, refreshing...")
            creds.refresh(Request())
            logger.info("Token refreshed successfully")
        else:
            raise ValueError("Invalid credentials and cannot refresh")

    return creds


def get_drive_service():
    """Create Google Drive service."""
    creds = get_credentials()
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


def get_folder_id(service):
    """Get the WorkPC_Transfer folder ID."""
    query = f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])

    if not files:
        logger.warning(f"Folder '{FOLDER_NAME}' not found")
        return None

    return files[0]['id']


def list_files(service, folder_id):
    """List all files in the folder with metadata."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name, modifiedTime, size)",
        orderBy="modifiedTime asc"
    ).execute()
    return results.get('files', [])


def delete_file(service, file_id, file_name):
    """Delete a file from Google Drive."""
    service.files().delete(fileId=file_id).execute()
    logger.info(f"Deleted: {file_name}")


def cleanup_old_files():
    """Main cleanup function."""
    logger.info("Starting cleanup process...")
    logger.info(f"Will delete files older than {MAX_AGE_DAYS} days")

    service = get_drive_service()
    folder_id = get_folder_id(service)

    if not folder_id:
        logger.info("No folder found, nothing to clean up")
        return 0

    files = list_files(service, folder_id)
    logger.info(f"Found {len(files)} files in folder")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    logger.info(f"Cutoff date: {cutoff_date.isoformat()}")

    deleted_count = 0

    for file in files:
        # Parse the modified time (ISO 8601 format)
        modified_time = datetime.fromisoformat(
            file['modifiedTime'].replace('Z', '+00:00')
        )

        if modified_time < cutoff_date:
            age_days = (datetime.now(timezone.utc) - modified_time).days
            logger.info(
                f"File '{file['name']}' is {age_days} days old - DELETING"
            )
            delete_file(service, file['id'], file['name'])
            deleted_count += 1
        else:
            age_days = (datetime.now(timezone.utc) - modified_time).days
            logger.info(f"Keeping: {file['name']} ({age_days} days old)")

    logger.info(f"Cleanup complete. Deleted {deleted_count} files.")
    return deleted_count


if __name__ == '__main__':
    try:
        deleted = cleanup_old_files()
        print(f"Cleanup successful. Deleted {deleted} old files.")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        print(f"Cleanup failed: {e}")
        exit(1)
