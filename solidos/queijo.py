"""
Modelagem da Fatia de Queijo (Cunha / Prisma Triangular).
Responsável: Matheus
"""

import numpy as np


def criar_queijo(
    raio: float = 2.5,
    angulo_graus: float = 45.0,
    altura: float = 1.2,
    cor: tuple[float, float, float] = (1.0, 0.75, 0.0),
) -> dict:
    """
    Cria a malha triangular de uma fatia de queijo (prisma em cunha).
    
    Retorna:
        dict no formato padrão do projeto.
    """
    rad = np.radians(angulo_graus)
    hy = altura / 2.0

    # Vértices da base inferior (y = -hy) e superior (y = +hy)
    # 0, 3: vértice do centro (origem)
    # 1, 4: ponto no raio no ângulo 0
    # 2, 5: ponto no raio no ângulo theta
    x1 = raio
    z1 = 0.0
    x2 = raio * np.cos(rad)
    z2 = raio * np.sin(rad)

    vertices = np.array([
        # Base inferior (y = -hy)
        [0.0, -hy, 0.0],  # 0
        [ x1, -hy,  z1],  # 1
        [ x2, -hy,  z2],  # 2
        # Base superior (y = +hy)
        [0.0,  hy, 0.0],  # 3
        [ x1,  hy,  z1],  # 4
        [ x2,  hy,  z2],  # 5
    ], dtype=np.float64)

    # Faces triangulares orientadas para fora (CCW vista de fora)
    faces = np.array([
        # Base inferior (aponta para baixo, normal -y)
        [0, 1, 2],
        # Base superior (aponta para cima, normal +y)
        [3, 5, 4],
        # Lateral reta 1 (no plano z=0, normal -z)
        [0, 4, 1], [0, 3, 4],
        # Lateral reta 2 (plano inclinado pelo ângulo theta)
        [0, 2, 5], [0, 5, 3],
        # Face curva/externa (arco frontal)
        [1, 5, 2], [1, 4, 5],
    ], dtype=np.int32)

    # Arestas únicas
    arestas_set = set()
    for f in faces:
        for i in range(3):
            e = tuple(sorted((f[i], f[(i + 1) % 3])))
            arestas_set.add(e)
    arestas = np.array(sorted(list(arestas_set)), dtype=np.int32)

    # Cálculo das normais das faces
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
        "nome": "queijo",
    }


if __name__ == "__main__":
    from visualizacao import validar_solido, plotar_solido
    
    # 1. Cria o sólido
    queijo = criar_queijo()
    
    # 2. Executa a bateria de testes matemáticos
    relatorio = validar_solido(queijo)
    
    # 3. Exibe o plot 3D interativo no sistema do objeto (Item 1e)
    plotar_solido(queijo, mostrar_normais=True, escala_normais=0.6, salvar_caminho="outputs/fig_1_queijo.png")
