"""
Módulo de Visualização do Pipeline para o Projeto de Computação Gráfica (2026.2 - IFCE).

Gera as figuras exigidas para os itens 4a, 5 e 6:
  - fig_4a_projecao_3d_2d.png: projeção perspectiva 3D no espaço da câmera + janela 2D
  - fig_5_iluminacao_phong.png: componentes Ambiente, Difusa, Especular e Total de Phong
  - fig_6_rasterizacao_resolucoes.png + fig_6_res_*.png: comparação em 3 resoluções
  - fig_6_variacao_eye_raster.png: rasterização variando o ponto de vista (eye)
"""

import os
import sys
import time

import matplotlib

if __name__ != "__main__" and "matplotlib.pyplot" not in sys.modules:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

from camera import camera, transformar_para_camera
from cena import montar_cena
from projecao import projetar
from visualizacao_3d import _configurar_limites_cubicos


def _selecionar_vertices_raios(solido_cam: dict, faces_vis: np.ndarray, max_raios: int = 2) -> np.ndarray:
    """Seleciona até `max_raios` vértices representativos para desenhar raios projetantes."""
    vertices = solido_cam["vertices"]
    if len(faces_vis) > 0:
        indices_unicos = np.unique(faces_vis)
    else:
        indices_unicos = np.arange(len(vertices))

    if len(indices_unicos) <= max_raios:
        return vertices[indices_unicos]

    # Seleciona os extremos ao longo de X_cam para boa distribuição visual dos raios
    pts = vertices[indices_unicos]
    idx_min = int(np.argmin(pts[:, 0]))
    idx_max = int(np.argmax(pts[:, 0]))
    if idx_min == idx_max:
        return pts[[0, len(pts) // 2]]
    return pts[[idx_min, idx_max]]


def _montar_figura_projecao_3d_2d(
    eye: tuple[float, float, float] | list[float] | np.ndarray = (12.0, 8.0, 14.0),
    at: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 0.0, 0.0),
    up: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 1.0, 0.0),
    d_proj: float = 1.8,
):
    """Constrói a figura Matplotlib lado a lado (3D + Janela 2D) dos Itens 4 e 4a."""
    cena_mundo = montar_cena()
    _, _, _, M_vis = camera(eye, at, up)

    fig = plt.figure(figsize=(15, 7))
    ax_3d = fig.add_subplot(1, 2, 1, projection="3d")
    ax_2d = fig.add_subplot(1, 2, 2)

    z_plano = -float(d_proj)
    moldura_pts = np.array(
        [
            [-1.0, -1.0, z_plano],
            [1.0, -1.0, z_plano],
            [1.0, 1.0, z_plano],
            [-1.0, 1.0, z_plano],
            [-1.0, -1.0, z_plano],
        ],
        dtype=np.float64,
    )

    todos_pontos = [np.zeros((1, 3)), moldura_pts]
    poligonos_2d: list[tuple[float, np.ndarray, tuple[float, float, float]]] = []
    handles_legenda: list[Patch] = []

    for solido_mundo in cena_mundo:
        solido_cam = transformar_para_camera(solido_mundo, M_vis)
        cor = tuple(float(c) for c in solido_cam["cor"])
        vertices_cam = solido_cam["vertices"]
        faces = solido_cam["faces"]
        todos_pontos.append(vertices_cam)

        if "cores_faces" in solido_cam:
            cores_f_3d = [tuple(float(c) for c in cf) for cf in solido_cam["cores_faces"]]
            mapa_cor_face = {
                tuple(int(v) for v in f): tuple(float(c) for c in cf)
                for f, cf in zip(faces, solido_cam["cores_faces"])
            }
        else:
            cores_f_3d = cor
            mapa_cor_face = {}

        # Sólido 3D no espaço da câmera (face e aresta com a mesma cor)
        colecao_3d = Poly3DCollection(
            vertices_cam[faces],
            facecolor=cores_f_3d,
            edgecolor=cores_f_3d,
            linewidth=0.35,
            alpha=0.55,
        )
        ax_3d.add_collection3d(colecao_3d)

        pts_2d, faces_vis = projetar(solido_cam, d=d_proj)
        if len(faces_vis) > 0:
            pts_plano_3d = np.column_stack([pts_2d, np.full(len(pts_2d), z_plano)])
            cores_vis = [
                mapa_cor_face.get(tuple(int(v) for v in face), cor)
                for face in faces_vis
            ]
            colecao_proj = Poly3DCollection(
                pts_plano_3d[faces_vis],
                facecolor=cores_vis,
                edgecolor=cores_vis,
                linewidth=0.5,
                alpha=0.85,
            )
            ax_3d.add_collection3d(colecao_proj)

            for face, cor_face in zip(faces_vis, cores_vis):
                profundidade_media = float(np.mean(-vertices_cam[face, 2]))
                poligonos_2d.append((profundidade_media, pts_2d[face], cor_face))

        # Raios projetantes conectando vértices representativos até a câmera (0, 0, 0)
        for pt in _selecionar_vertices_raios(solido_cam, faces_vis, max_raios=2):
            ax_3d.plot(
                [0.0, float(pt[0])],
                [0.0, float(pt[1])],
                [0.0, float(pt[2])],
                color=cor,
                linestyle="--",
                linewidth=0.75,
                alpha=0.45,
            )

        handles_legenda.append(
            Patch(
                facecolor=cor,
                edgecolor=cor,
                label=solido_cam["nome"].capitalize(),
            )
        )

    # Câmera na origem e moldura da janela de projeção em z = -d_proj
    h_cam = ax_3d.scatter(
        [0.0],
        [0.0],
        [0.0],
        color="black",
        marker="^",
        s=90,
        depthshade=False,
        label="Câmera (0, 0, 0)",
    )
    h_moldura = ax_3d.plot(
        moldura_pts[:, 0],
        moldura_pts[:, 1],
        moldura_pts[:, 2],
        color="#1e293b",
        linewidth=1.5,
        label=f"Janela (z = -{d_proj:.2f})",
    )[0]

    _configurar_limites_cubicos(ax_3d, np.vstack(todos_pontos), margem=1.0)
    ax_3d.set_xlabel("X_cam (u)")
    ax_3d.set_ylabel("Y_cam (v)")
    ax_3d.set_zlabel("Z_cam (w)")
    ax_3d.set_title("Item 4a — Espaço da Câmera + Plano de Projeção 3D", fontsize=11, fontweight="bold")
    ax_3d.legend(handles=[h_cam, h_moldura], loc="upper left", fontsize=8, frameon=True)

    # Subplot direito: Janela de Projeção 2D com faces visíveis ordenadas por profundidade
    if poligonos_2d:
        poligonos_2d.sort(key=lambda item: item[0], reverse=True)
        verts_2d = [item[1] for item in poligonos_2d]
        cores_2d = [item[2] for item in poligonos_2d]
        colecao_2d = PolyCollection(
            verts_2d,
            facecolors=cores_2d,
            edgecolors=cores_2d,
            linewidths=0.6,
        )
        ax_2d.add_collection(colecao_2d)

    ax_2d.set_xlim(-1.0, 1.0)
    ax_2d.set_ylim(-1.0, 1.0)
    ax_2d.set_aspect("equal", adjustable="box")
    ax_2d.grid(True, linestyle=":", alpha=0.45)
    ax_2d.set_xlabel("X_proj")
    ax_2d.set_ylabel("Y_proj")
    ax_2d.set_title("Item 4 — Janela de Projeção 2D (Faces Visíveis)", fontsize=11, fontweight="bold")
    ax_2d.legend(handles=handles_legenda, loc="upper left", fontsize=8, frameon=True)

    fig.suptitle(
        "Itens 4 e 4a — Projeção Perspectiva 3D (Espaço da Câmera) e Janela 2D",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    return fig


def plotar_projecao_3d_2d(
    eye: tuple[float, float, float] | list[float] | np.ndarray = (12.0, 8.0, 14.0),
    at: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 0.0, 0.0),
    up: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 1.0, 0.0),
    d_proj: float = 1.8,
    diretorio_saida: str = "outputs",
) -> str:
    """
    Itens 4 e 4a: Gera figura lado a lado com:
      - Subplot esquerdo: cena 3D no espaço da câmera, plano de projeção z = -d_proj
        com polígonos visíveis projetados e raios projetantes até (0, 0, 0).
      - Subplot direito: janela de projeção 2D [-1, 1] x [-1, 1] com faces visíveis.
    """
    os.makedirs(diretorio_saida, exist_ok=True)
    fig = _montar_figura_projecao_3d_2d(eye=eye, at=at, up=up, d_proj=d_proj)
    caminho = os.path.join(diretorio_saida, "fig_4a_projecao_3d_2d.png")
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


