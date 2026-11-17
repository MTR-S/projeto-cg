"""
Modelagem do Prato (Sólido de Revolução).
Responsável: Miller
"""

import numpy as np


def criar_prato(
    raio_base: float = 1.2,
    raio_borda: float = 2.4,
    altura: float = 0.5,
    num_fatias: int = 24,
    cor: tuple[float, float, float] = (0.92, 0.92, 0.95),
) -> dict:
    """
    Cria a malha triangular de um prato como sólido de revolução.
    
    Perfil 2D (fundo e borda) rotacionado em torno do eixo Y.
    
    Retorna:
        dict no formato padrão do projeto.
    """
    # Perfil: centro (0, 0), borda do fundo (raio_base, 0), aba superior (raio_borda, altura)
    thetas = np.linspace(0, 2 * np.pi, num_fatias, endpoint=False)
    
    vertices_list = [[0.0, 0.0, 0.0]]  # Vértice central do fundo (índice 0)
    
    # Anel 1: base (raio_base, y=0.0) -> índices 1 .. num_fatias
    for t in thetas:
        vertices_list.append([raio_base * np.cos(t), 0.0, raio_base * np.sin(t)])
        
    # Anel 2: borda superior (raio_borda, y=altura) -> índices (num_fatias + 1) .. (2 * num_fatias)
    for t in thetas:
        vertices_list.append([raio_borda * np.cos(t), altura, raio_borda * np.sin(t)])
        
    vertices = np.array(vertices_list, dtype=np.float64)
    faces_list = []
    
    # Fundo do prato (triângulos do centro para o anel da base)
    for i in range(num_fatias):
        next_i = (i + 1) % num_fatias
        # Índices 1-based para o anel 1
        p1 = 1 + i
        p2 = 1 + next_i
        faces_list.append([0, p2, p1])  # Face apontando para baixo (normal -y)
        
    # Borda inclinada (quads triangulados entre anel 1 e anel 2)
    offset_anel2 = num_fatias + 1
    for i in range(num_fatias):
        next_i = (i + 1) % num_fatias
        b1 = 1 + i
        b2 = 1 + next_i
        t1 = offset_anel2 + i
        t2 = offset_anel2 + next_i
        
        # Triangulação do anel
        faces_list.append([b1, b2, t2])
        faces_list.append([b1, t2, t1])
        
    faces = np.array(faces_list, dtype=np.int32)
    
    # Arestas únicas
    arestas_set = set()
    for f in faces:
        for i in range(3):
            e = tuple(sorted((f[i], f[(i + 1) % 3])))
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
        "nome": "prato",
    }


if __name__ == "__main__":
    prato = criar_prato()
    print(f"Prato criado com sucesso!")
    print(f" - Vértices: {len(prato['vertices'])}")
    print(f" - Faces: {len(prato['faces'])}")
    print(f" - Arestas: {len(prato['arestas'])}")
    print(f" - Normais: {prato['normais_faces'].shape}")
