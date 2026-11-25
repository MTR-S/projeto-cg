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
    espessura: float = 0.12,
) -> dict:
    """
    Cria a malha triangular fechada de um prato como sólido de revolução 3D.

    Perfil 2D com espessura (fundo externo, parede externa, borda superior,
    parede interna e fundo interno) rotacionado em torno do eixo Y, com
    todas as faces orientadas anti-horariamente (CCW) vistas de fora.

    Retorna:
        dict no formato padrão do projeto.
    """
    if not (0.0 < espessura < altura):
        raise ValueError("espessura deve satisfazer 0 < espessura < altura.")
    if not (0.0 < raio_base < raio_borda):
        raise ValueError("raios devem satisfazer 0 < raio_base < raio_borda.")

    # Raios internos consistentes com a espessura da parede sem auto-interseção
    dr = raio_borda - raio_base
    comp_parede = float(np.hypot(dr, altura))
    desloc_r = espessura * (comp_parede / altura)
    raio_interno_borda = raio_borda - desloc_r
    raio_interno_base = raio_base + (dr / altura) * espessura - desloc_r

    min_raio_base = 0.1 * raio_base
    if raio_interno_base < min_raio_base:
        raio_interno_base = min_raio_base
        raio_interno_borda = min_raio_base + dr * (1.0 - espessura / altura)

    thetas = np.linspace(0, 2 * np.pi, num_fatias, endpoint=False)

    vertices_list = [[0.0, 0.0, 0.0]]  # 0: centro do fundo externo

    # Anel 1: base externa (raio_base, y=0.0)
    for t in thetas:
        vertices_list.append([raio_base * np.cos(t), 0.0, raio_base * np.sin(t)])

    # Anel 2: borda externa superior (raio_borda, y=altura)
    for t in thetas:
        vertices_list.append([raio_borda * np.cos(t), altura, raio_borda * np.sin(t)])

    # Anel 3: borda interna superior (raio_interno_borda, y=altura)
    for t in thetas:
        vertices_list.append([raio_interno_borda * np.cos(t), altura, raio_interno_borda * np.sin(t)])

    # Anel 4: base interna (raio_interno_base, y=espessura)
    for t in thetas:
        vertices_list.append([raio_interno_base * np.cos(t), espessura, raio_interno_base * np.sin(t)])

    # Centro do fundo interno (y=espessura)
    idx_centro_interno = len(vertices_list)
    vertices_list.append([0.0, espessura, 0.0])

    vertices = np.array(vertices_list, dtype=np.float64)
    faces_list = []

    offset_anel1 = 1
    offset_anel2 = 1 + num_fatias
    offset_anel3 = 1 + 2 * num_fatias
    offset_anel4 = 1 + 3 * num_fatias

    # 1. Fundo externo (y = 0.0, normal -Y)
    for i in range(num_fatias):
        next_i = (i + 1) % num_fatias
        p1 = offset_anel1 + i
        p2 = offset_anel1 + next_i
        faces_list.append([0, p1, p2])

    # 2. Parede externa inclinada (entre anel 1 e anel 2, normal radial externa + -Y)
    for i in range(num_fatias):
        next_i = (i + 1) % num_fatias
        b1, b2 = offset_anel1 + i, offset_anel1 + next_i
        t1, t2 = offset_anel2 + i, offset_anel2 + next_i
        faces_list.append([b1, t2, b2])
        faces_list.append([b1, t1, t2])

    # 3. Borda superior (y = altura, entre anel 2 e anel 3, normal +Y)
    for i in range(num_fatias):
        next_i = (i + 1) % num_fatias
        eo1, eo2 = offset_anel2 + i, offset_anel2 + next_i
        ei1, ei2 = offset_anel3 + i, offset_anel3 + next_i
        faces_list.append([eo1, ei1, ei2])
        faces_list.append([eo1, ei2, eo2])

    # 4. Parede interna inclinada (entre anel 3 e anel 4, normal voltada para a cavidade)
    for i in range(num_fatias):
        next_i = (i + 1) % num_fatias
        ei1, ei2 = offset_anel3 + i, offset_anel3 + next_i
        bi1, bi2 = offset_anel4 + i, offset_anel4 + next_i
        faces_list.append([ei1, bi1, bi2])
        faces_list.append([ei1, bi2, ei2])

    # 5. Fundo interno (y = espessura, normal +Y)
    for i in range(num_fatias):
        next_i = (i + 1) % num_fatias
        bi1 = offset_anel4 + i
        bi2 = offset_anel4 + next_i
        faces_list.append([idx_centro_interno, bi2, bi1])

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
    import os
    import sys

    prato = criar_prato()
    print("Prato criado com sucesso!")
    print(f" - Vértices: {len(prato['vertices'])}")
    print(f" - Faces: {len(prato['faces'])}")
    print(f" - Arestas: {len(prato['arestas'])}")
    print(f" - Normais: {prato['normais_faces'].shape}")

    if "--no-plot" not in sys.argv:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        import matplotlib.pyplot as plt  # noqa: F401
        from visualizacao_3d import exibir_solido_interativo

        exibir_solido_interativo(prato)
