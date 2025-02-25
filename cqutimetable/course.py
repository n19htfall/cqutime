import re

from config import TimetableSettings
from datetime import datetime, timedelta
from typing import List, Optional

WEEKDAY_MAP = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "日": 6,
}


class Course:
    def __init__(
        self,
        config: TimetableSettings,
        name: str,
        number: str,
        time: str,
        place: str = "",
        teacher: str = "",
    ) -> None:
        self.config = config
        self.name = name
        self.number = number
        self.place = place
        self.teacher = teacher
        self.is_all_week = False
        self.week_range: List[int] = []
        self.weekday: Optional[int] = None
        self.class_range: Optional[List[int]] = None
        self.start: Optional[datetime] = None
        self.end: Optional[datetime] = None
        self.build_time(time)

    @staticmethod
    def parse_range_string(s: str) -> List[int]:
        """
        获取一个字符串中的数字，使之成为一个列表，同时解析“-”两边范围。

        例如：
        >>> self.parse_range_string(stirng='1,2-4,5')
        [1, 2, 3, 4, 5]
        """
        result = []
        for part in s.split(","):
            if "-" in part:
                start, end = map(int, part.split("-"))
                result.extend(range(start, end + 1))
            else:
                result.append(int(part))
        return result

    def build_time(self, description: str) -> None:
        """
        通过课程时间的描述获取上课的周数、星期几和第几节课。
        description like '1-5,8,9周星期一3-5节' or '14-17周'
        """
        full_pattern = r"([\d,-]+)周(?:星期([一二三四五六日]))?(\d+(?:-\d+)?)节?"
        week_only_pattern = r"([\d,-]+)周$"
        full_match = re.match(full_pattern, description)
        week_only_match = re.match(week_only_pattern, description)

        if full_match:
            week_range_str, weekday_str, class_range_str = full_match.groups()
        elif week_only_match:
            week_range_str = week_only_match.group(1)
            weekday_str = None
            class_range_str = None
            self.is_all_week = True
        else:
            raise ValueError(f"Invalid description format: {description}")

        # 解析周范围
        self.week_range = self.parse_range_string(week_range_str)

        # 如果不是全周课程，解析星期几和节次
        if not self.is_all_week:
            if weekday_str:
                self.weekday = WEEKDAY_MAP.get(weekday_str)
                if self.weekday is None:
                    raise ValueError(f"Invalid weekday: {weekday_str}")
            else:
                raise ValueError("Weekday is required for non-all-week courses")

            if class_range_str:
                self.class_range = self.parse_range_string(class_range_str)
                start_class = self.class_range[0]
                end_class = self.class_range[-1]
                self.start = datetime.strptime(
                    self.config.START_TIME[str(start_class)], "%H:%M"
                )
                self.end = datetime.strptime(
                    self.config.START_TIME[str(end_class)], "%H:%M"
                ) + timedelta(minutes=self.config.DURATION)
            else:
                raise ValueError("Class range is required for non-all-week courses")
