# src/controllers/flexao.py
import math

def calcular_flexao(mk: float, fcd: float, fyd: float, b: float, d: float, d_linha: float, fck: float) -> dict:
    """
    Calcula a flexão para vigas retangulares (Simples ou Dupla).
    """
    if mk <= 0:
        return {"status": "Momento nulo", "as_total_cm2": 0.0, "md_knm": 0.0, "beta_x": 0.0, "tipo_armadura": "Simples"}

    gamma_f = 1.4
    md = (mk * gamma_f) * 100.0  # kN.cm

    fcd_kncm2 = fcd / 10.0
    fyd_kncm2 = fyd / 10.0

    if fck <= 50:
        lamb = 0.8
        alpha_c = 0.85
        beta_x_lim = 0.45
        epsilon_cu = 3.5 / 1000.0
    else:
        delta_fck = fck - 50.0
        lamb = 0.8 - (delta_fck / 400.0)
        alpha_c = 0.85 * (1.0 - (delta_fck / 200.0))
        beta_x_lim = 0.35
        epsilon_cu = (2.6 + 35.0 * ((90.0 - fck) / 100.0) ** 4) / 1000.0

    k_eq = (2.0 * md) / (alpha_c * fcd_kncm2 * b)
    delta = (4.0 * (d ** 2)) - (4.0 * k_eq)

    if delta < 0:
        # Se ultrapassar a armadura simples máxima, dimensiona como Dupla
        pass
    else:
        y = (2.0 * d - math.sqrt(delta)) / 2.0
        beta_x = y / (lamb * d)

        if beta_x <= beta_x_lim:
            as_cm2 = md / (fyd_kncm2 * (d - 0.5 * y))
            return {
                "status": "Dimensionado com Armadura Simples.",
                "tipo_armadura": "Simples",
                "y_cm": y,
                "beta_x": beta_x,
                "md_knm": md / 100.0,
                "as_total_cm2": as_cm2,
                "as_linha_cm2": 0.0
            }

    # --- ARMADURA DUPLA ---
    y_lim = beta_x_lim * lamb * d
    md_lim = alpha_c * fcd_kncm2 * b * y_lim * (d - 0.5 * y_lim)
    delta_md = md - md_lim

    x_lim = beta_x_lim * d
    epsilon_s_linha = epsilon_cu * ((x_lim - d_linha) / x_lim)

    es_kncm2 = 21000.0
    sigma_s_linha = epsilon_s_linha * es_kncm2

    if sigma_s_linha > fyd_kncm2:
        sigma_s_linha = fyd_kncm2
    elif sigma_s_linha < 0:
        sigma_s_linha = fyd_kncm2

    as1 = md_lim / (fyd_kncm2 * (d - 0.5 * y_lim))
    as_linha = delta_md / (sigma_s_linha * (d - d_linha))
    as_delta_tracao = delta_md / (fyd_kncm2 * (d - d_linha))
    as_total = as1 + as_delta_tracao

    return {
        "status": "Armadura Dupla Necessária.",
        "tipo_armadura": "Dupla",
        "y_cm": y_lim,
        "beta_x": beta_x_lim,
        "md_knm": md / 100.0,
        "as_total_cm2": as_total,
        "as_linha_cm2": as_linha,
        "sigma_s_linha": sigma_s_linha * 10.0  # MPa
    }

def calcular_momento_limite_armadura_simples(fcd: float, fyd: float, b: float, d: float, fck: float) -> dict:
    fcd_kncm2 = fcd / 10.0
    fyd_kncm2 = fyd / 10.0

    if fck <= 50:
        lamb = 0.8
        alpha_c = 0.85
        beta_x_lim = 0.45
    else:
        delta_fck = fck - 50.0
        lamb = 0.8 - (delta_fck / 400.0)
        alpha_c = 0.85 * (1.0 - (delta_fck / 200.0))
        beta_x_lim = 0.35

    y_lim = beta_x_lim * lamb * d
    md_lim = alpha_c * fcd_kncm2 * b * y_lim * (d - 0.5 * y_lim)
    z_cm = d - 0.5 * y_lim
    as_cm2 = md_lim / (fyd_kncm2 * z_cm)

    return {
        "md_limite_knm": md_lim / 100.0,
        "beta_x": beta_x_lim,
        "z_cm": z_cm,
        "as_cm2": as_cm2,
        "md_knm": md_lim / 100.0
    }

