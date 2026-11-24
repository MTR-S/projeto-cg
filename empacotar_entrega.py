"""
Empacotador da entrega oficial em .zip para o Trabalho de Computação Gráfica (IFCE 2026.2).

Inclui apenas código-fonte limpo (*.py da raiz, solidos/*.py, tests/*.py),
README.md e requirements.txt, excluindo artefatos temporários, cache e saídas.
"""

from __future__ import annotations

import os
from pathlib import Path
import zipfile

ARQUIVOS_OBRIGATORIOS_ZIP: tuple[str, ...] = (
    "main.py",
    "requirements.txt",
    "README.md",
    "solidos/__init__.py",
    "solidos/esponja.py",
    "solidos/queijo.py",
    "solidos/prato.py",
    "solidos/boia.py",
    "solidos/rolo.py",
)

DIRETORIOS_EXCLUIDOS: set[str] = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "outputs",
    "docs",
}

EXTENSOES_EXCLUIDAS: tuple[str, ...] = (".pyc", ".pyo", ".zip")


def _eh_entrada_proibida(caminho_posix: str) -> bool:
    """Verifica se um caminho relativo POSIX pertence a diretório ou extensão proibida."""
    partes = caminho_posix.split("/")
    if any(parte in DIRETORIOS_EXCLUIDOS for parte in partes[:-1]):
        return True
    if any(parte in DIRETORIOS_EXCLUIDOS for parte in partes):
        return True
    nome_lower = caminho_posix.lower()
    return nome_lower.endswith(EXTENSOES_EXCLUIDAS)


def _coletar_arquivos_entrega(diretorio_raiz: Path) -> list[tuple[Path, str]]:
    """
    Seleciona os arquivos limpos permitidos para o pacote de entrega:
    - *.py na raiz
    - README.md e requirements.txt na raiz
    - solidos/*.py
    - tests/*.py
    """
    raiz = diretorio_raiz.resolve()
    selecionados: list[tuple[Path, str]] = []

    for arquivo in sorted(raiz.iterdir()):
        if arquivo.is_file() and (
            arquivo.suffix == ".py" or arquivo.name in {"README.md", "requirements.txt"}
        ):
            rel = arquivo.name
            if not _eh_entrada_proibida(rel):
                selecionados.append((arquivo, rel))

    for subpasta in ("solidos", "tests"):
        pasta = raiz / subpasta
        if pasta.is_dir():
            for arquivo in sorted(pasta.iterdir()):
                if arquivo.is_file() and arquivo.suffix == ".py":
                    rel = f"{subpasta}/{arquivo.name}"
                    if not _eh_entrada_proibida(rel):
                        selecionados.append((arquivo, rel))

    return selecionados


def validar_zip(caminho_zip: str) -> list[str]:
    """
    Valida a integridade, presença dos arquivos obrigatórios e ausência de
    arquivos/diretórios proibidos no arquivo .zip gerado.
    """
    if not os.path.isfile(caminho_zip):
        raise FileNotFoundError(f"Arquivo zip não encontrado: {caminho_zip}")

    with zipfile.ZipFile(caminho_zip, "r") as zf:
        arquivo_corrompido = zf.testzip()
        if arquivo_corrompido is not None:
            raise zipfile.BadZipFile(
                f"Arquivo corrompido detectado no zip: {arquivo_corrompido}"
            )
        entradas = zf.namelist()

    conjunto_entradas = set(entradas)
    faltantes = [
        req for req in ARQUIVOS_OBRIGATORIOS_ZIP if req not in conjunto_entradas
    ]
    if faltantes:
        raise ValueError(
            f"Arquivos obrigatórios ausentes no zip: {', '.join(faltantes)}"
        )

    proibidas = [e for e in entradas if _eh_entrada_proibida(e)]
    if proibidas:
        raise ValueError(
            f"Entradas proibidas encontradas no zip: {', '.join(proibidas)}"
        )

    return entradas


def empacotar_codigo(
    diretorio_raiz: str = ".",
    caminho_zip: str = "entrega_projeto_cg.zip",
) -> str:
    """
    Cria o pacote .zip contendo exclusivamente os arquivos-fonte limpos do projeto
    e valida seu conteúdo antes de retornar o caminho absoluto gerado.
    """
    raiz = Path(diretorio_raiz).resolve()
    if not raiz.is_dir():
        raise NotADirectoryError(f"Diretório raiz inválido: {diretorio_raiz}")

    zip_abs = os.path.abspath(caminho_zip)
    dir_pai = os.path.dirname(zip_abs)
    if dir_pai:
        os.makedirs(dir_pai, exist_ok=True)

    arquivos = _coletar_arquivos_entrega(raiz)
    with zipfile.ZipFile(zip_abs, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for caminho_real, caminho_posix in arquivos:
            zf.write(caminho_real, arcname=caminho_posix)

    validar_zip(zip_abs)
    return zip_abs


if __name__ == "__main__":
    zip_gerado = empacotar_codigo()
    entradas_zip = validar_zip(zip_gerado)
    tamanho_kb = os.path.getsize(zip_gerado) / 1024.0
    print(f"Pacote gerado com sucesso: {zip_gerado} ({tamanho_kb:.1f} KB)")
    print(f"Total de arquivos incluídos ({len(entradas_zip)}):")
    for entrada in entradas_zip:
        print(f" - {entrada}")
