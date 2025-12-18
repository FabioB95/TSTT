def generate_piecewise_linearization(mu, H=10):
    """
    Con questo andaimo a creare una linearizzazione piecewise per la funzione TTI(x) = 1 + 0.15 * (x/mu)^4
    Restituisce:
    - b (lista di breakpoint sull'asse x)
    - TTI (valori della funzione TTI ai breakpoint)
    - slope (pendenze per ogni intervallo)
    """
    if mu <= 0:
        raise ValueError("μ deve essere > 0")

    b = [i * mu / H for i in range(H + 1)]
    TTI = [1 + 0.15 * (x / mu) ** 4 for x in b]
    slope = [
        (TTI[h] - TTI[h - 1]) / (b[h] - b[h - 1])
        if b[h] != b[h - 1] else 0.0
        for h in range(1, H + 1)
    ]
    return b, TTI, slope


import pyomo.environ as pyo

def apply_linearization(model, pi_at_cpτ, P_c, T_c):
    model.Y = pyo.Var(model.TC, domain=pyo.Binary)

    def link_y_x(m, c, tau):
        return m.Y[c, tau] >= sum(m.X[c, p, tau] for p in P_c[c])
    model.LinkY = pyo.Constraint(model.TC, rule=link_y_x)
