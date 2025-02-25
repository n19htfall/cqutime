from config import TimetableSettings
from datetime import datetime, timedelta


class Course:
    def __init__(
        self,
        _config: TimetableSettings,
        _name: str,
        _number: str,
        _time: str,
        _place: str = "",
        _teacher: str = "",
    ) -> None:
        self.config = _config
        self.name = _name
        self.number = _number
        self.place = _place
        self.teacher = _teacher
        self.week_range: list[int] = []
        self.weekday: int = -1
        self.class_range: list[int] = []
        self.is_all_week = False
        self.build_time(_time)

    @staticmethod
    def parse_range_string(s: str) -> list[int]:
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
        """
        zhou_index = description.find("周")
        qi_index = description.find("期")
        if zhou_index == -1:
            return
        week_range_str = description[:zhou_index]
        self.week_range = self.parse_range_string(week_range_str)
        if qi_index == -1:
            self.is_all_week = True
        else:
            self.weekday = {
                "一": 0,
                "二": 1,
                "三": 2,
                "四": 3,
                "五": 4,
                "六": 5,
                "日": 6,
            }.get(description[qi_index + 1], None)
            class_range_str = description[qi_index + 2 : -1]
            self.class_range = self.parse_range_string(class_range_str)
        if not self.is_all_week:
            start_class = self.class_range[0]
            end_class = self.class_range[-1]
            self.start = datetime.strptime(
                self.config.START_TIME[str(start_class)], "%H:%M"
            )
            self.end = datetime.strptime(
                self.config.START_TIME[str(end_class)], "%H:%M"
            ) + timedelta(minutes=self.config.DURATION)
