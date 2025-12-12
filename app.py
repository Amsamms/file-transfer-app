"""
File Transfer App - Upload/Download files via Google Drive
Works as a bridge between personal devices and work PC
"""
import streamlit as st
import os
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_NAME = 'WorkPC_Transfer'

@st.cache_resource
def get_drive_service():
    """Create and cache the Google Drive service using OAuth."""
    creds = None

    # Try to load from Streamlit secrets (for cloud deployment)
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
    except Exception as e:
        st.warning(f"Could not load from secrets: {e}")

    # Fall back to local token file (for local development)
    if creds is None and os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds:
        st.error("No credentials found! Please configure secrets or run locally with token.json")
        st.stop()

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                st.error(f"Failed to refresh token: {e}")
                st.stop()
        else:
            st.error("Invalid credentials and cannot refresh!")
            st.stop()

    return build('drive', 'v3', credentials=creds)

@st.cache_data(ttl=60)
def get_folder_id(_service):
    """Get or create the WorkPC_Transfer folder."""
    query = f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = _service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])

    if files:
        return files[0]['id']

    folder_metadata = {
        'name': FOLDER_NAME,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = _service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

def list_files(service, folder_id):
    """List all files in the shared folder."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name, size, mimeType, createdTime, modifiedTime)",
        orderBy="modifiedTime desc"
    ).execute()
    return results.get('files', [])

def upload_file(service, folder_id, file_name, file_content, mime_type):
    """Upload a file to the shared folder."""
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaIoBaseUpload(
        io.BytesIO(file_content),
        mimetype=mime_type,
        resumable=True
    )
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name'
    ).execute()
    return file

def download_file(service, file_id):
    """Download a file from Google Drive."""
    request = service.files().get_media(fileId=file_id)
    file_content = io.BytesIO()
    downloader = MediaIoBaseDownload(file_content, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    file_content.seek(0)
    return file_content

def delete_file(service, file_id):
    """Delete a file from Google Drive."""
    service.files().delete(fileId=file_id).execute()

def format_size(size_bytes):
    """Format file size in human readable format."""
    if size_bytes is None:
        return "N/A"
    size_bytes = int(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

# Page configuration
st.set_page_config(
    page_title="File Transfer",
    page_icon="📁",
    layout="wide"
)

# Main UI
st.title("📁 File Transfer")
st.markdown("*Transfer files between your devices via Google Drive*")
st.divider()

# Get Drive service
try:
    service = get_drive_service()
    folder_id = get_folder_id(service)
except Exception as e:
    st.error(f"Failed to connect to Google Drive: {e}")
    st.stop()

# Create tabs
tab1, tab2 = st.tabs(["📤 Upload", "📥 Download"])

# Upload Tab
with tab1:
    st.header("Upload Files")

    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        help="Select one or more files to upload to your Google Drive folder"
    )

    if uploaded_files:
        if st.button("Upload All Files", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            success_count = 0
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Uploading: {uploaded_file.name}...")
                try:
                    file_content = uploaded_file.read()
                    mime_type = uploaded_file.type or 'application/octet-stream'
                    upload_file(service, folder_id, uploaded_file.name, file_content, mime_type)
                    success_count += 1
                except Exception as e:
                    st.error(f"Failed to upload {uploaded_file.name}: {e}")
                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.text("Upload complete!")
            if success_count > 0:
                st.success(f"Successfully uploaded {success_count} file(s)!")
                st.balloons()
                st.cache_data.clear()

# Download Tab
with tab2:
    st.header("Download Files")

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()

    try:
        files = list_files(service, folder_id)
    except Exception as e:
        st.error(f"Failed to list files: {e}")
        files = []

    if not files:
        st.info("No files in the folder yet. Upload some files first!")
    else:
        st.write(f"**{len(files)} file(s) available:**")
        st.divider()

        for file in files:
            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])

            with col1:
                mime = file.get('mimeType', '')
                if 'folder' in mime:
                    icon = "📁"
                elif 'image' in mime:
                    icon = "🖼️"
                elif 'pdf' in mime:
                    icon = "📕"
                elif 'zip' in mime or 'compressed' in mime:
                    icon = "🗜️"
                elif 'video' in mime:
                    icon = "🎬"
                elif 'audio' in mime:
                    icon = "🎵"
                elif 'spreadsheet' in mime or 'excel' in mime:
                    icon = "📊"
                elif 'document' in mime or 'word' in mime:
                    icon = "📝"
                else:
                    icon = "📄"
                st.write(f"{icon} **{file['name']}**")

            with col2:
                st.write(format_size(file.get('size')))

            with col3:
                try:
                    file_content = download_file(service, file['id'])
                    st.download_button(
                        label="⬇️",
                        data=file_content,
                        file_name=file['name'],
                        key=f"dl_{file['id']}",
                        help="Download this file"
                    )
                except Exception as e:
                    st.write("❌")

            with col4:
                if st.button("🗑️", key=f"del_{file['id']}", help="Delete"):
                    try:
                        delete_file(service, file['id'])
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")

# Footer
st.divider()
with st.expander("ℹ️ Info"):
    st.write(f"**Folder:** {FOLDER_NAME}")
    st.write(f"**Folder ID:** {folder_id}")
    st.caption("Files are stored in your personal Google Drive")
