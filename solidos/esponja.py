"""
Modelagem da Esponja de Lavar Louça.
Responsável: Matheus
"""

import numpy as np


def criar_esponja(
    largura: float = 3.0,
    altura: float = 1.2,
    profundidade: float = 2.0,
    cor: tuple[float, float, float] = (0.85, 0.85, 0.15),
) -> dict:
    """
    Cria a malha triangular de uma esponja de lavar louça (paralelepípedo).
    
    Vértices e faces orientados de forma anti-horária vista de fora (CCW).
    Normais unitárias apontando para fora.

    Retorna:
        dict no formato padrão do projeto.
    """
    hx = largura / 2.0
    hy = altura / 2.0
    hz = profundidade / 2.0

    # 8 vértices de uma caixa
    vertices = np.array([
        [-hx, -hy, -hz],  # 0
        [ hx, -hy, -hz],  # 1
        [ hx,  hy, -hz],  # 2
        [-hx,  hy, -hz],  # 3
        [-hx, -hy,  hz],  # 4
        [ hx, -hy,  hz],  # 5
        [ hx,  hy,  hz],  # 6
        [-hx,  hy,  hz],  # 7
    ], dtype=np.float64)

    # 12 faces triangulares (CCW vista de fora)
    faces = np.array([
        # Face traseira (z = -hz)
        [0, 2, 1], [0, 3, 2],
        # Face frontal (z = +hz)
        [4, 5, 6], [4, 6, 7],
        # Face esquerda (x = -hx)
        [0, 4, 7], [0, 7, 3],
        # Face direita (x = +hx)
        [1, 2, 6], [1, 6, 5],
        # Face inferior (y = -hy)
        [0, 1, 5], [0, 5, 4],
        # Face superior (y = +hy)
        [3, 7, 6], [3, 6, 2],
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

    return {
        "vertices": vertices,
        "faces": faces,
        "arestas": arestas,
        "normais_faces": normais_unitarias,
        "cor": cor,
        "nome": "esponja",
    }


if __name__ == "__main__":
    esponja = criar_esponja()
    print(f"Esponja criada com sucesso!")
    print(f" - Vértices: {len(esponja['vertices'])}")
    print(f" - Faces: {len(esponja['faces'])}")
    print(f" - Arestas: {len(esponja['arestas'])}")
    print(f" - Normais: {esponja['normais_faces'].shape}")
