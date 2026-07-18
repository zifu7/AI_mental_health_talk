import os
import uuid
from datetime import datetime
import aiofiles
from fastapi import UploadFile

UPLOAD_DIR = "uploads"

async def save_upload_file(
    file: UploadFile,
    business_type: str,
    business_id: str = None,
    business_field: str = None
) -> str:
    """异步保存上传文件"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    now = datetime.now()
    sub_dir = os.path.join(
        UPLOAD_DIR,
        business_type,
        str(now.year),
        f"{now.month:02d}",
        f"{now.day:02d}"
    )
    os.makedirs(sub_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    new_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(sub_dir, new_filename)

    async with aiofiles.open(file_path, "wb") as buffer:
        content = await file.read()
        await buffer.write(content)

    relative_path = f"/{sub_dir.replace(os.sep, '/')}/{new_filename}"
    return relative_path