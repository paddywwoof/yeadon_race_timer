from datetime import datetime

class Race:
    time: datetime
    duration: int

    def __init__(self, time, duration):
        self.update_time_to_today(time[0], time[1], time[2])
        self.duration = duration

    def update_time_to_today(self, h=None, m=None, s=None):
        if s is None: # i.e. if any not there
            h = self.time.hour
            m = self.time.minute
            s = self.time.second
        self.time = datetime.now().replace(hour=h, minute=m, second=s)

    def __lt__(self, other):
        self.time < other.time

race_times = sorted([
                Race((13, 0, 0), 3000),
                Race((14,30, 0), 3000),
                Race((16, 0, 0), 3000),
                Race((19, 0, 0), 3000)
            ])