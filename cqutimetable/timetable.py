import pandas as pd
import re
import warnings
import shutil
import os

from config import TimetableSettings
from cqutimetable.course import Course
from datetime import datetime, timedelta
from icalendar import Calendar
from urllib.parse import quote


def str_to_date(string: str) -> datetime:
    lst = [int(i) if i.isdigit() else -1 for i in re.split(r"[-./ ]", string)]
    if len(lst) != 2 and len(lst) != 3:
        return None
    try:
        date = (
            datetime(lst[0], lst[1], lst[2])
            if len(lst) == 3
            else datetime(int(datetime.now().year), lst[0], lst[1])
        )
    except:
        return None
    return date


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
        timetable_file = path
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            df = pd.read_excel(timetable_file, engine="openpyxl")
            headers = df.columns.tolist()
            first_row = df.iloc[0].tolist()
            if "课表" not in headers or first_row != [
                "课程名称",
                "教学班号",
                "上课时间",
                "上课地点",
                "上课教师",
            ]:
                raise ValueError("课表格式错误！")
        rows_as_lists = []
        for _, row in df.iterrows():
            row_list = list(row)
            rows_as_lists.append(row_list)
        for row in rows_as_lists:
            if row[0] == "课程名称":
                continue
            if len(row) != 5:
                continue
            lst = [str(item) if isinstance(item, str) else "" for item in row]
            this_course = Course(self.config, lst[0], lst[1], lst[2], lst[3], lst[4])
            this_course.create_event_in_ical(self.cal, self.semester_start)
            self.courses += [this_course]

    def course_in_week(self, week: int) -> list[Course]:
        return [c for c in self.courses if week in c.week_range]

    def course_in_day(self, week: int, day: int) -> list[Course]:
        return [c for c in self.course_in_week(week) if c.weekday == day]

    def find_one_day(self, string: str) -> list[Course]:
        date = str_to_date(string)
        if date is None:
            return None
        if date > self.semester_end or date < self.semester_start:
            return None
        this_week = (date - self.semester_start).days // 7 + 1
        this_weekday = date.weekday()
        course_list = self.course_in_day(this_week, this_weekday)
        course_list.sort(key=lambda x: x.start)
        return course_list

    def today(self) -> None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.find_one_day(date_str)

    def next_class(self, date: datetime = datetime.now()) -> None:
        current_date = datetime.now()
        delta = current_date - self.semester_start
        current_week = delta.days // 7 + 1
        current_weekday = current_date.weekday()
        today_class = self.course_in_day(current_week, current_weekday)
        today_class.sort(key=lambda x: x.start)
        is_today = False
        class_day = datetime.now()
        next_class = None
        next_class_delta = 0
        for i in range(len(today_class)):
            tmp = today_class[i].start.replace(
                year=date.year, month=date.month, day=date.day
            )
            if tmp > date:
                next_class = today_class[i]
                is_today = True
                break
        if not is_today:

            def date_range(start_date, end_date):
                current_date = start_date
                while current_date <= end_date:
                    yield current_date
                    current_date += timedelta(days=1)

            for date in date_range(date + timedelta(days=1), self.semester_end):
                next_class_delta += 1
                course_list = self.find_one_day(
                    date.strftime("%Y-%m-%d"), display=False
                )
                class_day = date
                if course_list:
                    break

            next_class = course_list[0]
        return next_class if next_class else None

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

    def get_semester_start_in_config(self) -> str:
        return self.config.SEMESTER_START

    def get_semester_name(self) -> str:
        assert self.semester_start.month > 0 and self.semester_start.month <= 12
        semester = "春" if self.semester_start.month <= 6 else "秋"
        return f"{self.semester_start.year}年{semester}季学期"
