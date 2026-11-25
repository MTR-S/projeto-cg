"""
Modelagem da Boia de Piscina (Toro).
Responsável: Vinicius

IDEIA GERAL
-----------
Um toro é um círculo pequeno (raio r) girado em torno de um eixo (aqui, o eixo y).
O centro do círculo pequeno fica a uma distância R desse eixo.

    R = "tamanho" da boia (distância do eixo até o meio do tubo)
    r = "grossura" da boia (raio do tubo)

Dois ângulos descrevem qualquer ponto da superfície:
    v : posição ao redor do círculo pequeno (0 a 2π)
    u : quanto o círculo pequeno foi girado em torno do eixo y (0 a 2π)

PASSO 1. Ponto do círculo pequeno, ainda no plano xy, com centro em (R, 0, 0):
    P(v) = (R + r·cos v,  r·sin v,  0)

PASSO 2. Gira esse ponto por um ângulo u em torno do eixo y (matriz Ry):
         [  cos u   0   sin u ]
    Ry = [    0     1     0   ]
         [ -sin u   0   cos u ]

    Ry · P(v) = ( (R + r·cos v)·cos u,
                   r·sin v,
                  -(R + r·cos v)·sin u )

Essa é a fórmula de cada vértice da boia.
"""

import numpy as np


def ponto_do_toro(u: float, v: float, R: float, r: float) -> list[float]:
    """Aplica a fórmula do toro: ponto do círculo pequeno girado em torno do eixo y."""
    a = R + r * np.cos(v)          # distância do ponto até o eixo y
    return [a * np.cos(u), r * np.sin(v), -a * np.sin(u)]


def criar_boia(
    R: float = 2.0,
    r: float = 0.7,
    n_u: int = 24,
    n_v: int = 16,
    cor: tuple[float, float, float] = (0.1, 0.65, 0.95),
) -> dict:
    """
    Cria a malha de triângulos da boia (toro).

    Parâmetros:
        R   : distância do eixo y até o centro do tubo
        r   : raio do tubo (r < R, senão o toro se cruza)
        n_u : quantas posições do círculo pequeno ao redor do eixo (divisões em u)
        n_v : quantos pontos em cada círculo pequeno (divisões em v)
        cor : cor RGB da boia, valores entre 0 e 1

    Retorna:
        dicionário no formato padrão do projeto.
    """
    if r >= R:
        raise ValueError("r precisa ser menor que R, senão o toro se cruza.")

    # ------------------------------------------------------------------
    # 1) VÉRTICES
    # Amostramos os ângulos SEM repetir o 2π (endpoint=False), porque o
    # ângulo 2π é o mesmo ponto que 0. O "fechamento" é feito nas faces.
    # ------------------------------------------------------------------
    us = np.linspace(0, 2 * np.pi, n_u, endpoint=False)
    vs = np.linspace(0, 2 * np.pi, n_v, endpoint=False)

    vertices = []
    for u in us:                 # cada u é um círculo pequeno (um "anel")
        for v in vs:             # cada v é um ponto desse anel
            vertices.append(ponto_do_toro(u, v, R, r))
    vertices = np.array(vertices, dtype=np.float64)

    # O vértice (i, j) da grade, com i para u e j para v, fica na posição:
    def indice(i: int, j: int) -> int:
        # O "% n" faz o último anel se ligar ao primeiro (fecha a boia)
        return (i % n_u) * n_v + (j % n_v)

    # ------------------------------------------------------------------
    # 2) FACES
    # A grade (u, v) vira uma colcha de quadradinhos. Cada quadradinho:
    #
    #      p01 ---- p11        p00 = (i,   j)
    #       |     /  |         p10 = (i+1, j)
    #       |   /    |         p11 = (i+1, j+1)
    #      p00 ---- p10        p01 = (i,   j+1)
    #
    # é cortado na diagonal p00–p11 em 2 triângulos.
    # A ordem [p00, p10, p11] foi escolhida para a normal sair PARA FORA:
    # andar em u e depois em v, com a regra da mão direita, aponta para
    # fora do tubo (conferido no teste do final do arquivo).
    # ------------------------------------------------------------------
    faces = []
    for i in range(n_u):
        for j in range(n_v):
            p00 = indice(i, j)
            p10 = indice(i + 1, j)
            p11 = indice(i + 1, j + 1)
            p01 = indice(i, j + 1)
            faces.append([p00, p10, p11])
            faces.append([p00, p11, p01])
    faces = np.array(faces, dtype=np.int32)

    # ------------------------------------------------------------------
    # 3) ARESTAS (cada lado de triângulo, sem repetir)
    # Cada aresta aparece em 2 triângulos; ordenar o par (menor, maior)
    # faz as duas aparições virarem a mesma e o set remove a repetida.
    # ------------------------------------------------------------------
    arestas = set()
    for a, b, c in faces:
        for e in ((a, b), (b, c), (c, a)):
            arestas.add(tuple(sorted(e)))
    arestas = np.array(sorted(arestas), dtype=np.int32)

    # ------------------------------------------------------------------
    # 4) NORMAIS DAS FACES
    # n = (v1 - v0) x (v2 - v0), dividido pelo próprio tamanho (unitária).
    # ------------------------------------------------------------------
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    normais = np.cross(v1 - v0, v2 - v0)
    normais /= np.linalg.norm(normais, axis=1, keepdims=True)

    return {
        "vertices": vertices,
        "faces": faces,
        "arestas": arestas,
        "normais_faces": normais,
        "cor": cor,
        "nome": "boia",
    }


def verificar_boia(boia: dict, R: float) -> dict:
    """
    Testes que provam que a malha está correta (bons para o relatório):
      - fechada: toda aresta é compartilhada por exatamente 2 triângulos
      - Euler: V - E + F = 0 para um toro (superfície com um "furo")
      - normais para fora: a normal de cada face aponta para longe do
        centro do tubo (o ponto do círculo de raio R mais próximo da face)
    """
    V, F, N = boia["vertices"], boia["faces"], boia["normais_faces"]
    pares = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    _, contagem = np.unique(pares, axis=0, return_counts=True)

    centroides = V[F].mean(axis=1)
    # centro do tubo mais próximo: projeta o centróide no plano xz e leva a distância R
    xz = centroides[:, [0, 2]]
    xz = xz / np.linalg.norm(xz, axis=1, keepdims=True) * R
    centro_tubo = np.column_stack([xz[:, 0], np.zeros(len(F)), xz[:, 1]])
    para_fora = np.einsum("ij,ij->i", N, centroides - centro_tubo) > 0

    return {
        "vertices": len(V),
        "arestas": len(boia["arestas"]),
        "faces": len(F),
        "euler": len(V) - len(boia["arestas"]) + len(F),
        "fechada": bool(np.all(contagem == 2)),
        "normais_para_fora": f"{para_fora.mean():.0%}",
    }


if __name__ == "__main__":
    import os
    import sys

    R, r = 2.0, 0.7
    boia = criar_boia(R=R, r=r)
    print("Boia criada com sucesso!")
    for chave, valor in verificar_boia(boia, R).items():
        print(f" - {chave:18s}: {valor}")

    if "--no-plot" not in sys.argv:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        import matplotlib.pyplot as plt  # noqa: F401
        from visualizacao_3d import exibir_solido_interativo

        exibir_solido_interativo(boia)