def exibir_projecao_3d_2d_interativa(
    eye: tuple[float, float, float] | list[float] | np.ndarray = (12.0, 8.0, 14.0),
    at: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 0.0, 0.0),
    up: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 1.0, 0.0),
    d_proj: float = 1.8,
) -> None:
    """Abre a janela interativa com a projeção 3D (esquerda) e a janela 2D (direita)."""
    matplotlib.rcParams["axes3d.mouserotationstyle"] = "arcball"
    _montar_figura_projecao_3d_2d(eye=eye, at=at, up=up, d_proj=d_proj)
    plt.show()


def _montar_figura_iluminacao_phong(
    eye: tuple[float, float, float] | list[float] | np.ndarray = (12.0, 8.0, 14.0),
    resolucao: tuple[int, int] = (250, 250),
):
    """Constrói a grade 2x2 comparando os componentes de iluminação de Phong (Item 5)."""
    from main import render

    modos = (
        ("ambiente", "Componente Ambiente (Ka · Ia)"),
        ("difusa", "Componente Difusa (Kd · Il · max(0, N·L))"),
        ("especular", "Componente Especular (Ks · Il · max(0, R·V)^n)"),
        ("total", "Iluminação Total de Phong (Sombreamento Gouraud)"),
    )

    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    for ax, (modo, titulo) in zip(axes.ravel(), modos):
        img = render(eye=eye, resolucao=resolucao, componente_phong=modo)
        ax.imshow(np.clip(img, 0.0, 1.0))
        ax.set_title(titulo, fontsize=11, fontweight="bold")
        ax.axis("off")

    fig.suptitle(
        "Item 5 — Decomposição do Modelo de Iluminação de Phong",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    return fig


def plotar_iluminacao_phong(
    eye: tuple[float, float, float] | list[float] | np.ndarray = (12.0, 8.0, 14.0),
    resolucao: tuple[int, int] = (250, 250),
    diretorio_saida: str = "outputs",
) -> str:
    """
    Item 5: Gera grade 2x2 comparando os componentes de iluminação de Phong:
    ambiente, difusa, especular e total.
    """
    os.makedirs(diretorio_saida, exist_ok=True)
    fig = _montar_figura_iluminacao_phong(eye=eye, resolucao=resolucao)
    caminho = os.path.join(diretorio_saida, "fig_5_iluminacao_phong.png")
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


def exibir_iluminacao_phong_interativa(
    eye: tuple[float, float, float] | list[float] | np.ndarray = (12.0, 8.0, 14.0),
    resolucao: tuple[int, int] = (200, 200),
) -> None:
    """Abre uma janela exibindo a decomposição 2x2 da iluminação de Phong."""
    _montar_figura_iluminacao_phong(eye=eye, resolucao=resolucao)
    plt.show()


def exibir_rasterizacao_interativa(
    eye: tuple[float, float, float] | list[float] | np.ndarray = (12.0, 8.0, 14.0),
    resolucoes: tuple[tuple[int, int], ...] = ((150, 150), (300, 300)),
) -> None:
    """Abre uma janela comparando a rasterização da cena em diferentes resoluções."""
    from main import render

    fig, axes = plt.subplots(1, len(resolucoes), figsize=(5 * len(resolucoes), 5), squeeze=False)
    for ax, (larg, alt) in zip(axes[0], resolucoes):
        inicio = time.perf_counter()
        img = render(eye=eye, resolucao=(larg, alt))
        dt = time.perf_counter() - inicio
        ax.imshow(np.clip(img, 0.0, 1.0))
        ax.set_title(f"{larg}×{alt} ({dt:.2f} s)", fontsize=11, fontweight="bold")
        ax.axis("off")

    fig.suptitle(
        "Item 6 — Rasterização da Cena (Bresenham + Par-Ímpar + Baricêntricas)",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.93))
    plt.show()