def calcular_viga_t(mk: float, fcd: float, fyd: float, bw: float, bf: float, hf: float, d: float, fck: float) -> dict:
    """
    Calcula a armadura para Seção T, identificando automaticamente se atua como T Falso ou T Verdadeiro.
    """
    if mk <= 0:
        return {"status": "Momento nulo", "as_total_cm2": 0.0, "md_knm": 0.0, "beta_x": 0.0, "tipo_armadura": "Simples"}

    gamma_f = 1.4
    md = (mk * gamma_f) * 100.0  # kN.cm

    fcd_kncm2 = fcd / 10.0
    fyd_kncm2 = fyd / 10.0

    if fck <= 50:
        lamb = 0.8
        alpha_c = 0.85
        beta_x_lim = 0.45
    else:
        delta_fck = fck - 50.0
        lamb = 0.8 - (delta_fck / 400.0)
        alpha_c = 0.85 * (1.0 - (delta_fck / 200.0))
        beta_x_lim = 0.35

    # 1. Pressupor seção retangular de largura bf (Verificação de T Falso)[cite: 28]
    k_eq = (2.0 * md) / (alpha_c * fcd_kncm2 * bf)
    delta = (4.0 * (d ** 2)) - (4.0 * k_eq)
    
    if delta < 0:
        return {
            "status": "Erro: Concreto esmagado na mesa.", 
            "as_total_cm2": 0.0, 
            "tipo_armadura": "Inválida", 
            "md_knm": md / 100.0, 
            "beta_x": 0.0,
            "tipo_secao": "Inválida"
        }

    y_falso = (2.0 * d - math.sqrt(delta)) / 2.0
    
    # 2. Verificação do Comportamento (y <= hf -> T Falso | y > hf -> T Verdadeiro)[cite: 28]
    if y_falso <= hf:
        # --- COMPORTAMENTO T FALSO ---
        beta_x = y_falso / (lamb * d)
        if beta_x <= beta_x_lim:
            as_cm2 = md / (fyd_kncm2 * (d - 0.5 * y_falso))
            return {
                "tipo_secao": "Viga T Falsa (Mesa absorve compressão)[cite: 28]",
                "status": "Armadura Simples",
                "tipo_armadura": "Simples",
                "y_cm": y_falso,
                "beta_x": beta_x,
                "md_knm": md / 100.0,
                "as_total_cm2": as_cm2,
                "as_linha_cm2": 0.0,
                "forma_secao": "t_falso"
            }
        else:
            return {
                "tipo_secao": "Viga T Falsa",
                "status": "Armadura dupla necessária (T Falso).", 
                "as_total_cm2": 0.0, 
                "tipo_armadura": "Dupla", 
                "forma_secao": "t_falso", 
                "md_knm": md / 100.0, 
                "beta_x": beta_x
            }
    else:
        # --- COMPORTAMENTO T VERDADEIRO ---
        # Parte 1: Momento resistente das abas da mesa (bf - bw)[cite: 28]
        cf_mesa = alpha_c * fcd_kncm2 * (bf - bw) * hf
        m0_mesa = cf_mesa * (d - 0.5 * hf)
        as_mesa = m0_mesa / (fyd_kncm2 * (d - 0.5 * hf))
        
        # Parte 2: Momento residual para a nervura (bw)[cite: 28]
        delta_md = md - m0_mesa
        if delta_md <= 0:
            delta_md = 0
             
        k_eq_nerv = (2.0 * delta_md) / (alpha_c * fcd_kncm2 * bw)
        delta_nerv = (4.0 * (d ** 2)) - (4.0 * k_eq_nerv)
        
        if delta_nerv < 0:
             return {
                 "tipo_secao": "Viga T Verdadeira",
                 "status": "Erro: Nervura esmagada.", 
                 "as_total_cm2": 0.0, 
                 "tipo_armadura": "Inválida", 
                 "forma_secao": "t_verdadeiro", 
                 "md_knm": md / 100.0, 
                 "beta_x": 0.0
             }
             
        y_nerv = (2.0 * d - math.sqrt(delta_nerv)) / 2.0
        beta_x_nerv = y_nerv / (lamb * d)
        
        if beta_x_nerv <= beta_x_lim:
            as_nerv = delta_md / (fyd_kncm2 * (d - 0.5 * y_nerv))
            as_total = as_mesa + as_nerv
            return {
                "tipo_secao": "Viga T Verdadeira (Compressão desce à nervura)[cite: 28]",
                "status": "Armadura Simples (Mesa + Nervura)[cite: 28]",
                "tipo_armadura": "Simples",
                "y_cm": y_nerv,
                "beta_x": beta_x_nerv,
                "md_knm": md / 100.0,
                "m0_mesa_knm": m0_mesa / 100.0,
                "delta_md_knm": delta_md / 100.0,
                "as_total_cm2": as_total,
                "as_linha_cm2": 0.0,
                "forma_secao": "t_verdadeiro"
            }
        else:
            return {
                "tipo_secao": "Viga T Verdadeira",
                "status": "Armadura dupla necessária na nervura do T Verdadeiro.", 
                "as_total_cm2": 0.0, 
                "tipo_armadura": "Dupla", 
                "forma_secao": "t_verdadeiro", 
                "md_knm": md / 100.0, 
                "beta_x": beta_x_nerv
            }