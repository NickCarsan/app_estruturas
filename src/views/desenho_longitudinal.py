# src/views/desenho_longitudinal.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, Optional

def gerar_grafico_longitudinal(
    l0_m: float,
    h_cm: float,
    cnom_mm: float,
    t1_cm: float,
    t2_cm: float,
    detalhe_as: Dict,
    lb_nec_cm: float,
    tem_gancho: bool,
    al_cm: Optional[float] = None
):
    """
    Gera o desenho técnico da elevação longitudinal no padrão CAD Monocromático:
    - Fundo escuro (#081018), apenas linhas brancas.
    - Diferenciação estrita por espessura de linha (penas).
    - Pilares cortados abertos.
    - Centralização exata do desenho no canvas.
    """
    c_fundo = "#081018"
    c_linha = "#FFFFFF"

    fig, ax = plt.subplots(figsize=(14, 4.5), facecolor=c_fundo)
    ax.set_facecolor(c_fundo)

    l0_cm = l0_m * 100.0
    cnom = cnom_mm / 10.0
    phi_as_cm = detalhe_as["phi_mm"] / 10.0
    phi_pe_cm = 0.5

    x_pilar_esq_fim = t1_cm
    x_pilar_dir_ini = t1_cm + l0_cm
    x_total = t1_cm + l0_cm + t2_cm
    h_pilar = max(30.0, h_cm * 0.7)

    # ==========================================
    # 1. Contorno de Concreto (Pena Média: 1.0)
    # ==========================================
    # Pilares descendo abertos
    ax.plot([0, 0], [0, -h_pilar], color=c_linha, lw=1.0, zorder=1)
    ax.plot([t1_cm, t1_cm], [0, -h_pilar], color=c_linha, lw=1.0, zorder=1)
    ax.plot([x_pilar_dir_ini, x_pilar_dir_ini], [0, -h_pilar], color=c_linha, lw=1.0, zorder=1)
    ax.plot([x_total, x_total], [0, -h_pilar], color=c_linha, lw=1.0, zorder=1)

    # Viga de fora a fora
    ax.plot([0, x_total], [0, 0], color=c_linha, lw=1.0, zorder=2)       # Base (sobre pilares)
    ax.plot([0, x_total], [h_cm, h_cm], color=c_linha, lw=1.0, zorder=2) # Topo
    ax.plot([0, 0], [0, h_cm], color=c_linha, lw=1.0, zorder=2)          # Face esq
    ax.plot([x_total, x_total], [0, h_cm], color=c_linha, lw=1.0, zorder=2)# Face dir

    # ==========================================
    # 2. Armaduras (Pena Grossa: 2.5)
    # ==========================================
    # Armadura Superior Constutritiva
    y_sup = h_cm - cnom - (phi_pe_cm / 2.0)
    x_sup_ini = cnom
    x_sup_fim = x_total - cnom
    ax.plot([x_sup_ini, x_sup_fim], [y_sup, y_sup], color=c_linha, lw=1.5, zorder=3)

    h_gancho_sup = max(8.0, 10.0 * phi_pe_cm)
    ax.plot([x_sup_ini, x_sup_ini], [y_sup, y_sup - h_gancho_sup], color=c_linha, lw=1.5, zorder=3)
    ax.plot([x_sup_fim, x_sup_fim], [y_sup, y_sup - h_gancho_sup], color=c_linha, lw=1.5, zorder=3)

    # Armadura Principal Inferior
    y_inf = cnom + (phi_as_cm / 2.0)
    x_inf_ini = cnom
    x_inf_fim = x_total - cnom
    ax.plot([x_inf_ini, x_inf_fim], [y_inf, y_inf], color=c_linha, lw=2.5, zorder=4)

    if tem_gancho:
        h_gancho = min(h_cm - 2.0 * cnom - 2.0, max(8.0 * phi_as_cm, lb_nec_cm * 0.55, 12.0))
        ax.plot([x_inf_ini, x_inf_ini], [y_inf, y_inf + h_gancho], color=c_linha, lw=2.5, zorder=4)
        ax.plot([x_inf_fim, x_inf_fim], [y_inf, y_inf + h_gancho], color=c_linha, lw=2.5, zorder=4)

    # ==========================================
    # 3. Estribos (Pena Muito Fina: 0.4)
    # ==========================================
    s_estribo = max(14.0, min(24.0, l0_cm / 22.0))
    x_est = t1_cm + 6.0
    while x_est < x_pilar_dir_ini - 5.0:
        ax.plot([x_est, x_est], [cnom, h_cm - cnom], color=c_linha, lw=0.4, ls="-", zorder=3)
        x_est += s_estribo

    # ==========================================
    # 4. Cotas e Textos (Pena Ultra Fina: 0.3)
    # ==========================================
    lw_cota = 0.3
    tk = max(2.0, h_cm * 0.05)
    font_tam = 9.0

    # 4.1 Identificação Armadura Inferior (Centralizada, afastada)
    y_texto_arm = -max(15.0, h_cm * 0.3)
    texto_as = f"{detalhe_as['n_barras']} \u03d5 {detalhe_as['phi_mm']:.1f} mm ({detalhe_as['distribuicao_camadas']})"
    ax.text(
        x_total / 2.0, y_texto_arm, texto_as,
        ha="center", va="center", fontsize=font_tam+1, color=c_linha,
        bbox=dict(boxstyle="square,pad=0.2", facecolor=c_fundo, edgecolor="none")
    )

    # 4.2 Cota dos Pilares (Mais baixa)
    y_cota_pilares = -h_pilar * 0.75
    ax.plot([0, t1_cm], [y_cota_pilares, y_cota_pilares], color=c_linha, lw=lw_cota)
    ax.plot([-tk, tk], [y_cota_pilares - tk, y_cota_pilares + tk], color=c_linha, lw=lw_cota)
    ax.plot([t1_cm - tk, t1_cm + tk], [y_cota_pilares - tk, y_cota_pilares + tk], color=c_linha, lw=lw_cota)
    ax.text(t1_cm / 2.0, y_cota_pilares - 4.0, f"t1 = {t1_cm:.0f} cm", ha="center", va="top", fontsize=font_tam, color=c_linha)

    ax.plot([x_pilar_dir_ini, x_total], [y_cota_pilares, y_cota_pilares], color=c_linha, lw=lw_cota)
    ax.plot([x_pilar_dir_ini - tk, x_pilar_dir_ini + tk], [y_cota_pilares - tk, y_cota_pilares + tk], color=c_linha, lw=lw_cota)
    ax.plot([x_total - tk, x_total + tk], [y_cota_pilares - tk, y_cota_pilares + tk], color=c_linha, lw=lw_cota)
    ax.text((x_pilar_dir_ini + x_total) / 2.0, y_cota_pilares - 4.0, f"t2 = {t2_cm:.0f} cm", ha="center", va="top", fontsize=font_tam, color=c_linha)

    # 4.3 Cota do Vão Livre (Nível mais profundo)
    y_cota_vao = -h_pilar - 20.0
    ax.plot([t1_cm, t1_cm], [-h_pilar, y_cota_vao - 2.0], color=c_linha, lw=0.3, ls=":")
    ax.plot([x_pilar_dir_ini, x_pilar_dir_ini], [-h_pilar, y_cota_vao - 2.0], color=c_linha, lw=0.3, ls=":")
    
    ax.plot([t1_cm, x_pilar_dir_ini], [y_cota_vao, y_cota_vao], color=c_linha, lw=lw_cota)
    ax.plot([t1_cm - tk, t1_cm + tk], [y_cota_vao - tk, y_cota_vao + tk], color=c_linha, lw=lw_cota)
    ax.plot([x_pilar_dir_ini - tk, x_pilar_dir_ini + tk], [y_cota_vao - tk, y_cota_vao + tk], color=c_linha, lw=lw_cota)
    ax.text((t1_cm + x_pilar_dir_ini) / 2.0, y_cota_vao - 4.0, f"l0 = {l0_m:.2f} m", ha="center", va="top", fontsize=font_tam+1, color=c_linha)

    # 4.4 Cota Ancoragem (Topo esquerda)
    y_cota_anc = h_cm + 20.0
    compr_anc_visivel = min(t1_cm - cnom, lb_nec_cm)
    ax.plot([cnom, cnom + compr_anc_visivel], [y_cota_anc, y_cota_anc], color=c_linha, lw=lw_cota)
    ax.plot([cnom - tk, cnom + tk], [y_cota_anc - tk, y_cota_anc + tk], color=c_linha, lw=lw_cota)
    ax.plot([cnom + compr_anc_visivel - tk, cnom + compr_anc_visivel + tk], [y_cota_anc - tk, y_cota_anc + tk], color=c_linha, lw=lw_cota)
    
    txt_anc = f"lb,nec = {lb_nec_cm:.1f} cm" + (" (c/ gancho)" if tem_gancho else " (reto)")
    ax.text(cnom, y_cota_anc + 4.0, txt_anc, ha="left", va="bottom", fontsize=font_tam, color=c_linha)

    # 4.5 Cota Altura (h) (Lateral externa esquerda)
    x_cota_h = -max(25.0, x_total * 0.05)
    ax.plot([x_cota_h, x_cota_h], [0, h_cm], color=c_linha, lw=lw_cota)
    ax.plot([x_cota_h - tk, x_cota_h + tk], [-tk, tk], color=c_linha, lw=lw_cota)
    ax.plot([x_cota_h - tk, x_cota_h + tk], [h_cm - tk, h_cm + tk], color=c_linha, lw=lw_cota)
    ax.text(x_cota_h - 4.0, h_cm / 2.0, f"h = {h_cm:.0f} cm", ha="right", va="center", fontsize=font_tam, rotation=90, color=c_linha)

    # ==========================================
    # 5. LÓGICA DE CENTRALIZAÇÃO FORÇADA
    # ==========================================
    margem_sup = 35.0
    margem_inf = abs(y_cota_vao) + 15.0

    centro_viga_x = x_total / 2.0
    
    dist_limite_esq = centro_viga_x - (x_cota_h - 15.0)
    dist_limite_dir = (x_total + max(15.0, x_total * 0.08)) - centro_viga_x
    dist_maxima_simetrica = max(dist_limite_esq, dist_limite_dir)

    ax.set_xlim(centro_viga_x - dist_maxima_simetrica, centro_viga_x + dist_maxima_simetrica)
    ax.set_ylim(-margem_inf, h_cm + margem_sup)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    return fig