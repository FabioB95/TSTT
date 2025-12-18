class Arc:
    def __init__(self, ID, from_node, to_node, capacity, free_flow_time, distance):
        self.ID = ID
        self.from_node = from_node
        self.to_node = to_node
        self.capacity = capacity
        self.free_flow_time = free_flow_time
        self.distance = distance  
        self.Z = []      # forecast flows per t
        self.alpha = []  # acceptance threshold per t
        self.TTI = []    # matrix: h × t
        self.b = []      # matrix: h × t

    def to_dict(self):
        return {
            "ID": self.ID,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "capacity": self.capacity,
            "free_flow_time": self.free_flow_time,
            "distance": self.distance,  
            "Z": self.Z,
            "alpha": self.alpha,
            "TTI": self.TTI,
            "b": self.b
        }

    @staticmethod
    def from_dict(d):
        maxspeed = float(d["maxspeed"])
        distance = float(d["distance"])
        if maxspeed == 0:
            free_flow_time = 9999
        else:
            free_flow_time = distance / maxspeed * 60  # minuti

        return Arc(
            ID=f"{d['from_node']}_{d['to_node']}",
            from_node=d["from_node"],
            to_node=d["to_node"],
            capacity=int(d["capacity"]),
            free_flow_time=free_flow_time,
            distance=distance 
        )

    def get_Z_at(self, t):
        return self.Z[t]

    def get_alpha_at(self, t):
        return self.alpha[t]

    def evaluate_current_tt(self, t):
        return self.free_flow_time * (1 + 0.15 * (self.Z[t] / self.capacity) ** 4)

    def evaluate_experienced_tt(self, x_t):
        return self.free_flow_time * (1 + 0.15 * (x_t / self.capacity) ** 4)

    def __repr__(self):
        return f"Arc(ID={self.ID}, from={self.from_node}, to={self.to_node}, fft={self.free_flow_time})"
