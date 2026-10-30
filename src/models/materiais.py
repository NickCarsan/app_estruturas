# src/models/materiais.py
from src.config import GAMA_C, GAMA_S

class Concreto:
    def __init__(self, fck: float):
        self.fck = fck  # MPa
        self.fcd = fck / GAMA_C  # MPa
        # Resistência à tração média (fct,m) e inferior (fctk,inf) para fck <= 50 MPa
        self.fctm = 0.3 * (fck ** (2/3))
        self.fctk_inf = 0.7 * self.fctm

class Aco:
    def __init__(self, fyk: float = 500):
        self.fyk = fyk  # MPa (500 para CA-50, 600 para CA-60)
        self.fyd = fyk / GAMA_S  # MPa