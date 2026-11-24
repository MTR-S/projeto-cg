import copy
import os
import sys
import unittest
from unittest.mock import patch

import numpy as np

# Garante importação de `cena` quando executado de dentro ou fora de projeto-cg
PROJETO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJETO_DIR not in sys.path:
    sys.path.insert(0, PROJETO_DIR)

import cena


class TestCena(unittest.TestCase):
    def test_montar_cena_cinco_solidos_cores_e_normais_unitarias(self) -> None:
        solidos = cena.montar_cena()
        self.assertEqual(len(solidos), 5)

        nomes = [s["nome"] for s in solidos]
        self.assertEqual(nomes, ["esponja", "queijo", "prato", "rolo", "boia"])

        cores = [s["cor"] for s in solidos]
        self.assertEqual(len(set(cores)), 5)

        for solido in solidos:
            normais = solido["normais_faces"]
            comprimentos = np.linalg.norm(normais, axis=1)
            np.testing.assert_allclose(comprimentos, np.ones(len(normais)), atol=1e-12)

    def test_limites_coordenadas_mundo(self) -> None:
        solidos = cena.montar_cena()
        for solido in solidos:
            max_coord = float(np.max(np.abs(solido["vertices"])))
            self.assertLessEqual(max_coord, 10.0)

    def test_sem_intersecao_aabb_entre_pares(self) -> None:
        solidos = cena.montar_cena()
        bboxes = [cena.obter_bounding_box(s["vertices"]) for s in solidos]
        for i in range(len(bboxes)):
            for j in range(i + 1, len(bboxes)):
                self.assertFalse(
                    cena.verificar_intersecao_aabb(bboxes[i], bboxes[j]),
                    f"Interseção inesperada entre {solidos[i]['nome']} e {solidos[j]['nome']}",
                )

    def test_escala_invocada_com_fatores_positivos_em_montar_cena(self) -> None:
        with patch("cena.escala", wraps=cena.escala) as mock_escala:
            cena.montar_cena()
            self.assertGreaterEqual(mock_escala.call_count, 1)
            for call in mock_escala.call_args_list:
                sx, sy, sz = call.args
                self.assertGreater(sx, 0.0)
                self.assertGreater(sy, 0.0)
                self.assertGreater(sz, 0.0)

    def test_validar_cena_rejeita_coordenada_acima_de_10(self) -> None:
        solidos = cena.montar_cena()
        solidos_invalidos = copy.deepcopy(solidos)
        solidos_invalidos[0]["vertices"][0, 0] = 10.01

        with self.assertRaises(AssertionError):
            cena.validar_cena(solidos_invalidos)

    def test_validar_cena_rejeita_sobreposicao_aabb(self) -> None:
        solidos = cena.montar_cena()
        solidos_sobrepostos = copy.deepcopy(solidos)
        # Move os vértices do segundo sólido para coincidir com a AABB do primeiro
        solidos_sobrepostos[1]["vertices"] = solidos_sobrepostos[0]["vertices"].copy()

        with self.assertRaises(AssertionError):
            cena.validar_cena(solidos_sobrepostos)


if __name__ == "__main__":
    unittest.main()
