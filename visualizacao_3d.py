"""
Módulo de Visualização 3D para o Projeto de Computação Gráfica (2026.2 - IFCE).

Gera as figuras 3D exigidas para os itens 1e, 2b, 3c, 3d e 3e:
  - fig_1e_solidos_isolados.png: 5 sólidos isolados no referencial de objeto com normais
  - fig_2b_cena_mundo.png: cena composta no sistema de coordenadas do mundo
  - fig_3c_cena_camera.png: cena no sistema de coordenadas da câmera (VRC) com origem do mundo
  - fig_3e_variacao_eye.png: comparação de múltiplos pontos de vista (eye)
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

from camera import camera, obter_origem_mundo_na_camera, transformar_para_camera
from cena import montar_cena
from solidos import (
    criar_boia,
    criar_esponja,
    criar_prato,
    criar_queijo,
    criar_rolo,
)


def _cor_borda_sutil(cor: tuple[float, float, float]) -> tuple[float, float, float]:
    """Retorna uma versão levemente escurecida da cor do sólido para as arestas."""
    return tuple(max(0.0, float(c) * 0.55) for c in cor)


def _normalizar_zero(val: float, tol: float = 1e-9) -> float:
    """Converte valores próximos de zero (inclusive -0.0) para +0.0."""
    f = float(val)
    return 0.0 if abs(f) < tol else f


def _limpar_vetor(v: np.ndarray, tol: float = 1e-9) -> np.ndarray:
    """Normaliza componentes próximos de zero para +0.0 em vetores NumPy."""
    return np.where(np.abs(v) < tol, 0.0, v) + 0.0


def _arredondar_vetor(v: np.ndarray, casas: int = 3) -> np.ndarray:
    """Arredonda vetor NumPy garantindo ausência de -0.0 na exibição."""
    arr = np.round(_limpar_vetor(v), casas)
    return np.where(arr == 0.0, 0.0, arr) + 0.0


def _formatar_tupla_ponto(ponto: tuple[float, ...] | list[float] | np.ndarray) -> tuple[float, ...]:
    """Converte um ponto 3D para tupla de floats Python sem np.float64 nem -0.0."""
    return tuple(_normalizar_zero(round(float(c), 4)) for c in ponto)


def _configurar_limites_cubicos(
    ax,
    pontos: np.ndarray,
    margem: float = 0.5,
) -> None:
    """Define limites iguais nos três eixos em torno do centro para preservar proporções 1:1:1."""
    min_pt = np.min(pontos, axis=0)
    max_pt = np.max(pontos, axis=0)
    centro = (min_pt + max_pt) / 2.0
    semi_lado = max(float(np.max(max_pt - min_pt)) / 2.0, 0.5) + margem

    ax.set_xlim(centro[0] - semi_lado, centro[0] + semi_lado)
    ax.set_ylim(centro[1] - semi_lado, centro[1] + semi_lado)
    ax.set_zlim(centro[2] - semi_lado, centro[2] + semi_lado)
    ax.set_box_aspect([1, 1, 1])


def plotar_solido_3d(
    ax,
    solido: dict,
    mostrar_normais: bool = True,
    alpha: float = 0.85,
    passo_normal: int | None = None,
) -> None:
    """
    Plota um sólido 3D em um eixo Matplotlib usando Poly3DCollection e,
    opcionalmente, vetores normais das faces com ax.quiver.
    """
    vertices = solido["vertices"]
    faces = solido["faces"]
    cor = tuple(float(c) for c in solido["cor"])
    cor_borda = _cor_borda_sutil(cor)

    triangulos = vertices[faces]
    colecao = Poly3DCollection(
        triangulos,
        facecolor=cor,
        edgecolor=cor_borda,
        linewidth=0.35,
        alpha=alpha,
    )
    ax.add_collection3d(colecao)

    if mostrar_normais and len(faces) > 0:
        normais = solido["normais_faces"]
        centroides = (
            vertices[faces[:, 0]] + vertices[faces[:, 1]] + vertices[faces[:, 2]]
        ) / 3.0
        passo = max(1, len(faces) // 40) if passo_normal is None else max(1, int(passo_normal))

        c_amostra = centroides[::passo]
        n_amostra = normais[::passo]
        ax.quiver(
            c_amostra[:, 0],
            c_amostra[:, 1],
            c_amostra[:, 2],
            n_amostra[:, 0],
            n_amostra[:, 1],
            n_amostra[:, 2],
            length=0.45,
            normalize=True,
            color=cor_borda,
            linewidth=0.9,
            alpha=0.9,
        )


def plotar_solidos_isolados(diretorio_saida: str = "outputs") -> str:
    """
    Item 1e: Gera figura 2x3 com os 5 sólidos isolados em seus sistemas de coordenadas
    de objeto, incluindo amostra de vetores normais externos.
    """
    os.makedirs(diretorio_saida, exist_ok=True)
    solidos = [
        criar_esponja(),
        criar_queijo(),
        criar_prato(),
        criar_rolo(),
        criar_boia(),
    ]

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(
        "Item 1e — Sólidos Isolados no Sistema de Coordenadas do Objeto",
        fontsize=14,
        fontweight="bold",
    )

    for idx, solido in enumerate(solidos, start=1):
        ax = fig.add_subplot(2, 3, idx, projection="3d")
        plotar_solido_3d(ax, solido, mostrar_normais=True, alpha=0.85)
        _configurar_limites_cubicos(ax, solido["vertices"], margem=0.6)
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.yaxis.set_major_locator(MaxNLocator(5))
        ax.zaxis.set_major_locator(MaxNLocator(5))
        ax.set_xlabel("X_obj")
        ax.set_ylabel("Y_obj")
        ax.set_zlabel("Z_obj")
        n_vert = len(solido["vertices"])
        n_faces = len(solido["faces"])
        ax.set_title(
            f"{solido['nome'].capitalize()}\n({n_vert} vértices, {n_faces} faces)",
            fontsize=11,
        )

    ax_resumo = fig.add_subplot(2, 3, 6)
    ax_resumo.axis("off")
    linhas_resumo = ["Resumo dos Sólidos (Malha + Normais)", "-" * 38]
    for s in solidos:
        linhas_resumo.append(
            f"{s['nome'].capitalize():8s}: {len(s['vertices']):4d} vértices | {len(s['faces']):4d} faces"
        )
    ax_resumo.text(
        0.05,
        0.5,
        "\n".join(linhas_resumo),
        va="center",
        ha="left",
        family="monospace",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.6", "facecolor": "#f4f6f8", "edgecolor": "#cbd5e1"},
    )

    fig.subplots_adjust(left=0.03, right=0.98, top=0.88, bottom=0.08, hspace=0.38, wspace=0.12)
    caminho = os.path.join(diretorio_saida, "fig_1e_solidos_isolados.png")
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


def plotar_cena_mundo(diretorio_saida: str = "outputs") -> str:
    """
    Item 2b: Gera figura 3D da cena composta no sistema de coordenadas do mundo.
    """
    os.makedirs(diretorio_saida, exist_ok=True)
    cena = montar_cena()

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(1, 1, 1, projection="3d")

    handles_legenda = []
    for solido in cena:
        plotar_solido_3d(ax, solido, mostrar_normais=False, alpha=0.88)
        cor = tuple(float(c) for c in solido["cor"])
        handles_legenda.append(
            Patch(
                facecolor=cor,
                edgecolor=_cor_borda_sutil(cor),
                label=solido["nome"].capitalize(),
            )
        )

    ax.set_xlim(-10.0, 10.0)
    ax.set_ylim(-10.0, 10.0)
    ax.set_zlim(-10.0, 10.0)
    ax.set_box_aspect([1, 1, 1])
    ax.set_xlabel("X_mundo")
    ax.set_ylabel("Y_mundo")
    ax.set_zlabel("Z_mundo")
    ax.set_title(
        "Item 2b — Cena Composta no Sistema de Coordenadas do Mundo ([-10, 10]³)",
        fontsize=13,
        fontweight="bold",
    )
    ax.legend(handles=handles_legenda, loc="upper left", frameon=True)

    fig.tight_layout()
    caminho = os.path.join(diretorio_saida, "fig_2b_cena_mundo.png")
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


def _desenhar_cena_na_camera(
    ax,
    cena_mundo: list[dict],
    eye: tuple[float, float, float] | list[float] | np.ndarray,
    at: tuple[float, float, float] | list[float] | np.ndarray,
    up: tuple[float, float, float] | list[float] | np.ndarray,
    incluir_legenda: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list]:
    """
    Transforma a cena do mundo para o espaço da câmera (u, v, w), plota os sólidos,
    marca a origem da câmera (0,0,0) e a origem do mundo transformada.
    """
    u, v, w, M_vis = camera(eye, at, up)
    u = _limpar_vetor(u)
    v = _limpar_vetor(v)
    w = _limpar_vetor(w)
    origem_mundo = _limpar_vetor(obter_origem_mundo_na_camera(M_vis))

    todos_pontos = [np.zeros((1, 3)), origem_mundo.reshape(1, 3)]
    handles_legenda = []

    for solido_mundo in cena_mundo:
        solido_cam = transformar_para_camera(solido_mundo, M_vis)
        plotar_solido_3d(ax, solido_cam, mostrar_normais=False, alpha=0.85)
        todos_pontos.append(solido_cam["vertices"])

        cor = tuple(float(c) for c in solido_cam["cor"])
        handles_legenda.append(
            Patch(
                facecolor=cor,
                edgecolor=_cor_borda_sutil(cor),
                label=solido_cam["nome"].capitalize(),
            )
        )

    h_cam = ax.scatter(
        [0.0],
        [0.0],
        [0.0],
        color="black",
        marker="^",
        s=90,
        depthshade=False,
        label="Origem Câmera (0, 0, 0)",
    )
    ox = _normalizar_zero(origem_mundo[0])
    oy = _normalizar_zero(origem_mundo[1])
    oz = _normalizar_zero(origem_mundo[2])
    ox_fmt = _normalizar_zero(round(ox, 2))
    oy_fmt = _normalizar_zero(round(oy, 2))
    oz_fmt = _normalizar_zero(round(oz, 2))

    h_mundo = ax.scatter(
        [ox],
        [oy],
        [oz],
        color="red",
        marker="*",
        s=180,
        depthshade=False,
        label=f"Origem Mundo ({ox_fmt:.2f}, {oy_fmt:.2f}, {oz_fmt:.2f})",
    )

    _configurar_limites_cubicos(ax, np.vstack(todos_pontos), margem=1.0)
    ax.set_xlabel("X_cam (u)")
    ax.set_ylabel("Y_cam (v)")
    ax.set_zlabel("Z_cam (w)")

    x2, y2, _ = proj3d.proj_transform(ox, oy, oz, ax.get_proj())
    ax.annotate(
        f"Origem Mundo\n({ox_fmt:.2f}, {oy_fmt:.2f}, {oz_fmt:.2f})",
        xy=(x2, y2),
        xytext=(18, -26),
        textcoords="offset points",
        color="#b91c1c",
        fontsize=8,
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": "#b91c1c", "lw": 1.0},
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": "#ef4444",
            "alpha": 0.9,
        },
        zorder=20,
    )

    cx2, cy2, _ = proj3d.proj_transform(0.0, 0.0, 0.0, ax.get_proj())
    ax.annotate(
        "Câmera (0, 0, 0)",
        xy=(cx2, cy2),
        xytext=(10, 10),
        textcoords="offset points",
        color="black",
        fontsize=8,
        arrowprops={"arrowstyle": "->", "color": "black", "lw": 0.8},
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": "white",
            "edgecolor": "#64748b",
            "alpha": 0.85,
        },
        zorder=20,
    )

    handles_legenda.extend([h_cam, h_mundo])
    if incluir_legenda:
        ax.legend(handles=handles_legenda, loc="upper left", fontsize=8, frameon=True)

    return u, v, w, origem_mundo, handles_legenda


def plotar_cena_camera(
    eye: tuple[float, float, float] | list[float] | np.ndarray = (12.0, 8.0, 14.0),
    at: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 0.0, 0.0),
    up: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 1.0, 0.0),
    diretorio_saida: str = "outputs",
    nome_arquivo: str = "fig_3c_cena_camera.png",
) -> str:
    """
    Itens 3c e 3d: Gera figura 3D da cena no sistema de coordenadas da câmera (VRC),
    exibindo a base (u, v, w), a origem da câmera e a origem do mundo transformada.
    """
    os.makedirs(diretorio_saida, exist_ok=True)
    cena_mundo = montar_cena()

    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(1, 1, 1, projection="3d")

    u, v, w, _, _ = _desenhar_cena_na_camera(ax, cena_mundo, eye, at, up, incluir_legenda=True)
    eye_fmt = _formatar_tupla_ponto(eye)
    ax.set_title(
        f"Itens 3c–3d — Cena no Sistema da Câmera (eye={eye_fmt})\n"
        f"u={_arredondar_vetor(u, 3)} | v={_arredondar_vetor(v, 3)} | w={_arredondar_vetor(w, 3)}",
        fontsize=11,
        fontweight="bold",
    )

    fig.tight_layout()
    caminho = os.path.join(diretorio_saida, nome_arquivo)
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


def plotar_variacao_eye(
    eyes: tuple[tuple[float, float, float], ...] = (
        (12.0, 8.0, 14.0),
        (-12.0, 8.0, 14.0),
        (0.0, 14.0, 16.0),
    ),
    at: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 0.0, 0.0),
    up: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 1.0, 0.0),
    diretorio_saida: str = "outputs",
) -> str:
    """
    Item 3e: Compara múltiplos pontos de vista (eye) lado a lado no sistema da câmera,
    marcando a origem do mundo e a origem da câmera em cada subplot.
    """
    if not eyes:
        raise ValueError("É necessário informar ao menos um ponto de vista em 'eyes'.")

    os.makedirs(diretorio_saida, exist_ok=True)
    cena_mundo = montar_cena()

    n_views = len(eyes)
    fig = plt.figure(figsize=(6 * n_views, 6))
    fig.suptitle(
        "Item 3e — Comparação de Pontos de Vista da Câmera (Variação de eye)",
        fontsize=13,
        fontweight="bold",
    )

    handles_figura = None
    for idx, eye in enumerate(eyes, start=1):
        ax = fig.add_subplot(1, n_views, idx, projection="3d")
        u, v, w, origem_mundo, handles_legenda = _desenhar_cena_na_camera(
            ax, cena_mundo, eye, at, up, incluir_legenda=False
        )
        if handles_figura is None:
            handles_legenda[-1].set_label("Origem do Mundo")
            handles_figura = handles_legenda

        eye_fmt = _formatar_tupla_ponto(eye)
        ax.set_title(
            f"eye = {eye_fmt}\n"
            f"O_mundo = {_arredondar_vetor(origem_mundo, 2)}\n"
            f"w = {_arredondar_vetor(w, 2)}",
            fontsize=10,
        )

    if handles_figura:
        fig.legend(
            handles=handles_figura,
            loc="lower center",
            ncol=7,
            frameon=True,
            fontsize=9,
        )

    fig.subplots_adjust(left=0.02, right=0.98, top=0.82, bottom=0.14, wspace=0.10)
    caminho = os.path.join(diretorio_saida, "fig_3e_variacao_eye.png")
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


def gerar_figuras_3d(diretorio_saida: str = "outputs") -> dict[str, str]:
    """
    Gera todas as figuras 3D dos itens 1e, 2b, 3c–3d e 3e e retorna um dicionário
    mapeando cada identificador ao caminho do arquivo PNG gerado.
    """
    return {
        "fig_1e": plotar_solidos_isolados(diretorio_saida=diretorio_saida),
        "fig_2b": plotar_cena_mundo(diretorio_saida=diretorio_saida),
        "fig_3c": plotar_cena_camera(diretorio_saida=diretorio_saida),
        "fig_3e": plotar_variacao_eye(diretorio_saida=diretorio_saida),
    }
