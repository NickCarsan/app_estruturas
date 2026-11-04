# src/controllers/estatica.py
import numpy as np

def calcular_estatica_viga(L: float, q: float, P: float, a: float):
    """
    Calcula as reações e os diagramas de esforço cortante e momento fletor
    para uma viga bi-apoiada com carga distribuída (q) e pontual (P).
    """
    # Equações de Equilíbrio (Soma M = 0, Soma Fy = 0)
    Rb = (q * (L**2) / 2.0 + P * a) / L
    Ra = (q * L) + P - Rb

    # Discretização do vão para gerar os gráficos
    x = np.linspace(0, L, 500)
    V = np.zeros_like(x)
    M = np.zeros_like(x)

    for i, xi in enumerate(x):
        # Esforço Cortante V(x)
        V[i] = Ra - q * xi - (P if xi >= a else 0)
        # Momento Fletor M(x)
        M[i] = Ra * xi - q * (xi**2) / 2.0 - (P * (xi - a) if xi >= a else 0)

    # Identificação dos pontos de máximo
    idx_max = np.argmax(M)
    M_max = M[idx_max]
    x_max = x[idx_max]

    return {
        "Ra": Ra, "Rb": Rb,
        "x": x, "V": V, "M": M,
        "M_max": M_max, "x_max": x_max
    }