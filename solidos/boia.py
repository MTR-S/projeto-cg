"""
Modelagem da Boia de Piscina (Toro Paramétrico).
Responsável: Vinicius
"""

import numpy as np


def criar_boia(
    R: float = 2.0,
    r: float = 0.7,
    n_u: int = 24,
    n_v: int = 16,
    cor: tuple[float, float, float] = (0.1, 0.65, 0.95),
) -> dict:
    """
    Cria a malha triangular de uma boia de piscina (toro).
    
    Parametrização:
        x = (R + r * cos(v)) * cos(u)
        y = r * sin(v)
        z = (R + r * cos(v)) * sin(u)
    com u em [0, 2pi) e v em [0, 2pi).
    
    Retorna:
        dict no formato padrão do projeto.
    """
    u = np.linspace(0, 2 * np.pi, n_u, endpoint=False)
    v = np.linspace(0, 2 * np.pi, n_v, endpoint=False)

    vertices_list = []
    # Grid de vértices: linha i (u), coluna j (v)
    for i in range(n_u):
        for j in range(n_v):
            ui = u[i]
            vj = v[j]
            x = (R + r * np.cos(vj)) * np.cos(ui)
            y = r * np.sin(vj)
            z = (R + r * np.cos(vj)) * np.sin(ui)
            vertices_list.append([x, y, z])

    vertices = np.array(vertices_list, dtype=np.float64)

    # Triangulação da grade toroidal com fechamento em ambas as direções
    faces_list = []
    for i in range(n_u):
        next_i = (i + 1) % n_u
        for j in range(n_v):
            next_j = (j + 1) % n_v

            # 4 vértices do quad no grid
            p00 = i * n_v + j
            p10 = next_i * n_v + j
            p11 = next_i * n_v + next_j
            p01 = i * n_v + next_j

            # 2 triângulos com orientação externa (CCW)
            faces_list.append([p00, p11, p10])
            faces_list.append([p00, p01, p11])

    faces = np.array(faces_list, dtype=np.int32)

    # Arestas únicas
    arestas_set = set()
    for f in faces:
        for k in range(3):
            e = tuple(sorted((f[k], f[(k + 1) % 3])))
            arestas_set.add(e)
    arestas = np.array(sorted(list(arestas_set)), dtype=np.int32)

    # Normais das faces
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
        "nome": "boia",
    }


if __name__ == "__main__":
    boia = criar_boia()
    print(f"Boia criada com sucesso!")
    print(f" - Vértices: {len(boia['vertices'])}")
    print(f" - Faces: {len(boia['faces'])}")
    print(f" - Arestas: {len(boia['arestas'])}")
    print(f" - Normais: {boia['normais_faces'].shape}")
