class Nodo:
    def __init__(self, ID, lat=0.0, lon=0.0, P=0.0, H=0.0, K=0.0, I=0.0):
        self.ID = ID
        self.lat = lat
        self.lon = lon
        self.P = P
        self.H = H
        self.K = K
        self.I = I

    def to_dict(self):
        return {
            "ID": self.ID,
            "lat": self.lat,
            "lon": self.lon,
            "P": self.P,
            "H": self.H,
            "K": self.K,
            "I": self.I
        }

    @staticmethod
    def from_dict(d):
        return Nodo(
            d["ID"],                 
            d["lat"],
            d["lon"],
            d["population"],         
            d.get("H_i", 0.0),         # valore di default se non esiste
            d["K_i"],                
            d.get("I_i", 0.0)          # valore di default se non esiste
    )


    def eval_origin_prob(self, total_P, total_K):
        return (self.P * self.K) / (total_P * total_K)

    def eval_dest_prob(self, total_I, total_H):
        return (self.I * self.H) / (total_I * total_H)

    def __repr__(self):
        return f"Nodo(ID={self.ID}, lat={self.lat}, lon={self.lon})"
