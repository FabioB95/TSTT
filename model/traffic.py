class Traffic:
    def __init__(self, start, end):
        self.start = str(start)
        self.end = str(end)
        self.values = {}  # {time: tti}

    def add_entry(self, time, tti):
        self.values[int(time)] = float(tti)

    def get_tti(self, time):
        return self.values.get(int(time), None)

    def __repr__(self):
        preview = dict(list(self.values.items())[:3])
        return f"Traffic({self.start},{self.end}) -> {preview}..."
