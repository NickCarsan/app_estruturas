# src/views/desenho_secao.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, Optional

def gerar_grafico_secao(
    bw_cm: float,
    h_cm: float,
    cnom_mm: float,
    phi_t_mm: float,
    detalhe_as: Dict,
    detalhe_as_linha: Optional[Dict] = None,
    d_max_agregado_mm: float = 19.0,
    bf_cm: float = 0.0,
    hf_cm: float = 0.0,
    forma: str = "Retangular"
):
    """
    Renderiza o detalhamento da seção transversal no padrão CAD Monocromático:
    - Fundo escuro
    - Apenas linhas brancas com espessuras (penas) variadas.
    - Centralização exata da peça estrutural no canvas.
    """
    c_fundo = "#081018"
    c_linha = "#FFFFFF" 
    
    fig, ax = plt.subplots(figsize=(7.5, 7.5), facecolor=c_fundo)
    ax.set_facecolor(c_fundo)

    cnom = cnom_mm / 10.0
    phi_t = phi_t_mm / 10.0
    d_max = d_max_agregado_mm / 10.0
    
    eh_secao_t = (forma == "Seção T (Verdadeiro ou Falso)" and bf_cm > bw_cm and hf_cm > 0)
    largura_total = bf_cm if eh_secao_t else bw_cm

    # 1. Contorno externo do concreto (Pena Média)
    lw_concreto = 1.0
    if eh_secao_t:
        x_mesa_esq = -(bf_cm - bw_cm) / 2.0
        x_mesa_dir = bw_cm + (bf_cm - bw_cm) / 2.0
        verts = [
            (0, 0), (bw_cm, 0),
            (bw_cm, h_cm - hf_cm),
            (x_mesa_dir, h_cm - hf_cm),
            (x_mesa_dir, h_cm),
            (x_mesa_esq, h_cm),
            (x_mesa_esq, h_cm - hf_cm),
            (0, h_cm - hf_cm),
            (0, 0)
        ]
        poly = patches.Polygon(verts, closed=True, linewidth=lw_concreto, edgecolor=c_linha, facecolor="none", zorder=1)
        ax.add_patch(poly)
    else:
        x_mesa_esq = 0.0
        x_mesa_dir = bw_cm
        ax.add_patch(
            patches.Rectangle(
                (0, 0), bw_cm, h_cm,
                linewidth=lw_concreto, edgecolor=c_linha, facecolor="none", zorder=1
            )
        )

    # 2. Estribo (Pena Fina)
    lw_estribo = 0.5
    x_est = cnom
    y_est = cnom
    w_est = bw_cm - 2.0 * cnom
    h_est = h_cm - 2.0 * cnom
    raio_dobra = max(0.4, 1.5 * phi_t)

    ax.add_patch(
        patches.FancyBboxPatch(
            (x_est, y_est), w_est, h_est,
            boxstyle=f"round,pad=0,rounding_size={raio_dobra}",
            linewidth=lw_estribo, edgecolor=c_linha, facecolor="none", zorder=2
        )
    )

    escala_visual = 1.25

    # 3. Armadura Tracionada (As) - (Pena Grossa/Preenchida)
    phi_as_cm = detalhe_as["phi_mm"] / 10.0
    raio_desenho_as = (phi_as_cm / 2.0) * escala_visual
    camadas_as = [int(q.replace("Φ", "")) for q in detalhe_as["distribuicao_camadas"].split(" + ")]
    s_v_as = max(2.0, phi_as_cm, 0.5 * d_max)

    y_centro = cnom + phi_t + (phi_as_cm / 2.0)
    primeiras_barras_coords = []
    camadas_pontos_dir = []

    for idx_c, qtd_barras in enumerate(camadas_as):
        if qtd_barras == 1:
            coords_x = [bw_cm / 2.0]
        else:
            x_ini = cnom + phi_t + (phi_as_cm / 2.0)
            x_fim = bw_cm - cnom - phi_t - (phi_as_cm / 2.0)
            passo = (x_fim - x_ini) / (qtd_barras - 1)
            coords_x = [x_ini + i * passo for i in range(qtd_barras)]

        for xc in coords_x:
            circ = patches.Circle(
                (xc, y_centro), raio_desenho_as,
                facecolor=c_linha, edgecolor=c_linha, linewidth=1.0, zorder=4
            )
            ax.add_patch(circ)
            if idx_c == 0:
                primeiras_barras_coords.append((xc, y_centro))

        camadas_pontos_dir.append((coords_x[-1], y_centro))
        y_centro += phi_as_cm + s_v_as

    # 4. Armadura Superior (A's ou Porta-estribos)
    barras_sup_coords = []
    if detalhe_as_linha and detalhe_as_linha.get("n_barras", 0) > 0:
        phi_asl_cm = detalhe_as_linha["phi_mm"] / 10.0
        raio_desenho_asl = (phi_asl_cm / 2.0) * escala_visual
        camadas_asl = [int(q.replace("Φ", "")) for q in detalhe_as_linha["distribuicao_camadas"].split(" + ")]
        s_v_asl = max(2.0, phi_asl_cm, 0.5 * d_max)

        y_centro_sup = h_cm - cnom - phi_t - (phi_asl_cm / 2.0)
        for qtd_barras in camadas_asl:
            if qtd_barras == 1:
                coords_x = [bw_cm / 2.0]
            else:
                x_ini = cnom + phi_t + (phi_asl_cm / 2.0)
                x_fim = bw_cm - cnom - phi_t - (phi_asl_cm / 2.0)
                passo = (x_fim - x_ini) / (qtd_barras - 1)
                coords_x = [x_ini + i * passo for i in range(qtd_barras)]

            for xc in coords_x:
                circ = patches.Circle(
                    (xc, y_centro_sup), raio_desenho_asl,
                    facecolor="none", edgecolor=c_linha, linewidth=1.5, zorder=4
                )
                ax.add_patch(circ)
                barras_sup_coords.append((xc, y_centro_sup))
            y_centro_sup -= (phi_asl_cm + s_v_asl)

        texto_arm_sup = f"{detalhe_as_linha['n_barras']} \u03d5 {detalhe_as_linha['phi_mm']:.1f}"
    else:
        phi_pe_cm = max(0.5, phi_t)
        raio_desenho_pe = (phi_pe_cm / 2.0) * escala_visual
        y_pe = h_cm - cnom - phi_t - (phi_pe_cm / 2.0)
        for xc in [cnom + phi_t + (phi_pe_cm / 2.0), bw_cm - cnom - phi_t - (phi_pe_cm / 2.0)]:
            circ = patches.Circle(
                (xc, y_pe), raio_desenho_pe,
                facecolor="none", edgecolor=c_linha, linewidth=1.0, zorder=4
            )
            ax.add_patch(circ)
            barras_sup_coords.append((xc, y_pe))
        texto_arm_sup = f"2 \u03d5 {phi_pe_cm * 10.0:.1f}"

    # 5. Cotas Técnicas (Afastadas e Muito Finas)
    offset_cota_h = max(12.0, largura_total * 0.35)
    offset_cota_b = max(10.0, h_cm * 0.18)
    tk = 0.8
    lw_cota = 0.3
    font_cotas = 8.0

    y_cota_b = h_cm + offset_cota_b
    ax.plot([x_mesa_esq, x_mesa_esq], [h_cm, y_cota_b + 0.6], color=c_linha, lw=lw_cota)
    ax.plot([x_mesa_dir, x_mesa_dir], [h_cm, y_cota_b + 0.6], color=c_linha, lw=lw_cota)
    ax.plot([x_mesa_esq, x_mesa_dir], [y_cota_b, y_cota_b], color=c_linha, lw=lw_cota)
    ax.plot([x_mesa_esq - tk, x_mesa_esq + tk], [y_cota_b - tk, y_cota_b + tk], color=c_linha, lw=lw_cota)
    ax.plot([x_mesa_dir - tk, x_mesa_dir + tk], [y_cota_b - tk, y_cota_b + tk], color=c_linha, lw=lw_cota)
    
    label_b = f"bf = {largura_total:.0f} cm" if eh_secao_t else f"b = {largura_total:.0f} cm"
    ax.text((x_mesa_esq + x_mesa_dir) / 2.0, y_cota_b + 1.2, label_b, ha="center", va="bottom", fontsize=font_cotas, color=c_linha)

    if eh_secao_t:
        y_cota_bw = -offset_cota_b
        ax.plot([0, 0], [0, y_cota_bw - 0.6], color=c_linha, lw=lw_cota)
        ax.plot([bw_cm, bw_cm], [0, y_cota_bw - 0.6], color=c_linha, lw=lw_cota)
        ax.plot([0, bw_cm], [y_cota_bw, y_cota_bw], color=c_linha, lw=lw_cota)
        ax.plot([-tk, tk], [y_cota_bw - tk, y_cota_bw + tk], color=c_linha, lw=lw_cota)
        ax.plot([bw_cm - tk, bw_cm + tk], [y_cota_bw - tk, y_cota_bw + tk], color=c_linha, lw=lw_cota)
        ax.text(bw_cm / 2.0, y_cota_bw - 1.2, f"bw = {bw_cm:.0f} cm", ha="center", va="top", fontsize=font_cotas, color=c_linha)

        x_cota_hf = x_mesa_esq - offset_cota_h * 0.45
        ax.plot([x_mesa_esq, x_cota_hf - 0.6], [h_cm, h_cm], color=c_linha, lw=lw_cota)
        ax.plot([x_mesa_esq, x_cota_hf - 0.6], [h_cm - hf_cm, h_cm - hf_cm], color=c_linha, lw=lw_cota)
        ax.plot([x_cota_hf, x_cota_hf], [h_cm - hf_cm, h_cm], color=c_linha, lw=lw_cota)
        ax.plot([x_cota_hf - tk, x_cota_hf + tk], [h_cm - hf_cm - tk, h_cm - hf_cm + tk], color=c_linha, lw=lw_cota)
        ax.plot([x_cota_hf - tk, x_cota_hf + tk], [h_cm - tk, h_cm + tk], color=c_linha, lw=lw_cota)
        ax.text(x_cota_hf - 1.2, h_cm - hf_cm / 2.0, f"hf = {hf_cm:.0f} cm", ha="right", va="center", fontsize=font_cotas, color=c_linha)

    x_cota_h = x_mesa_esq - offset_cota_h
    ax.plot([x_mesa_esq, x_cota_h - 0.6], [0, 0], color=c_linha, lw=lw_cota)
    ax.plot([x_mesa_esq, x_cota_h - 0.6], [h_cm, h_cm], color=c_linha, lw=lw_cota)
    ax.plot([x_cota_h, x_cota_h], [0, h_cm], color=c_linha, lw=lw_cota)
    ax.plot([x_cota_h - tk, x_cota_h + tk], [-tk, tk], color=c_linha, lw=lw_cota)
    ax.plot([x_cota_h - tk, x_cota_h + tk], [h_cm - tk, h_cm + tk], color=c_linha, lw=lw_cota)
    ax.text(x_cota_h - 1.5, h_cm / 2.0, f"h = {h_cm:.0f} cm", ha="right", va="center", fontsize=font_cotas, rotation=90, color=c_linha)

    # 6. Linhas de Chamada (Afastadas)
    x_chamada = x_mesa_dir + offset_cota_h * 1.2
    font_chamada = 8.5

    if len(barras_sup_coords) >= 2:
        alvo_sup_esq = barras_sup_coords[0]
        alvo_sup_dir = barras_sup_coords[1]
        y_chamada_sup = h_cm + 2.0
        ax.plot([alvo_sup_esq[0], x_chamada - 1.2], [alvo_sup_esq[1], y_chamada_sup], color=c_linha, lw=lw_cota)
        ax.plot([alvo_sup_dir[0], x_chamada - 1.2], [alvo_sup_dir[1], y_chamada_sup], color=c_linha, lw=lw_cota)
        ax.plot([x_chamada - 1.2, x_chamada], [y_chamada_sup, y_chamada_sup], color=c_linha, lw=lw_cota)
        ax.text(x_chamada + 0.8, y_chamada_sup, texto_arm_sup, ha="left", va="center", fontsize=font_chamada, color=c_linha)

    x_alvo_est = bw_cm - cnom
    y_alvo_est = (h_cm - hf_cm) * 0.55 if eh_secao_t else h_cm * 0.5
    y_chamada_est = y_alvo_est
    ax.plot([x_alvo_est, x_chamada], [y_alvo_est, y_chamada_est], color=c_linha, lw=lw_cota)
    ax.text(x_chamada + 0.8, y_chamada_est, f"\u03d5 {phi_t_mm:.1f}", ha="left", va="center", fontsize=font_chamada, color=c_linha)

    texto_as = f"{detalhe_as['n_barras']} \u03d5 {detalhe_as['phi_mm']:.1f}"
    y_chamada_inf = -offset_cota_b * 2.2 if eh_secao_t else -offset_cota_b * 1.8

    if len(primeiras_barras_coords) >= 2:
        b_esq = primeiras_barras_coords[0]
        b_dir = primeiras_barras_coords[-1]
        x_meio = bw_cm / 2.0
        ax.plot([b_esq[0], x_meio], [b_esq[1] - raio_desenho_as, y_chamada_inf + 1.2], color=c_linha, lw=lw_cota)
        ax.plot([b_dir[0], x_meio], [b_dir[1] - raio_desenho_as, y_chamada_inf + 1.2], color=c_linha, lw=lw_cota)
        ax.plot([x_meio, x_meio], [y_chamada_inf + 1.2, y_chamada_inf + 0.2], color=c_linha, lw=lw_cota)
        ax.text(x_meio, y_chamada_inf - 0.8, texto_as, ha="center", va="top", fontsize=font_chamada, color=c_linha)
    elif len(primeiras_barras_coords) == 1:
        b_unica = primeiras_barras_coords[0]
        ax.plot([b_unica[0], b_unica[0]], [b_unica[1] - raio_desenho_as, y_chamada_inf + 0.2], color=c_linha, lw=lw_cota)
        ax.text(b_unica[0], y_chamada_inf - 0.8, texto_as, ha="center", va="top", fontsize=font_chamada, color=c_linha)

    # ========================================================
    # 7. NOVO: LÓGICA DE CENTRALIZAÇÃO FORÇADA
    # ========================================================
    margem_dir = offset_cota_h * 2.8 # Espaço para os textos das linhas de chamada
    margem_esq = offset_cota_h * 1.8 # Espaço para a cota h
    margem_sup = offset_cota_b * 2.2
    margem_inf = offset_cota_b * 2.5

    # Achamos o meio exato do bloco de concreto
    centro_viga_x = (x_mesa_esq + x_mesa_dir) / 2.0
    
    # Calculamos qual dos lados precisa de mais espaço e espelhamos esse limite para o outro lado
    dist_limite_esq = centro_viga_x - (x_mesa_esq - margem_esq)
    dist_limite_dir = (x_mesa_dir + margem_dir) - centro_viga_x
    dist_maxima_simetrica = max(dist_limite_esq, dist_limite_dir)

    # Força os limites da imagem (xlim) a serem simétricos a partir do meio da viga
    ax.set_xlim(centro_viga_x - dist_maxima_simetrica, centro_viga_x + dist_maxima_simetrica)
    ax.set_ylim(-margem_inf, h_cm + margem_sup)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    return fig