def plotar_rasterizacao_resolucoes(
    eye: tuple[float, float, float] | list[float] | np.ndarray = (12.0, 8.0, 14.0),
    resolucoes: tuple[tuple[int, int], ...] = ((200, 200), (400, 400), (800, 800)),
    diretorio_saida: str = "outputs",
) -> tuple[str, dict[str, float]]:
    """
    Item 6: Rasteriza a cena em múltiplas resoluções, salva cada imagem individualmente
    e gera um painel comparativo lado a lado com o tempo de execução.
    """
    from main import render

    if not resolucoes:
        raise ValueError("É necessário informar ao menos uma resolução em 'resolucoes'.")

    os.makedirs(diretorio_saida, exist_ok=True)
    resultados: list[tuple[int, int, np.ndarray, float]] = []
    tempos_por_res: dict[str, float] = {}

    for larg, alt in resolucoes:
        nome_res = f"fig_6_res_{larg}.png" if larg == alt else f"fig_6_res_{larg}x{alt}.png"
        caminho_res = os.path.join(diretorio_saida, nome_res)
        inicio = time.perf_counter()
        img = render(eye=eye, resolucao=(larg, alt), salvar_caminho=caminho_res)
        dt = time.perf_counter() - inicio
        tempos_por_res[f"{larg}x{alt}"] = dt
        resultados.append((larg, alt, img, dt))

    fig, axes = plt.subplots(1, len(resolucoes), figsize=(5 * len(resolucoes), 5), squeeze=False)
    for ax, (larg, alt, img, dt) in zip(axes[0], resultados):
        ax.imshow(np.clip(img, 0.0, 1.0))
        ax.set_title(f"{larg}×{alt} ({dt:.2f} s)", fontsize=11, fontweight="bold")
        ax.axis("off")

    fig.suptitle(
        "Item 6 — Comparação de Rasterização em Múltiplas Resoluções",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.93))

    caminho_painel = os.path.join(diretorio_saida, "fig_6_rasterizacao_resolucoes.png")
    fig.savefig(caminho_painel, dpi=150)
    plt.close(fig)
    return caminho_painel, tempos_por_res


