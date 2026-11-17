"""
Modelagem do Rolo de Massa (Cilindro com Hastes).
Responsável: Miller
"""

import numpy as np


def criar_rolo(
    raio_rolo: float = 0.8,
    comp_rolo: float = 3.0,
    raio_haste: float = 0.25,
    comp_haste: float = 1.0,
    fatias: int = 20,
    cor: tuple[float, float, float] = (0.76, 0.60, 0.42),
) -> dict:
    """
    Cria a malha triangular de um rolo de massa alinhado ao eixo X.
    
    Composto por:
    - Cilindro central (comprimento comp_rolo, raio raio_rolo)
    - Haste esquerda (comprimento comp_haste, raio raio_haste)
    - Haste direita (comprimento comp_haste, raio raio_haste)
    
    Retorna:
        dict no formato padrão do projeto.
    """
    thetas = np.linspace(0, 2 * np.pi, fatias, endpoint=False)
    
    # Seções ao longo de X:
    # x0: ponta esquerda da haste esquerda: -comp_rolo/2 - comp_haste
    # x1: junção haste esquerda / rolo: -comp_rolo/2
    # x2: junção rolo / haste direita: +comp_rolo/2
    # x3: ponta direita da haste direita: +comp_rolo/2 + comp_haste
    x0 = -comp_rolo / 2.0 - comp_haste
    x1 = -comp_rolo / 2.0
    x2 =  comp_rolo / 2.0
    x3 =  comp_rolo / 2.0 + comp_haste

    vertices_list = []
    
    # Tampa da ponta esquerda (vértice central índice 0)
    vertices_list.append([x0, 0.0, 0.0])
    
    # Anel 0: raio_haste em x0 (índices 1 .. fatias)
    for t in thetas:
        vertices_list.append([x0, raio_haste * np.cos(t), raio_haste * np.sin(t)])
        
    # Anel 1: raio_haste em x1 (índices fatias+1 .. 2*fatias)
    for t in thetas:
        vertices_list.append([x1, raio_haste * np.cos(t), raio_haste * np.sin(t)])
        
    # Anel 2: raio_rolo em x1 (índices 2*fatias+1 .. 3*fatias)
    for t in thetas:
        vertices_list.append([x1, raio_rolo * np.cos(t), raio_rolo * np.sin(t)])
        
    # Anel 3: raio_rolo em x2 (índices 3*fatias+1 .. 4*fatias)
    for t in thetas:
        vertices_list.append([x2, raio_rolo * np.cos(t), raio_rolo * np.sin(t)])
        
    # Anel 4: raio_haste em x2 (índices 4*fatias+1 .. 5*fatias)
    for t in thetas:
        vertices_list.append([x2, raio_haste * np.cos(t), raio_haste * np.sin(t)])
        
    # Anel 5: raio_haste em x3 (índices 5*fatias+1 .. 6*fatias)
    for t in thetas:
        vertices_list.append([x3, raio_haste * np.cos(t), raio_haste * np.sin(t)])
        
    # Tampa da ponta direita (vértice central índice 6*fatias + 1)
    vertices_list.append([x3, 0.0, 0.0])
    idx_tampa_dir = len(vertices_list) - 1

    vertices = np.array(vertices_list, dtype=np.float64)
    faces_list = []

    def anel_idx(num_anel):
        return 1 + num_anel * fatias

    # Tampa esquerda (leque ligando centro 0 ao anel 0)
    for i in range(fatias):
        next_i = (i + 1) % fatias
        faces_list.append([0, anel_idx(0) + next_i, anel_idx(0) + i])

    # Haste esquerda: ligando anel 0 ao anel 1
    for i in range(fatias):
        next_i = (i + 1) % fatias
        a0_1, a0_2 = anel_idx(0) + i, anel_idx(0) + next_i
        a1_1, a1_2 = anel_idx(1) + i, anel_idx(1) + next_i
        faces_list.append([a0_1, a0_2, a1_2])
        faces_list.append([a0_1, a1_2, a1_1])

    # Degrau esquerdo: ligando anel 1 ao anel 2 (em x1)
    for i in range(fatias):
        next_i = (i + 1) % fatias
        a1_1, a1_2 = anel_idx(1) + i, anel_idx(1) + next_i
        a2_1, a2_2 = anel_idx(2) + i, anel_idx(2) + next_i
        faces_list.append([a1_1, a2_1, a2_2])
        faces_list.append([a1_1, a2_2, a1_2])

    # Corpo principal: ligando anel 2 ao anel 3
    for i in range(fatias):
        next_i = (i + 1) % fatias
        a2_1, a2_2 = anel_idx(2) + i, anel_idx(2) + next_i
        a3_1, a3_2 = anel_idx(3) + i, anel_idx(3) + next_i
        faces_list.append([a2_1, a2_2, a3_2])
        faces_list.append([a2_1, a3_2, a3_1])

    # Degrau direito: ligando anel 3 ao anel 4 (em x2)
    for i in range(fatias):
        next_i = (i + 1) % fatias
        a3_1, a3_2 = anel_idx(3) + i, anel_idx(3) + next_i
        a4_1, a4_2 = anel_idx(4) + i, anel_idx(4) + next_i
        faces_list.append([a3_1, a4_2, a4_1])
        faces_list.append([a3_1, a3_2, a4_2])

    # Haste direita: ligando anel 4 ao anel 5
    for i in range(fatias):
        next_i = (i + 1) % fatias
        a4_1, a4_2 = anel_idx(4) + i, anel_idx(4) + next_i
        a5_1, a5_2 = anel_idx(5) + i, anel_idx(5) + next_i
        faces_list.append([a4_1, a4_2, a5_2])
        faces_list.append([a4_1, a5_2, a5_1])

    # Tampa direita (leque ligando centro idx_tampa_dir ao anel 5)
    for i in range(fatias):
        next_i = (i + 1) % fatias
        faces_list.append([idx_tampa_dir, anel_idx(5) + i, anel_idx(5) + next_i])

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
        "nome": "rolo",
    }


if __name__ == "__main__":
    rolo = criar_rolo()
    print(f"Rolo criado com sucesso!")
    print(f" - Vértices: {len(rolo['vertices'])}")
    print(f" - Faces: {len(rolo['faces'])}")
    print(f" - Arestas: {len(rolo['arestas'])}")
    print(f" - Normais: {rolo['normais_faces'].shape}")
