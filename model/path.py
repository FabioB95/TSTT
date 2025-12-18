class Path:
    def __init__(self, ID, arcs):
        self.ID = ID
        self.arcs = arcs
        self.base_times = []
        self.real_times = []

    def total_time(self):
        if self.real_times:
            return self.real_times[-1] - self.real_times[0]
        return float('inf')

    def to_dict(self):
        return {
            "ID": self.ID,
            "arcs": self.arcs,
            "base_times": self.base_times,
            "real_times": self.real_times
        }
    

    @staticmethod
    def from_dict(d):
        path = Path(d["ID"], d["arcs"])
        path.base_times = d.get("base_times", [])
        path.real_times = d.get("real_times", [])
        return path




    def value_real_times(self, start_time):
        self.real_times = [start_time]
        for i in range(1, len(self.base_times)):
                next_time = self.real_times[-1] + self.base_times[i - 1]
                self.real_times.append(next_time)


    def evaluate_pi(self, arc_id, time):
        for i in range(len(self.arcs)):
            if self.real_times[i] <= time < self.real_times[i + 1]:
                return 1 if self.arcs[i] == arc_id else 0
        return 0
    def __repr__(self):
        return f"Path(ID={self.ID}, arcs={self.arcs}, base_times={self.base_times})"
