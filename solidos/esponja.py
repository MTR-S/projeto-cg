"""
Modelagem da Esponja de Lavar Louça.
Responsável: Matheus
"""

import numpy as np


def criar_esponja(
    largura: float = 3.0,
    altura: float = 1.2,
    profundidade: float = 2.0,
    cor: tuple[float, float, float] = (0.95, 0.82, 0.12),
    cor_fibra: tuple[float, float, float] = (0.12, 0.45, 0.20),
    proporcao_fibra: float = 0.25,
) -> dict:
    """
    Cria a malha triangular de uma esponja de lavar louça com duas camadas:
    a espuma amarela e a manta abrasiva verde (paralelepípedo subdividido).
    
    Vértices e faces orientados de forma anti-horária vista de fora (CCW).
    Normais unitárias apontando para fora.

    Retorna:
        dict no formato padrão do projeto.
    """
    hx = largura / 2.0
    hy = altura / 2.0
    hz = profundidade / 2.0
    y_div = hy - altura * float(proporcao_fibra)

    # 12 vértices:
    # 0..3: base inferior da espuma amarela (y = -hy)
    # 4..7: plano intermediário de junção amarelo/verde (y = y_div)
    # 8..11: topo superior da fibra verde (y = +hy)
    vertices = np.array([
        # Plano inferior (y = -hy)
        [-hx, -hy, -hz],    # 0: traseiro esquerdo
        [ hx, -hy, -hz],    # 1: traseiro direito
        [ hx, -hy,  hz],    # 2: frontal direito
        [-hx, -hy,  hz],    # 3: frontal esquerdo
        # Plano divisor amarelo/verde (y = y_div)
        [-hx, y_div, -hz],  # 4: traseiro esquerdo
        [ hx, y_div, -hz],  # 5: traseiro direito
        [ hx, y_div,  hz],  # 6: frontal direito
        [-hx, y_div,  hz],  # 7: frontal esquerdo
        # Plano superior (y = +hy)
        [-hx,  hy, -hz],    # 8: traseiro esquerdo
        [ hx,  hy, -hz],    # 9: traseiro direito
        [ hx,  hy,  hz],    # 10: frontal direito
        [-hx,  hy,  hz],    # 11: frontal esquerdo
    ], dtype=np.float64)

    # 20 faces triangulares (CCW vista de fora):
    # Primeiras 10 faces (0..9): camada amarela (base + 4 laterais inferiores)
    # Últimas 10 faces (10..19): camada verde (topo + 4 laterais superiores)
    faces = np.array([
        # --- CAMADA AMARELA (inferior) ---
        # Base inferior (y = -hy, normal -Y)
        [0, 1, 2], [0, 2, 3],
        # Traseira inferior (z = -hz, normal -Z)
        [0, 4, 5], [0, 5, 1],
        # Frontal inferior (z = +hz, normal +Z)
        [3, 2, 6], [3, 6, 7],
        # Esquerda inferior (x = -hx, normal -X)
        [0, 3, 7], [0, 7, 4],
        # Direita inferior (x = +hx, normal +X)
        [1, 5, 6], [1, 6, 2],

        # --- CAMADA VERDE (superior) ---
        # Topo superior (y = +hy, normal +Y)
        [8, 11, 10], [8, 10, 9],
        # Traseira superior (z = -hz, normal -Z)
        [4, 8, 9], [4, 9, 5],
        # Frontal superior (z = +hz, normal +Z)
        [7, 6, 10], [7, 10, 11],
        # Esquerda superior (x = -hx, normal -X)
        [4, 7, 11], [4, 11, 8],
        # Direita superior (x = +hx, normal +X)
        [5, 9, 10], [5, 10, 6],
    ], dtype=np.int32)

    # Arestas únicas
    arestas_set = set()
    for f in faces:
        for i in range(3):
            e = tuple(sorted((f[i], f[(i + 1) % 3])))
            arestas_set.add(e)
    arestas = np.array(sorted(list(arestas_set)), dtype=np.int32)

    # Cálculo das normais das faces: cross(v1 - v0, v2 - v0)
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    normais = np.cross(v1 - v0, v2 - v0)
    normas = np.linalg.norm(normais, axis=1, keepdims=True)
    normais_unitarias = normais / np.where(normas == 0, 1.0, normas)

    cores_faces = np.array(
        [cor] * 10 + [cor_fibra] * 10,
        dtype=np.float64,
    )

    return {
        "vertices": vertices,
        "faces": faces,
        "arestas": arestas,
        "normais_faces": normais_unitarias,
        "cor": cor,
        "cores_faces": cores_faces,
        "nome": "esponja",
    }


if __name__ == "__main__":
    import os
    import sys

    esponja = criar_esponja()
    print("Esponja criada com sucesso!")
    print(f" - Vértices: {len(esponja['vertices'])}")
    print(f" - Faces: {len(esponja['faces'])}")
    print(f" - Arestas: {len(esponja['arestas'])}")
    print(f" - Normais: {esponja['normais_faces'].shape}")

    if "--no-plot" not in sys.argv:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        import matplotlib.pyplot as plt  # noqa: F401
        from visualizacao_3d import exibir_solido_interativo

        exibir_solido_interativo(esponja)
