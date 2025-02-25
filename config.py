from typing import List

# App配置类
class Settings:
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 1024 * 1024 * 2  # 2MB
    ALLOWED_EXTENSIONS: List[str] = [".xls", ".xlsx"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/vnd.ms-excel",  # .xls
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    ]
    CHUNK_SIZE: int = 1024 * 1024  # 1MB chunks for large files
        
# 课表设置
class TimetableSettings:
    TIMEZONE: str = "Asia/Shanghai"
    SEMESTER_START: str
    DURATION: int = 45
    START_TIME: dict = {
        "1": "08:30",
        "2": "09:25",
        "3": "10:30",
        "4": "11:25",
        "5": "13:30",
        "6": "14:25",
        "7": "15:20",
        "8": "16:25",
        "9": "17:20",
        "10": "19:00",
        "11": "19:55",
        "12": "20:50",
        "13": "21:45",
    }