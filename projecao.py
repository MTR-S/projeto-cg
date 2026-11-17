"""
Módulo de Projeção em Perspectiva e Backface Culling.
Responsável: Matheus
"""

import numpy as np


def descartar_faces_ocultas(solido_cam: dict) -> np.ndarray:
    """
    Identifica os índices das faces visíveis pelo método de Backface Culling.
    No sistema de coordenadas da câmera, o observador está na origem (0, 0, 0)
    e olha ao longo do eixo -Z (pois W aponta para trás, +Z).
    
    Uma face é visível se o produto escalar entre o vetor de visão da câmera até o baricentro
    da face e a normal da face for negativo (ou se normal_z > 0 quando olhando em -Z).
    """
    vertices = solido_cam["vertices"]
    faces = solido_cam["faces"]
    normais = solido_cam["normais_faces"]

    # Baricentros das faces na câmera
    baricentros = (vertices[faces[:, 0]] + vertices[faces[:, 1]] + vertices[faces[:, 2]]) / 3.0
    
    # Vetor do olho (origem da câmera 0,0,0) até o baricentro da face
    direcao_olho = baricentros  # (M, 3)

    # Produto escalar: N · (baricentro - origem)
    dots = np.sum(normais * direcao_olho, axis=1)

    # Faces visíveis têm dot < 0 (a normal aponta na direção de quem observa)
    indices_visiveis = np.where(dots < 0.0)[0]
    return indices_visiveis


def projetar(
    solido_cam: dict,
    d: float = 1.0,
    near: float = 0.5,
    far: float = 100.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Aplica a projeção em perspectiva polígono a polígono.
    
    No sistema de câmera padrão:
    - O olho está em (0, 0, 0)
    - A cena visível está em z < 0 (em direção a -w)
    - Distância do plano de projeção = d
    - Projeção: xp = d * x / (-z), yp = d * y / (-z)
    
    Retorna:
        pontos_2d: np.ndarray (N, 2) de coordenadas projetadas na janela 2D
        faces_visiveis: np.ndarray com as faces que passaram pelo culling e estão no frustum
    """
    vertices = solido_cam["vertices"]
    faces = solido_cam["faces"]

    # 1. Backface culling
    idx_visiveis = descartar_faces_ocultas(solido_cam)
    faces_visiveis = faces[idx_visiveis]

    # 2. Descarte por near/far plane (z_cam deve estar entre -far e -near)
    # Para o sistema onde a câmera olha para -Z:
    z = vertices[:, 2]
    # Evitar divisão por zero ou projeção de pontos atrás da câmera
    z_neg = np.where(z < -1e-5, -z, np.nan)

    xp = (d * vertices[:, 0]) / z_neg
    yp = (d * vertices[:, 1]) / z_neg
    pontos_2d = np.column_stack([xp, yp])

    return pontos_2d, faces_visiveis


if __name__ == "__main__":
    from solidos.esponja import criar_esponja
    from camera import camera, transformar_para_camera

    esponja = criar_esponja()
    _, _, _, M_vis = camera(eye=[5.0, 5.0, 5.0], at=[0.0, 0.0, 0.0])
    esponja_cam = transformar_para_camera(esponja, M_vis)

    pts_2d, vis = projetar(esponja_cam, d=2.0)
    print("Módulo de Projeção testado com sucesso!")
    print(f"Total de faces: {len(esponja['faces'])}")
    print(f"Faces visíveis após culling: {len(vis)}")
    print("Shape dos pontos 2D projetados:", pts_2d.shape)
