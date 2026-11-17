"""
Módulo de Transformações Geométricas 3D (Matrizes Homogêneas 4x4).
Responsável: Matheus
"""

import numpy as np


def escala(sx: float, sy: float, sz: float) -> np.ndarray:
    """Retorna matriz homogênea 4x4 de escala."""
    return np.array([
        [sx, 0.0, 0.0, 0.0],
        [0.0, sy, 0.0, 0.0],
        [0.0, 0.0, sz, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=np.float64)


def rotacao_x(theta: float) -> np.ndarray:
    """Retorna matriz homogênea 4x4 de rotação em torno do eixo X (theta em radianos)."""
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0,   c,  -s, 0.0],
        [0.0,   s,   c, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=np.float64)


def rotacao_y(theta: float) -> np.ndarray:
    """Retorna matriz homogênea 4x4 de rotação em torno do eixo Y (theta em radianos)."""
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([
        [  c, 0.0,   s, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [ -s, 0.0,   c, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=np.float64)


def rotacao_z(theta: float) -> np.ndarray:
    """Retorna matriz homogênea 4x4 de rotação em torno do eixo Z (theta em radianos)."""
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([
        [  c,  -s, 0.0, 0.0],
        [  s,   c, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=np.float64)


def translacao(tx: float, ty: float, tz: float) -> np.ndarray:
    """Retorna matriz homogênea 4x4 de translação."""
    return np.array([
        [1.0, 0.0, 0.0,  tx],
        [0.0, 1.0, 0.0,  ty],
        [0.0, 0.0, 1.0,  tz],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=np.float64)


def aplicar_transformacao(vertices: np.ndarray, matriz: np.ndarray) -> np.ndarray:
    """
    Aplica uma matriz 4x4 a um conjunto de vértices (N, 3).
    Retorna os vértices transformados (N, 3).
    """
    n = len(vertices)
    homogeneos = np.hstack([vertices, np.ones((n, 1), dtype=np.float64)])  # (N, 4)
    transformados = (matriz @ homogeneos.T).T                              # (N, 4)
    
    # Normalização por w se w != 1
    w = transformados[:, 3:4]
    w = np.where(np.abs(w) < 1e-9, 1.0, w)
    return transformados[:, :3] / w


def transformar_solido(solido: dict, matriz: np.ndarray) -> dict:
    """
    Aplica a transformação homogênea 4x4 aos vértices e recalcula as normais das faces.
    """
    novos_vertices = aplicar_transformacao(solido["vertices"], matriz)
    faces = solido["faces"]
    
    # Recalcula normais após a transformação
    v0 = novos_vertices[faces[:, 0]]
    v1 = novos_vertices[faces[:, 1]]
    v2 = novos_vertices[faces[:, 2]]
    normais = np.cross(v1 - v0, v2 - v0)
    normas = np.linalg.norm(normais, axis=1, keepdims=True)
    normais_unitarias = normais / np.where(normas == 0, 1.0, normas)

    return {
        "vertices": novos_vertices,
        "faces": faces,
        "arestas": solido["arestas"],
        "normais_faces": normais_unitarias,
        "cor": solido["cor"],
        "nome": solido.get("nome", "solido"),
    }


if __name__ == "__main__":
    cubo_teste = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0]
    ], dtype=np.float64)
    
    M = translacao(2, 3, 4) @ rotacao_z(np.pi / 2) @ escala(2, 2, 2)
    res = aplicar_transformacao(cubo_teste, M)
    print("Módulo de transformações testado com sucesso!")
    print("Vértices transformados:\n", res)
