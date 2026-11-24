import os
import sys
import unittest

import numpy as np

# Garante importação de `solidos` quando executado de dentro ou fora de projeto-cg
PROJETO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJETO_DIR not in sys.path:
    sys.path.insert(0, PROJETO_DIR)

from solidos import (
    criar_boia,
    criar_esponja,
    criar_prato,
    criar_queijo,
    criar_rolo,
)


def volume_assinado(vertices: np.ndarray, faces: np.ndarray) -> float:
    """Calcula o volume assinado via teorema da divergência."""
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    return float(np.sum(np.einsum("ij,ij->i", v0, np.cross(v1, v2))) / 6.0)


def normais_ccw(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Recalcula normais unitárias pela regra da mão direita (CCW)."""
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    n = np.cross(v1 - v0, v2 - v0)
    normas = np.linalg.norm(n, axis=1, keepdims=True)
    return n / normas


class TestSolidosOrientacaoENormais(unittest.TestCase):
    def _validar_contrato_basico(self, solido: dict, nome_esperado: str) -> None:
        chaves_obrigatorias = {
            "vertices",
            "faces",
            "arestas",
            "normais_faces",
            "cor",
            "nome",
        }
        self.assertTrue(chaves_obrigatorias.issubset(set(solido.keys())))
        self.assertEqual(solido["nome"], nome_esperado)
        self.assertIsInstance(solido["cor"], tuple)
        self.assertEqual(len(solido["cor"]), 3)
        for c in solido["cor"]:
            self.assertGreaterEqual(c, 0.0)
            self.assertLessEqual(c, 1.0)

        vertices = solido["vertices"]
        faces = solido["faces"]
        arestas = solido["arestas"]
        normais = solido["normais_faces"]

        self.assertEqual(vertices.dtype, np.float64)
        self.assertEqual(faces.dtype, np.int32)
        self.assertEqual(arestas.dtype, np.int32)
        self.assertEqual(normais.dtype, np.float64)

        self.assertEqual(vertices.ndim, 2)
        self.assertEqual(vertices.shape[1], 3)
        self.assertEqual(faces.ndim, 2)
        self.assertEqual(faces.shape[1], 3)
        self.assertEqual(arestas.ndim, 2)
        self.assertEqual(arestas.shape[1], 2)
        self.assertEqual(normais.shape, (len(faces), 3))

        # Normais unitárias (||n|| == 1) e consistentes com orientação CCW
        comprimentos = np.linalg.norm(normais, axis=1)
        np.testing.assert_allclose(comprimentos, np.ones(len(faces)), atol=1e-12)
        np.testing.assert_allclose(normais, normais_ccw(vertices, faces), atol=1e-12)

        # Malha fechada (cada meio-aresta (u, v) possui oposta (v, u))
        meio_arestas = set()
        for f in faces:
            for k in range(3):
                e = (int(f[k]), int(f[(k + 1) % 3]))
                self.assertNotIn(e, meio_arestas, f"Meio-aresta duplicada {e} em {nome_esperado}")
                meio_arestas.add(e)
        for u, v in meio_arestas:
            self.assertIn((v, u), meio_arestas, f"Borda aberta {(u, v)} em {nome_esperado}")

        # Volume assinado positivo (teorema da divergência)
        vol = volume_assinado(vertices, faces)
        self.assertGreater(vol, 0.0, f"Volume assinado deve ser > 0 em {nome_esperado}")

    def test_esponja(self) -> None:
        esponja = criar_esponja()
        self._validar_contrato_basico(esponja, "esponja")

        vertices = esponja["vertices"]
        faces = esponja["faces"]
        normais = esponja["normais_faces"]
        centro = np.mean(vertices, axis=0)
        centroides = np.mean(vertices[faces], axis=1)
        dots = np.einsum("ij,ij->i", centroides - centro, normais)
        self.assertTrue(np.all(dots > 0.0), f"Esponja com normais invertidas: {dots}")

    def test_queijo(self) -> None:
        queijo = criar_queijo()
        self._validar_contrato_basico(queijo, "queijo")

        vertices = queijo["vertices"]
        faces = queijo["faces"]
        normais = queijo["normais_faces"]
        centro = np.mean(vertices, axis=0)
        centroides = np.mean(vertices[faces], axis=1)
        dots = np.einsum("ij,ij->i", centroides - centro, normais)
        self.assertTrue(np.all(dots > 0.0), f"Queijo com normais invertidas: {dots}")

    def test_boia(self) -> None:
        R, r, n_u, n_v = 2.0, 0.7, 24, 16
        boia = criar_boia(R=R, r=r, n_u=n_u, n_v=n_v)
        self._validar_contrato_basico(boia, "boia")
        self.assertEqual(len(boia["faces"]), 2 * n_u * n_v)

        vertices = boia["vertices"]
        faces = boia["faces"]
        normais = boia["normais_faces"]
        centroides = np.mean(vertices[faces], axis=1)
        r_xz = np.hypot(centroides[:, 0], centroides[:, 2])
        centros_tubo = np.stack(
            [R * centroides[:, 0] / r_xz, np.zeros_like(r_xz), R * centroides[:, 2] / r_xz],
            axis=1,
        )
        dots = np.einsum("ij,ij->i", centroides - centros_tubo, normais)
        self.assertTrue(np.all(dots > 0.0), "Boia com normais apontando para dentro do tubo")

    def test_rolo(self) -> None:
        fatias = 20
        rolo = criar_rolo(fatias=fatias)
        self._validar_contrato_basico(rolo, "rolo")

        vertices = rolo["vertices"]
        faces = rolo["faces"]
        normais = rolo["normais_faces"]
        centroides = np.mean(vertices[faces], axis=1)

        # Seções sequenciais em rolo.py:
        # 0..20: tampa_esq (-X)
        # 20..60: haste_esq (radial YZ)
        # 60..100: degrau_esq (-X)
        # 100..140: corpo (radial YZ)
        # 140..180: degrau_dir (+X)
        # 180..220: haste_dir (radial YZ)
        # 220..240: tampa_dir (+X)
        n_tampa_esq = normais[:fatias]
        n_haste_esq = normais[fatias : 3 * fatias]
        c_haste_esq = centroides[fatias : 3 * fatias]
        n_degrau_esq = normais[3 * fatias : 5 * fatias]
        n_corpo = normais[5 * fatias : 7 * fatias]
        c_corpo = centroides[5 * fatias : 7 * fatias]
        n_degrau_dir = normais[7 * fatias : 9 * fatias]
        n_haste_dir = normais[9 * fatias : 11 * fatias]
        c_haste_dir = centroides[9 * fatias : 11 * fatias]
        n_tampa_dir = normais[11 * fatias : 12 * fatias]

        self.assertTrue(np.all(n_tampa_esq[:, 0] < -0.999))
        self.assertTrue(np.all(n_degrau_esq[:, 0] < -0.999))
        self.assertTrue(np.all(n_degrau_dir[:, 0] > 0.999))
        self.assertTrue(np.all(n_tampa_dir[:, 0] > 0.999))

        for n_sec, c_sec in [
            (n_haste_esq, c_haste_esq),
            (n_corpo, c_corpo),
            (n_haste_dir, c_haste_dir),
        ]:
            radial_dots = c_sec[:, 1] * n_sec[:, 1] + c_sec[:, 2] * n_sec[:, 2]
            self.assertTrue(np.all(radial_dots > 0.0))

    def test_prato(self) -> None:
        num_fatias = 24
        prato = criar_prato(num_fatias=num_fatias)
        self._validar_contrato_basico(prato, "prato")

        vertices = prato["vertices"]
        faces = prato["faces"]
        normais = prato["normais_faces"]
        centroides = np.mean(vertices[faces], axis=1)

        # Seções sequenciais em prato.py:
        # 0 .. num_fatias: fundo externo (-Y)
        # num_fatias .. 3*num_fatias: parede externa (+radial, -Y)
        # 3*num_fatias .. 5*num_fatias: borda superior (+Y)
        # 5*num_fatias .. 7*num_fatias: parede interna (-radial, +Y)
        # 7*num_fatias .. 8*num_fatias: fundo interno (+Y)
        s0 = num_fatias
        s1 = 3 * num_fatias
        s2 = 5 * num_fatias
        s3 = 7 * num_fatias
        s4 = 8 * num_fatias

        self.assertEqual(len(faces), s4)
        np.testing.assert_allclose(normais[:s0], np.tile([0.0, -1.0, 0.0], (s0, 1)), atol=1e-12)
        np.testing.assert_allclose(normais[s1:s2], np.tile([0.0, 1.0, 0.0], (s2 - s1, 1)), atol=1e-12)
        np.testing.assert_allclose(normais[s3:s4], np.tile([0.0, 1.0, 0.0], (s4 - s3, 1)), atol=1e-12)

        # Parede externa: radial > 0 e componente Y < 0
        c_ext = centroides[s0:s1]
        n_ext = normais[s0:s1]
        dots_ext = c_ext[:, 0] * n_ext[:, 0] + c_ext[:, 2] * n_ext[:, 2]
        self.assertTrue(np.all(dots_ext > 0.0))
        self.assertTrue(np.all(n_ext[:, 1] < 0.0))

        # Parede interna: voltada para a cavidade (radial < 0 e componente Y > 0)
        c_int = centroides[s2:s3]
        n_int = normais[s2:s3]
        dots_int = c_int[:, 0] * n_int[:, 0] + c_int[:, 2] * n_int[:, 2]
        self.assertTrue(np.all(dots_int < 0.0))
        self.assertTrue(np.all(n_int[:, 1] > 0.0))

    def test_prato_compatibilidade_e_validacao(self) -> None:
        # Chamada compatível com cena.py (sem passar espessura explicitamente)
        prato_cena = criar_prato(
            raio_base=1.2,
            raio_borda=2.4,
            altura=0.6,
            num_fatias=24,
            cor=(0.95, 0.95, 0.98),
        )
        self._validar_contrato_basico(prato_cena, "prato")

        # Proporção estreita e espessa não deve gerar volume negativo ou auto-interseção
        prato_extremo = criar_prato(
            raio_base=0.1,
            raio_borda=0.5,
            altura=0.4,
            espessura=0.35,
            num_fatias=16,
        )
        self._validar_contrato_basico(prato_extremo, "prato")

        # Validações de parâmetros inválidos
        with self.assertRaises(ValueError):
            criar_prato(espessura=0.0)
        with self.assertRaises(ValueError):
            criar_prato(altura=0.5, espessura=0.5)
        with self.assertRaises(ValueError):
            criar_prato(altura=0.5, espessura=0.7)
        with self.assertRaises(ValueError):
            criar_prato(raio_base=0.0, raio_borda=1.0)
        with self.assertRaises(ValueError):
            criar_prato(raio_base=2.0, raio_borda=2.0)
        with self.assertRaises(ValueError):
            criar_prato(raio_base=2.5, raio_borda=2.0)


if __name__ == "__main__":
    unittest.main()
