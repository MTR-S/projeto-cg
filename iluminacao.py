"""
Módulo de Iluminação pelo Modelo de Phong.
Responsável: Miller
"""

import numpy as np


def calcular_normais_vertices(solido: dict) -> np.ndarray:
    """
    Calcula as normais dos vértices como a média das normais das faces adjacentes (sombreamento Gouraud).
    
    Retorna:
        normais_vertices: np.ndarray (N, 3) unitárias
    """
    vertices = solido["vertices"]
    faces = solido["faces"]
    normais_faces = solido["normais_faces"]

    normais_vert = np.zeros_like(vertices, dtype=np.float64)

    # Acumula a normal da face em cada vértice que a compõe
    for face_idx, face in enumerate(faces):
        fn = normais_faces[face_idx]
        normais_vert[face[0]] += fn
        normais_vert[face[1]] += fn
        normais_vert[face[2]] += fn

    # Normaliza cada vetor de vértice
    normas = np.linalg.norm(normais_vert, axis=1, keepdims=True)
    return normais_vert / np.where(normas == 0, 1.0, normas)


def phong(
    solido: dict,
    luz_pos: np.ndarray | list[float],
    eye_pos: np.ndarray | list[float],
    ia: float = 0.2,
    il: float = 0.8,
    ka: float = 0.3,
    kd: float = 0.7,
    ks: float = 0.5,
    n_especular: float = 16.0,
    normais_vertices: np.ndarray | None = None,
    retornar_componentes: bool = False,
) -> np.ndarray | tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Aplica o modelo de reflexão de Phong nos vértices de um sólido.
    
    Equação:
        I = Ka * Ia + Kd * Il * max(0, N · L) + Ks * Il * max(0, R · V)^n
        
    Parâmetros:
        solido: dict com vertices, faces, etc.
        luz_pos: Posição da fonte de luz pontual no espaço
        eye_pos: Posição do observador
        ia: Intensidade da luz ambiente
        il: Intensidade da fonte de luz
        ka, kd, ks: Coeficientes do material (ambiente, difuso, especular)
        n_especular: Expoente de brilho especular (rugosidade)
        normais_vertices: (N, 3) se fornecido; caso contrário, é computado.
        retornar_componentes: se True, retorna (I_total, I_amb, I_dif, I_esp)
        
    Retorna:
        Cores RGB em cada vértice (N, 3) no intervalo [0.0, 1.0]
    """
    vertices = solido["vertices"]
    cor_base = np.array(solido.get("cor", (1.0, 1.0, 1.0)), dtype=np.float64)

    if normais_vertices is None:
        normais_vertices = calcular_normais_vertices(solido)

    luz = np.array(luz_pos, dtype=np.float64)
    eye = np.array(eye_pos, dtype=np.float64)

    # 1. Vetor de iluminação L (do vértice até a luz)
    vec_l = luz - vertices
    norm_l = np.linalg.norm(vec_l, axis=1, keepdims=True)
    L = vec_l / np.where(norm_l == 0, 1.0, norm_l)

    # 2. Vetor de visão V (do vértice até o olho)
    vec_v = eye - vertices
    norm_v = np.linalg.norm(vec_v, axis=1, keepdims=True)
    V = vec_v / np.where(norm_v == 0, 1.0, norm_v)

    # 3. Vetor normal N
    N = normais_vertices

    # 4. Componente ambiente: I_amb = Ka * Ia * cor_base
    I_amb = ka * ia * cor_base

    # 5. Componente difusa: I_dif = Kd * Il * max(0, N · L) * cor_base
    n_dot_l = np.sum(N * L, axis=1, keepdims=True)
    cos_difuso = np.maximum(0.0, n_dot_l)
    I_dif = kd * il * cos_difuso * cor_base

    # 6. Componente especular: R = 2 * (N · L) * N - L
    R = 2.0 * n_dot_l * N - L
    norm_r = np.linalg.norm(R, axis=1, keepdims=True)
    R = R / np.where(norm_r == 0, 1.0, norm_r)

    r_dot_v = np.sum(R * V, axis=1, keepdims=True)
    cos_especular = np.maximum(0.0, r_dot_v)
    # Especular normalmente usa a cor da luz (branca)
    cor_luz = np.array([1.0, 1.0, 1.0])
    I_esp = ks * il * (cos_especular ** n_especular) * cor_luz

    # Intensidade total combinada
    I_total = np.clip(I_amb + I_dif + I_esp, 0.0, 1.0)

    if retornar_componentes:
        return I_total, I_amb, I_dif, I_esp
    return I_total


if __name__ == "__main__":
    triangulo = {
        "vertices": np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64),
        "faces": np.array([[0, 1, 2]], dtype=np.int32),
        "normais_faces": np.array([[0, 0, 1]], dtype=np.float64),
        "cor": (0.2, 0.7, 0.3),
        "arestas": np.array([[0, 1], [1, 2], [2, 0]]),
    }
    cores_v = phong(triangulo, luz_pos=[2, 2, 5], eye_pos=[0, 0, 10])
    print("Módulo de Iluminação Phong testado com sucesso!")
    print("Cores calculadas por vértice:\n", cores_v)
