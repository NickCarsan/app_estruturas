# src/views/interface.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
from src.config import CLASSES_CONCRETO, BITOLAS_ACO, COBRIMENTOS_VIGA
from src.models.materiais import Concreto, Aco
from src.models.elementos import VigaRetangular, VigaT
from src.controllers.flexao import calcular_flexao, calcular_momento_limite_armadura_simples, calcular_viga_t
from src.controllers.detalhamento import detalhar_arranjo, AGREGADOS
from src.controllers.ancoragem import (
    calcular_fbd, 
    calcular_comprimento_ancoragem, 
    ancoragem_apoio_extremo,
    calcular_vao_efetivo
)
from src.views.desenho_secao import gerar_grafico_secao
from src.views.desenho_longitudinal import gerar_grafico_longitudinal

def renderizar_tela():
    st.set_page_config(page_title="Dimensionamento Estrutural - NBR 6118", layout="wide")
    
    st.title("🏗️ Dimensionamento de Vigas de Concreto Armado")
    st.markdown("Cálculo de flexão simples e dupla conforme a **ABNT NBR 6118 / UNASP**.")

    st.sidebar.header("1. Materiais e Durabilidade")
    fck_escolhido = st.sidebar.selectbox("Concreto fck (MPa)", CLASSES_CONCRETO, index=1)
    tipo_aco = st.sidebar.selectbox("Aço Longitudinal", ["CA-50 (500 MPa)", "CA-60 (600 MPa)"])
    fyk = 500 if "CA-50" in tipo_aco else 600

    caa_escolhida = st.sidebar.selectbox("Classe de Agressividade (CAA)", list(COBRIMENTOS_VIGA.keys()))
    cnom_mm = COBRIMENTOS_VIGA[caa_escolhida]

    agregado_nome = st.sidebar.selectbox(
        r"Diâmetro Máximo do Agregado ($d_{\text{máx}}$)", 
        list(AGREGADOS.keys()), 
        index=1
    )
    d_max_agregado = AGREGADOS[agregado_nome]

    concreto = Concreto(fck=fck_escolhido)
    aco = Aco(fyk=fyk)

    st.sidebar.markdown(f"**$f_{{cd}}$:** `{concreto.fcd:.2f} MPa`")
    st.sidebar.markdown(f"**$f_{{yd}}$:** `{aco.fyd:.2f} MPa`")
    st.sidebar.markdown(f"**Cobrimento ($c_{{nom}}$):** `{cnom_mm} mm`")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("2. Geometria da Seção")
        
        forma_secao = st.radio("Formato da Seção", ["Retangular", "Seção T (Verdadeiro ou Falso)"], horizontal=True)
        
        bw = st.number_input("Largura da Nervura (bw) em cm", min_value=12.0, value=30.0, step=1.0)
        h = st.number_input("Altura total (h) em cm", min_value=20.0, value=45.0, step=5.0)
        
        if forma_secao == "Seção T (Verdadeiro ou Falso)":
            col_mesa1, col_mesa2 = st.columns(2)
            with col_mesa1:
                bf = st.number_input("Largura colaborante (bf) cm", min_value=bw, value=80.0, step=5.0)
            with col_mesa2:
                hf = st.number_input("Espessura da mesa (hf) cm", min_value=5.0, value=10.0, step=1.0)
        else:
            bf, hf = bw, 0.0

        st.markdown("---")
        st.subheader("Diâmetros Adotados Preliminares")
        phi_t = st.selectbox(r"Estribo ($\phi_t$ em mm)", [5.0, 6.3, 8.0, 10.0], index=1)
        phi_l = st.selectbox(r"Armadura Longitudinal ($\phi_l$ em mm)", BITOLAS_ACO, index=3)

        if forma_secao == "Seção T (Verdadeiro ou Falso)":
            viga = VigaT(bw=bw, h=h, bf=bf, hf=hf, cnom_mm=cnom_mm, phi_t_mm=phi_t, phi_l_mm=phi_l)
        else:
            viga = VigaRetangular(bw=bw, h=h, cnom_mm=cnom_mm, phi_t_mm=phi_t, phi_l_mm=phi_l)
            
        d_linha_padrao = round(cnom_mm / 10.0 + phi_t / 10.0 + (phi_l / 10.0) / 2.0, 2)
        d_linha = st.number_input("d' adotado armadura de compressão (cm)", min_value=2.0, value=d_linha_padrao, step=0.5)

        st.info(f"📐 **Altura Útil Calculada (d):** `{viga.d:.2f} cm` | **d':** `{d_linha:.2f} cm`")

    with col2:
        st.subheader("3. Esforços Solicitantes")
        tipo_entrada = st.radio(
            "Como deseja definir o esforço?",
            [
                "Digitar o Momento Fletor (Mk direto)", 
                "Calcular por Carga e Vão (Viga Bi-apoiada)",
                "Capacidade Máxima da Seção (Cálculo Inverso)"
            ]
        )

        vk_calc = 0.0
        dados_vao = None
        t_apoio_medio_cm = 20.0

        if tipo_entrada == "Digitar o Momento Fletor (Mk direto)":
            mk = st.number_input("Momento Fletor Característico Mk (kN.m)", min_value=0.0, value=308.0, step=5.0)
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                vk_calc = st.number_input("Cortante Vk no apoio (kN) [Opcional]", min_value=0.0, value=0.0, step=5.0)
            with col_v2:
                t_apoio_medio_cm = st.number_input("Largura dos pilares de apoio (cm)", min_value=12.0, value=20.0, step=5.0)

        elif tipo_entrada == "Calcular por Carga e Vão (Viga Bi-apoiada)":
            q_k = st.number_input("Carga Total Característica qk (kN/m)", min_value=0.0, value=20.0, step=1.0)
            
            modo_vao = st.radio(
                "Definição do Vão da Viga:",
                ["Informar Vão Livre e Pilares (NBR 6118)", "Informar Vão Teórico Direto (L)"],
                horizontal=True
            )
            
            if modo_vao == "Informar Vão Livre e Pilares (NBR 6118)":
                col_v1, col_v2, col_v3 = st.columns(3)
                with col_v1:
                    l0_m = st.number_input("Vão Livre $l_0$ (m)", min_value=1.0, value=5.0, step=0.5)
                with col_v2:
                    t1_cm = st.number_input("Pilar Esquerdo $t_1$ (cm)", min_value=12.0, value=20.0, step=5.0)
                with col_v3:
                    t2_cm = st.number_input("Pilar Direito $t_2$ (cm)", min_value=12.0, value=20.0, step=5.0)
                
                dados_vao = calcular_vao_efetivo(l0_m=l0_m, t1_cm=t1_cm, t2_cm=t2_cm, h_cm=viga.h)
                l_calculo = dados_vao["lef_m"]
                t_apoio_medio_cm = (t1_cm + t2_cm) / 2.0
                
                st.caption(
                    f"📏 **Vão Efetivo ($l_{ef}$):** `{dados_vao['lef_m']:.2f} m` | "
                    f"**Comprimento Total:** `{dados_vao['l_total_m']:.2f} m`"
                )
            else:
                l_calculo = st.number_input("Vão Teórico L (m)", min_value=1.0, value=5.0, step=0.5)
                t_apoio_medio_cm = st.number_input("Largura dos pilares de apoio (cm)", min_value=12.0, value=20.0, step=5.0)
                
            mk = (q_k * (l_calculo ** 2)) / 8.0
            vk_calc = (q_k * l_calculo) / 2.0
            st.info(f"📌 **Mk de cálculo:** `{mk:.2f} kN.m` | **Vk no apoio:** `{vk_calc:.2f} kN`")

        else:
            mk = 0.0
            st.info("📌 **Modo Inverso:** Calcula a capacidade máxima resistente $M_1$ no limite da armadura simples.")

    st.divider()

    if st.button("Calcular Armaduras", type="primary"):
        if tipo_entrada == "Capacidade Máxima da Seção (Cálculo Inverso)":
            res = calcular_momento_limite_armadura_simples(
                fcd=concreto.fcd,
                fyd=aco.fyd,
                b=viga.bw,
                d=viga.d,
                fck=fck_escolhido
            )
            res["modo_inverso"] = True
        else:
            if forma_secao == "Retangular":
                res = calcular_flexao(
                    mk=mk, fcd=concreto.fcd, fyd=aco.fyd, 
                    b=viga.bw, d=viga.d, d_linha=d_linha, fck=fck_escolhido
                )
            else:
                res = calcular_viga_t(
                    mk=mk, fcd=concreto.fcd, fyd=aco.fyd, 
                    bw=viga.bw, bf=viga.bf, hf=viga.hf, 
                    d=viga.d, fck=fck_escolhido
                )
            res["modo_inverso"] = False
        
        st.session_state["resultado_calculo"] = res
        st.session_state["viga_calculada"] = viga
        st.session_state["cnom_mm"] = cnom_mm
        st.session_state["phi_t"] = phi_t
        st.session_state["d_linha"] = d_linha
        st.session_state["d_max_agregado"] = d_max_agregado
        st.session_state["forma_secao"] = forma_secao
        st.session_state["fck"] = fck_escolhido
        st.session_state["fyd"] = aco.fyd
        st.session_state["vk_calc"] = vk_calc
        st.session_state["t_apoio_cm"] = t_apoio_medio_cm
        st.session_state["dados_vao"] = dados_vao

    if "resultado_calculo" in st.session_state:
        resultado = st.session_state["resultado_calculo"]
        viga_calc = st.session_state["viga_calculada"]
        c_nom = st.session_state["cnom_mm"]
        p_t = st.session_state["phi_t"]
        d_lin = st.session_state["d_linha"]
        d_agreg = st.session_state["d_max_agregado"]
        forma = st.session_state["forma_secao"]
        fck_val = st.session_state.get("fck", 25.0)
        fyd_val = st.session_state.get("fyd", 434.78)
        vk_val = st.session_state.get("vk_calc", 0.0)
        t_apoio = st.session_state.get("t_apoio_cm", 20.0)
        d_vao = st.session_state.get("dados_vao", None)

        if resultado.get("modo_inverso", False):
            st.success("Cálculo da capacidade máxima realizado com sucesso!")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Momento Máx. Resistente ($M_d$)", f"{resultado['md_limite_knm']:.2f} kN.m")
            c2.metric(r"Linha Neutra Limite ($\beta_x$)", f"{resultado['beta_x']:.2f}")
            c3.metric("Braço de Alavanca ($z$)", f"{resultado['z_cm']:.2f} cm")
            c4.metric(r"Área de Aço ($A_s$)", f"{resultado['as_cm2']:.2f} cm²")
            as_alvo = resultado["as_cm2"]
            as_linha_alvo = 0.0
            eh_dupla = False
        else:
            st.success("Dimensionamento concluído!")
            c1, c2, c3 = st.columns(3)
            c1.metric("Momento de Cálculo ($M_d$)", f"{resultado.get('md_knm', 0.0):.2f} kN.m")
            c2.metric(r"Linha Neutra ($\beta_x$)", f"{resultado.get('beta_x', 0.0):.2f}")
            c3.metric("Tipo de Armadura", resultado.get("tipo_armadura", "Simples"))
            
            eh_dupla = resultado.get("tipo_armadura") == "Dupla"
            as_alvo = resultado.get("as_total_cm2", 0.0)
            as_linha_alvo = resultado.get("as_linha_cm2", 0.0)

            if "tipo_secao" in resultado:
                st.info(f"🔎 Comportamento detectado: **{resultado['tipo_secao']}**")

            if eh_dupla:
                st.warning(f"⚠️ {resultado.get('status', 'Armadura Dupla Necessária')}")
                ca1, ca2, ca3 = st.columns(3)
                ca1.metric(r"Armadura Tracionada Total ($A_s$)", f"{resultado['as_total_cm2']:.2f} cm²")
                ca2.metric(r"Armadura Comprimida ($A'_s$)", f"{resultado['as_linha_cm2']:.2f} cm²")
                ca3.metric(r"Tensão no Aço Comprimido ($\sigma'_s$)", f"{resultado.get('sigma_s_linha', 0.0):.2f} MPa")
            elif as_alvo > 0:
                st.info(f"✅ {resultado.get('status', 'Armadura Simples')}")
                st.metric(r"Área de Aço Tracionada ($A_s$)", f"{resultado['as_total_cm2']:.2f} cm²")

        st.markdown("---")
        st.markdown("### 📋 Detalhamento Comercial e Recálculo da Altura Útil ($d_{real}$)")

        arranjos_as = detalhar_arranjo(as_alvo, viga_calc.bw, viga_calc.h, c_nom, p_t, d_agreg)

        st.subheader(r"Opções de Distribuição para Armadura Tracionada ($A_s$)")
        dados_as = []
        opcoes_labels_as = []
        for item in arranjos_as:
            label = f"{item['n_barras']} Φ {item['phi_mm']:.1f} mm — ({item['distribuicao_camadas']}) | Fornecido: {item['as_efetivo']:.2f} cm² | d_real: {item['d_real_cm']:.2f} cm"
            opcoes_labels_as.append(label)
            dados_as.append({
                "Bitola": f"Φ {item['phi_mm']:.1f} mm",
                "Total": f"{item['n_barras']} barras",
                "Distribuição": item["distribuicao_camadas"],
                "Camadas": f"{item['num_camadas']} camada(s)",
                "As Fornecido": f"{item['as_efetivo']:.2f} cm²",
                "Folga": f"+{item['sobra_percentual']:.1f}%",
                "Espaçamento H": f"{item['espacamento_h_real_cm']:.2f} cm",
                "d real": f"{item['d_real_cm']:.2f} cm",
                "Dif. p/ d adotado": f"{(item['d_real_cm'] - viga_calc.d):+.2f} cm"
            })
        st.dataframe(pd.DataFrame(dados_as), use_container_width=True)

        indice_as_escolhido = st.selectbox(
            "Selecione o arranjo final de armadura tracionada ($A_s$) para gerar a seção:",
            range(len(opcoes_labels_as)) if len(opcoes_labels_as) > 0 else [0],
            format_func=lambda x: opcoes_labels_as[x] if len(opcoes_labels_as) > 0 else "Nenhuma",
            key="sel_arranjo_as"
        )
        arranjo_as_selecionado = arranjos_as[indice_as_escolhido] if arranjos_as else None

        arranjo_asl_selecionado = None
        if eh_dupla and as_linha_alvo > 0:
            arranjos_as_linha = detalhar_arranjo(as_linha_alvo, viga_calc.bw, viga_calc.h, c_nom, p_t, d_agreg)
            st.subheader(r"Opções de Distribuição para Armadura Comprimida ($A'_s$)")
            dados_as_linha = []
            opcoes_labels_asl = []
            for item in arranjos_as_linha:
                label = f"{item['n_barras']} Φ {item['phi_mm']:.1f} mm — ({item['distribuicao_camadas']}) | Fornecido: {item['as_efetivo']:.2f} cm²"
                opcoes_labels_asl.append(label)
                dados_as_linha.append({
                    "Bitola": f"Φ {item['phi_mm']:.1f} mm",
                    "Total": f"{item['n_barras']} barras",
                    "Distribuição": item["distribuicao_camadas"],
                    "Camadas": f"{item['num_camadas']} camada(s)",
                    "A's Fornecido": f"{item['as_efetivo']:.2f} cm²",
                    "Folga": f"+{item['sobra_percentual']:.1f}%",
                    "d' real": f"{item['d_linha_real_cm']:.2f} cm",
                    "Dif. p/ d' adotado": f"{(item['d_linha_real_cm'] - d_lin):+.2f} cm"
                })
            st.dataframe(pd.DataFrame(dados_as_linha), use_container_width=True)

            indice_asl_escolhido = st.selectbox(
                "Selecione o arranjo de armadura comprimida ($A'_s$):",
                range(len(opcoes_labels_asl)) if len(opcoes_labels_asl) > 0 else [0],
                format_func=lambda x: opcoes_labels_asl[x] if len(opcoes_labels_asl) > 0 else "Nenhuma",
                key="sel_arranjo_asl"
            )
            arranjo_asl_selecionado = arranjos_as_linha[indice_asl_escolhido] if arranjos_as_linha else None

        # --- MÓDULO DE ANCORAGEM (NBR 6118 / AULA 07) ---
        if arranjo_as_selecionado:
            st.markdown("---")
            st.subheader("⚓ Ancoragem das Armaduras Longitudinais (NBR 6118)")
            
            tipo_bar = "nervurada" if "CA-50" in tipo_aco else "lisa"
            
            # Painel interativo para ancoragem
            col_anc_cfg1, col_anc_cfg2 = st.columns(2)
            with col_anc_cfg1:
                pos_aderencia_inf = st.selectbox(
                    "Condição de Aderência da Armadura:",
                    options=["boa", "ma"],
                    format_func=lambda x: "Boa Aderência (inferior / h ≤ 60 cm)" if x == "boa" else "Má Aderência (superior / exsudação)",
                    index=0 if viga_calc.h <= 60.0 else 1
                )
            with col_anc_cfg2:
                gancho_opcao = st.radio(
                    "Tipo de Extremidade:",
                    options=["Com gancho convencional (α = 0.7)", "Barra reta sem gancho (α = 1.0)"],
                    horizontal=True
                )
                tem_gancho = "Com gancho" in gancho_opcao
            
            phi_inf = arranjo_as_selecionado["phi_mm"]
            as_ef_inf = arranjo_as_selecionado["as_efetivo"]
            
            res_fbd_inf = calcular_fbd(fck=fck_val, tipo_barra=tipo_bar, 
                                       posicao_aderencia=pos_aderencia_inf, phi_mm=phi_inf)
            
            anc_reta_inf = calcular_comprimento_ancoragem(phi_mm=phi_inf, fyd_mpa=fyd_val, 
                                                          fbd_mpa=res_fbd_inf["fbd"], 
                                                          as_calc=as_alvo, as_ef=as_ef_inf, 
                                                          com_gancho=False, comprimida=False)
            
            anc_escolhida = calcular_comprimento_ancoragem(phi_mm=phi_inf, fyd_mpa=fyd_val, 
                                                           fbd_mpa=res_fbd_inf["fbd"], 
                                                           as_calc=as_alvo, as_ef=as_ef_inf, 
                                                           com_gancho=tem_gancho, comprimida=False)

            col_anc1, col_anc2, col_anc3, col_anc4 = st.columns(4)
            col_anc1.metric(r"Tensão de Aderência ($f_{bd}$)", f"{res_fbd_inf['fbd']:.2f} MPa")
            col_anc2.metric(r"Comprimento Básico ($l_b$)", f"{anc_reta_inf['lb_cm']:.1f} cm")
            col_anc3.metric(r"Mínimo Normativo ($l_{b,\text{mín}}$)", f"{anc_reta_inf['lb_min_cm']:.1f} cm")
            col_anc4.metric(r"Comprimento Necessário ($l_{b,\text{nec}}$)", f"{anc_escolhida['lb_nec_cm']:.1f} cm")

            if anc_escolhida.get("aviso_gancho"):
                st.warning(f"⚠️ {anc_escolhida['aviso_gancho']}")

            # Verificação de espaço físico no pilar
            c_nom_cm = c_nom / 10.0
            espaco_livre_pilar_cm = max(0.0, t_apoio - c_nom_cm)
            lb_reta_nec = anc_reta_inf["lb_nec_cm"]
            
            if lb_reta_nec <= espaco_livre_pilar_cm:
                st.success(
                    f"✅ **Verificação no Apoio:** A ancoragem reta ({lb_reta_nec:.1f} cm) "
                    f"cabe no pilar ({espaco_livre_pilar_cm:.1f} cm livres descontado o cobrimento)."
                )
            else:
                st.warning(
                    f"⚠️ **Pilar Estreito para Ancoragem Reta:** O comprimento reto necessário ({lb_reta_nec:.1f} cm) "
                    f"supera o espaço no pilar ({espaco_livre_pilar_cm:.1f} cm). **É obrigatório o gancho em 90°** "
                    f"(comprimento com gancho: {anc_escolhida['lb_nec_cm']:.1f} cm)."
                )

            with st.expander("ℹ️ Ver detalhes normativos do cálculo de ancoragem"):
                st.write(f"• **Resistência à tração direta do concreto ($f_{{ctd}}$):** {res_fbd_inf['fctd']:.2f} MPa")
                st.write(f"• **Coeficientes de aderência:** $\\eta_1 = {res_fbd_inf['eta1']:.2f}$ (barra {tipo_bar}) | $\\eta_2 = {res_fbd_inf['eta2']:.2f}$ ({pos_aderencia_inf} aderência) | $\\eta_3 = {res_fbd_inf['eta3']:.2f}$")
                st.write(f"• **Relação de aproveitamento ($A_{{s,	ext{{calc}}}} / A_{{s,	ext{{ef}}}}$):** {anc_escolhida['razao_as']:.3f}")
                st.write(f"• **Fator de gancho ($\\alpha$):** {anc_escolhida['alpha']:.2f}")
                st.caption("Nota: Em barras comprimidas (armadura dupla) a NBR 6118 veda o uso de ganchos devido à concentração de tensões e risco de fendilhamento.")

            # Verificação no apoio extremo se houver cortante
            if vk_val > 0:
                vd_val = vk_val * 1.4
                res_apoio = ancoragem_apoio_extremo(vd_kn=vd_val, d_cm=viga_calc.d, fyd_mpa=fyd_val)
                st.info(
                    f"📌 **Ancoragem no Apoio Extremo (NBR 6118, item 18.3.2.4):** \n"
                    f"• Esforço $V_d = {vd_val:.2f}\text{{ kN}}$ | Força na biela $R_s = {res_apoio['rs_kn']:.2f}\text{{ kN}} \n"
                    f"• Armadura mínima no apoio: **{res_apoio['as_apoio_nec_cm2']:.2f} cm²** (Fornecido: **{as_ef_inf:.2f} cm²**)."
                )

        # --- VISTA GRÁFICA DA SEÇÃO TRANSVERSAL ---
        if arranjo_as_selecionado:
            st.markdown("---")
            st.subheader("📐 Vista Gráfica da Seção Transversal")
            
            bf_grafico = getattr(viga_calc, 'bf', 0.0)
            hf_grafico = getattr(viga_calc, 'hf', 0.0)

            fig_secao = gerar_grafico_secao(
                bw_cm=viga_calc.bw,
                h_cm=viga_calc.h,
                cnom_mm=c_nom,
                phi_t_mm=p_t,
                detalhe_as=arranjo_as_selecionado,
                detalhe_as_linha=arranjo_asl_selecionado,
                d_max_agregado_mm=d_agreg,
                bf_cm=bf_grafico,
                hf_cm=hf_grafico,
                forma=forma
            )
            
            st.pyplot(fig_secao, use_container_width=False)

            
            # --- VISTA LONGITUDINAL E ANCORAGEM NOS APOIOS ---
            st.markdown("---")
            st.subheader("📐 Vista Gráfica Longitudinal e Ancoragem nos Apoios")

            # Recupera dados dos apoios
            l0_m_plot = d_vao["l0_m"] if d_vao else 5.0
            t1_cm_plot = d_vao["t1_cm"] if d_vao else t_apoio
            t2_cm_plot = d_vao["t2_cm"] if d_vao else t_apoio

            fig_long = gerar_grafico_longitudinal(
                l0_m=l0_m_plot,
                h_cm=viga_calc.h,
                cnom_mm=c_nom,
                t1_cm=t1_cm_plot,
                t2_cm=t2_cm_plot,
                detalhe_as=arranjo_as_selecionado,
                lb_nec_cm=anc_escolhida["lb_nec_cm"],
                tem_gancho=tem_gancho
            )
            st.pyplot(fig_long, use_container_width=True)

            st.markdown("#### Resumo do Detalhamento Escolhido")
            if forma == "Seção T (Verdadeiro ou Falso)":
                st.write(f"• **Formato:** Seção T ({resultado.get('forma_secao', 'Desconhecido').replace('_', ' ').title()})")
                st.write(f"• **Dimensões Nervura:** {viga_calc.bw:.0f} × {viga_calc.h:.0f} cm")
                st.write(f"• **Dimensões Mesa:** {bf_grafico:.0f} × {hf_grafico:.0f} cm")
            else:
                st.write(f"• **Dimensões:** {viga_calc.bw:.0f} × {viga_calc.h:.0f} cm")
            
            if d_vao:
                st.write(f"• **Comprimento da Peça:** Vão livre $l_0 = {d_vao['l0_m']:.2f}\text{{ m}}$ | Total = {d_vao['l_total_m']:.2f} m")
                
            st.write(f"• **Cobrimento ($c_{{nom}}$):** {c_nom:.0f} mm")
            st.write(f"• **Estribo:** Φ {p_t:.1f} mm")
            st.write(f"• **Armadura Inferior ($A_s$):** {arranjo_as_selecionado['n_barras']} Φ {arranjo_as_selecionado['phi_mm']:.1f} mm")
            st.write(f"• **Distribuição das Camadas:** {arranjo_as_selecionado['distribuicao_camadas']}")
            st.write(f"• **Altura Útil Real ($d_{{real}}$):** {arranjo_as_selecionado['d_real_cm']:.2f} cm")
            
            if arranjo_asl_selecionado:
                st.write(f"• **Armadura Superior ($A'_s$):** {arranjo_asl_selecionado['n_barras']} Φ {arranjo_asl_selecionado['phi_mm']:.1f} mm")
                st.write(f"• **$d'_{{real}}$:** {arranjo_asl_selecionado['d_linha_real_cm']:.2f} cm")
            else:
                st.write("• **Armadura Superior:** 2 Φ Porta-estribos construtivos")

if __name__ == "__main__":
    renderizar_tela()
