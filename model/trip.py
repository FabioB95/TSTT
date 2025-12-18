class Trip:
    def __init__(self, ID, origin, destination, departure_times, demand):
        self.ID = ID
        self.origin = origin
        self.destination = destination
        self.departure_times = departure_times
        self.demand = demand  
        self.FP = 0.0
        self.X = []  # M x N matrix: X[time][arc]
        self.paths = []
        self.schedule = []
        self.FP = None

    def to_dict(self):
        return {
            "ID": self.ID,
            "origin": self.origin,
            "destination": self.destination,
            "departure_times": self.departure_times,
            "demand": self.demand,
            "FP": self.FP,
            "X": self.X,
            "paths": [p.to_dict() for p in self.paths],
            "schedule": self.schedule
        }

    def evaluate_all_travel_times(self):
        self.X = []
        for path in self.paths:
            row = []
            for t in self.departure_times:
                path.value_real_times(t)
                travel_time = path.real_times[-1] - t
                row.append(travel_time)
            self.X.append(row)

    def evaluate_fastest_path(self):
        min_time = float("inf")
        for row in self.X:
            min_row = min(row)
            if min_row < min_time:
                min_time = min_row
        self.FP = min_time
    def __repr__(self):
        return f"Trip(ID={self.ID}, origin={self.origin}, dest={self.destination}, times={self.departure_times}, demand={self.demand})"
