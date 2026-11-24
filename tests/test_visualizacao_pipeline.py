import os
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

PROJETO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJETO_DIR not in sys.path:
    sys.path.insert(0, PROJETO_DIR)

import main
import visualizacao_pipeline
from cena import montar_cena
from iluminacao import phong


class TestVisualizacaoPipeline(unittest.TestCase):
    def _assert_png_valido(self, caminho: str) -> None:
        self.assertTrue(os.path.isfile(caminho), f"Arquivo não encontrado: {caminho}")
        self.assertGreater(os.path.getsize(caminho), 0, f"Arquivo vazio: {caminho}")
        with Image.open(caminho) as img:
            largura, altura = img.size
            self.assertGreater(largura, 0)
            self.assertGreater(altura, 0)

    def test_phong_retornar_componentes_shapes_e_limites(self) -> None:
        cena = montar_cena()
        luz_pos = [0.0, 10.0, 5.0]
        eye_pos = [12.0, 8.0, 14.0]

        for solido in cena:
            n_vertices = len(solido["vertices"])
            i_tot, i_amb, i_dif, i_esp = phong(
                solido,
                luz_pos=luz_pos,
                eye_pos=eye_pos,
                retornar_componentes=True,
            )
            for nome_comp, arr in (
                ("I_total", i_tot),
                ("I_amb", i_amb),
                ("I_dif", i_dif),
                ("I_esp", i_esp),
            ):
                with self.subTest(solido=solido["nome"], componente=nome_comp):
                    self.assertEqual(arr.shape, (n_vertices, 3))
                    self.assertTrue(np.all(arr >= 0.0))
                    self.assertTrue(np.all(arr <= 1.0))

    def test_render_componentes_phong_distintos_e_validacao(self) -> None:
        modos = ("ambiente", "difusa", "especular", "total")
        imagens = {
            modo: main.render(resolucao=(60, 60), componente_phong=modo)
            for modo in modos
        }

        for modo, img in imagens.items():
            self.assertEqual(img.shape, (60, 60, 3))

        for idx_a in range(len(modos)):
            for idx_b in range(idx_a + 1, len(modos)):
                modo_a = modos[idx_a]
                modo_b = modos[idx_b]
                self.assertFalse(
                    np.array_equal(imagens[modo_a], imagens[modo_b]),
                    f"As imagens de '{modo_a}' e '{modo_b}' não deveriam ser idênticas.",
                )

        with self.assertRaises(ValueError):
            main.render(resolucao=(40, 40), componente_phong="invalido")

    def test_render_salvar_caminho_sem_diretorio_pai(self) -> None:
        cwd_original = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                os.chdir(tmp_dir)
                img = main.render(
                    resolucao=(40, 40),
                    salvar_caminho="render_sem_dir.png",
                )
                self.assertEqual(img.shape, (40, 40, 3))
                self._assert_png_valido(os.path.join(tmp_dir, "render_sem_dir.png"))
            finally:
                os.chdir(cwd_original)

    def test_gerar_figuras_pipeline_cria_todos_pngs_validos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            caminhos = visualizacao_pipeline.gerar_figuras_pipeline(
                diretorio_saida=tmp_dir,
                resolucoes=((60, 60), (90, 90), (120, 120)),
            )
            chaves_esperadas = {
                "fig_4a",
                "fig_5",
                "fig_6_resolucoes",
                "fig_6_eyes",
                "fig_6_res_60",
                "fig_6_res_90",
                "fig_6_res_120",
            }
            self.assertEqual(set(caminhos.keys()), chaves_esperadas)

            for chave, caminho in caminhos.items():
                with self.subTest(figura=chave):
                    self._assert_png_valido(caminho)


if __name__ == "__main__":
    unittest.main()
