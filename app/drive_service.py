"""
CartLink - Google Drive Service
Handles all interactions with the Google Drive API
"""

import os
import mimetypes
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request


class DriveService:
    """
    Wrapper around the Google Drive API v3.
    Handles file upload, permission management, and link generation.
    """

    def __init__(self, credentials):
        """
        Initialize the Drive service with valid OAuth2 credentials.

        Args:
            credentials: google.oauth2.credentials.Credentials object
        """
        # Refresh credentials if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        self.service = build('drive', 'v3', credentials=credentials)

    def upload_file(self, file_path: str, filename: str, folder_id: str = None) -> tuple:
        """
        Upload a file to Google Drive.

        Args:
            file_path: Local path to the file
            filename: Original filename to use in Drive
            folder_id: Optional Drive folder ID to upload into

        Returns:
            Tuple of (file_id, file_name)
        """
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        # File metadata
        file_metadata = {'name': filename}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        # Create media upload object with resumable upload for large files
        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True,
            chunksize=1024 * 1024  # 1MB chunks
        )

        # Execute upload
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, size, mimeType'
        ).execute()

        return file['id'], file['name']

    def set_public_permission(self, file_id: str) -> None:
        """
        Set file permission to 'anyone with the link can view'.

        Args:
            file_id: Google Drive file ID
        """
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }

        self.service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()

    def get_shareable_link(self, file_id: str) -> str:
        """
        Get the public shareable link for a file.

        Args:
            file_id: Google Drive file ID

        Returns:
            Shareable URL string
        """
        return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

    def get_file_info(self, file_id: str) -> dict:
        """
        Get metadata for a Drive file.

        Args:
            file_id: Google Drive file ID

        Returns:
            Dictionary with file metadata
        """
        return self.service.files().get(
            fileId=file_id,
            fields='id, name, size, mimeType, createdTime, webViewLink'
        ).execute()

    def delete_file(self, file_id: str) -> None:
        """
        Delete a file from Drive (useful for cleanup).

        Args:
            file_id: Google Drive file ID
        """
        self.service.files().delete(fileId=file_id).execute()
