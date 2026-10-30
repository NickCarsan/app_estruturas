# src/controllers/ancoragem.py
import math

def calcular_fbd(fck: float, fyk: float = 500.0, tipo_barra: str = "nervurada", 
                 posicao_aderencia: str = "boa", phi_mm: float = 10.0) -> dict:
    """
    Calcula a resistência de aderência de cálculo (fbd) em MPa conforme ABNT NBR 6118.
    """
    gamma_c = 1.4
    
    if fck <= 50.0:
        fctm = 0.3 * (fck ** (2.0 / 3.0))
    else:
        fctm = 2.12 * math.log(1.0 + 0.11 * fck)
        
    fctk_inf = 0.7 * fctm
    fctd = fctk_inf / gamma_c

    if tipo_barra.lower() == "nervurada":
        eta1 = 2.25
    elif tipo_barra.lower() == "entalhada":
        eta1 = 1.40
    else:
        eta1 = 1.00

    eta2 = 1.00 if posicao_aderencia.lower() == "boa" else 0.70

    if phi_mm <= 32.0:
        eta3 = 1.00
    else:
        eta3 = max(0.0, (132.0 - phi_mm) / 100.0)

    fbd = eta1 * eta2 * eta3 * fctd

    return {
        "fctm": fctm,
        "fctk_inf": fctk_inf,
        "fctd": fctd,
        "eta1": eta1,
        "eta2": eta2,
        "eta3": eta3,
        "fbd": fbd
    }

def calcular_comprimento_ancoragem(phi_mm: float, fyd_mpa: float, fbd_mpa: float, 
                                  as_calc: float, as_ef: float, 
                                  com_gancho: bool = False, 
                                  comprimida: bool = False) -> dict:
    """
    Calcula o comprimento básico (lb) e o comprimento necessário (lb_nec) em cm.
    """
    phi_cm = phi_mm / 10.0
    lb_cm = (phi_cm / 4.0) * (fyd_mpa / fbd_mpa)

    if comprimida or not com_gancho:
        alpha = 1.0
    else:
        alpha = 0.7

    razao_as = min(1.0, as_calc / as_ef) if as_ef > 0 else 1.0
    lb_min_cm = max(0.3 * lb_cm, 10.0 * phi_cm, 10.0)
    lb_nec_cm = max(alpha * lb_cm * razao_as, lb_min_cm)

    return {
        "lb_cm": lb_cm,
        "lb_min_cm": lb_min_cm,
        "lb_nec_cm": lb_nec_cm,
        "alpha": alpha,
        "razao_as": razao_as
    }