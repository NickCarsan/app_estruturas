# src/models/elementos.py

class VigaRetangular:
    def __init__(self, bw: float, h: float, cnom_mm: float, phi_t_mm: float, phi_l_mm: float):
        self.bw = bw  # Largura (cm)
        self.h = h    # Altura total (cm)
        
        # Cálculo automático da altura útil (d) em centímetros
        # d = h - (cobrimento + estribo + raio da barra longitudinal) convertidos para cm
        cobrimento_cm = cnom_mm / 10.0
        phi_t_cm = phi_t_mm / 10.0
        phi_l_cm = (phi_l_mm / 10.0) / 2.0
        
        self.d = self.h - (cobrimento_cm + phi_t_cm + phi_l_cm)

class VigaT:
    def __init__(self, bw: float, h: float, bf: float, hf: float, cnom_mm: float, phi_t_mm: float, phi_l_mm: float):
        self.bw = bw
        self.h = h
        self.bf = bf
        self.hf = hf
        
        # O cálculo do d estimado é o mesmo da retangular, partindo da base da nervura
        cnom_cm = cnom_mm / 10.0
        phi_t_cm = phi_t_mm / 10.0
        phi_l_cm = phi_l_mm / 10.0
        
        self.d = self.h - (cnom_cm + phi_t_cm + (phi_l_cm / 2.0))