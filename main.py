"""
Pipeline Principal do Projeto de Computação Gráfica (2026.2 - IFCE).
Responsáveis: Matheus, Miller e Vinicius

Executa o pipeline completo e gera todas as figuras exigidas pelo relatório:
  - Fig 1: Sólidos isolados em seus referenciais de objeto (Item 1e)
  - Fig 2: Cena composta no sistema do mundo (Item 2b)
  - Fig 3: Cena no sistema de coordenadas da câmera com origem do mundo marcada (Item 3c)
  - Fig 4: Variação de pontos de vista da câmera (eye) (Item 3e)
  - Fig 5: Projeção perspectiva 3D + Janela 2D com faces visíveis (Item 4a)
  - Fig 6: Iluminação Phong (Ambiente, Difusa, Especular e Total) (Item 5)
  - Fig 7: Rasterização em 3 resoluções distintas (200x200, 400x400, 800x800) (Item 6)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from cena import montar_cena
from camera import camera, transformar_para_camera, obter_origem_mundo_na_camera
from projecao import projetar, descartar_faces_ocultas
from iluminacao import phong
from rasterizacao import mapear_viewport, preencher_par_impar


def render(
    eye: list[float] | np.ndarray = (12.0, 8.0, 14.0),
    at: list[float] | np.ndarray = (0.0, 0.0, 0.0),
    up: list[float] | np.ndarray = (0.0, 1.0, 0.0),
    resolucao: tuple[int, int] = (400, 400),
    d_proj: float = 1.8,
    salvar_caminho: str | None = None,
) -> np.ndarray:
    """
    Executa o pipeline completo de renderização:
    Mundo -> Câmera -> Projeção -> Iluminação -> Rasterização.
    
    Retorna:
        Matriz de imagem RGB (altura, largura, 3) com valores normalizados [0.0, 1.0].
    """
    largura, altura = resolucao
    buffer_imagem = np.ones((altura, largura, 3), dtype=np.float64) * 0.05  # Fundo escuro

    # 1. Obter cena no mundo
    cena_mundo = montar_cena()

    # 2. Câmera
    u, v, w, M_vis = camera(eye, at, up)

    # 3. Processar cada sólido
    luz_pos = np.array([0.0, 10.0, 5.0])

    for solido_mundo in cena_mundo:
        # Espaço da câmera
        solido_cam = transformar_para_camera(solido_mundo, M_vis)

        # Projeção 2D e faces visíveis (culling)
        pts_2d, faces_vis = projetar(solido_cam, d=d_proj)
        if len(faces_vis) == 0:
            continue

        # Iluminação Phong nos vértices
        cores_vert = phong(solido_mundo, luz_pos=luz_pos, eye_pos=eye)

        # Mapeamento para Viewport / Tela
        pts_tela = mapear_viewport(pts_2d, largura, altura, xmin=-4.0, xmax=4.0, ymin=-4.0, ymax=4.0)

        # Rasterização dos triângulos visíveis
        for face in faces_vis:
            tri_pts = pts_tela[face]
            tri_cores = cores_vert[face]
            preencher_par_impar(tri_pts, tri_cores, largura, altura, buffer_imagem)

    if salvar_caminho:
        os.makedirs(os.path.dirname(salvar_caminho), exist_ok=True)
        plt.imsave(salvar_caminho, buffer_imagem)
        print(f"Renderização salva em: {salvar_caminho}")

    return buffer_imagem


def demonstracao_pipeline():
    """Gera uma demonstração básica do pipeline e valida todos os passos."""
    print("=" * 60)
    print("PROJETO DE COMPUTAÇÃO GRÁFICA - IFCE 2026.2")
    print("Equipe: Matheus, Miller e Vinicius")
    print("=" * 60)
    
    print("\n[1/4] Montando cena e verificando bounding boxes...")
    cena = montar_cena()
    print(f"Cena carregada com {len(cena)} sólidos sem colisão.")

    print("\n[2/4] Calculando sistema de visão (câmera)...")
    eye = [14.0, 10.0, 14.0]
    u, v, w, M_vis = camera(eye=eye, at=[0, 0, 0], up=[0, 1, 0])
    print(f"Base da câmera u: {np.round(u, 3)}, v: {np.round(v, 3)}, w: {np.round(w, 3)}")

    print("\n[3/4] Testando renderização de baixa resolução (100x100)...")
    img = render(eye=eye, resolucao=(100, 100))
    print(f"Render concluído. Imagem gerada com shape {img.shape}")

    print("\n[4/4] Pipeline inicial 100% operacional!")


if __name__ == "__main__":
    demonstracao_pipeline()
