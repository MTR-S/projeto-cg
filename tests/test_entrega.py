import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

from PIL import Image

PROJETO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJETO_DIR not in sys.path:
    sys.path.insert(0, PROJETO_DIR)

import empacotar_entrega
import gerar_relatorio

FIGURAS_ESPERADAS = {
    "fig_1e": "fig_1e_solidos_isolados.png",
    "fig_2b": "fig_2b_cena_mundo.png",
    "fig_3c": "fig_3c_cena_camera.png",
    "fig_3e": "fig_3e_variacao_eye.png",
    "fig_4a": "fig_4a_projecao_3d_2d.png",
    "fig_5": "fig_5_iluminacao_phong.png",
    "fig_6_resolucoes": "fig_6_rasterizacao_resolucoes.png",
    "fig_6_eyes": "fig_6_variacao_eye_raster.png",
}


class TestEntregaERelatorio(unittest.TestCase):
    def test_html_relatorio_contem_secoes_obrigatorias(self) -> None:
        metricas = gerar_relatorio.coletar_dados_estaticos_pipeline()
        metricas["tempos_resolucoes"] = {
            "200x200": 0.12,
            "400x400": 0.48,
            "800x800": 1.92,
        }

        outputs_dir = os.path.join(PROJETO_DIR, "outputs")
        caminhos_outputs = {
            chave: os.path.join(outputs_dir, nome)
            for chave, nome in FIGURAS_ESPERADAS.items()
        }
        usar_outputs = all(os.path.isfile(p) for p in caminhos_outputs.values())

        with tempfile.TemporaryDirectory() as tmp_dir:
            if usar_outputs:
                caminhos_figuras = caminhos_outputs
            else:
                caminhos_figuras = {}
                for idx, (chave, nome) in enumerate(FIGURAS_ESPERADAS.items(), start=1):
                    caminho_png = os.path.join(tmp_dir, nome)
                    img = Image.new("RGB", (64, 64), color=(20 * idx, 80, 140))
                    img.save(caminho_png, format="PNG")
                    caminhos_figuras[chave] = caminho_png

            html_str = gerar_relatorio.montar_html_relatorio(metricas, caminhos_figuras)

        secoes_obrigatorias = (
            "IFCE",
            "1. Introdução",
            "2. Objetivo",
            "3. Desenvolvimento",
            "4. Simulações Computacionais",
            "5. Conclusão",
            "6. Referências",
        )
        for secao in secoes_obrigatorias:
            with self.subTest(secao=secao):
                self.assertIn(secao, html_str)

        for solido in ("Esponja", "Queijo", "Prato", "Rolo", "Boia"):
            with self.subTest(solido=solido):
                self.assertIn(solido, html_str)

        self.assertEqual(html_str.count("data:image/png;base64,"), 8)
        html_sem_b64 = re.sub(r"data:image/png;base64,[A-Za-z0-9+/=]+", "", html_str)
        self.assertNotIn("None", html_sem_b64)

    def test_relatorio_pdf_existe_e_valido(self) -> None:
        if os.environ.get("CG_EMPACOTAMENTO_SUBPROCESS") == "1":
            self.skipTest("Diretório docs/ é excluído intencionalmente do .zip limpo.")

        caminho_pdf = os.path.join(PROJETO_DIR, "docs", "relatorio_trabalho_cg.pdf")
        self.assertTrue(
            os.path.isfile(caminho_pdf),
            f"Relatório PDF não encontrado em: {caminho_pdf}",
        )
        tamanho = os.path.getsize(caminho_pdf)
        self.assertGreater(
            tamanho,
            50_000,
            f"Relatório PDF menor que o esperado ({tamanho} bytes).",
        )
        with open(caminho_pdf, "rb") as f:
            self.assertEqual(f.read(5), b"%PDF-")

    def test_empacotar_codigo_e_executar_zip_limpo(self) -> None:
        if os.environ.get("CG_EMPACOTAMENTO_SUBPROCESS") == "1":
            self.skipTest("Evita recursão infinita dentro do subprocesso extraído.")

        with tempfile.TemporaryDirectory() as tmp_zip_dir, tempfile.TemporaryDirectory() as tmp_extract_dir:
            zip_path = os.path.join(tmp_zip_dir, "entrega_teste.zip")
            gerado = empacotar_entrega.empacotar_codigo(PROJETO_DIR, zip_path)
            self.assertTrue(os.path.isfile(gerado))

            entradas = empacotar_entrega.validar_zip(gerado)
            self.assertIn("gerar_relatorio.py", entradas)
            self.assertIn("empacotar_entrega.py", entradas)
            for entrada in entradas:
                self.assertNotIn("__pycache__", entrada)
                self.assertFalse(entrada.endswith(".pyc"))
                self.assertFalse(entrada.startswith(".git/"))
                self.assertFalse(entrada.startswith("outputs/"))
                self.assertFalse(entrada.startswith("docs/"))

            with zipfile.ZipFile(gerado, "r") as zf:
                zf.extractall(tmp_extract_dir)

            res_main = subprocess.run(
                [sys.executable, "main.py"],
                cwd=tmp_extract_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(res_main.returncode, 0)

            env_sub = os.environ.copy()
            env_sub["CG_EMPACOTAMENTO_SUBPROCESS"] = "1"
            res_tests = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                cwd=tmp_extract_dir,
                env=env_sub,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(res_tests.returncode, 0)


if __name__ == "__main__":
    unittest.main()
