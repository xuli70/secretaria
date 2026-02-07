import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials


def _get_service(creds: Credentials):
    return build("drive", "v3", credentials=creds)


MIME_ICONS = {
    "application/vnd.google-apps.folder": "folder",
    "application/vnd.google-apps.document": "gdoc",
    "application/vnd.google-apps.spreadsheet": "gsheet",
    "application/vnd.google-apps.presentation": "gslides",
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
    "text/plain": "txt",
}


def list_files(
    creds: Credentials,
    query: str = "",
    folder_id: str | None = None,
    max_results: int = 30,
) -> list[dict]:
    service = _get_service(creds)
    q_parts = ["trashed=false"]
    if folder_id:
        q_parts.append(f"'{folder_id}' in parents")
    if query:
        q_parts.append(f"name contains '{query}'")

    result = (
        service.files()
        .list(
            q=" and ".join(q_parts),
            pageSize=max_results,
            fields="files(id,name,mimeType,size,modifiedTime,webViewLink,iconLink,parents)",
            orderBy="modifiedTime desc",
        )
        .execute()
    )
    return [_format_file(f) for f in result.get("files", [])]


def list_recent(creds: Credentials, max_results: int = 20) -> list[dict]:
    service = _get_service(creds)
    result = (
        service.files()
        .list(
            q="trashed=false and 'me' in owners",
            pageSize=max_results,
            fields="files(id,name,mimeType,size,modifiedTime,webViewLink,iconLink,parents)",
            orderBy="modifiedTime desc",
        )
        .execute()
    )
    return [_format_file(f) for f in result.get("files", [])]


def get_file(creds: Credentials, file_id: str) -> dict:
    service = _get_service(creds)
    f = (
        service.files()
        .get(
            fileId=file_id,
            fields="id,name,mimeType,size,modifiedTime,webViewLink,iconLink,parents,description",
        )
        .execute()
    )
    return _format_file(f)


def download_file(creds: Credentials, file_id: str) -> tuple[bytes, str, str]:
    """Download file content. Returns (bytes, filename, mime_type)."""
    service = _get_service(creds)
    meta = service.files().get(fileId=file_id, fields="name,mimeType").execute()
    mime = meta.get("mimeType", "")
    name = meta.get("name", "file")

    # Google Workspace files need export
    export_map = {
        "application/vnd.google-apps.document": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx",
        ),
        "application/vnd.google-apps.spreadsheet": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
        ),
        "application/vnd.google-apps.presentation": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".pptx",
        ),
    }

    if mime in export_map:
        export_mime, ext = export_map[mime]
        content = service.files().export(fileId=file_id, mimeType=export_mime).execute()
        if not name.endswith(ext):
            name += ext
        return content, name, export_mime

    content = service.files().get_media(fileId=file_id).execute()
    return content, name, mime


def upload_file(
    creds: Credentials,
    filename: str,
    content: bytes,
    mime_type: str,
    folder_id: str | None = None,
) -> dict:
    service = _get_service(creds)
    file_metadata: dict = {"name": filename}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)
    f = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id,name,mimeType,size,modifiedTime,webViewLink",
        )
        .execute()
    )
    return _format_file(f)


def list_folders(creds: Credentials) -> list[dict]:
    service = _get_service(creds)
    result = (
        service.files()
        .list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            pageSize=100,
            fields="files(id,name,modifiedTime)",
            orderBy="name",
        )
        .execute()
    )
    return [
        {
            "id": f.get("id", ""),
            "name": f.get("name", ""),
            "modified": f.get("modifiedTime", ""),
        }
        for f in result.get("files", [])
    ]


def _format_file(f: dict) -> dict:
    mime = f.get("mimeType", "")
    is_folder = mime == "application/vnd.google-apps.folder"
    size = int(f.get("size", 0)) if f.get("size") else None
    file_type = MIME_ICONS.get(mime, mime.split("/")[-1] if "/" in mime else "file")
    return {
        "id": f.get("id", ""),
        "name": f.get("name", ""),
        "mime_type": mime,
        "size": size,
        "modified": f.get("modifiedTime", ""),
        "web_link": f.get("webViewLink", ""),
        "is_folder": is_folder,
        "file_type": file_type,
    }
