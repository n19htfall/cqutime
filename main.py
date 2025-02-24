import os
import mimetypes
import aiofiles
import logging
import uuid

from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
from config import Settings
from UrlConfig import FRONTED_URL
from cqutimetable.timetable import Timetable


# FastAPI 实现
fast_app = FastAPI()
settings = Settings()

fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTED_URL],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],  # 允许所有请求头
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FileUploadError(HTTPException):
    pass


@fast_app.exception_handler(FileUploadError)
async def file_upload_error_handler(request: Request, exc: FileUploadError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


# 响应模型
class FileResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    upload_time: datetime
    timetable: str


# 工具函数
def validate_file(file: UploadFile, content: bytes) -> None:
    """验证文件的扩展名和 MIME 类型"""
    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise FileUploadError(
            status_code=400,
            detail=f"不支持的文件类型。允许的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # 检查 MIME 类型
    mime_type, _ = mimetypes.guess_type(file.filename)
    if not mime_type or mime_type not in settings.ALLOWED_MIME_TYPES:
        raise FileUploadError(
            status_code=400,
            detail=f"不支持的文件类型。允许的 MIME 类型: {', '.join(settings.ALLOWED_MIME_TYPES)}",
        )


async def save_file(file: UploadFile, file_id: str) -> Path:
    """异步保存文件"""
    upload_dir = Path(settings.UPLOAD_DIR) / datetime.now().strftime("%Y/%m/%d")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{file_id}{os.path.splitext(file.filename)[1]}"

    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            while content := await file.read(settings.CHUNK_SIZE):
                await out_file.write(content)
    except Exception as e:
        logger.error(f"保存文件失败: {str(e)}")
        raise FileUploadError(status_code=500, detail="文件保存失败")
    return file_path


@fast_app.post("/upload", response_model=FileResponse)
async def fastapi_upload(file: UploadFile = File(...), semester: str = Form(...)):
    # 检查文件大小
    file_size = 0
    content = await file.read()
    file_size = len(content)
    if file_size > settings.MAX_FILE_SIZE:
        raise FileUploadError(
            status_code=400,
            detail=f"文件太大。最大允许大小: {settings.MAX_FILE_SIZE/1024/1024}MB",
        )

    # 验证文件
    validate_file(file, content)

    # 生成唯一文件ID
    file_id = str(uuid.uuid4())

    # 重置文件指针
    await file.seek(0)

    # 保存excel文件
    file_path = await save_file(file, file_id)

    file_paths = [file_id + ".txt", file_id + ".ics"]
    # 创建课表
    try:
        tt = Timetable(file_path, file_id, semester)
        if tt is None:
            for fpath in file_paths:
                if os.path.exists(fpath):
                    os.remove(fpath)
            raise FileUploadError(
                status_code=500,
                detail="课表解析失败",
            )
    except ValueError:
        for fpath in file_paths:
            if os.path.exists(fpath):
                os.remove(fpath)
        raise FileUploadError(
            status_code=400,
            detail="格式错误",
        )
    try:
        tt.export_ics()
    except Exception:
        for fpath in file_paths:
            if os.path.exists(fpath):
                os.remove(fpath)
        raise FileUploadError(
            status_code=500,
            detail="导出ics文件失败",
        )

    with open(file_id + ".txt", "rb") as f:
        content = f.read()

    for fpath in file_paths:
        if os.path.exists(fpath):
            os.remove(fpath)

    # 返回响应
    return FileResponse(
        file_id=file_id,
        filename=file.filename,
        size=file_size,
        upload_time=datetime.now(),
        timetable=content.decode("utf-8"),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(fast_app, host="0.0.0.0", port=8849)
