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
from src.views.desenho_secao import gerar_grafico_secao

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

        if tipo_entrada == "Digitar o Momento Fletor (Mk direto)":
            mk = st.number_input("Momento Fletor Característico Mk (kN.m)", min_value=0.0, value=308.0, step=5.0)
        elif tipo_entrada == "Calcular por Carga e Vão (Viga Bi-apoiada)":
            q_k = st.number_input("Carga Total Característica qk (kN/m)", min_value=0.0, value=20.0, step=1.0)
            l_vao = st.number_input("Vão da Viga L (m)", min_value=1.0, value=5.0, step=0.5)
            mk = (q_k * (l_vao ** 2)) / 8.0
            st.info(f"📌 **Mk calculado:** `{mk:.2f} kN.m`")
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

    if "resultado_calculo" in st.session_state:
        resultado = st.session_state["resultado_calculo"]
        viga_calc = st.session_state["viga_calculada"]
        c_nom = st.session_state["cnom_mm"]
        p_t = st.session_state["phi_t"]
        d_lin = st.session_state["d_linha"]
        d_agreg = st.session_state["d_max_agregado"]
        forma = st.session_state["forma_secao"]

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
            
            # --- DEFINIÇÃO UNIVERSAL DAS VARIÁVEIS DE AÇO ---
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

            st.markdown("#### Resumo do Detalhamento Escolhido")
            if forma == "Seção T (Verdadeiro ou Falso)":
                st.write(f"• **Formato:** Seção T ({resultado.get('forma_secao', 'Desconhecido').replace('_', ' ').title()})")
                st.write(f"• **Dimensões Nervura:** {viga_calc.bw:.0f} × {viga_calc.h:.0f} cm")
                st.write(f"• **Dimensões Mesa:** {bf_grafico:.0f} × {hf_grafico:.0f} cm")
            else:
                st.write(f"• **Dimensões:** {viga_calc.bw:.0f} × {viga_calc.h:.0f} cm")
            st.write(f"• **Cobrimento ($c_{{nom}}$):** {c_nom:.0f} mm")
            st.write(f"• **Estribo:** Φ {p_t:.1f} mm")
            st.write(f"• **Armadura Inferior ($A_s$):** {arranjo_as_selecionado['n_barras']} Φ {arranjo_as_selecionado['phi_mm']:.1f} mm")
            st.write(f"• **Distribuição das Camadas:** {arranjo_as_selecionado['distribuicao_camadas']}")
            st.write(f"• **Altura Útil Real ($d_{{real}}$):** `{arranjo_as_selecionado['d_real_cm']:.2f} cm`")
            
            if arranjo_asl_selecionado:
                st.write(f"• **Armadura Superior ($A'_s$):** {arranjo_asl_selecionado['n_barras']} Φ {arranjo_asl_selecionado['phi_mm']:.1f} mm")
                st.write(f"• **$d'_{{real}}$:** `{arranjo_asl_selecionado['d_linha_real_cm']:.2f} cm`")
            else:
                st.write("• **Armadura Superior:** 2 Φ Porta-estribos construtivos")

if __name__ == "__main__":
    renderizar_tela()
