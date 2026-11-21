import os
import sys
import unittest
from unittest.mock import patch

import numpy as np

# Garante importação dos módulos do projeto quando executado de dentro ou fora de projeto-cg
PROJETO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJETO_DIR not in sys.path:
    sys.path.insert(0, PROJETO_DIR)

import main
import rasterizacao
from camera import camera, transformar_para_camera
from cena import montar_cena
from projecao import projetar
from rasterizacao import (
    baricentricas,
    bresenham,
    desenhar_arestas_bresenham,
    mapear_viewport,
    preencher_par_impar,
)


class TestZBufferEBresenham(unittest.TestCase):
    def test_oclusao_z_buffer_nas_duas_ordens(self) -> None:
        largura, altura = 40, 40
        tri_proximo = np.array([[5.0, 5.0], [35.0, 5.0], [20.0, 35.0]], dtype=np.float64)
        tri_distante = np.array([[5.0, 5.0], [35.0, 5.0], [20.0, 35.0]], dtype=np.float64)

        cor_a = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        cor_b = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        cores_a = np.tile(cor_a, (3, 1))
        cores_b = np.tile(cor_b, (3, 1))

        z_proximo = np.array([2.0, 2.0, 2.0], dtype=np.float64)
        z_distante = np.array([5.0, 5.0, 5.0], dtype=np.float64)

        # Ordem 1: próximo primeiro, depois distante
        buf1 = np.zeros((altura, largura, 3), dtype=np.float64)
        zbuf1 = np.full((altura, largura), np.inf, dtype=np.float64)
        preencher_par_impar(
            tri_proximo, cores_a, largura, altura, buf1, z_vertices=z_proximo, z_buffer=zbuf1
        )
        preencher_par_impar(
            tri_distante, cores_b, largura, altura, buf1, z_vertices=z_distante, z_buffer=zbuf1
        )

        # Ordem 2: distante primeiro, depois próximo
        buf2 = np.zeros((altura, largura, 3), dtype=np.float64)
        zbuf2 = np.full((altura, largura), np.inf, dtype=np.float64)
        preencher_par_impar(
            tri_distante, cores_b, largura, altura, buf2, z_vertices=z_distante, z_buffer=zbuf2
        )
        preencher_par_impar(
            tri_proximo, cores_a, largura, altura, buf2, z_vertices=z_proximo, z_buffer=zbuf2
        )

        # Ponto interno comum (20, 15) deve manter cor A e z=2.0 em ambas as ordens
        np.testing.assert_allclose(buf1[15, 20], cor_a)
        np.testing.assert_allclose(buf2[15, 20], cor_a)
        self.assertAlmostEqual(zbuf1[15, 20], 2.0)
        self.assertAlmostEqual(zbuf2[15, 20], 2.0)
        np.testing.assert_allclose(buf1, buf2)

    def test_preencher_par_impar_retrocompatibilidade_sem_zbuffer(self) -> None:
        largura, altura = 20, 20
        tri = np.array([[2.0, 2.0], [18.0, 2.0], [10.0, 18.0]], dtype=np.float64)
        cores_a = np.tile([1.0, 0.0, 0.0], (3, 1))
        cores_b = np.tile([0.0, 1.0, 0.0], (3, 1))
        buf = np.zeros((altura, largura, 3), dtype=np.float64)

        preencher_par_impar(tri, cores_a, largura, altura, buf)
        preencher_par_impar(tri, cores_b, largura, altura, buf)
        np.testing.assert_allclose(buf[8, 10], np.array([0.0, 1.0, 0.0]))

    def test_desenhar_arestas_bresenham_usa_bresenham_e_desenha_pixels(self) -> None:
        largura, altura = 30, 30
        tri = np.array([[2.0, 3.0], [20.0, 7.0], [10.0, 24.0]], dtype=np.float64)
        cor_aresta = (0.2, 0.8, 0.4)
        buf = np.zeros((altura, largura, 3), dtype=np.float64)

        with patch("rasterizacao.bresenham", wraps=bresenham) as mock_bresenham:
            desenhar_arestas_bresenham(tri, cor_aresta, largura, altura, buf)
            self.assertEqual(mock_bresenham.call_count, 3)

        for i0, i1 in ((0, 1), (1, 2), (2, 0)):
            x0, y0 = int(round(tri[i0, 0])), int(round(tri[i0, 1]))
            x1, y1 = int(round(tri[i1, 0])), int(round(tri[i1, 1]))
            for px, py in bresenham(x0, y0, x1, y1):
                np.testing.assert_allclose(buf[py, px], np.array(cor_aresta))

    def test_desenhar_arestas_bresenham_respeita_limites_da_tela(self) -> None:
        largura, altura = 20, 20
        tri_fora = np.array([[-10.0, -5.0], [30.0, 10.0], [10.0, 35.0]], dtype=np.float64)
        buf = np.zeros((altura, largura, 3), dtype=np.float64)
        zbuf = np.full((altura, largura), np.inf, dtype=np.float64)
        z_vert = np.array([3.0, 3.0, 3.0], dtype=np.float64)

        desenhar_arestas_bresenham(
            tri_fora, (1.0, 0.5, 0.0), largura, altura, buf, z_vertices=z_vert, z_buffer=zbuf
        )
        self.assertTrue(np.any(buf > 0.0))

    def test_desenhar_arestas_bresenham_respeita_z_buffer(self) -> None:
        largura, altura = 30, 30
        tri_proximo = np.array([[4.0, 4.0], [26.0, 4.0], [15.0, 26.0]], dtype=np.float64)
        cor_proximo = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        cores_proximo = np.tile(cor_proximo, (3, 1))
        z_proximo = np.array([2.0, 2.0, 2.0], dtype=np.float64)

        buf = np.zeros((altura, largura, 3), dtype=np.float64)
        zbuf = np.full((altura, largura), np.inf, dtype=np.float64)
        preencher_par_impar(
            tri_proximo, cores_proximo, largura, altura, buf, z_vertices=z_proximo, z_buffer=zbuf
        )

        # Aresta distante cruzando o interior do triângulo próximo em y=10
        tri_distante = np.array([[5.0, 10.0], [25.0, 10.0], [15.0, 20.0]], dtype=np.float64)
        z_distante = np.array([6.0, 6.0, 6.0], dtype=np.float64)
        cor_distante = (0.0, 1.0, 0.0)

        desenhar_arestas_bresenham(
            tri_distante,
            cor_distante,
            largura,
            altura,
            buf,
            z_vertices=z_distante,
            z_buffer=zbuf,
        )

        # Pixels sobrepostos pelo triângulo próximo mantêm cor_proximo
        np.testing.assert_allclose(buf[10, 15], cor_proximo)
        self.assertAlmostEqual(zbuf[10, 15], 2.0)

    def test_oclusao_z_buffer_triangulos_cruzando_profundidade_duas_ordens(self) -> None:
        largura, altura = 30, 30
        tri = np.array([[0.0, 0.0], [20.0, 0.0], [10.0, 20.0]], dtype=np.float64)
        cor_a = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        cor_b = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        cores_a = np.tile(cor_a, (3, 1))
        cores_b = np.tile(cor_b, (3, 1))

        # Triângulos que se cruzam ao longo de X (esquerda: A < B; direita: B < A)
        z_a = np.array([1.0, 9.0, 5.0], dtype=np.float64)
        z_b = np.array([9.0, 1.0, 5.0], dtype=np.float64)

        buf1 = np.zeros((altura, largura, 3), dtype=np.float64)
        zbuf1 = np.full((altura, largura), np.inf, dtype=np.float64)
        preencher_par_impar(tri, cores_a, largura, altura, buf1, z_vertices=z_a, z_buffer=zbuf1)
        preencher_par_impar(tri, cores_b, largura, altura, buf1, z_vertices=z_b, z_buffer=zbuf1)

        buf2 = np.zeros((altura, largura, 3), dtype=np.float64)
        zbuf2 = np.full((altura, largura), np.inf, dtype=np.float64)
        preencher_par_impar(tri, cores_b, largura, altura, buf2, z_vertices=z_b, z_buffer=zbuf2)
        preencher_par_impar(tri, cores_a, largura, altura, buf2, z_vertices=z_a, z_buffer=zbuf2)

        np.testing.assert_allclose(zbuf1, zbuf2)
        # Fora da linha de empate exato (x=10, onde z_A == z_B == 5.0), ambas as ordens são idênticas
        mascara_sem_empate = np.ones((altura, largura), dtype=bool)
        mascara_sem_empate[:, 10] = False
        np.testing.assert_allclose(buf1[mascara_sem_empate], buf2[mascara_sem_empate])

        # Lado esquerdo (x=4, y=4): triângulo A é mais próximo
        l0, l1, l2 = baricentricas((4, 4), tri[0], tri[1], tri[2])
        expected_z_esq = l0 * z_a[0] + l1 * z_a[1] + l2 * z_a[2]
        np.testing.assert_allclose(buf1[4, 4], cor_a)
        np.testing.assert_allclose(buf2[4, 4], cor_a)
        self.assertAlmostEqual(zbuf1[4, 4], expected_z_esq)

        # Lado direito (x=16, y=4): triângulo B é mais próximo
        l0, l1, l2 = baricentricas((16, 4), tri[0], tri[1], tri[2])
        expected_z_dir = l0 * z_b[0] + l1 * z_b[1] + l2 * z_b[2]
        np.testing.assert_allclose(buf1[4, 16], cor_b)
        np.testing.assert_allclose(buf2[4, 16], cor_b)
        self.assertAlmostEqual(zbuf1[4, 16], expected_z_dir)

    def test_desenhar_arestas_bresenham_coordenadas_continuas_sem_auto_oclusao(self) -> None:
        largura, altura = 30, 30
        tri = np.array([[10.49, 10.0], [20.49, 10.0], [15.49, 20.0]], dtype=np.float64)
        z = np.array([10.0, 12.0, 11.0], dtype=np.float64)
        cores = np.tile([0.2, 0.2, 0.2], (3, 1))
        cor_aresta = np.array([1.0, 0.0, 0.0], dtype=np.float64)

        buf = np.zeros((altura, largura, 3), dtype=np.float64)
        zbuf = np.full((altura, largura), np.inf, dtype=np.float64)

        preencher_par_impar(tri, cores, largura, altura, buf, z_vertices=z, z_buffer=zbuf)
        desenhar_arestas_bresenham(
            tri, cor_aresta, largura, altura, buf, z_vertices=z, z_buffer=zbuf
        )

        # Aresta (0, 1) com endpoints contínuos (10.49->20.49) e aresta (2, 0) não sofrem auto-oclusão
        for i0, i1 in ((0, 1), (2, 0)):
            x0, y0 = int(round(tri[i0, 0])), int(round(tri[i0, 1]))
            x1, y1 = int(round(tri[i1, 0])), int(round(tri[i1, 1]))
            for px, py in bresenham(x0, y0, x1, y1):
                np.testing.assert_allclose(buf[py, px], cor_aresta)

    def test_triangulo_degenerado_colinear_nao_corrompe_zbuffer(self) -> None:
        largura, altura = 25, 25
        tri_colinear = np.array([[10.0, 5.0], [10.0, 15.0], [10.0, 10.0]], dtype=np.float64)
        cores = np.tile([1.0, 0.0, 0.0], (3, 1))
        z_vert = np.array([2.0, 3.0, 2.5], dtype=np.float64)

        buf = np.zeros((altura, largura, 3), dtype=np.float64)
        zbuf = np.full((altura, largura), np.inf, dtype=np.float64)

        preencher_par_impar(
            tri_colinear, cores, largura, altura, buf, z_vertices=z_vert, z_buffer=zbuf
        )

        self.assertTrue(np.all(np.isinf(zbuf)))
        np.testing.assert_allclose(buf, 0.0)

    def test_nan_em_z_vertices_nao_sobrescreve_buffers(self) -> None:
        largura, altura = 25, 25
        tri = np.array([[4.0, 4.0], [20.0, 4.0], [12.0, 20.0]], dtype=np.float64)
        cor_base = np.array([0.3, 0.6, 0.9], dtype=np.float64)
        cores_base = np.tile(cor_base, (3, 1))
        z_valido = np.array([4.0, 4.0, 4.0], dtype=np.float64)

        buf = np.zeros((altura, largura, 3), dtype=np.float64)
        zbuf = np.full((altura, largura), np.inf, dtype=np.float64)
        preencher_par_impar(
            tri, cores_base, largura, altura, buf, z_vertices=z_valido, z_buffer=zbuf
        )

        buf_antes = buf.copy()
        zbuf_antes = zbuf.copy()

        z_nan_parcial = np.array([np.nan, 1.0, 1.0], dtype=np.float64)
        z_nan_total = np.array([np.nan, np.nan, np.nan], dtype=np.float64)
        cores_nan = np.tile([1.0, 0.0, 0.0], (3, 1))
        preencher_par_impar(
            tri, cores_nan, largura, altura, buf, z_vertices=z_nan_parcial, z_buffer=zbuf
        )
        desenhar_arestas_bresenham(
            tri, (1.0, 1.0, 0.0), largura, altura, buf, z_vertices=z_nan_total, z_buffer=zbuf
        )

        self.assertFalse(np.any(np.isnan(zbuf)))
        np.testing.assert_allclose(buf, buf_antes)
        np.testing.assert_allclose(zbuf, zbuf_antes)


