"""
Módulo de Composição da Cena no Sistema de Coordenadas do Mundo.
Responsável: Matheus
"""

import numpy as np
from solidos import (
    criar_esponja,
    criar_queijo,
    criar_prato,
    criar_boia,
    criar_rolo,
)
from transformacoes import (
    escala,
    rotacao_x,
    rotacao_y,
    rotacao_z,
    translacao,
    transformar_solido,
)


def obter_bounding_box(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Retorna os cantos mínimo e máximo (min_pt, max_pt) de um conjunto de vértices 3D."""
    return np.min(vertices, axis=0), np.max(vertices, axis=0)


def verificar_intersecao_aabb(box_a: tuple[np.ndarray, np.ndarray], box_b: tuple[np.ndarray, np.ndarray]) -> bool:
    """Verifica se há sobreposição entre duas Axis-Aligned Bounding Boxes."""
    min_a, max_a = box_a
    min_b, max_b = box_b
    return (
        (min_a[0] <= max_b[0] and max_a[0] >= min_b[0]) and
        (min_a[1] <= max_b[1] and max_a[1] >= min_b[1]) and
        (min_a[2] <= max_b[2] and max_a[2] >= min_b[2])
    )


def montar_cena() -> list[dict]:
    """
    Instancia e posiciona os 5 sólidos no sistema de coordenadas do mundo.
    
    Regras satisfeitas:
    1. Máximo valor absoluto de qualquer componente <= 10 (|x|, |y|, |z| <= 10).
    2. Objetos distribuídos sem sobreposição ou intersecção física (validação AABB).
    3. Cada sólido recebe uma cor distinta.
    """
    # 1. Esponja (amarela/esverdeada) - quadrante superior esquerdo
    esponja = criar_esponja(largura=2.6, altura=1.0, profundidade=1.8, cor=(0.85, 0.85, 0.15))
    m_esponja = translacao(-6.0, 5.0, -2.0) @ rotacao_y(np.radians(20)) @ escala(1.15, 1.2, 1.1)
    esponja_mundo = transformar_solido(esponja, m_esponja)

    # 2. Fatia de queijo (alaranjado) - quadrante inferior esquerdo
    queijo = criar_queijo(raio=2.2, angulo_graus=50.0, altura=1.0, cor=(1.0, 0.65, 0.0))
    m_queijo = translacao(-6.0, -4.0, 2.0) @ rotacao_y(np.radians(45))
    queijo_mundo = transformar_solido(queijo, m_queijo)

    # 3. Prato (cinza claro / cerâmica) - centro inferior
    prato = criar_prato(raio_base=1.2, raio_borda=2.4, altura=0.6, num_fatias=24, cor=(0.95, 0.95, 0.98))
    m_prato = translacao(0.0, -4.0, 0.0)
    prato_mundo = transformar_solido(prato, m_prato)

    # 4. Rolo de massa (madeira clara) - centro superior
    rolo = criar_rolo(raio_rolo=0.7, comp_rolo=2.8, raio_haste=0.25, comp_haste=0.8, cor=(0.76, 0.58, 0.40))
    m_rolo = translacao(0.0, 5.0, 0.0) @ rotacao_z(np.radians(15))
    rolo_mundo = transformar_solido(rolo, m_rolo)

    # 5. Boia de piscina (azul ciano) - lado direito
    boia = criar_boia(R=1.8, r=0.6, n_u=20, n_v=14, cor=(0.1, 0.7, 0.9))
    m_boia = translacao(6.0, 0.0, 0.0) @ rotacao_x(np.radians(70))
    boia_mundo = transformar_solido(boia, m_boia)

    cena = [esponja_mundo, queijo_mundo, prato_mundo, rolo_mundo, boia_mundo]

    # Validação automática das restrições do professor
    validar_cena(cena)
    return cena


def validar_cena(cena: list[dict]) -> None:
    """Verifica os limites de coordenadas (|coord| <= 10) e a não sobreposição das AABBs."""
    bboxes = []
    for solido in cena:
        v = solido["vertices"]
        max_coord = np.max(np.abs(v))
        assert max_coord <= 10.0, f"Objeto {solido['nome']} excedeu o limite de 10: {max_coord:.2f}"
        bboxes.append((solido["nome"], obter_bounding_box(v)))

    # Testa pares de bounding boxes
    n = len(bboxes)
    for i in range(n):
        for j in range(i + 1, n):
            nome_a, box_a = bboxes[i]
            nome_b, box_b = bboxes[j]
            intersecao = verificar_intersecao_aabb(box_a, box_b)
            assert not intersecao, f"Sobreposição detectada entre {nome_a} e {nome_b}!"


if __name__ == "__main__":
    cena = montar_cena()
    print("Cena montada e validada com sucesso!")
    for s in cena:
        min_pt, max_pt = obter_bounding_box(s["vertices"])
        print(f" - {s['nome']:8s} | BBox Min: {np.round(min_pt, 2)} | BBox Max: {np.round(max_pt, 2)}")
