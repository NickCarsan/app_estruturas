# src/controllers/detalhamento.py
import math
from typing import List, Dict

# Diâmetros comerciais de barras CA-50 em mm e respectivas áreas individuais (cm²)
TABELA_BARRAS = {
    6.3: (math.pi * (0.63 ** 2)) / 4.0,
    8.0: (math.pi * (0.80 ** 2)) / 4.0,
    10.0: (math.pi * (1.00 ** 2)) / 4.0,
    12.5: (math.pi * (1.25 ** 2)) / 4.0,
    16.0: (math.pi * (1.60 ** 2)) / 4.0,
    20.0: (math.pi * (2.00 ** 2)) / 4.0,
    25.0: (math.pi * (2.50 ** 2)) / 4.0,
    32.0: (math.pi * (3.20 ** 2)) / 4.0,
}

AGREGADOS = {
    "Brita 0 (dmáx = 9,5 mm)": 9.5,
    "Brita 1 (dmáx = 19,0 mm)": 19.0,
    "Brita 2 (dmáx = 25,0 mm)": 25.0,
    "Brita 3 (dmáx = 38,0 mm)": 38.0,
}

def detalhar_arranjo(as_necessario: float, bw_cm: float, h_cm: float, cnom_mm: float, 
                     phi_t_mm: float, d_max_agregado_mm: float = 19.0) -> List[Dict]:
    """
    Calcula detalhamento com arredondamento para cima, distribuição em camadas
    e determinação analítica do d_real (baricentro).
    """
    if as_necessario <= 0:
        return []

    cnom_cm = cnom_mm / 10.0
    phi_t_cm = phi_t_mm / 10.0
    d_max_cm = d_max_agregado_mm / 10.0

    resultados = []

    for phi_mm, as_unit in TABELA_BARRAS.items():
        phi_cm = phi_mm / 10.0
        
        # 1. Regra de arredondamento estrito para cima (mínimo de 2 barras de canto)
        n_barras = max(2, math.ceil(as_necessario / as_unit))
        as_efetivo = n_barras * as_unit

        # 2. Espaçamentos livres mínimos (NBR 6118)
        s_h_cm = max(2.0, phi_cm, 1.2 * d_max_cm)
        s_v_cm = max(2.0, phi_cm, 0.5 * d_max_cm)

        # 3. Capacidade por camada
        largura_util = bw_cm - 2.0 * cnom_cm - 2.0 * phi_t_cm
        if largura_util < phi_cm:
            continue
            
        n_max_camada = max(1, int((largura_util + s_h_cm) // (phi_cm + s_h_cm)))

        # 4. Distribuição das barras pelas camadas (de baixo para cima)
        camadas = []
        barras_restantes = n_barras
        while barras_restantes > 0:
            alocadas = min(barras_restantes, n_max_camada)
            camadas.append(alocadas)
            barras_restantes -= alocadas

        num_camadas = len(camadas)

        # 5. Cálculo do Baricentro das barras (y_cg a partir da face externa)
        # y1 = cnom + phi_t + phi/2
        soma_momentos_estaticos = 0.0
        y_atual = cnom_cm + phi_t_cm + (phi_cm / 2.0)

        for qtd in camadas:
            soma_momentos_estaticos += qtd * y_atual
            y_atual += phi_cm + s_v_cm  # sobe o diâmetro da barra + o espaçador vertical

        y_cg = soma_momentos_estaticos / n_barras
        d_real = h_cm - y_cg
        d_linha_real = y_cg

        # Espaçamento horizontal real na primeira camada
        if camadas[0] > 1:
            espaco_livre_h = (largura_util - (camadas[0] * phi_cm)) / (camadas[0] - 1)
        else:
            espaco_livre_h = largura_util - phi_cm

        resultados.append({
            "phi_mm": phi_mm,
            "n_barras": n_barras,
            "as_efetivo": as_efetivo,
            "sobra_percentual": ((as_efetivo - as_necessario) / as_necessario) * 100.0,
            "num_camadas": num_camadas,
            "distribuicao_camadas": " + ".join([f"{qtd}Φ" for qtd in camadas]),
            "espacamento_h_real_cm": espaco_livre_h,
            "y_cg_cm": y_cg,
            "d_real_cm": d_real,
            "d_linha_real_cm": d_linha_real
        })

    return resultados