class TestPipelineRenderViewport(unittest.TestCase):
    def test_render_viewport_sem_cortes_e_cinco_solidos_visiveis(self) -> None:
        largura, altura = 200, 200
        d_proj = 1.8
        cor_fundo = np.array([0.05, 0.05, 0.05])

        for eye in [(12.0, 8.0, 14.0), (14.0, 10.0, 14.0)]:
            with self.subTest(eye=eye):
                with patch(
                    "main.desenhar_arestas_bresenham",
                    wraps=rasterizacao.desenhar_arestas_bresenham,
                ) as mock_arestas:
                    img = main.render(eye=eye, resolucao=(largura, altura), d_proj=d_proj)
                    self.assertGreater(mock_arestas.call_count, 0)

                self.assertEqual(img.shape, (altura, largura, 3))
                self.assertTrue(np.all(np.isfinite(img)))
                self.assertTrue(np.all((img >= 0.0) & (img <= 1.0)))

                cena = montar_cena()
                _, _, _, M_vis = camera(eye=eye, at=(0.0, 0.0, 0.0), up=(0.0, 1.0, 0.0))

                for solido in cena:
                    solido_cam = transformar_para_camera(solido, M_vis)
                    pts_2d, faces_vis = projetar(solido_cam, d=d_proj)
                    self.assertGreater(len(faces_vis), 0, f"{solido['nome']} sem faces visíveis")

                    pts_tela = mapear_viewport(
                        pts_2d, largura, altura, xmin=-1.0, xmax=1.0, ymin=-1.0, ymax=1.0
                    )
                    pts_vis = pts_tela[np.unique(faces_vis)]

                    # Todos os vértices das faces visíveis dentro da viewport [0, W-1] x [0, H-1]
                    self.assertTrue(
                        np.all(pts_vis[:, 0] >= 0.0) and np.all(pts_vis[:, 0] <= largura - 1),
                        f"Corte horizontal em {solido['nome']} para eye={eye}",
                    )
                    self.assertTrue(
                        np.all(pts_vis[:, 1] >= 0.0) and np.all(pts_vis[:, 1] <= altura - 1),
                        f"Corte vertical em {solido['nome']} para eye={eye}",
                    )

                    # Deve haver pixels não-fundo na bounding box projetada de cada sólido
                    x0 = max(0, int(np.floor(pts_vis[:, 0].min())))
                    x1 = min(largura - 1, int(np.ceil(pts_vis[:, 0].max())))
                    y0 = max(0, int(np.floor(pts_vis[:, 1].min())))
                    y1 = min(altura - 1, int(np.ceil(pts_vis[:, 1].max())))

                    regiao = img[y0 : y1 + 1, x0 : x1 + 1]
                    pixels_nao_fundo = np.any(np.abs(regiao - cor_fundo) > 1e-6, axis=2)
                    self.assertTrue(
                        np.any(pixels_nao_fundo),
                        f"Nenhum pixel renderizado na região de {solido['nome']} para eye={eye}",
                    )


if __name__ == "__main__":
    unittest.main()
