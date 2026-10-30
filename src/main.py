# src/main.py
import sys
from pathlib import Path

# Adiciona a raiz do projeto ao PYTHONPATH
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

from src.views.interface import renderizar_tela

if __name__ == "__main__":
    renderizar_tela()