def plotar_rasterizacao_eyes(
    eyes: tuple[tuple[float, float, float], ...] = (
        (12.0, 8.0, 14.0),
        (-12.0, 8.0, 14.0),
        (0.0, 14.0, 16.0),
    ),
    resolucao: tuple[int, int] = (300, 300),
    diretorio_saida: str = "outputs",
) -> str:
    """
    Item 6: Rasteriza a cena completa para múltiplos pontos de vista (eye) lado a lado.
    """
    from main import render

    if not eyes:
        raise ValueError("É necessário informar ao menos um ponto de vista em 'eyes'.")

    os.makedirs(diretorio_saida, exist_ok=True)
    fig, axes = plt.subplots(1, len(eyes), figsize=(5 * len(eyes), 5), squeeze=False)

    for ax, eye in zip(axes[0], eyes):
        img = render(eye=eye, resolucao=resolucao)
        eye_fmt = tuple(float(c) for c in eye)
        ax.imshow(np.clip(img, 0.0, 1.0))
        ax.set_title(f"eye = {eye_fmt}", fontsize=11, fontweight="bold")
        ax.axis("off")

    fig.suptitle(
        "Item 6 — Rasterização sob Diferentes Pontos de Vista (eye)",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.93))

    caminho = os.path.join(diretorio_saida, "fig_6_variacao_eye_raster.png")
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


def gerar_figuras_pipeline(
    diretorio_saida: str = "outputs",
    resolucoes: tuple[tuple[int, int], ...] = ((200, 200), (400, 400), (800, 800)),
) -> dict[str, str]:
    """
    Executa todas as visualizações do pipeline (itens 4a, 5 e 6) e retorna
    um dicionário mapeando cada identificador ao caminho do arquivo PNG gerado.
    """
    caminho_4a = plotar_projecao_3d_2d(diretorio_saida=diretorio_saida)
    caminho_5 = plotar_iluminacao_phong(diretorio_saida=diretorio_saida)
    caminho_6_res, _ = plotar_rasterizacao_resolucoes(
        resolucoes=resolucoes,
        diretorio_saida=diretorio_saida,
    )
    caminho_6_eyes = plotar_rasterizacao_eyes(diretorio_saida=diretorio_saida)

    caminhos: dict[str, str] = {
        "fig_4a": caminho_4a,
        "fig_5": caminho_5,
        "fig_6_resolucoes": caminho_6_res,
        "fig_6_eyes": caminho_6_eyes,
    }
    for larg, alt in resolucoes:
        if larg == alt:
            chave = f"fig_6_res_{larg}"
            nome = f"fig_6_res_{larg}.png"
        else:
            chave = f"fig_6_res_{larg}x{alt}"
            nome = f"fig_6_res_{larg}x{alt}.png"
        caminhos[chave] = os.path.join(diretorio_saida, nome)

    return caminhos
