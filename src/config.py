# src/config.py

# Coeficientes de ponderação das resistências (ELU)
GAMA_C = 1.4   
GAMA_S = 1.15  

# Classes de concreto usuais (fck em MPa) cobrindo Grupo I e II da NBR 6118
CLASSES_CONCRETO = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]

# Bitolas comerciais de aço (diâmetro em mm)
BITOLAS_ACO = [5.0, 6.3, 8.0, 10.0, 12.5, 16.0, 20.0, 25.0, 32.0]

# Cobrimentos nominais para Vigas / Pilares conforme NBR 6118 (Tabela 7.2) em mm
COBRIMENTOS_VIGA = {
    "CAA I (Fraca - 25 mm)": 25.0,
    "CAA II (Moderada - 30 mm)": 30.0,
    "CAA III (Forte - 40 mm)": 40.0,
    "CAA IV (Muito Forte - 50 mm)": 50.0
}