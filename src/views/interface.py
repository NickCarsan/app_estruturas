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
from src.controllers.estatica import calcular_estatica_viga
from src.views.desenho_diagramas import gerar_diagramas_blueprint
from src.views.desenho_secao import gerar_grafico_secao
from src.views.desenho_longitudinal import gerar_grafico_longitudinal
from src.controllers.cisalhamento import calcular_cisalhamento

def renderizar_tela():
    # Layout Wide e Side Bar oculta por padrão
    st.set_page_config(page_title="App Estruturas - CAD Mode", layout="wide", initial_sidebar_state="collapsed")
    
    # CSS Customizado (Tema Blueprint, Quadriculado sutil e Tipografia)
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;700&display=swap');
        
        .stApp {
            background-color: #081018;
            background-image:
              linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
            background-size: 20px 20px;
            font-family: 'Inter', sans-serif;
            color: #d0d0d0;
        }
        
        input[type="number"], .stMarkdown code {
            font-family: 'JetBrains Mono', monospace !important;
            color: #00ffff !important;
        }
        
        h1, h2, h3 { color: #ffffff !important; font-weight: 600; }
        
        .stTabs [data-baseweb="tab-list"] { background-color: rgba(255,255,255,0.05); border-radius: 8px; }
        
        .stButton>button {
            background-color: #ff3b5c;
            color: #ffffff;
            font-weight: 700;
            border-radius: 4px;
        }
        .stButton>button:hover {
            background-color: #ff5270;
            color: #ffffff;
        }

        /* Estilizando o dataframe para ficar escuro e tecnico */
        [data-testid="stDataFrame"] {
            background-color: #111b27;
            border: 1px solid #1a293b;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### 🖥️ Análise Estrutural Interativa")
    
    # Split-Screen Layout: Coluna Esquerda (Entrada) e Coluna Direita (Canvas/Gráficos)
    col_esq, col_dir = st.columns([1.2, 2.0], gap="large")

    with col_esq:
        # Organização em Abas lógicas
        tab_geo, tab_cargas = st.tabs(["📐 Geometria & Apoios", "⚖️ Esforços Solicitantes"])

        with tab_geo:
            st.subheader("Geometria da Viga")
            forma_secao = st.radio("Selecione a Tipologia:", ["Retangular", "Seção T (Verdadeiro ou Falso)"], horizontal=True, label_visibility="collapsed")
            bw = st.number_input(r"Largura da Nervura ($b_w$) [cm]", min_value=12.0, value=30.0, step=1.0)
            h = st.number_input(r"Altura Total ($h$) [cm]", min_value=20.0, value=45.0, step=5.0)
            
            if forma_secao == "Seção T (Verdadeiro ou Falso)":
                c_bf, c_hf = st.columns(2)
                with c_bf: bf = st.number_input(r"Largura Colaborante ($b_f$) [cm]", min_value=bw, value=80.0, step=5.0)
                with c_hf: hf = st.number_input(r"Espessura Mesa ($h_f$) [cm]", min_value=5.0, value=10.0, step=1.0)
            else:
                bf, hf = bw, 0.0
                
            st.markdown("---")
            st.subheader("Apoios e Vão")
            l0_m = st.number_input(r"Vão Livre $l_0$ [m]", min_value=1.0, value=5.0, step=0.1)
            
            c_t1, c_t2 = st.columns(2)
            with c_t1: t1_cm = st.number_input(r"Apoio Esq. $t_1$ [cm]", min_value=12.0, value=20.0, step=5.0)
            with c_t2: t2_cm = st.number_input(r"Apoio Dir. $t_2$ [cm]", min_value=12.0, value=20.0, step=5.0)
            
            dados_vao = calcular_vao_efetivo(l0_m=l0_m, t1_cm=t1_cm, t2_cm=t2_cm, h_cm=h)
            L = dados_vao["lef_m"]
            t_apoio_medio_cm = (t1_cm + t2_cm) / 2.0
            st.caption(f"**Vão Efetivo ($l_{{ef}}$):** `{L:.2f} m` | **Total:** `{dados_vao['l_total_m']:.2f} m`")

            st.markdown("---")
            st.subheader("Pré-dimensionamento / Materiais")
            
            with st.expander("Parâmetros Normativos (NBR 6118)", expanded=False):
                fck_escolhido = st.selectbox("Classe do Concreto (fck)", CLASSES_CONCRETO, index=1, format_func=lambda x: f"C{x} ({x} MPa)")
                tipo_aco = st.selectbox("Aço Longitudinal", ["CA-50 (500 MPa)", "CA-60 (600 MPa)"])
                fyk = 500 if "CA-50" in tipo_aco else 600
                caa_escolhida = st.selectbox("Classe de Agressividade (CAA)", list(COBRIMENTOS_VIGA.keys()))
                cnom_mm = COBRIMENTOS_VIGA[caa_escolhida]
                agregado_nome = st.selectbox(r"Agregado Graúdo ($d_{	ext{máx}}$)", list(AGREGADOS.keys()), index=1)
                d_max_agregado = AGREGADOS[agregado_nome]

            concreto = Concreto(fck=fck_escolhido)
            aco = Aco(fyk=fyk)
            
            c_phi1, c_phi2 = st.columns(2)
            with c_phi1: phi_t = st.selectbox(r"Estribo Adotado ($\phi_t$) [mm]", [5.0, 6.3, 8.0, 10.0], index=1)
            with c_phi2: phi_l = st.selectbox(r"Barra Principal ($\phi_l$) [mm]", BITOLAS_ACO, index=3)

            if forma_secao == "Seção T (Verdadeiro ou Falso)":
                viga = VigaT(bw=bw, h=h, bf=bf, hf=hf, cnom_mm=cnom_mm, phi_t_mm=phi_t, phi_l_mm=phi_l)
            else:
                viga = VigaRetangular(bw=bw, h=h, cnom_mm=cnom_mm, phi_t_mm=phi_t, phi_l_mm=phi_l)
                
            d_linha_padrao = round(cnom_mm / 10.0 + phi_t / 10.0 + (phi_l / 10.0) / 2.0, 2)
            d_linha = st.number_input(r"Distância $d'$ (Comprimida) [cm]", min_value=2.0, value=d_linha_padrao, step=0.5)

            st.info(f"**Altura Útil de Cálculo ($d$):** `{viga.d:.2f} cm` | **$d'$:** `{d_linha:.2f} cm`")

        with tab_cargas:
            st.markdown("Carga Distribuída Permanente")
            q = st.number_input("Carga q [kN/m]", min_value=0.0, value=20.0, step=1.0)
            
            st.markdown("---")
            st.markdown("Carga Pontual (Arrastar)")
            P = st.number_input("Carga P [kN]", min_value=0.0, value=50.0, step=5.0)
            
            a = st.slider("Posição da Carga P (m)", min_value=0.0, max_value=float(L), value=L/2, step=0.1)
            
            res_estatica = calcular_estatica_viga(L, q, P, a)
            mk_calc = res_estatica["M_max"]
            vk_calc = max(abs(res_estatica["Ra"]), abs(res_estatica["Rb"]))

        st.markdown("<br>", unsafe_allow_html=True)
        executar_calculo = st.button("Calcular Armaduras NBR 6118", type="primary", use_container_width=True)

    with col_dir:
        if "res_estatica" not in locals():
            res_estatica = calcular_estatica_viga(L, 20.0, 50.0, L/2)
            mk_calc = res_estatica["M_max"]
            vk_calc = max(abs(res_estatica["Ra"]), abs(res_estatica["Rb"]))

        fig = gerar_diagramas_blueprint(L, q, P, a, res_estatica)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with st.expander("Exibir Memorial Analítico de Estática"):
            st.markdown("#### Equações de Equilíbrio Estático")
            st.latex(r"\sum M_A = 0 \implies R_B \cdot L - q \cdot L \cdot \frac{L}{2} - P \cdot a = 0")
            st.latex(f"R_B = \frac{{({q:.2f} \times {L:.2f}^2 / 2) + ({P:.2f} \times {a:.2f})}}{{{L:.2f}}} = {res_estatica['Rb']:.2f} \text{{ kN}}")
            
            st.markdown("---")
            st.latex(r"\sum F_y = 0 \implies R_A + R_B - q \cdot L - P = 0")
            st.latex(f"R_A = ({q:.2f} \times {L:.2f}) + {P:.2f} - {res_estatica['Rb']:.2f} = {res_estatica['Ra']:.2f} \text{{ kN}}")
            
            st.markdown("#### Esforços Máximos Mapeados")
            st.info(f"**Momento Fletor Máximo:** `{res_estatica['M_max']:.2f} kN.m` em `x = {res_estatica['x_max']:.2f} m`")

    # --- PROCESSAMENTO DO DIMENSIONAMENTO ---
    if executar_calculo:
        with st.spinner('A processar limites normativos...'):
            # 1. Flexão
            if forma_secao == "Retangular":
                res = calcular_flexao(mk=mk_calc, fcd=concreto.fcd, fyd=aco.fyd, b=viga.bw, d=viga.d, d_linha=d_linha, fck=fck_escolhido)
            else:
                res = calcular_viga_t(mk=mk_calc, fcd=concreto.fcd, fyd=aco.fyd, bw=viga.bw, bf=viga.bf, hf=viga.hf, d=viga.d, fck=fck_escolhido)
            res["modo_inverso"] = False
            
            # 2. Cisalhamento (Estribos)
            res_cisalhamento = calcular_cisalhamento(vk_kn=vk_calc, fck_mpa=fck_escolhido, bw_cm=viga.bw, d_cm=viga.d, fyk_mpa=500.0)
            
            st.session_state["resultado_calculo"] = res
            st.session_state["resultado_cisalhamento"] = res_cisalhamento
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
            st.session_state["mostrar_painel"] = True

    if st.session_state.get("mostrar_painel", False):
        st.markdown("---")
        
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

        st.header("Síntese Analítica")

        c1, c2, c3 = st.columns(3)
        c1.metric("Momento de Cálculo ($M_d$)", f"{resultado.get('md_knm', 0.0):.2f} kN.m")
        c2.metric(r"Posição Relativa L.N. ($\beta_x$)", f"{resultado.get('beta_x', 0.0):.2f}")
        c3.metric("Regime de Armadura", resultado.get("tipo_armadura", "Simples"))
        
        eh_dupla = resultado.get("tipo_armadura") == "Dupla"
        as_alvo = resultado.get("as_total_cm2", 0.0)
        as_linha_alvo = resultado.get("as_linha_cm2", 0.0)

        if "tipo_secao" in resultado:
            st.caption(f"Comportamento Estrutural Identificado: **{resultado['tipo_secao']}**")

        if eh_dupla:
            st.error(f"Atenção: {resultado.get('status', 'Armadura Dupla Necessária')}")
            ca1, ca2, ca3 = st.columns(3)
            ca1.metric(r"Armadura Tracionada Total Necessária ($A_s$)", f"{resultado['as_total_cm2']:.2f} cm²")
            ca2.metric(r"Armadura Comprimida Necessária ($A'_s$)", f"{resultado['as_linha_cm2']:.2f} cm²")
            ca3.metric(r"Tensão no Aço Comprimido ($\sigma'_s$)", f"{resultado.get('sigma_s_linha', 0.0):.2f} MPa")
        elif as_alvo > 0:
            st.success(f"Status: {resultado.get('status', 'Dimensionamento em Armadura Simples Estável.')}")
            st.metric(r"Área de Aço Tracionada Necessária ($A_s$)", f"{resultado['as_total_cm2']:.2f} cm²")

        st.markdown("#### Esforço Cortante e Armadura Transversal")
        res_cis = st.session_state["resultado_cisalhamento"]
        
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("Cortante de Cálculo ($V_{sd}$)", f"{res_cis.get('vsd_kn', 0.0):.2f} kN")
        cc2.metric("Resistência da Biela ($V_{Rd2}$)", f"{res_cis.get('vrd2_kn', 0.0):.2f} kN")
        cc3.metric("Estribos Necessários ($A_{sw}/s$)", f"{res_cis.get('asw_s_final_cm2_m', 0.0):.2f} cm²/m")
        
        if res_cis.get('vsd_kn', 0) > res_cis.get('vrd2_kn', 0):
            st.error(res_cis.get('status'))
        else:
            st.success(f"Biela verificada. {res_cis.get('status')}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.header("Detalhamento Executivo e Documentação Gráfica")
        
        tab_detalhe, tab_ancoragem, tab_2d = st.tabs(["Opções de Armação", "Ancoragem", "Prancha Técnica 2D"])

        arranjos_as = detalhar_arranjo(as_alvo, viga_calc.bw, viga_calc.h, c_nom, p_t, d_agreg)

        with tab_detalhe:
            st.subheader(r"Arranjos Geométricos - Armadura de Tração ($A_s$)")
            dados_as = []
            opcoes_labels_as = []
            for item in arranjos_as:
                label = f"{item['n_barras']} Φ {item['phi_mm']:.1f} mm — ({item['distribuicao_camadas']}) | d_real: {item['d_real_cm']:.2f} cm"
                opcoes_labels_as.append(label)
                dados_as.append({
                    "Configuração": f"{item['n_barras']} Φ {item['phi_mm']:.1f}",
                    "Distribuição Física": item["distribuicao_camadas"],
                    "Área Efetiva [cm²]": f"{item['as_efetivo']:.2f}",
                    "Margem Segurança": f"+{item['sobra_percentual']:.1f}%",
                    "Afastamento Horizontal [cm]": f"{item['espacamento_h_real_cm']:.2f}",
                    "Altura Útil Efetiva ($d_{real}$) [cm]": f"{item['d_real_cm']:.2f}"
                })
            st.dataframe(pd.DataFrame(dados_as), use_container_width=True, hide_index=True)

            indice_as_escolhido = st.selectbox("Selecione o detalhamento definitivo para o projeto ($A_s$):", range(len(opcoes_labels_as)), format_func=lambda x: opcoes_labels_as[x])
            arranjo_as_selecionado = arranjos_as[indice_as_escolhido] if arranjos_as else None

            arranjo_asl_selecionado = None
            if eh_dupla and as_linha_alvo > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader(r"Arranjos Geométricos - Armadura de Compressão ($A'_s$)")
                arranjos_as_linha = detalhar_arranjo(as_linha_alvo, viga_calc.bw, viga_calc.h, c_nom, p_t, d_agreg)
                dados_as_linha = []
                opcoes_labels_asl = []
                for item in arranjos_as_linha:
                    label = f"{item['n_barras']} Φ {item['phi_mm']:.1f} mm — ({item['distribuicao_camadas']})"
                    opcoes_labels_asl.append(label)
                    dados_as_linha.append({
                        "Configuração": f"{item['n_barras']} Φ {item['phi_mm']:.1f}",
                        "Distribuição Física": item["distribuicao_camadas"],
                        "Área Efetiva [cm²]": f"{item['as_efetivo']:.2f}",
                        "Margem Segurança": f"+{item['sobra_percentual']:.1f}%",
                        "Altura ($d'_{real}$) [cm]": f"{item['d_linha_real_cm']:.2f}"
                    })
                st.dataframe(pd.DataFrame(dados_as_linha), use_container_width=True, hide_index=True)
                indice_asl_escolhido = st.selectbox("Selecione o detalhamento definitivo ($A'_s$):", range(len(opcoes_labels_asl)), format_func=lambda x: opcoes_labels_asl[x])
                arranjo_asl_selecionado = arranjos_as_linha[indice_asl_escolhido] if arranjos_as_linha else None

        with tab_ancoragem:
            if arranjo_as_selecionado:
                st.subheader("Critérios de Aderência e Ancoragem Longitudinal")
                tipo_bar = "nervurada" if "CA-50" in tipo_aco else "lisa"
                
                col_anc_cfg1, col_anc_cfg2 = st.columns(2)
                with col_anc_cfg1:
                    pos_aderencia_inf = st.selectbox("Região de Concretagem:", ["boa", "ma"], format_func=lambda x: "Região de Boa Aderência (Inferior)" if x == "boa" else "Região de Má Aderência (Superior)", index=0 if viga_calc.h <= 60.0 else 1)
                with col_anc_cfg2:
                    gancho_opcao = st.radio("Configuração da Extremidade:", ["Ancoragem com gancho ($\\alpha = 0,7$)", "Ancoragem reta ($\\alpha = 1,0$)"], horizontal=True)
                    tem_gancho = "gancho" in gancho_opcao
                
                phi_inf = arranjo_as_selecionado["phi_mm"]
                as_ef_inf = arranjo_as_selecionado["as_efetivo"]
                
                res_fbd = calcular_fbd(fck=fck_val, tipo_barra=tipo_bar, posicao_aderencia=pos_aderencia_inf, phi_mm=phi_inf)
                anc_reta = calcular_comprimento_ancoragem(phi_mm=phi_inf, fyd_mpa=fyd_val, fbd_mpa=res_fbd["fbd"], as_calc=as_alvo, as_ef=as_ef_inf, com_gancho=False)
                anc_esc = calcular_comprimento_ancoragem(phi_mm=phi_inf, fyd_mpa=fyd_val, fbd_mpa=res_fbd["fbd"], as_calc=as_alvo, as_ef=as_ef_inf, com_gancho=tem_gancho)

                c1, c2, c3 = st.columns(3)
                c1.metric(r"Tensão Resistente de Aderência $f_{bd}$", f"{res_fbd['fbd']:.2f} MPa")
                c2.metric(r"Comprimento Básico de Ancoragem $l_b$", f"{anc_reta['lb_cm']:.1f} cm")
                c3.metric(r"Comprimento Necessário $l_{b,nec}$", f"{anc_esc['lb_nec_cm']:.1f} cm")

                c_nom_cm = c_nom / 10.0
                espaco_livre = max(0.0, t_apoio - c_nom_cm)
                if anc_reta["lb_nec_cm"] <= espaco_livre:
                    st.success(f"Condição Geométrica Satisfeita: O comprimento reto da ancoragem é compatível com a largura do pilar ({espaco_livre:.1f} cm disponíveis livres de cobrimento).")
                else:
                    st.warning(f"Incompatibilidade Geométrica: O pilar apresenta largura restrita ({espaco_livre:.1f} cm disponíveis livres de cobrimento). O dobramento em gancho 90° na extremidade é estruturalmente obrigatório.")

                if vk_val > 0:
                    vd_val = vk_val * 1.4
                    res_apoio = ancoragem_apoio_extremo(vd_kn=vd_val, d_cm=viga_calc.d, fyd_mpa=fyd_val)
                    st.info(f"Esforços Adicionais no Apoio Extremo (Biela de Compressão): Força Tracionante $R_s$ = {res_apoio['rs_kn']:.2f} kN → Exigência Mínima Ancorada $A_{{s,nec}}$ = {res_apoio['as_apoio_nec_cm2']:.2f} cm² (Arranjo Fornece: {as_ef_inf:.2f} cm²)")

        with tab_2d:
            if arranjo_as_selecionado:
                
                # ==========================================
                # 1. CONTROLE DE TAMANHO: CORTE TRANSVERSAL
                # O array [1, 1.5, 1] cria margens laterais. 
                # Diminua o 1.5 para deixar o desenho menor, ou aumente para deixá-lo maior.
                # ==========================================
                col_esq1, col_centro1, col_dir1 = st.columns([1, 1.5, 1])
                
                with col_centro1:
                    st.subheader("Corte Transversal")
                    bf_grafico = getattr(viga_calc, 'bf', 0.0)
                    hf_grafico = getattr(viga_calc, 'hf', 0.0)

                    fig_secao = gerar_grafico_secao(
                        bw_cm=viga_calc.bw, h_cm=viga_calc.h, cnom_mm=c_nom, phi_t_mm=p_t,
                        detalhe_as=arranjo_as_selecionado, detalhe_as_linha=arranjo_asl_selecionado,
                        d_max_agregado_mm=d_agreg, bf_cm=bf_grafico, hf_cm=hf_grafico, forma=forma
                    )
                    st.pyplot(fig_secao, use_container_width=True)

                st.markdown("<br><br>", unsafe_allow_html=True) # Dá um respiro entre os dois desenhos

                # ==========================================
                # 2. CONTROLE DE TAMANHO: ELEVAÇÃO LONGITUDINAL
                # Como a viga é comprida, usamos [0.5, 3, 0.5] para dar margens menores.
                # Diminua o 3 para deixar a vista longitudinal mais curta na tela.
                # ==========================================
                col_esq2, col_centro2, col_dir2 = st.columns([0.5, 3, 0.5])
                
                with col_centro2:
                    st.subheader("Elevação Longitudinal")
                    l0_m_plot = d_vao["l0_m"] if d_vao else 5.0
                    t1_cm_plot = d_vao["t1_cm"] if d_vao else t_apoio
                    t2_cm_plot = d_vao["t2_cm"] if d_vao else t_apoio

                    if 'anc_esc' not in locals():
                        res_fbd_temp = calcular_fbd(fck=fck_val, tipo_barra=tipo_bar, posicao_aderencia=pos_aderencia_inf, phi_mm=phi_inf)
                        anc_esc = calcular_comprimento_ancoragem(phi_mm=phi_inf, fyd_mpa=fyd_val, fbd_mpa=res_fbd_temp["fbd"], as_calc=as_alvo, as_ef=as_ef_inf, com_gancho=tem_gancho)
                        
                    fig_long = gerar_grafico_longitudinal(
                        l0_m=l0_m_plot, h_cm=viga_calc.h, cnom_mm=c_nom, t1_cm=t1_cm_plot, t2_cm=t2_cm_plot,
                        detalhe_as=arranjo_as_selecionado, lb_nec_cm=anc_esc["lb_nec_cm"], tem_gancho=tem_gancho
                    )
                    st.pyplot(fig_long, use_container_width=True)

if __name__ == "__main__":
    renderizar_tela()
