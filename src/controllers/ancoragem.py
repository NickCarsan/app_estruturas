# src/controllers/ancoragem.py
import math
from typing import Dict, Any

def calcular_fbd(
    fck: float, 
    tipo_barra: str = "nervurada", 
    posicao_aderencia: str = "boa", 
    phi_mm: float = 10.0
) -> Dict[str, float]:
    """
    Calcula a tensão de aderência de cálculo (fbd) segundo a ABNT NBR 6118.
    """
    gamma_c = 1.4
    
    # 1. Resistência à tração do concreto (fctd)
    if fck <= 50.0:
        fctm = 0.3 * (fck ** (2.0 / 3.0))
    else:
        fctm = 2.12 * math.log(1.0 + 0.11 * fck)
        
    fctk_inf = 0.7 * fctm
    fctd = fctk_inf / gamma_c

    # 2. Coeficiente eta 1 (conformação superficial)
    if tipo_barra.lower() == "nervurada":
        eta1 = 2.25  # CA-50
    elif tipo_barra.lower() == "entalhada":
        eta1 = 1.40
    else:
        eta1 = 1.00  # CA-25 ou lisa

    # 3. Coeficiente eta 2 (posição de concretagem)
    eta2 = 1.00 if posicao_aderencia.lower() == "boa" else 0.70

    # 4. Coeficiente eta 3 (efeito escala do diâmetro)
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

def calcular_comprimento_ancoragem(
    phi_mm: float, 
    fyd_mpa: float, 
    fbd_mpa: float, 
    as_calc: float, 
    as_ef: float, 
    com_gancho: bool = False, 
    comprimida: bool = False
) -> Dict[str, Any]:
    """
    Calcula o comprimento básico (lb) e o comprimento necessário (lb_nec) em cm.
    Aplica as restrições da NBR 6118 para barras com phi > 32 mm.
    """
    phi_cm = phi_mm / 10.0

    # Comprimento básico reto: lb = (phi / 4) * (fyd / fbd)
    lb_cm = (phi_cm / 4.0) * (fyd_mpa / fbd_mpa)

    # Restrição: phi > 32 mm não deve usar ganchos (NBR 6118)
    aviso_gancho = None
    if phi_mm > 32.0 and com_gancho:
        com_gancho = False
        aviso_gancho = "NBR 6118: Barras com φ > 32 mm devem ter ancoragem exclusivamente reta."

    # Coeficiente alfa (gancho)
    if comprimida or not com_gancho:
        alpha = 1.0
    else:
        alpha = 0.7

    # Relação de áreas (As_calc / As_ef <= 1.0)
    razao_as = min(1.0, as_calc / as_ef) if as_ef > 0 else 1.0

    # Comprimento mínimo normativo
    lb_min_cm = max(0.3 * lb_cm, 10.0 * phi_cm, 10.0)

    # Comprimento de ancoragem necessário
    lb_nec_cm = max(alpha * lb_cm * razao_as, lb_min_cm)

    return {
        "lb_cm": lb_cm,
        "lb_min_cm": lb_min_cm,
        "lb_nec_cm": lb_nec_cm,
        "alpha": alpha,
        "razao_as": razao_as,
        "aviso_gancho": aviso_gancho
    }

def calcular_vao_efetivo(
    l0_m: float, 
    t1_cm: float, 
    t2_cm: float, 
    h_cm: float
) -> Dict[str, float]:
    """
    Calcula o vão teórico efetivo (l_ef) conforme o item 14.6.2.4 da ABNT NBR 6118.
    l_ef = l0 + a1 + a2, onde a = min(0.5*t, 0.3*h)
    """
    l0_cm = l0_m * 100.0
    a1_cm = min(0.5 * t1_cm, 0.3 * h_cm)
    a2_cm = min(0.5 * t2_cm, 0.3 * h_cm)
    
    lef_cm = l0_cm + a1_cm + a2_cm
    lef_m = lef_cm / 100.0
    l_total_m = (l0_cm + t1_cm + t2_cm) / 100.0

    return {
        "l0_m": l0_m,
        "lef_m": lef_m,
        "l_total_m": l_total_m,
        "a1_cm": a1_cm,
        "a2_cm": a2_cm,
        "t1_cm": t1_cm,
        "t2_cm": t2_cm
    }

def ancoragem_apoio_extremo(
    vd_kn: float, 
    d_cm: float, 
    al_cm: float = None, 
    nd_kn: float = 0.0, 
    fyd_mpa: float = 434.78
) -> Dict[str, float]:
    """
    Calcula a armadura necessária a ancorar no apoio extremo pela biela de compressão:
    Rs = (al / d) * Vd + Nd (NBR 6118, item 18.3.2.4).
    """
    if al_cm is None:
        al_cm = d_cm

    rs_kn = (al_cm / d_cm) * abs(vd_kn) + nd_kn
    fyd_kn_cm2 = fyd_mpa / 10.0
    as_apoio_nec = rs_kn / fyd_kn_cm2

    return {
        "rs_kn": rs_kn,
        "al_cm": al_cm,
        "as_apoio_nec_cm2": as_apoio_nec
    }
