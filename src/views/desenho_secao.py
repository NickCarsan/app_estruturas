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
    Renderiza o detalhamento da seção transversal no padrão técnico:
    - Escala reduzida e harmoniosa de textos e cotas.
    - Chamada da armadura inferior tracionada (As) jogada lateralmente para a direita.
    - Suporte a seções Retangulares e T (Falso/Verdadeiro).
    """
    fig, ax = plt.subplots(figsize=(6.0, 7.5), facecolor="white")
    ax.set_facecolor("white")

    cnom = cnom_mm / 10.0
    phi_t = phi_t_mm / 10.0
    d_max = d_max_agregado_mm / 10.0
    
    eh_secao_t = (forma == "Seção T (Verdadeiro ou Falso)" and bf_cm > bw_cm and hf_cm > 0)
    largura_total = bf_cm if eh_secao_t else bw_cm

    # 1. Contorno externo do concreto
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
        poly = patches.Polygon(verts, closed=True, linewidth=1.8, edgecolor="black", facecolor="white", zorder=1)
        ax.add_patch(poly)
    else:
        x_mesa_esq = 0.0
        x_mesa_dir = bw_cm
        ax.add_patch(
            patches.Rectangle(
                (0, 0), bw_cm, h_cm,
                linewidth=1.8, edgecolor="black", facecolor="white", zorder=1
            )
        )

    # 2. Estribo fechado na nervura
    x_est = cnom
    y_est = cnom
    w_est = bw_cm - 2.0 * cnom
    h_est = h_cm - 2.0 * cnom
    raio_dobra = max(0.4, 1.5 * phi_t)

    ax.add_patch(
        patches.FancyBboxPatch(
            (x_est, y_est), w_est, h_est,
            boxstyle=f"round,pad=0,rounding_size={raio_dobra}",
            linewidth=1.2, edgecolor="black", facecolor="none", zorder=2
        )
    )

    escala_visual = 1.25

    # 3. Armadura Tracionada (As)
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
                facecolor="black", edgecolor="black", linewidth=0.8, zorder=4
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
                    facecolor="black", edgecolor="black", linewidth=0.8, zorder=4
                )
                ax.add_patch(circ)
                barras_sup_coords.append((xc, y_centro_sup))
            y_centro_sup -= (phi_asl_cm + s_v_asl)

        texto_arm_sup = f"{detalhe_as_linha['n_barras']} ϕ {detalhe_as_linha['phi_mm']:.1f}"
    else:
        phi_pe_cm = max(0.5, phi_t)
        raio_desenho_pe = (phi_pe_cm / 2.0) * escala_visual
        y_pe = h_cm - cnom - phi_t - (phi_pe_cm / 2.0)
        for xc in [cnom + phi_t + (phi_pe_cm / 2.0), bw_cm - cnom - phi_t - (phi_pe_cm / 2.0)]:
            circ = patches.Circle(
                (xc, y_pe), raio_desenho_pe,
                facecolor="black", edgecolor="black", linewidth=0.8, zorder=4
            )
            ax.add_patch(circ)
            barras_sup_coords.append((xc, y_pe))
        texto_arm_sup = f"2 ϕ {phi_pe_cm * 10.0:.1f}"

    # 5. Cotas Técnicas (Fontes e offsets otimizados)
    offset_cota_h = max(7.0, largura_total * 0.22)
    offset_cota_b = max(5.0, h_cm * 0.10)
    tk = 0.6
    lw_cota = 0.7
    font_cotas = 8.5

    # 5.1 Cota de Largura Superior (bf ou b)
    y_cota_b = h_cm + offset_cota_b
    ax.plot([x_mesa_esq, x_mesa_esq], [h_cm, y_cota_b + 0.6], color="black", lw=lw_cota)
    ax.plot([x_mesa_dir, x_mesa_dir], [h_cm, y_cota_b + 0.6], color="black", lw=lw_cota)
    ax.plot([x_mesa_esq, x_mesa_dir], [y_cota_b, y_cota_b], color="black", lw=lw_cota)
    ax.plot([x_mesa_esq - tk, x_mesa_esq + tk], [y_cota_b - tk, y_cota_b + tk], color="black", lw=lw_cota)
    ax.plot([x_mesa_dir - tk, x_mesa_dir + tk], [y_cota_b - tk, y_cota_b + tk], color="black", lw=lw_cota)
    
    label_b = f"bf = {largura_total:.0f} cm" if eh_secao_t else f"b = {largura_total:.0f} cm"
    ax.text((x_mesa_esq + x_mesa_dir) / 2.0, y_cota_b + 0.8, label_b, ha="center", va="bottom", fontsize=font_cotas, fontweight="bold")

    # 5.2 Se for Seção T: cota bw na base e hf na lateral esquerda
    if eh_secao_t:
        y_cota_bw = -offset_cota_b
        ax.plot([0, 0], [0, y_cota_bw - 0.6], color="black", lw=lw_cota)
        ax.plot([bw_cm, bw_cm], [0, y_cota_bw - 0.6], color="black", lw=lw_cota)
        ax.plot([0, bw_cm], [y_cota_bw, y_cota_bw], color="black", lw=lw_cota)
        ax.plot([-tk, tk], [y_cota_bw - tk, y_cota_bw + tk], color="black", lw=lw_cota)
        ax.plot([bw_cm - tk, bw_cm + tk], [y_cota_bw - tk, y_cota_bw + tk], color="black", lw=lw_cota)
        ax.text(bw_cm / 2.0, y_cota_bw - 0.8, f"bw = {bw_cm:.0f} cm", ha="center", va="top", fontsize=font_cotas, fontweight="bold")

        x_cota_hf = x_mesa_esq - offset_cota_h * 0.45
        ax.plot([x_mesa_esq, x_cota_hf - 0.6], [h_cm, h_cm], color="black", lw=lw_cota)
        ax.plot([x_mesa_esq, x_cota_hf - 0.6], [h_cm - hf_cm, h_cm - hf_cm], color="black", lw=lw_cota)
        ax.plot([x_cota_hf, x_cota_hf], [h_cm - hf_cm, h_cm], color="black", lw=lw_cota)
        ax.plot([x_cota_hf - tk, x_cota_hf + tk], [h_cm - hf_cm - tk, h_cm - hf_cm + tk], color="black", lw=lw_cota)
        ax.plot([x_cota_hf - tk, x_cota_hf + tk], [h_cm - tk, h_cm + tk], color="black", lw=lw_cota)
        ax.text(x_cota_hf - 0.8, h_cm - hf_cm / 2.0, f"hf = {hf_cm:.0f} cm", ha="right", va="center", fontsize=font_cotas, fontweight="bold")

    # 5.3 Cota de Altura Total (h)
    x_cota_h = x_mesa_esq - offset_cota_h
    ax.plot([x_mesa_esq, x_cota_h - 0.6], [0, 0], color="black", lw=lw_cota)
    ax.plot([x_mesa_esq, x_cota_h - 0.6], [h_cm, h_cm], color="black", lw=lw_cota)
    ax.plot([x_cota_h, x_cota_h], [0, h_cm], color="black", lw=lw_cota)
    ax.plot([x_cota_h - tk, x_cota_h + tk], [-tk, tk], color="black", lw=lw_cota)
    ax.plot([x_cota_h - tk, x_cota_h + tk], [h_cm - tk, h_cm + tk], color="black", lw=lw_cota)
    ax.text(x_cota_h - 1.0, h_cm / 2.0, f"h = {h_cm:.0f} cm", ha="right", va="center", fontsize=font_cotas, fontweight="bold", rotation=90)

    # 6. Linhas de Chamada das Armaduras (TODAS NA LATERAL DIREITA)
    x_chamada = x_mesa_dir + offset_cota_h * 0.75
    font_chamada = 9.0

    # 6.1 Armadura Superior (topo)
    if len(barras_sup_coords) >= 2:
        alvo_sup_esq = barras_sup_coords[0]
        alvo_sup_dir = barras_sup_coords[1]
        y_chamada_sup = h_cm - cnom - phi_t - 1.2
        ax.plot([alvo_sup_esq[0], x_chamada - 1.2], [alvo_sup_esq[1], y_chamada_sup], color="black", lw=lw_cota)
        ax.plot([alvo_sup_dir[0], x_chamada - 1.2], [alvo_sup_dir[1], y_chamada_sup], color="black", lw=lw_cota)
        ax.plot([x_chamada - 1.2, x_chamada], [y_chamada_sup, y_chamada_sup], color="black", lw=lw_cota)
        ax.text(x_chamada + 0.4, y_chamada_sup, texto_arm_sup, ha="left", va="center", fontsize=font_chamada, fontweight="bold")

    # 6.2 Estribo (meia altura da nervura)
    x_alvo_est = bw_cm - cnom
    y_alvo_est = (h_cm - hf_cm) * 0.55 if eh_secao_t else h_cm * 0.5
    y_chamada_est = y_alvo_est
    ax.plot([x_alvo_est, x_chamada], [y_alvo_est, y_chamada_est], color="black", lw=lw_cota)
    ax.text(x_chamada + 0.4, y_chamada_est, f"ϕ {phi_t_mm:.1f}", ha="left", va="center", fontsize=font_chamada, fontweight="bold")

    # 6.3 Armadura Inferior (As) - Jogada lateralmente para a direita
    texto_as = f"{detalhe_as['n_barras']} ϕ {detalhe_as['phi_mm']:.1f}"
    y_alvo_inf = cnom + phi_t + (phi_as_cm / 2.0)
    y_chamada_inf = y_alvo_inf

    # Puxa linhas de chamada das barras mais externas para a ponta da chamada lateral
    if primeiras_barras_coords:
        p_esq = primeiras_barras_coords[0]
        p_dir = primeiras_barras_coords[-1]
        ax.plot([p_esq[0], x_chamada - 1.2], [p_esq[1], y_chamada_inf], color="black", lw=lw_cota)
        ax.plot([p_dir[0], x_chamada - 1.2], [p_dir[1], y_chamada_inf], color="black", lw=lw_cota)
        ax.plot([x_chamada - 1.2, x_chamada], [y_chamada_inf, y_chamada_inf], color="black", lw=lw_cota)
        ax.text(x_chamada + 0.4, y_chamada_inf, texto_as, ha="left", va="center", fontsize=font_chamada, fontweight="bold")

    # 7. Margens e enquadramento limpo
    margem_dir = offset_cota_h * 2.2
    margem_esq = offset_cota_h * 1.6
    margem_sup = offset_cota_b * 1.8
    margem_inf = offset_cota_b * 1.8

    ax.set_xlim(x_mesa_esq - margem_esq, x_mesa_dir + margem_dir)
    ax.set_ylim(-margem_inf, h_cm + margem_sup)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    return fig
