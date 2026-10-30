# 🏗️ Dimensionamento e Detalhamento de Vigas de Concreto Armado

Aplicativo web interativo desenvolvido em **Python** e **Streamlit** para dimensionamento e detalhamento técnico de vigas de concreto armado submetidas à flexão simples e dupla, em total conformidade com os critérios da **ABNT NBR 6118**.

---

## 📌 Funcionalidades

- **Materiais e Durabilidade:**
  - Classes de concreto de $f_{ck} = 20\text{ MPa}$ até $90\text{ MPa}$ com correção automática dos parâmetros $\alpha_c$ e $\lambda$ da parábola-retângulo.
  - Aços longitudinais CA-50 e CA-60.
  - Cobrimentos nominais ($c_{nom}$) definidos automaticamente pela Classe de Agressividade Ambiental (CAA I a IV).
  - Determinação rigorosa da altura útil estimada ($d$) e do espaçamento entre barras com base no diâmetro máximo do agregado ($d_{\text{máx}}$).

- **Geometria da Seção:**
  - Seções **Retangulares** e **Seções T** (com triagem analítica entre *T Falso* e *T Verdadeiro* baseada na profundidade da linha neutra $y \le h_f$ ou $y > h_f$).
  - Suporte à análise de vigas contínuas e seções em T invertido (considerando aba comprimida em apoios e desprezada em vãos tracionados).

- **Modos de Análise de Esforços:**
  - Inserção direta do Momento Fletor Característico ($M_k$).
  - Cálculo automático por carregamento distribuído ($q_k$) e vão livre ($L$) para vigas bi-apoiadas.
  - **Cálculo Inverso:** Determinação da capacidade resistente máxima da seção ($M_{d,\text{limite}}$) no limite de deformação do concreto e do aço ($\beta_{x,\text{lim}} = 0,45$).

- **Dimensionamento e Detalhamento Automático:**
  - Transição contínua entre Armadura Simples e Armadura Dupla (com cálculo da tensão de compressão $\sigma'_s$ no aço).
  - Sugestão de arranjos comerciais de barras com distribuição em camadas e cálculo exato do baricentro ($CG$) para determinação da altura útil real ($d_{real}$).
  - Desenho técnico proporcional da seção transversal em **Matplotlib**, incluindo estribos com dobras, círculos de barras preenchidos, cotas normativas e linhas de chamada laterais limpas.

# 🏗️ Dimensionamento e Detalhamento de Vigas de Concreto Armado

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://appestruturas-nhylzc8h4uc44gaez7xotb.streamlit.app/)

> 🌐 **Acesse a aplicação online:** [https://appestruturas-nhylzc8h4uc44gaez7xotb.streamlit.app/](https://appestruturas-nhylzc8h4uc44gaez7xotb.streamlit.app/)
---

## 📁 Estrutura do Projeto

O projeto segue a arquitetura **MVC (Model-View-Controller)** para garantir modularidade e manutenibilidade:

```text
app_estruturas/
│
├── .venv/                      # Ambiente virtual isolado
├── .gitignore                  # Arquivos ignorados pelo Git
├── README.md                   # Documentação do projeto
├── requirements.txt            # Dependências e bibliotecas
│
└── src/
    ├── __init__.py
    ├── main.py                 # Ponto de entrada do sistema
    ├── config.py               # Constantes e coeficientes da NBR 6118
    │
    ├── models/                 # Modelagem dos dados físicos
    │   ├── materiais.py        # Classes Concreto (fcd, fctm) e Aco (fyd)
    │   └── elementos.py        # Classes VigaRetangular e VigaT
    │
    ├── controllers/            # Motores de cálculo e lógica estrutural
    │   ├── flexao.py           # Equacionamento de flexão simples, dupla e vigas T
    │   └── detalhamento.py     # Arranjos comerciais e espaçamentos normativos
    │
    └── views/                  # Interface gráfica e desenhos técnicos
        ├── interface.py        # Interface web construída em Streamlit
        └── desenho_secao.py    # Renderização vetorial da seção transversal