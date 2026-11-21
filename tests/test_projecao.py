import os
import sys
import unittest

import numpy as np

# Garante importação dos módulos do projeto quando executado de dentro ou fora de projeto-cg
PROJETO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJETO_DIR not in sys.path:
    sys.path.insert(0, PROJETO_DIR)

from camera import camera, transformar_para_camera
from projecao import descartar_faces_ocultas, projetar
from solidos import criar_boia, criar_queijo


def _criar_solido_triangulo(vertices: np.ndarray, normal: list[float]) -> dict:
    """Cria um sólido de teste com uma única face triangular e normal unitária."""
    n = np.array(normal, dtype=np.float64)
    n = n / np.linalg.norm(n)
    return {
        "vertices": np.array(vertices, dtype=np.float64),
        "faces": np.array([[0, 1, 2]], dtype=np.int32),
        "arestas": np.array([[0, 1], [1, 2], [2, 0]], dtype=np.int32),
        "normais_faces": np.array([n], dtype=np.float64),
        "cor": (1.0, 1.0, 1.0),
        "nome": "triangulo_teste",
    }


class TestProjecaoClippingECulling(unittest.TestCase):
    def test_validacao_parametros_near_far(self) -> None:
        solido = _criar_solido_triangulo(
            [[0.0, 0.0, -5.0], [1.0, 0.0, -5.0], [0.0, 1.0, -5.0]],
            normal=[0.0, 0.0, 1.0],
        )
        with self.assertRaises(ValueError):
            projetar(solido, near=0.0, far=10.0)
        with self.assertRaises(ValueError):
            projetar(solido, near=-1.0, far=10.0)
        with self.assertRaises(ValueError):
            projetar(solido, near=5.0, far=5.0)
        with self.assertRaises(ValueError):
            projetar(solido, near=10.0, far=5.0)

    def test_descarta_faces_atras_da_camera(self) -> None:
        # Face inteiramente atrás da câmera (z > 0) com normal voltada para a origem
        # para passar pelo produto escalar do culling e ser barrada pelo clipping.
        atras = _criar_solido_triangulo(
            [[0.0, 0.0, 4.0], [1.0, 0.0, 4.0], [0.0, 1.0, 4.0]],
            normal=[0.0, 0.0, -1.0],
        )
        pts, vis = projetar(atras, d=2.0, near=0.5, far=100.0)
        self.assertEqual(len(vis), 0)
        self.assertTrue(np.all(np.isnan(pts)))

        # Face com vértice exatamente em z == 0
        no_olho = _criar_solido_triangulo(
            [[0.0, 0.0, 0.0], [1.0, 0.0, -2.0], [0.0, 1.0, -2.0]],
            normal=[0.0, 0.0, 1.0],
        )
        _, vis_olho = projetar(no_olho, d=2.0, near=0.5, far=100.0)
        self.assertEqual(len(vis_olho), 0)

        # Face cruzando z = 0 (um vértice atrás da câmera, dois na frente)
        cruzando = _criar_solido_triangulo(
            [[0.0, 0.0, 1.0], [1.0, 0.0, -5.0], [0.0, 1.0, -5.0]],
            normal=[0.0, 0.0, 1.0],
        )
        _, vis_cruzando = projetar(cruzando, d=2.0, near=0.5, far=100.0)
        self.assertEqual(len(vis_cruzando), 0)

    def test_descarta_faces_mais_proximas_que_near(self) -> None:
        # Todos os vértices entre -near e 0 (-near < z < 0)
        muito_perto = _criar_solido_triangulo(
            [[0.0, 0.0, -0.4], [1.0, 0.0, -0.3], [0.0, 1.0, -0.2]],
            normal=[0.0, 0.0, 1.0],
        )
        _, vis = projetar(muito_perto, d=1.0, near=0.5, far=100.0)
        self.assertEqual(len(vis), 0)

        # Apenas um vértice violando o plano near
        parcial_perto = _criar_solido_triangulo(
            [[0.0, 0.0, -0.49], [1.0, 0.0, -2.0], [0.0, 1.0, -2.0]],
            normal=[0.0, 0.0, 1.0],
        )
        _, vis_parcial = projetar(parcial_perto, d=1.0, near=0.5, far=100.0)
        self.assertEqual(len(vis_parcial), 0)

    def test_descarta_faces_alem_de_far(self) -> None:
        # Todos os vértices além de far (z < -far)
        muito_longe = _criar_solido_triangulo(
            [[0.0, 0.0, -101.0], [1.0, 0.0, -105.0], [0.0, 1.0, -120.0]],
            normal=[0.0, 0.0, 1.0],
        )
        _, vis = projetar(muito_longe, d=1.0, near=0.5, far=100.0)
        self.assertEqual(len(vis), 0)

        # Apenas um vértice além do plano far
        parcial_longe = _criar_solido_triangulo(
            [[0.0, 0.0, -10.0], [1.0, 0.0, -10.0], [0.0, 1.0, -10.5]],
            normal=[0.0, 0.0, 1.0],
        )
        _, vis_parcial = projetar(parcial_longe, d=1.0, near=0.5, far=10.0)
        self.assertEqual(len(vis_parcial), 0)

    def test_mantem_faces_no_frustum_e_projeta_valores_exatos(self) -> None:
        d = 2.5
        near = 1.0
        far = 20.0
        solido = {
            "vertices": np.array(
                [
                    [-2.0, 4.0, -5.0],    # 0: dentro
                    [3.0, -6.0, -10.0],   # 1: dentro
                    [1.0, 2.0, -1.0],     # 2: exatamente em -near
                    [-4.0, -8.0, -20.0],  # 3: exatamente em -far
                    [0.0, 0.0, 2.0],      # 4: atrás da câmera (não referenciado em face visível)
                ],
                dtype=np.float64,
            ),
            "faces": np.array(
                [
                    [0, 1, 2],  # face visível dentro de [-far, -near]
                    [0, 3, 1],  # face visível tocando -far
                    [0, 1, 4],  # face parcialmente atrás da câmera -> descartada
                ],
                dtype=np.int32,
            ),
            "arestas": np.array([[0, 1], [1, 2], [2, 0]], dtype=np.int32),
            "normais_faces": np.array(
                [
                    [0.0, 0.0, 1.0],
                    [0.0, 0.0, 1.0],
                    [0.0, 0.0, 1.0],
                ],
                dtype=np.float64,
            ),
            "cor": (0.5, 0.5, 0.5),
            "nome": "multi_faces",
        }

        pontos_2d, faces_visiveis = projetar(solido, d=d, near=near, far=far)
        self.assertEqual(faces_visiveis.shape, (2, 3))
        np.testing.assert_array_equal(faces_visiveis, np.array([[0, 1, 2], [0, 3, 1]], dtype=np.int32))

        # Nenhum vértice referenciado pelas faces visíveis pode ser NaN ou inf
        pts_referenciados = pontos_2d[faces_visiveis]
        self.assertTrue(np.all(np.isfinite(pts_referenciados)))

        # Valores esperados: xp = d * x / (-z), yp = d * y / (-z)
        esperado = np.array(
            [
                [d * (-2.0) / 5.0, d * 4.0 / 5.0],
                [d * 3.0 / 10.0, d * (-6.0) / 10.0],
                [d * 1.0 / 1.0, d * 2.0 / 1.0],
                [d * (-4.0) / 20.0, d * (-8.0) / 20.0],
            ],
            dtype=np.float64,
        )
        np.testing.assert_allclose(pontos_2d[:4], esperado, atol=1e-12)

    def test_descarta_face_se_projecao_resultar_nao_finita(self) -> None:
        # Mesmo com near > 0 muito pequeno (ex: 1e-6), z = -1e-6 cai no limite de
        # segurança z < -1e-5 e produz NaN em pontos_2d; a face não deve ser retornada.
        muito_proximo_zero = _criar_solido_triangulo(
            [[0.0, 0.0, -1e-6], [1.0, 0.0, -1.0], [0.0, 1.0, -1.0]],
            normal=[0.0, 0.0, 1.0],
        )
        pts, vis = projetar(muito_proximo_zero, d=1.0, near=1e-7, far=10.0)
        self.assertEqual(len(vis), 0)
        self.assertTrue(np.isnan(pts[0]).all())

    def test_backface_culling_queijo_e_boia_de_frente(self) -> None:
        _, _, _, matriz_visao = camera(eye=[0.0, 0.0, 10.0], at=[0.0, 0.0, 0.0])

        for solido in (criar_queijo(), criar_boia()):
            with self.subTest(solido=solido["nome"]):
                solido_cam = transformar_para_camera(solido, matriz_visao)
                idx_vis = descartar_faces_ocultas(solido_cam)
                pts_2d, faces_vis = projetar(solido_cam, d=2.0, near=0.5, far=100.0)

                total_faces = len(solido_cam["faces"])
                self.assertGreater(len(faces_vis), 0)
                self.assertLess(len(faces_vis), total_faces)
                self.assertEqual(len(faces_vis), len(idx_vis))

                # Todas as faces mantidas devem estar voltadas para a câmera (dot < 0)
                vertices = solido_cam["vertices"]
                faces = solido_cam["faces"]
                normais = solido_cam["normais_faces"]
                baricentros = (
                    vertices[faces[:, 0]] + vertices[faces[:, 1]] + vertices[faces[:, 2]]
                ) / 3.0
                dots = np.sum(normais * baricentros, axis=1)

                self.assertTrue(np.all(dots[idx_vis] < 0.0))

                mask_ocultas = np.ones(total_faces, dtype=bool)
                mask_ocultas[idx_vis] = False
                self.assertTrue(np.all(dots[mask_ocultas] >= 0.0))

                # Todos os vértices referenciados pelas faces visíveis devem ser finitos
                self.assertTrue(np.all(np.isfinite(pts_2d[faces_vis])))


if __name__ == "__main__":
    unittest.main()
