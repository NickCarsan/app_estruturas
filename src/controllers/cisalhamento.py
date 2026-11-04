# src/controllers/cisalhamento.py
import math
from typing import Dict, Any

def calcular_cisalhamento(
    vk_kn: float, 
    fck_mpa: float, 
    bw_cm: float, 
    d_cm: float, 
    fyk_mpa: float = 500.0
) -> Dict[str, Any]:
    """
    Dimensiona a armadura transversal (estribos) para força cortante 
    segundo o Modelo de Cálculo I da NBR 6118 (bielas a 45°).
    """
    if vk_kn <= 0:
        return {"status": "Cortante nulo", "asw_s_cm2_m": 0.0, "vsd_kn": 0.0}

    # Coeficientes de minoração/majoração
    gamma_c = 1.4
    gamma_s = 1.15
    gamma_f = 1.4

    # Esforço cortante de cálculo
    vsd = vk_kn * gamma_f  # kN

    # Propriedades dos materiais
    fcd = (fck_mpa / gamma_c) / 10.0  # kN/cm²
    fywd = (fyk_mpa / gamma_s) / 10.0 # kN/cm²

    # Resistência à tração do concreto
    if fck_mpa <= 50.0:
        fctm = 0.3 * (fck_mpa ** (2.0 / 3.0))
    else:
        fctm = 2.12 * math.log(1.0 + 0.11 * fck_mpa)
        
    fctk_inf = 0.7 * fctm
    fctd = (fctk_inf / gamma_c) / 10.0  # kN/cm²

    # 1. Verificação da Ruína por Compressão Diagonal do Concreto (VRd2)
    # alpha_v2 = (1 - fck/250)
    alpha_v2 = 1.0 - (fck_mpa / 250.0)
    
    # VRd2 = 0.27 * alpha_v2 * fcd * bw * d (Modelo I)
    vrd2 = 0.27 * alpha_v2 * fcd * bw_cm * d_cm

    if vsd > vrd2:
        return {
            "status": "ERRO: Esmagamento da biela de compressão. Aumente a seção (bw ou h) ou o fck.",
            "vsd_kn": vsd,
            "vrd2_kn": vrd2,
            "asw_s_cm2_m": 0.0
        }

    # 2. Cálculo da Parcela Resistida pelo Concreto (Vc)
    # Vc0 = 0.6 * fctd * bw * d (Para flexão simples)
    vc = 0.6 * fctd * bw_cm * d_cm

    # 3. Cálculo da Armadura Transversal Necessária (Vsw)
    vsw = max(0.0, vsd - vc)

    # Asw/s = Vsw / (0.9 * d * fywd) -> Resultado em cm²/cm
    asw_s_cm2_cm = vsw / (0.9 * d_cm * fywd)
    
    # Convertendo para cm²/m
    asw_s_cm2_m = asw_s_cm2_cm * 100.0

    # 4. Armadura Mínima de Cisalhamento
    # rho_w_min = 0.2 * (fctm / fyk)
    rho_w_min = 0.2 * (fctm / fyk_mpa)
    asw_s_min_cm2_m = rho_w_min * bw_cm * 100.0

    asw_s_final = max(asw_s_cm2_m, asw_s_min_cm2_m)

    status = "Armadura mínima adotada." if asw_s_min_cm2_m >= asw_s_cm2_m else "Armadura calculada adotada."

    return {
        "status": status,
        "vsd_kn": vsd,
        "vrd2_kn": vrd2,
        "vc_kn": vc,
        "vsw_kn": vsw,
        "asw_s_calc_cm2_m": asw_s_cm2_m,
        "asw_s_min_cm2_m": asw_s_min_cm2_m,
        "asw_s_final_cm2_m": asw_s_final
    }