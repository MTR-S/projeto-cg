"""
Módulo de Câmera e Sistema de Coordenadas de Visão (VRC).
Responsável: Matheus
"""

import numpy as np
from transformacoes import aplicar_transformacao


def camera(
    eye: np.ndarray | list[float],
    at: np.ndarray | list[float] = (0.0, 0.0, 0.0),
    up: np.ndarray | list[float] = (0.0, 1.0, 0.0),
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula a base vetorial ortonormal (u, v, w) e a matriz de visão 4x4.
    
    Parâmetros:
        eye: Ponto onde a câmera está localizada no mundo.
        at: Ponto para onde a câmera está apontando.
        up: Vetor que indica a orientação "para cima" do mundo.
        
    Retorna:
        u: Eixo X da câmera (horizontal/direita)
        v: Eixo Y da câmera (vertical/cima)
        w: Eixo Z da câmera (aponta na direção oposta à visão, de at para eye)
        matriz_visao: Matriz 4x4 que transforma pontos do mundo para o espaço da câmera
    """
    eye_arr = np.array(eye, dtype=np.float64)
    at_arr = np.array(at, dtype=np.float64)
    up_arr = np.array(up, dtype=np.float64)

    # Vetor w (direção contrária à linha de visão)
    w_vec = eye_arr - at_arr
    norm_w = np.linalg.norm(w_vec)
    if norm_w == 0:
        raise ValueError("eye e at não podem coincidir.")
    w = w_vec / norm_w

    # Vetor u (produto vetorial up x w)
    u_vec = np.cross(up_arr, w)
    norm_u = np.linalg.norm(u_vec)
    if norm_u == 0:
        raise ValueError("Vetor up não pode ser paralelo à linha de visão.")
    u = u_vec / norm_u

    # Vetor v (produto vetorial w x u para garantir ortogonalidade estrita)
    v = np.cross(w, u)

    # Matriz de Rotação da Câmera (u, v, w nas linhas)
    R = np.array([
        [u[0], u[1], u[2], 0.0],
        [v[0], v[1], v[2], 0.0],
        [w[0], w[1], w[2], 0.0],
        [ 0.0,  0.0,  0.0, 1.0],
    ], dtype=np.float64)

    # Matriz de Translação (-eye)
    T = np.array([
        [1.0, 0.0, 0.0, -eye_arr[0]],
        [0.0, 1.0, 0.0, -eye_arr[1]],
        [0.0, 0.0, 1.0, -eye_arr[2]],
        [0.0, 0.0, 0.0,         1.0],
    ], dtype=np.float64)

    matriz_visao = R @ T
    return u, v, w, matriz_visao


def transformar_para_camera(solido: dict, matriz_visao: np.ndarray) -> dict:
    """
    Transforma todos os vértices e normais de um sólido para o sistema de coordenadas da câmera.
    """
    novos_vertices = aplicar_transformacao(solido["vertices"], matriz_visao)
    
    # Rotação das normais (apenas a parte 3x3 ortogonal da matriz de visão)
    R3x3 = matriz_visao[:3, :3]
    normais_cam = (R3x3 @ solido["normais_faces"].T).T
    normas = np.linalg.norm(normais_cam, axis=1, keepdims=True)
    normais_unitarias = normais_cam / np.where(normas == 0, 1.0, normas)

    resultado = {
        "vertices": novos_vertices,
        "faces": solido["faces"],
        "arestas": solido["arestas"],
        "normais_faces": normais_unitarias,
        "cor": solido["cor"],
        "nome": solido.get("nome", "solido"),
    }
    if "cores_faces" in solido:
        resultado["cores_faces"] = solido["cores_faces"]
    return resultado


def obter_origem_mundo_na_camera(matriz_visao: np.ndarray) -> np.ndarray:
    """Retorna as coordenadas da origem do mundo (0, 0, 0) expressas no sistema da câmera."""
    origem_mundo = np.array([[0.0, 0.0, 0.0]])
    return aplicar_transformacao(origem_mundo, matriz_visao)[0]


if __name__ == "__main__":
    import sys

    eye = [12.0, 8.0, 14.0]
    at = [0.0, 0.0, 0.0]
    up = [0.0, 1.0, 0.0]

    u, v, w, M_vis = camera(eye, at, up)
    print("Módulo de Câmera testado com sucesso!")
    print("Base ortonormal da câmera:")
    print(f" u = {np.round(u, 4)}")
    print(f" v = {np.round(v, 4)}")
    print(f" w = {np.round(w, 4)}")
    print("Origem do mundo na câmera:", np.round(obter_origem_mundo_na_camera(M_vis), 4))

    if "--no-plot" not in sys.argv:
        import matplotlib.pyplot as plt  # noqa: F401
        from visualizacao_3d import exibir_cena_camera_interativa

        exibir_cena_camera_interativa(eye=eye, at=at, up=up)
