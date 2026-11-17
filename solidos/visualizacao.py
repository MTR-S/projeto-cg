"""
Módulo de Validação Geométrica e Visualização 3D de Sólidos.
Responsável: Matheus (Compartilhado com toda a equipe)
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def validar_solido(solido: dict, verbose: bool = True) -> dict:
    """
    Executa testes matemáticos rigorosos para verificar a consistência do sólido:
    1. Existência e shapes das chaves obrigatórias.
    2. Validade dos índices das faces e arestas.
    3. Normais unitárias (norma = 1.0).
    4. Normais apontando para fora (produto escalar com o vetor saindo do centroide).
    """
    nome = solido.get("nome", "desconhecido")
    vertices = solido.get("vertices")
    faces = solido.get("faces")
    arestas = solido.get("arestas")
    normais = solido.get("normais_faces")

    assert vertices is not None and isinstance(vertices, np.ndarray), "vertices deve ser np.ndarray"
    assert faces is not None and isinstance(faces, np.ndarray), "faces deve ser np.ndarray"
    assert normais is not None and isinstance(normais, np.ndarray), "normais_faces deve ser np.ndarray"
    assert vertices.shape[1] == 3, f"Vértices devem ser (N, 3), recebido {vertices.shape}"
    assert faces.shape[1] == 3, f"Faces devem ser triangulares (M, 3), recebido {faces.shape}"
    assert normais.shape == faces.shape, f"Normais devem ter formato (M, 3), recebido {normais.shape}"

    num_vertices = len(vertices)
    assert np.all(faces >= 0) and np.all(faces < num_vertices), "Índices de faces fora do intervalo de vértices!"

    # 1. Teste de normalização (norma deve ser 1.0)
    normas = np.linalg.norm(normais, axis=1)
    normais_unitarias = np.allclose(normas, 1.0, atol=1e-5)
    assert normais_unitarias, f"Existem normais não-unitárias no sólido {nome}!"

    # 2. Teste de apontamento para fora (para sólidos convexos / centroide)
    centroide = np.mean(vertices, axis=0)
    baricentros_faces = (vertices[faces[:, 0]] + vertices[faces[:, 1]] + vertices[faces[:, 2]]) / 3.0
    vetores_para_fora = baricentros_faces - centroide
    
    # Produto escalar N · (baricentro - centroide)
    dots = np.sum(normais * vetores_para_fora, axis=1)
    # Para formas convexas como esponja e queijo, dots deve ser estritamente > 0
    normais_apontam_fora = np.all(dots > -1e-5)

    relatorio = {
        "nome": nome,
        "num_vertices": len(vertices),
        "num_faces": len(faces),
        "num_arestas": len(arestas) if arestas is not None else 0,
        "normais_unitarias": bool(normais_unitarias),
        "normais_apontam_fora": bool(normais_apontam_fora),
        "centroide": centroide,
        "limites_min": np.min(vertices, axis=0),
        "limites_max": np.max(vertices, axis=0),
    }

    if verbose:
        print("=" * 55)
        print(f" RELATÓRIO DE VALIDAÇÃO: {nome.upper()}")
        print("=" * 55)
        print(f" • Vértices: {relatorio['num_vertices']}")
        print(f" • Faces Triangulares: {relatorio['num_faces']}")
        print(f" • Arestas: {relatorio['num_arestas']}")
        print(f" • Normais Unitárias: {'[OK]' if normais_unitarias else '[FALHOU]'}")
        print(f" • Normais Apontando Para Fora: {'[OK]' if normais_apontam_fora else '[AVISO: Verificar concavidades]'}")
        print(f" • Centroide: {np.round(centroide, 3)}")
        print(f" • Dimensões (Bounding Box):")
        print(f"     Min: {np.round(relatorio['limites_min'], 3)}")
        print(f"     Max: {np.round(relatorio['limites_max'], 3)}")
        print("=" * 55)

    return relatorio


def plotar_solido(
    solido: dict,
    mostrar_normais: bool = True,
    escala_normais: float = 0.5,
    salvar_caminho: str | None = None,
    mostrar_plot: bool = True,
) -> None:
    """
    Gera o plot 3D do sólido em seu sistema de coordenadas do objeto (Item 1e).
    
    Exibe:
    - Malha poligonal renderizada com transparência.
    - Arestas do objeto.
    - Setas das normais das faces saindo dos baricentros (ax.quiver).
    - Eixos coordenados locais do objeto: X (Vermelho), Y (Verde), Z (Azul).
    - Origem local (0, 0, 0) destacada.
    """
    vertices = solido["vertices"]
    faces = solido["faces"]
    normais = solido["normais_faces"]
    cor = solido.get("cor", (0.8, 0.8, 0.2))
    nome = solido.get("nome", "Sólido").capitalize()

    fig = plt.figure(figsize=(9, 8))
    ax = fig.add_subplot(111, projection="3d")

    # 1. Plotar a malha poligonal
    triangulos = [vertices[face] for face in faces]
    poly3d = Poly3DCollection(
        triangulos,
        facecolors=cor,
        edgecolors="black",
        linewidths=0.8,
        alpha=0.85,
    )
    ax.add_collection3d(poly3d)

    # 2. Plotar vetores normais saindo do baricentro de cada face
    if mostrar_normais:
        baricentros = (vertices[faces[:, 0]] + vertices[faces[:, 1]] + vertices[faces[:, 2]]) / 3.0
        ax.quiver(
            baricentros[:, 0], baricentros[:, 1], baricentros[:, 2],
            normais[:, 0], normais[:, 1], normais[:, 2],
            length=escala_normais,
            color="red",
            linewidth=1.2,
            arrow_length_ratio=0.3,
            label="Normais das Faces",
        )

    # 3. Plotar os eixos coordenados do objeto (X=Vermelho, Y=Verde, Z=Azul)
    comprimento_eixo = float(np.max(np.abs(vertices))) * 1.3
    ax.quiver(0, 0, 0, comprimento_eixo, 0, 0, color="crimson", linewidth=2.5, arrow_length_ratio=0.1, label="Eixo X (Objeto)")
    ax.quiver(0, 0, 0, 0, comprimento_eixo, 0, color="forestgreen", linewidth=2.5, arrow_length_ratio=0.1, label="Eixo Y (Objeto)")
    ax.quiver(0, 0, 0, 0, 0, comprimento_eixo, color="royalblue", linewidth=2.5, arrow_length_ratio=0.1, label="Eixo Z (Objeto)")

    # 4. Ponto na origem local (0,0,0)
    ax.scatter([0], [0], [0], color="black", s=60, zorder=10, label="Origem (0,0,0)")

    # Ajuste de limites e proporção cúbica
    todos_pts = np.vstack([vertices, [[-comprimento_eixo]*3, [comprimento_eixo]*3]])
    min_val = np.min(todos_pts)
    max_val = np.max(todos_pts)
    ax.set_xlim([min_val, max_val])
    ax.set_ylim([min_val, max_val])
    ax.set_zlim([min_val, max_val])

    ax.set_xlabel("X (Objeto)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Y (Objeto)", fontsize=11, fontweight="bold")
    ax.set_zlabel("Z (Objeto)", fontsize=11, fontweight="bold")
    ax.set_title(f"Item 1e: {nome} no Sistema de Coordenadas do Objeto\n(Normais apontando para fora)", fontsize=13, fontweight="bold", pad=15)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), fontsize=9)

    plt.tight_layout()

    if salvar_caminho:
        import os
        os.makedirs(os.path.dirname(salvar_caminho), exist_ok=True)
        plt.savefig(salvar_caminho, dpi=300, bbox_inches="tight")
        print(f"Figura salva em: {salvar_caminho}")

    if mostrar_plot:
        plt.show()
    else:
        plt.close()
