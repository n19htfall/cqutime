import pandas as pd
import warnings
import shutil
import os

from config import TimetableSettings
from cqutimetable.course import Course
from datetime import datetime, timedelta
from icalendar import Calendar
from urllib.parse import quote
from typing import List
from zipfile import BadZipFile

EXPECTED_COLUMNS = [
    "课程名称",
    "教学班号",
    "上课时间",
    "上课地点",
    "上课教师",
]


def validate_format(df: pd.DataFrame) -> None:
    if (
        df.empty
        or "课表" not in df.columns.tolist()
        or df.iloc[0].tolist() != EXPECTED_COLUMNS
    ):
        raise ValueError("课表格式错误！")


def process_course_row(row, config) -> Course:
    row_lst = row.tolist()
    if len(row_lst) != 5:
        return None
    if row_lst[0] == "课程名称":
        return None
    return Course(
        _config=config,
        _name=row_lst[0],
        _number=row_lst[1],
        _time=row_lst[2],
        _place=row_lst[3],
        _teacher=row_lst[4],
    )


class Timetable:
    def __init__(self, path: str, name: str, semester_start_str: str):
        self.courses: list[Course] = []
        self.cal = Calendar()
        self.timetable_name = name
        self.config = TimetableSettings()
        if (
            semester_start_str is not None
            and datetime.strptime(semester_start_str, "%Y-%m-%d").weekday() == 0
        ):
            self.config.SEMESTER_START = semester_start_str
        self.semester_start = datetime.strptime(self.config.SEMESTER_START, "%Y-%m-%d")
        self.semester_end = self.semester_start + timedelta(weeks=20, days=-1)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            try:
                df = pd.read_excel(path, engine="openpyxl", dtype=str)
            except BadZipFile:
                raise ValueError("不是Zip文件，格式错误！")
        validate_format(df)
        courses: List[Course] = (
            df.apply(
                lambda row: process_course_row(row, self.config),
                axis=1,
            )
            .dropna()
            .tolist()
        )
        for course in courses:
            course.create_event_in_ical(self.cal, self.semester_start)
        self.courses = courses

    def export_ics(self):
        with open(self.timetable_name + ".ics", "wb") as f:
            f.write(self.cal.to_ical())
        shutil.copy(self.timetable_name + ".ics", self.timetable_name + "_p.txt")
        with open(self.timetable_name + "_p.txt", "r", encoding="utf-8") as f:
            content = f.read()
        encoded_content = quote(content)
        with open(self.timetable_name + ".txt", "w", encoding="utf-8") as f:
            f.write("data:text/calendar," + encoded_content)
        try:
            os.remove(self.timetable_name + "_p.txt")
        except OSError as e:
            print(f"删除文件时出错: {e}")
