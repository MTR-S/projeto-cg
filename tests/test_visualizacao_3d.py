import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

PROJETO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJETO_DIR not in sys.path:
    sys.path.insert(0, PROJETO_DIR)

import main
import visualizacao_3d
from camera import obter_origem_mundo_na_camera


class TestVisualizacao3D(unittest.TestCase):
    def _assert_png_valido(self, caminho: str) -> None:
        self.assertTrue(os.path.isfile(caminho), f"Arquivo não encontrado: {caminho}")
        self.assertGreater(os.path.getsize(caminho), 0, f"Arquivo vazio: {caminho}")
        with Image.open(caminho) as img:
            largura, altura = img.size
            self.assertGreater(largura, 100)
            self.assertGreater(altura, 100)

    def test_gerar_figuras_3d_cria_quatro_pngs_validos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            caminhos = visualizacao_3d.gerar_figuras_3d(diretorio_saida=tmp_dir)
            self.assertEqual(set(caminhos.keys()), {"fig_1e", "fig_2b", "fig_3c", "fig_3e"})

            for chave, caminho in caminhos.items():
                with self.subTest(figura=chave):
                    self._assert_png_valido(caminho)

    def test_obter_origem_mundo_na_camera_invocada_em_camera_e_variacao_eye(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch(
                "visualizacao_3d.obter_origem_mundo_na_camera",
                wraps=obter_origem_mundo_na_camera,
            ) as mock_origem:
                visualizacao_3d.plotar_cena_camera(diretorio_saida=tmp_dir)
                self.assertEqual(mock_origem.call_count, 1)

                mock_origem.reset_mock()
                eyes = ((12.0, 8.0, 14.0), (-12.0, 8.0, 14.0), (0.0, 14.0, 16.0))
                visualizacao_3d.plotar_variacao_eye(eyes=eyes, diretorio_saida=tmp_dir)
                self.assertEqual(mock_origem.call_count, len(eyes))

    def test_plotar_cena_camera_gera_imagens_distintas_para_eyes_diferentes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            caminho_a = visualizacao_3d.plotar_cena_camera(
                eye=(12.0, 8.0, 14.0),
                diretorio_saida=tmp_dir,
                nome_arquivo="cam_a.png",
            )
            caminho_b = visualizacao_3d.plotar_cena_camera(
                eye=(-12.0, 8.0, 14.0),
                diretorio_saida=tmp_dir,
                nome_arquivo="cam_b.png",
            )

            with Image.open(caminho_a) as img_a:
                arr_a = np.array(img_a.convert("RGB"))
            with Image.open(caminho_b) as img_b:
                arr_b = np.array(img_b.convert("RGB"))

            self.assertEqual(arr_a.shape, arr_b.shape)
            self.assertFalse(
                np.array_equal(arr_a, arr_b),
                "As renderizações para eyes distintos não deveriam ser idênticas.",
            )

    def test_main_gerar_todas_figuras_e_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_fn, tempfile.TemporaryDirectory() as tmp_dir_cli:
            caminhos = main.gerar_todas_figuras(diretorio_saida=tmp_dir_fn)
            self.assertEqual(set(caminhos.keys()), {"fig_1e", "fig_2b", "fig_3c", "fig_3e"})
            for caminho in caminhos.values():
                self._assert_png_valido(caminho)

            resultado = subprocess.run(
                [sys.executable, "main.py", "--figuras", "--saida", tmp_dir_cli],
                cwd=PROJETO_DIR,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                resultado.returncode,
                0,
                f"CLI falhou:\nSTDOUT:\n{resultado.stdout}\nSTDERR:\n{resultado.stderr}",
            )
            for nome in (
                "fig_1e_solidos_isolados.png",
                "fig_2b_cena_mundo.png",
                "fig_3c_cena_camera.png",
                "fig_3e_variacao_eye.png",
            ):
                self._assert_png_valido(os.path.join(tmp_dir_cli, nome))


if __name__ == "__main__":
    unittest.main()
