"""
Módulo de Sólidos para o Projeto de Computação Gráfica (2026.2 - IFCE).

Contrato padrão do sólido:
{
    "vertices": np.ndarray,      # (N, 3) float64
    "faces": np.ndarray,         # (M, 3) int32, triângulos com orientação anti-horária (CCW)
    "arestas": np.ndarray,       # (K, 2) int32
    "normais_faces": np.ndarray, # (M, 3) float64, unitárias apontando para fora
    "cor": tuple,                # (r, g, b) no intervalo [0.0, 1.0]
    "nome": str                  # Identificador do sólido
}
"""

from .esponja import criar_esponja
from .queijo import criar_queijo
from .prato import criar_prato
from .boia import criar_boia
from .rolo import criar_rolo
from .visualizacao import validar_solido, plotar_solido

__all__ = [
    "criar_esponja",
    "criar_queijo",
    "criar_prato",
    "criar_boia",
    "criar_rolo",
    "validar_solido",
    "plotar_solido",
]
