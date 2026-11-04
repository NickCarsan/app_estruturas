# src/views/desenho_diagramas.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def gerar_diagramas_blueprint(L: float, q: float, P: float, a: float, res_estatica: dict):
    """
    Gera os diagramas de Esforço Cortante e Momento Fletor utilizando Plotly
    com o tema Blueprint (AutoCAD CAD Mode).
    """
    x = res_estatica["x"]
    V = res_estatica["V"]
    M = res_estatica["M"]

    # Paleta de cores CAD
    c_fundo = "#081018"
    c_grid = "#1a293b"
    c_eixos = "#E0E0E0"
    c_cortante = "#00FFFF" # Ciano
    c_momento = "#FF00FF"  # Magenta

    # Criação da figura com dois subgráficos
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Diagrama de Esforço Cortante (V) [kN]", "Diagrama de Momento Fletor (M) [kN.m]")
    )

    # 1. Diagrama de Cortante
    fig.add_trace(
        go.Scatter(
            x=x, y=V, 
            fill='tozeroy', 
            mode='lines',
            line=dict(color=c_cortante, width=2),
            fillcolor='rgba(0, 255, 255, 0.1)',
            name='Esforço Cortante',
            hovertemplate="x: %{x:.2f} m<br>V: %{y:.2f} kN<extra></extra>"
        ),
        row=1, col=1
    )

    # 2. Diagrama de Momento Fletor
    fig.add_trace(
        go.Scatter(
            x=x, y=M, 
            fill='tozeroy', 
            mode='lines',
            line=dict(color=c_momento, width=2),
            fillcolor='rgba(255, 0, 255, 0.1)',
            name='Momento Fletor',
            hovertemplate="x: %{x:.2f} m<br>M: %{y:.2f} kN.m<extra></extra>"
        ),
        row=2, col=1
    )

    # Configuração de Layout e Tema (Blueprint)
    fig.update_layout(
        paper_bgcolor=c_fundo,
        plot_bgcolor=c_fundo,
        font=dict(color=c_eixos, family="JetBrains Mono, monospace"),
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified"
    )

    # Eixos X (Grelha e Linha Zero)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=c_grid, zeroline=True, zerolinewidth=2, zerolinecolor=c_eixos)
    
    # Eixos Y (Grelha e Linha Zero)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=c_grid, zeroline=True, zerolinewidth=2, zerolinecolor=c_eixos, row=1, col=1)
    
    # Inverter eixo Y do Momento Fletor (Padrão da engenharia estrutural: tração para baixo)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=c_grid, zeroline=True, zerolinewidth=2, zerolinecolor=c_eixos, autorange="reversed", row=2, col=1)

    # Alterar cor dos títulos dos subgráficos para adequar ao tema
    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=14, color="#FFFFFF", family="Inter, sans-serif")

    return fig