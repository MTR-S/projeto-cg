"""
Módulo de Rasterização de Retas e Polígonos.
Responsáveis: Vinicius (Bresenham e Par-Ímpar com Scanline) e Miller (Baricêntricas e Viewport)
"""

import numpy as np


def bresenham(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """
    Algoritmo de traçado de retas de Bresenham para todos os octantes.
    
    Retorna:
        Lista de coordenadas inteiras (x, y) que formam o segmento de reta.
    """
    pixels = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    curr_x, curr_y = x0, y0
    while True:
        pixels.append((curr_x, curr_y))
        if curr_x == x1 and curr_y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            curr_x += sx
        if e2 < dx:
            err += dx
            curr_y += sy

    return pixels


def baricentricas(
    p: tuple[float, float],
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> tuple[float, float, float]:
    """
    Calcula as coordenadas baricêntricas (lambda0, lambda1, lambda2) do ponto p
    em relação ao triângulo ABC no plano 2D.
    """
    px, py = p
    ax, ay = a
    bx, by = b
    cx, cy = c

    det_t = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(det_t) < 1e-10:
        return 0.0, 0.0, 0.0

    l0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / det_t
    l1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / det_t
    l2 = 1.0 - l0 - l1

    return l0, l1, l2


def preencher_par_impar(
    triangulo_2d: np.ndarray,
    cores_vertices: np.ndarray,
    largura: int,
    altura: int,
    buffer_cor: np.ndarray,
) -> None:
    """
    Preenche um triângulo 2D usando o algoritmo Par-Ímpar com Scanline e
    interpola as cores nos pixels internos via coordenadas baricêntricas.
    
    Convenção:
        triangulo_2d: array (3, 2) com as coordenadas em pixels (x, y)
        cores_vertices: array (3, 3) com as cores RGB dos 3 vértices
        buffer_cor: matriz de pixels (altura, largura, 3) onde os pixels são gravados
    """
    pts = triangulo_2d
    a, b, c = pts[0], pts[1], pts[2]
    c_a, c_b, c_c = cores_vertices[0], cores_vertices[1], cores_vertices[2]

    # Bounding box do triângulo limitada pelas dimensões do buffer
    min_x = max(0, int(np.floor(np.min(pts[:, 0]))))
    max_x = min(largura - 1, int(np.ceil(np.max(pts[:, 0]))))
    min_y = max(0, int(np.floor(np.min(pts[:, 1]))))
    max_y = min(altura - 1, int(np.ceil(np.max(pts[:, 1]))))

    # Algoritmo Scanline para cada linha y
    arestas = [(a, b), (b, c), (c, a)]

    for y in range(min_y, max_y + 1):
        intersecoes_x = []
        for p0, p1 in arestas:
            x_a, y_a = p0[0], p0[1]
            x_b, y_b = p1[0], p1[1]

            # Ignora arestas horizontais
            if y_a == y_b:
                continue

            # Regra de borda: y_min <= y < y_max (para evitar contagem dupla de vértices)
            if (y_a <= y < y_b) or (y_b <= y < y_a):
                # Interseção da reta com a linha horizontal y
                t = (y - y_a) / (y_b - y_a)
                x_inter = x_a + t * (x_b - x_a)
                intersecoes_x.append(x_inter)

        intersecoes_x.sort()

        # Preenchimento entre pares de interseções (par-ímpar)
        for i in range(0, len(intersecoes_x) - 1, 2):
            x_start = max(min_x, int(np.ceil(intersecoes_x[i])))
            x_end = min(max_x, int(np.floor(intersecoes_x[i + 1])))

            for x in range(x_start, x_end + 1):
                # Interpolação de cor via coordenadas baricêntricas
                l0, l1, l2 = baricentricas((x, y), a, b, c)
                # Verifica se o ponto está dentro do triângulo (com pequena tolerância)
                if l0 >= -1e-4 and l1 >= -1e-4 and l2 >= -1e-4:
                    cor_interpolada = l0 * c_a + l1 * c_b + l2 * c_c
                    buffer_cor[y, x] = np.clip(cor_interpolada, 0.0, 1.0)


def mapear_viewport(
    pontos_2d: np.ndarray,
    largura: int,
    altura: int,
    xmin: float = -3.0,
    xmax: float = 3.0,
    ymin: float = -3.0,
    ymax: float = 3.0,
) -> np.ndarray:
    """
    Mapeia coordenadas contínuas da janela de projeção para coordenadas inteiras de viewport/tela.
    """
    sx = (largura - 1) / (xmax - xmin)
    sy = (altura - 1) / (ymax - ymin)

    px = (pontos_2d[:, 0] - xmin) * sx
    # Inverte o eixo Y para o padrão de imagens de topo para baixo
    py = (ymax - pontos_2d[:, 1]) * sy
    return np.column_stack([px, py])


if __name__ == "__main__":
    # Teste unitário de Bresenham
    reta = bresenham(0, 0, 5, 2)
    print("Bresenham testado. Pixels:", reta)

    # Teste de baricêntricas
    b = baricentricas((0.2, 0.2), (0, 0), (1, 0), (0, 1))
    print("Baricêntricas testadas:", b)
